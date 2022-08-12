"""The njsPC-HA integration."""
from __future__ import annotations

import logging

import socketio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import aiohttp_client

from .const import (
    API_CONFIG_BODY,
    API_CONFIG_CIRCUIT,
    API_CONFIG_HEATERS,
    API_HEATMODES,
    API_LIGHTTHEMES,
    API_STATE_ALL,
    API_LIGHTCOMMANDS,
    DOMAIN,
    EVENT_AVAILABILITY,
    EVENT_BODY,
    EVENT_CHLORINATOR,
    EVENT_CIRCUIT,
    EVENT_CIRCUITGROUP,
    EVENT_FEATURE,
    EVENT_LIGHTGROUP,
    EVENT_PUMP,
)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.LIGHT,
    Platform.BUTTON
]


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up njsPC-HA from a config entry."""
    # TODO Store an API object for your platforms to access

    api = NjsPCHAapi(hass, entry.data)
    await api.get_config()

    coordinator = NjsPCHAdata(hass, api)
    await coordinator.sio_connect()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def _async_sio_close(_: Event) -> None:
        await coordinator.sio_close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_sio_close)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        hass.async_create_task(coordinator.sio_close())

    return unload_ok


class NjsPCHAdata(DataUpdateCoordinator):
    """Data coordinator for receiving from nodejs-PoolController"""

    def __init__(self, hass: HomeAssistant, api: NjsPCHAapi):
        """Initialize data coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
        )
        self.api = api
        self.sio = None

    async def sio_connect(self):
        """Method to connect to nodejs-PoolController"""
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=1,
            reconnection_delay_max=10,
            logger=False,
            engineio_logger=False,
        )

        @self.sio.on("temps")
        async def handle_temps(data):
            data["event"] = "temps"
            self.async_set_updated_data(data)

        @self.sio.on("pump")
        async def handle_pump(data):
            data["event"] = EVENT_PUMP
            self.async_set_updated_data(data)

        @self.sio.on("circuit")
        async def handle_circuit(data):
            data["event"] = EVENT_CIRCUIT
            self.async_set_updated_data(data)

        @self.sio.on("chlorinator")
        async def handle_chlorinator(data):
            data["event"] = EVENT_CHLORINATOR
            self.async_set_updated_data(data)

        @self.sio.on("body")
        async def handle_body(data):
            data["event"] = EVENT_BODY
            self.async_set_updated_data(data)

        @self.sio.on("lightGroup")
        async def handle_lightgroup(data):
            data["event"] = EVENT_LIGHTGROUP
            self.async_set_updated_data(data)

        @self.sio.on("circuitGroup")
        async def handle_circuitgroup(data):
            data["event"] = EVENT_CIRCUITGROUP
            self.async_set_updated_data(data)

        @self.sio.on("feature")
        async def handle_feature(data):
            data["event"] = EVENT_FEATURE
            self.async_set_updated_data(data)

        @self.sio.event
        async def connect():
            print("I'm connected!")
            avail = {"event": EVENT_AVAILABILITY, "available": True}
            self.async_set_updated_data(avail)
            self.logger.debug(f"SocketIO connect to {self.api._base_url}")

        @self.sio.event
        async def connect_error(data):
            avail = {"event": EVENT_AVAILABILITY, "available": False}
            self.async_set_updated_data(avail)
            self.logger.error(f"SocketIO connection error: {data}")
            print("The connection failed!")

        @self.sio.event
        async def disconnect():
            avail = {"event": EVENT_AVAILABILITY, "available": False}
            self.async_set_updated_data(avail)
            self.logger.debug(f"SocketIO disconnect to {self.api._base_url}")
            print("I'm disconnected!")

        await self.sio.connect(self.api._base_url)

    async def sio_close(self):
        await self.sio.disconnect()


class NjsPCHAapi:
    """API for sending data to nodejs-PoolController"""

    def __init__(self, hass: HomeAssistant, data) -> None:
        self.hass = hass
        self.data = data
        self._base_url = f"http://{data[CONF_HOST]}:{data[CONF_PORT]}"
        self._config = None
        self._session = None

    async def command(self, url: str, data):
        """Send commands to nodejs-PoolController via PUT request"""
        async with self._session.put(f"{self._base_url}/{url}", json=data) as resp:
            if resp.status == 200:
                pass
            else:
                _LOGGER.error(await resp.text())

    async def get_config(self):
        """Let the initial config from nodejs-PoolController"""
        self._session = aiohttp_client.async_get_clientsession(self.hass)
        async with self._session.get(f"{self._base_url}/{API_STATE_ALL}") as resp:
            if resp.status == 200:
                self._config = await resp.json()
            else:
                _LOGGER.error(await resp.text())

    async def get_heatmodes(self, id):
        """Get the available heat modes for body"""
        async with self._session.get(
            f"{self._base_url}/{API_CONFIG_BODY}/{id}/{API_HEATMODES}"
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                _LOGGER.error(await resp.text())
                return

    async def get_lightthemes(self, id):
        """Get list of themes for light"""
        async with self._session.get(
            f"{self._base_url}/{API_CONFIG_CIRCUIT}/{id}/{API_LIGHTTHEMES}"
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                _LOGGER.error(await resp.text())
                return

    async def get_lightcommands(self, id):
        """Get light commands for lights"""
        async with self._session.get(
            f"{self._base_url}/{API_CONFIG_CIRCUIT}/{id}/{API_LIGHTCOMMANDS}"
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                _LOGGER.error(await resp.text())
                return

    async def has_cooling(self, body) -> bool:
        """Check to see if any of the heaters have cooling enabled"""
        _has_cooling: bool = False
        async with self._session.get(f"{self._base_url}/{API_CONFIG_HEATERS}") as resp:
            if resp.status == 200:
                data = await resp.json()
                for heater in data["heaters"]:
                    if "coolingEnabled" in heater:
                        # only run if cooling enabled is a key
                        if body == 0:
                            if (
                                heater["body"] == 0 or heater["body"] == 32
                            ) and "coolingEnabled" in heater:
                                _has_cooling = (
                                    True
                                    if heater["coolingEnabled"] is True
                                    else _has_cooling
                                )

                        else:
                            if heater["body"] == 1 or heater["body"] == 32:
                                _has_cooling = (
                                    True
                                    if heater["coolingEnabled"] is True
                                    else _has_cooling
                                )
                return _has_cooling

            else:
                _LOGGER.error(await resp.text())
                return _has_cooling

    def get_unique_id(self, name) -> str:
        """Create a unique id for entity"""
        _id = f'{self.data[CONF_HOST].replace(".", "")}{self.data[CONF_PORT]}_{name.lower()}'
        return _id
