"""The njsPC-HA integration."""
from __future__ import annotations

import asyncio
import logging
import random

import aiohttp
import socketio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, Event
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers import aiohttp_client


PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.LIGHT,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
]
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
    EVENT_CHEM_CONTROLLER,
    EVENT_CIRCUIT,
    EVENT_CIRCUITGROUP,
    EVENT_CONTROLLER,
    EVENT_FEATURE,
    EVENT_LIGHTGROUP,
    EVENT_PUMP,
    EVENT_PUMP_EXT,
    EVENT_FILTER,
    EVENT_VIRTUAL_CIRCUIT,
    EVENT_TEMPS,
    EVENT_SCHEDULE,
    RECONNECT_INITIAL_DELAY,
    RECONNECT_MAX_DELAY,
    RECONNECT_BACKOFF_MULTIPLIER,
    RECONNECT_JITTER_FACTOR,
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up njsPC-HA from a config entry."""

    api = NjsPCHAapi(hass, entry.data)
    try:
        await api.get_initial()
    except Exception as err:
        raise ConfigEntryNotReady(
            f"Unable to connect to njsPC at {api.get_base_url()}: {err}"
        ) from err

    if api.config is None:
        raise ConfigEntryNotReady(
            f"Unable to retrieve config from njsPC at {api.get_base_url()}"
        )

    coordinator = NjsPCHAdata(hass, api)
    try:
        await coordinator.sio_connect()
    except Exception as err:
        _LOGGER.warning(
            "Socket.IO initial connection failed, will retry in background: %s", err
        )
        coordinator.start_reconnect_loop()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
        await coordinator.sio_close()

    return unload_ok


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    return True


class NjsPCHAdata(DataUpdateCoordinator):
    """Data coordinator for receiving from nodejs-PoolController"""

    def __init__(self, hass: HomeAssistant, api: NjsPCHAapi) -> None:
        """Initialize data coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
        )
        self.api = api
        self.sio = None
        self.model = api.config["model"]
        self.version = "Unknown"
        # Cache this off so the creation of entities is faster
        self.controller_id = api.get_controller_id()
        if "appVersionState" in api.config:
            self.version = f'{api.config["appVersionState"]["installed"]} ({api.config["appVersionState"]["gitLocalBranch"]}-{api.config["appVersionState"]["gitLocalCommit"][-7:]})'

        # Reconnection state
        self._reconnect_task: asyncio.Task | None = None
        self._unloading: bool = False

    def _register_sio_handlers(self):
        """Register Socket.IO event handlers on the current client."""

        @self.sio.on("temps")
        async def handle_temps(data):
            data["event"] = EVENT_TEMPS
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("pump")
        async def handle_pump(data):
            data["event"] = EVENT_PUMP
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("pumpExt")
        async def handle_pump_ext(data):
            data["event"] = EVENT_PUMP_EXT
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("circuit")
        async def handle_circuit(data):
            data["event"] = EVENT_CIRCUIT
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("chlorinator")
        async def handle_chlorinator(data):
            data["event"] = EVENT_CHLORINATOR
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("chemController")
        async def handle_chem_controller(data):
            data["event"] = EVENT_CHEM_CONTROLLER
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("body")
        async def handle_body(data):
            data["event"] = EVENT_BODY
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("lightGroup")
        async def handle_lightgroup(data):
            data["event"] = EVENT_LIGHTGROUP
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("circuitGroup")
        async def handle_circuitgroup(data):
            data["event"] = EVENT_CIRCUITGROUP
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("feature")
        async def handle_feature(data):
            data["event"] = EVENT_FEATURE
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("controller")
        async def handle_controller(data):
            data["event"] = EVENT_CONTROLLER
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("filter")
        async def handle_filter(data):
            data["event"] = EVENT_FILTER
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("virtualCircuit")
        async def handle_virtual_circuit(data):
            data["event"] = EVENT_VIRTUAL_CIRCUIT
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.on("schedule")
        async def handle_schedule(data):
            data["event"] = EVENT_SCHEDULE
            self.async_set_updated_data(data)
            self.send_to_bus(data)

        @self.sio.event
        async def connect():
            _LOGGER.info("Socket.IO connected to %s", self.api.get_base_url())
            avail = {"event": EVENT_AVAILABILITY, "available": True}
            self.async_set_updated_data(avail)

        @self.sio.event
        async def connect_error(data):
            _LOGGER.error("Socket.IO connection error: %s", data)
            avail = {"event": EVENT_AVAILABILITY, "available": False}
            self.async_set_updated_data(avail)

        @self.sio.event
        async def disconnect():
            _LOGGER.warning(
                "Socket.IO disconnected from %s", self.api.get_base_url()
            )
            avail = {"event": EVENT_AVAILABILITY, "available": False}
            self.async_set_updated_data(avail)
            if not self._unloading:
                self.start_reconnect_loop()

    async def sio_connect(self):
        """Create a Socket.IO client and connect to njsPC."""
        self.sio = socketio.AsyncClient(
            reconnection=False,
            logger=False,
            engineio_logger=False,
        )
        # Suppress socketio/engineio library logging
        logging.getLogger("socketio.client").setLevel(logging.ERROR)
        logging.getLogger("engineio.client").setLevel(logging.ERROR)

        self._register_sio_handlers()
        await self.sio.connect(self.api.get_base_url())

    def start_reconnect_loop(self):
        """Start the reconnection loop if not already running."""
        if self._reconnect_task is not None and not self._reconnect_task.done():
            _LOGGER.debug("Reconnect loop already running, not starting another")
            return
        if self._unloading:
            _LOGGER.debug("Unloading in progress, not starting reconnect loop")
            return
        _LOGGER.info("Starting reconnection loop to %s", self.api.get_base_url())
        self._reconnect_task = self.hass.async_create_task(
            self._reconnect_loop()
        )

    async def _reconnect_loop(self):
        """Repeatedly attempt to reconnect with exponential backoff."""
        delay = RECONNECT_INITIAL_DELAY
        attempt = 0

        while not self._unloading:
            attempt += 1
            jitter = random.uniform(0, RECONNECT_JITTER_FACTOR * delay)
            actual_delay = delay + jitter
            _LOGGER.info(
                "Reconnect attempt %d in %.1f seconds (base delay: %ds)",
                attempt, actual_delay, delay,
            )

            try:
                await asyncio.sleep(actual_delay)
            except asyncio.CancelledError:
                _LOGGER.debug("Reconnect loop cancelled during sleep")
                return

            if self._unloading:
                return

            try:
                # Clean up old client
                await self._safe_disconnect()

                # Re-fetch state via HTTP
                _LOGGER.debug("Re-fetching state from %s", self.api.get_base_url())
                await self.api.get_initial()
                if self.api.config is None:
                    raise ConnectionError("Failed to fetch config (non-200 response)")

                # Create fresh Socket.IO client and connect
                await self.sio_connect()

                _LOGGER.info(
                    "Successfully reconnected to %s on attempt %d",
                    self.api.get_base_url(), attempt,
                )
                return

            except asyncio.CancelledError:
                _LOGGER.debug("Reconnect loop cancelled during connection attempt")
                return

            except Exception as err:
                _LOGGER.warning(
                    "Reconnect attempt %d failed: %s", attempt, err,
                )
                delay = min(delay * RECONNECT_BACKOFF_MULTIPLIER, RECONNECT_MAX_DELAY)

        _LOGGER.debug("Reconnect loop exiting (unloading=%s)", self._unloading)

    async def _safe_disconnect(self):
        """Safely disconnect the existing Socket.IO client, ignoring errors."""
        if self.sio is not None:
            try:
                if self.sio.connected:
                    await self.sio.disconnect()
            except Exception as err:
                _LOGGER.debug("Error disconnecting old Socket.IO client: %s", err)
            self.sio = None

    async def sio_close(self):
        """Close the connection to njsPC and stop reconnection."""
        self._unloading = True

        # Cancel the reconnect loop if running
        if self._reconnect_task is not None and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None

        await self._safe_disconnect()

    def send_to_bus(self, data):
        """Send incoming messages to HA event bus"""
        bus_data = {"evt": data["event"], "data": data}
        self.hass.bus.async_fire("njspc-ha_event", bus_data)


