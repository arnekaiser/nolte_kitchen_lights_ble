from __future__ import annotations

import logging

from .nolte_kitchen_lights import NolteKitchenLightsInstance
import voluptuous as vol

from pprint import pformat

import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, 
    ATTR_COLOR_TEMP_KELVIN,
    PLATFORM_SCHEMA, 
    ColorMode, 
    LightEntity
)
from homeassistant.const import CONF_NAME, CONF_MAC
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_MAC): cv.string,
})

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    LOGGER.info(pformat(config))
    
    light = {
        "name": config[CONF_NAME],
        "mac": config[CONF_MAC]
    }
    
    add_entities([KitchenLight(light, hass)])

class KitchenLight(LightEntity):
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = { ColorMode.COLOR_TEMP }
    _attr_min_color_temp_kelvin = 2000
    _attr_max_color_temp_kelvin = 6500

    def __init__(self, light, hass) -> None:
        LOGGER.info(pformat(light))
        self._light = NolteKitchenLightsInstance(
            light["mac"], 
            hass, 
            self._attr_min_color_temp_kelvin, 
            self._attr_max_color_temp_kelvin
        )
        self._name = light["name"]
        self._state = None
        self._brightness = None
        self._color_temp_kelvin = None

    @property
    def unique_id(self):
        return f"nolte_kitchen_light_{ self._light.mac.replace(':', '_').lower() }"

    @property
    def device_info(self):
        return {
            "identifiers": { ("nolte_kitchen_lights_ble", self._light.mac) },
            "name": self._name,
            "manufacturer": "Nolte",
            "model": "LED-Emotion-Bluetooth-Modul",
        }

    @property
    def name(self) -> str:
        return self._name

    @property
    def brightness(self) -> int | None:
        return self._brightness

    @property
    def color_temp_kelvin(self) -> int | None:
        return self._color_temp_kelvin

    @property
    def is_on(self) -> bool | None:
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:   
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs.get(ATTR_BRIGHTNESS)

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._color_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
            
        await self._light.turn_on(self._brightness, self._color_temp_kelvin)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._light.turn_off()

    def update(self) -> None:
        self._state = self._light.is_on
        self._brightness = self._light.brightness
        self._color_temp_kelvin = self._light.color_temp_kelvin