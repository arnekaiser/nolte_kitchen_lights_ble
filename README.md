# Nolte Kitchen Lights BLE
Unoffical Home Assistant integration for Nolte kitchen lights with LED-Emotion-Bluetooth-Modul

## Installation 
This integration needs to be installed manually. Copy the folder `nolte_kitchen_lights_ble` into the `custom_components` folder of your Home Assistant instance.

## Usage
First, you need to determine the MAC address of the light controller. This can be done using an app like **nRF Connect**. Look for a device named **"Quintic BLE"**.  

Once you have the MAC address, add the light controller to your `configuration.yaml`:  

```
light:
  - platform: nolte_kitchen_lights_ble
    name: "Kitchen light"
    mac: "XX:XX:XX:XX:XX:XX"
```
