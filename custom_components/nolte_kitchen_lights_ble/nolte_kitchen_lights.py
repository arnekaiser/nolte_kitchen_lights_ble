import asyncio
import logging

from bleak import BleakClient, BleakError
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

SERVICE_UUID = "0000cc02-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000ee03-0000-1000-8000-00805f9b34fb"
COMMAND_UUID = "0000ee02-0000-1000-8000-00805f9b34fb"
READ_UUID = "0000ee01-0000-1000-8000-00805f9b34fb"

LOGGER = logging.getLogger(__name__)

class NolteKitchenLightsInstance:
    def __init__(self, mac: str, hass: HomeAssistant, kelvin_min: int, kelvin_max: int) -> None:
        self._mac = mac
        self._hass = hass
        self._device = None
        self._client = None
        self._is_on = None
        self._brightness = 254
        self._kelvin_min = kelvin_min
        self._kelvin_max = kelvin_max
        self._color_temp_kelvin = (kelvin_min + kelvin_max) / 2 
        self._is_initialized = False

        self._hass.add_job(self.init_lights())

    async def get_device(self):
        scanner = bluetooth.async_get_scanner(self._hass)
        self._device = await scanner.find_device_by_address(self._mac)

    async def init_lights(self):
        await self.connect()
        try:
            if self._client is None or self._client.services is None:
                return
            for service in self._client.services:
                if service.uuid == SERVICE_UUID:
                    for char in service.characteristics:
                        if char.uuid == READ_UUID:
                            await self._client.start_notify(char.uuid, self.on_start_notify)
                            await self._client.write_gatt_char(COMMAND_UUID, bytes.fromhex('73656c66'))
            self._is_initialized = True
        except (BleakError) as error:
            LOGGER.warning(f'Cannot init: {error}')
            
    async def _send(self, data: bytearray) -> bool:
        if self._is_initialized:
            await self.connect()
        else:
            await self.init_lights()
            
        if self._client is not None and self._client.is_connected:
            await self._client.write_gatt_char(WRITE_UUID, data)
            return True
        else: 
            return False

    @property
    def mac(self):
        return self._mac

    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        return self._brightness

    @property
    def color_temp_kelvin(self):
        return self._color_temp_kelvin

    async def turn_on(self, brightness: int, color_temp_kelvin: int):
        if brightness is not None:
            self._brightness = brightness
        if color_temp_kelvin is not None:
            self._color_temp_kelvin = color_temp_kelvin
        if await self._send(self.get_command(self._brightness, self._color_temp_kelvin)):
            self._is_on = True

    async def turn_off(self):
        if await self._send(self.get_command(0, 0)):
            self._is_on = False

    async def connect(self):
        LOGGER.debug('Trying to connect ...')
        if self._device is None:
            await self.get_device()
        
        if self._device is not None and self._client is None:
            self._client = BleakClient(
                self._device, 
                disconnected_callback = self.on_disconnect
            )
    
        if self._client is None:
            LOGGER.debug('Cannot connect: client is none')
            return

        if self._client.is_connected:
            LOGGER.debug('Already connected')
        else:
            try:
                await self._client.connect()
                LOGGER.debug('Connected')
            except (BleakError, asyncio.TimeoutError) as error:
                self._client = None
                self._is_initialized = False
                LOGGER.warning(f'Cannot connect: {error}')

    async def disconnect(self):
        if self._client.is_connected:
            try:
                await self._client.disconnect()
            except BleakError as error:
                LOGGER.warning(f'Cannot disconnect: {error}')
        self._client = None

    async def reconnect(self):
        await asyncio.sleep(3)
        await self.connect()
        
    def on_disconnect(self, client):
        LOGGER.debug('Disconnected')
        self._client = None
        self._hass.add_job(self.reconnect())

    def on_start_notify(self, sender, data):
        LOGGER.debug(f'Start notify done. Sender: {sender} data: {data}')

    def get_command(self, brightness: int, color_temp_kelvin: int):
        brightness = min(brightness, 254)
        warm_brightness = int((1.0 - (float(color_temp_kelvin - self._kelvin_min) / float(self._kelvin_max - self._kelvin_min))) * 254.0)
        warm_white = int(((254 - warm_brightness) / 254.0) * brightness)
        cold_white = int((warm_brightness / 254.0) * brightness)
        return bytes.fromhex("0202") + warm_white.to_bytes() + cold_white.to_bytes()