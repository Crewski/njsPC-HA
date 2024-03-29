# njsPC-HA
njsPC-HA is a custom integration for [Home Assistant](https://www.home-assistant.io/) to interact with [nodejs-PoolController](https://github.com/tagyoureit/nodejs-poolController).

# Requirement
Due to how Home Assistant changed the number entity, Home Assistant 2022.7.0 or greater is required (only applies to pools with a SWG).

# Installation

## HACS (preferred)
Add the respository URL as a custom [repository integration](https://hacs.xyz/docs/faq/custom_repositories).

## Manual
Copy the njspc_ha folder from this repo to config/custom_components (create custom_components folder if it doesn't exist already)

## Setup
Once njsPC-HA is installed, you can set it up by adding it as an integration.  The integration should automatically find the instance of nodejs-poolcontroller for you.  It it doesn't, it'll prompt you to enter the IP address and port (default 4200).


# Data
njsPC-HA communicates with nodejs-PoolController via the native API, the same way dashPanel works.  This removes the need for MQTT.  If the data connection is lost, the entities in Home Assistant will go unavailable.  njsPC-HA will try to reconnect until the connection is established again.  Data for things like light shows and heater options are pulled directly from nodejs-PoolController so should stay up to date with any changes.

## Supported
- Temperatures
- Pumps
    - RPM
    - Watts
    - Flow
    - Status
- Lights
    - light shows / colors show up as effects in Home Assistant
- Circuits
- Features
- Light Groups
- Circuit Groups
- Heaters
    - Cooling options are supported
    - If there are only 2 options (off/heat) then the climate modes will reflect that.  If there are more options like `solar preferred` or `heat pump only`, the climate mode will be `AUTO` and the different options will be presets.
- SWG
    - Setpoints per body
    - Current output
    - Super chlorinate
    - Super chlorinate duration (hrs)
    - Salt level
        - Salt target and salt needed are attributes
    - Status
    - Salt Target
    - Salt Needed
- pH/Orp
- Schedules (toggle)
- Chem Controllers
- Filters

# EVENT BUS
If there is something in nodejs-PoolController that isn't in njsPC-HA, you can maninpulate the data yourself.  All incoming data is sent to the Home Assistant event bus under the event `njspc-ha_event`.  You can subscribe and view these events in the `EVENTS` tab in `Developer Tools`.  The event topic is found in `data.evt` and the data is `data.data`.  These are the same messages that Dashpanel receives which you can view them by using the developer console on your browser.  If you find something you think should be added to this integration, just let us know.

# Home Assistant
![Home Assistant](/images/lovelace.png)
![SWG](/images/swg.png)
![Colorlogic Lights](/images/light.png)
![Heater](/images/heater.png)