class NjsPCHAapi:
    """API for sending data to nodejs-PoolController"""

    def __init__(self, hass: HomeAssistant, data) -> None:
        self.hass = hass
        self.data = data
        self._base_url = f"http://{data[CONF_HOST]}:{data[CONF_PORT]}"
        self.config = None
        self._session = None
        self.model = "Unknown"
        self.version = "Unknown"

    def get_base_url(self):
        """Return the base url"""
        return self._base_url

    def get_config(self):
        """Return the initial config"""
        return self.config

    async def command(self, url: str, data):
        """Send commands to nodejs-PoolController via PUT request"""
        async with self._session.put(f"{self._base_url}/{url}", json=data) as resp:
            if resp.status == 200:
                pass
            else:
                _LOGGER.error(await resp.text())

    async def get_initial(self):
        """Get the initial config from nodejs-PoolController."""
        if self._session is None:
            self._session = aiohttp_client.async_get_clientsession(self.hass)
        try:
            async with self._session.get(
                f"{self._base_url}/{API_STATE_ALL}"
            ) as resp:
                if resp.status == 200:
                    self.config = await resp.json()
                else:
                    error_text = await resp.text()
                    _LOGGER.error("Error fetching initial config: %s", error_text)
                    raise ConnectionError(
                        f"njsPC returned status {resp.status}: {error_text}"
                    )
        except aiohttp.ClientError as err:
            raise ConnectionError(
                f"Cannot connect to njsPC at {self._base_url}: {err}"
            ) from err

    async def get_heatmodes(self, identifier):
        """Get the available heat modes for body"""
        async with self._session.get(
            f"{self._base_url}/{API_CONFIG_BODY}/{identifier}/{API_HEATMODES}"
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                _LOGGER.error(await resp.text())
                return

    async def get_lightthemes(self, identifier):
        """Get list of themes for light"""
        async with self._session.get(
            f"{self._base_url}/{API_CONFIG_CIRCUIT}/{identifier}/{API_LIGHTTHEMES}"
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                _LOGGER.error(await resp.text())
                return

    async def get_lightcommands(self, identifier):
        """Get light commands for lights"""
        async with self._session.get(
            f"{self._base_url}/{API_CONFIG_CIRCUIT}/{identifier}/{API_LIGHTCOMMANDS}"
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

    def get_controller_id(self) -> str:
        """Gets the unique id of the njsPC controller"""
        # Maybe we rethink this and pass a uuid from njsPC. It already exists in the data.
        return f'{self.data[CONF_HOST].replace(".", "")}{self.data[CONF_PORT]}'

    def get_unique_id(self, name) -> str:
        """Create a unique id for entity"""
        _id = f'{self.data[CONF_HOST].replace(".", "")}{self.data[CONF_PORT]}_{name.lower()}'
        return _id
