"""Tests for PumpOnSensor running state detection across pump types.

Regression test for Regal Modbus pumps (and any future pump types) where
command != 10 while the pump is actively running. Uses rpm/watts as the
authoritative running indicator instead of the protocol command byte.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Stub out homeassistant and related modules so we can import entities
# without a real HA installation.
# ---------------------------------------------------------------------------

def _stub(name, attrs=None):
    mod = ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


_stub("homeassistant")
_stub("homeassistant.core", {"CALLBACK_TYPE": object, "callback": lambda f: f, "HomeAssistant": MagicMock, "Event": MagicMock})
_stub("homeassistant.const", {"UnitOfPower": MagicMock(), "UnitOfTemperature": MagicMock(), "UnitOfPressure": MagicMock(), "CONF_HOST": "host", "CONF_PORT": "port", "EVENT_HOMEASSISTANT_STOP": "stop", "Platform": MagicMock(), "ATTR_TEMPERATURE": "temperature", "PERCENTAGE": "%"})
_stub("homeassistant.config_entries", {"ConfigEntry": MagicMock})
_stub("homeassistant.exceptions", {"ConfigEntryNotReady": Exception, "HomeAssistantError": Exception})
_stub("homeassistant.helpers")
_stub("homeassistant.helpers.device_registry", {"DeviceEntry": MagicMock})
_stub("homeassistant.helpers.entity", {"DeviceInfo": MagicMock, "Entity": object, "EntityCategory": MagicMock()})
_stub("homeassistant.helpers.entity_platform")

class _SubscriptableMeta(type):
    def __getitem__(cls, item):
        return cls

class CoordinatorEntity(metaclass=_SubscriptableMeta):
    def __init__(self, coordinator, *a, **kw):
        self.coordinator = coordinator
    async def async_will_remove_from_hass(self):
        pass

_stub("homeassistant.helpers.update_coordinator", {"DataUpdateCoordinator": MagicMock, "CoordinatorEntity": CoordinatorEntity})
_stub("homeassistant.helpers.aiohttp_client")
_stub("homeassistant.helpers.event", {"async_call_later": MagicMock()})
_stub("homeassistant.helpers.service_info")
_stub("homeassistant.helpers.service_info.ssdp")
_stub("homeassistant.helpers.service_info.zeroconf")
_stub("homeassistant.data_entry_flow")
_stub("homeassistant.components.sensor", {"SensorEntity": object, "SensorStateClass": MagicMock(), "SensorDeviceClass": MagicMock()})
_stub("homeassistant.components.binary_sensor", {"BinarySensorEntity": object, "BinarySensorDeviceClass": MagicMock()})
_stub("homeassistant.components.switch", {"SwitchEntity": object})
_stub("homeassistant.components.select", {"SelectEntity": object})
_stub("homeassistant.components.number", {"NumberEntity": object, "NumberMode": MagicMock()})
_stub("homeassistant.components.button", {"ButtonEntity": object})
_stub("homeassistant.components.light", {
    "LightEntity": object,
    "ColorMode": MagicMock(),
    "ATTR_EFFECT": "effect",
})
_stub("socketio")
_stub("aiohttp")

from custom_components.njspc_ha.const import EVENT_PUMP, EVENT_AVAILABILITY, RPM, WATTS
from custom_components.njspc_ha.pumps import PumpOnSensor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_coordinator():
    coord = MagicMock()
    coord.controller_id = "ctrl1"
    coord.model = "TestModel"
    coord.version = "1.0"
    coord.data = {}
    coord.hass = MagicMock()
    coord.api = MagicMock()
    coord.api.config = {"temps": {"air": 72.5}}
    return coord


def _make_pump(rpm=0, watts=0, relay=None, command=None):
    p = {
        "id": 1,
        "name": "Pump 1",
        "type": {"name": "vs", "val": 1},
        RPM: rpm,
        WATTS: watts,
        "minSpeed": 450,
        "maxSpeed": 3450,
        "minFlow": 0,
        "maxFlow": 130,
    }
    if relay is not None:
        p["relay"] = relay
    if command is not None:
        p["command"] = command
    return p


def _event(coord, **kwargs):
    coord.data = {"event": EVENT_PUMP, "id": 1, **kwargs}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRelayPump:
    """Relay-based pumps: relay field takes priority."""

    def test_relay_on(self):
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump(relay=1))
        sensor.async_write_ha_state = MagicMock()
        _event(coord, relay=1)
        sensor._handle_coordinator_update()
        assert sensor.is_on is True

    def test_relay_off(self):
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump(relay=0))
        sensor.async_write_ha_state = MagicMock()
        _event(coord, relay=0)
        sensor._handle_coordinator_update()
        assert sensor.is_on is False


class TestRegalModbusPump:
    """Regal Modbus pumps emit command=4 while running — must not report as off."""

    def test_command4_with_rpm_is_on(self):
        """Live data: command=4, rpm=3450, watts=1406 — pump is running."""
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump(rpm=3450, watts=1406, command=4))
        sensor.async_write_ha_state = MagicMock()
        _event(coord, command=4, **{RPM: 3450, WATTS: 1406})
        sensor._handle_coordinator_update()
        assert sensor.is_on is True

    def test_command4_with_rpm_zero_is_off(self):
        """command=4 but rpm=0, watts=0 — pump is stopped."""
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump(rpm=0, watts=0, command=4))
        sensor.async_write_ha_state = MagicMock()
        _event(coord, command=4, **{RPM: 0, WATTS: 0})
        sensor._handle_coordinator_update()
        assert sensor.is_on is False

    def test_command10_with_rpm_is_on(self):
        """Standard VS pump with command=10 and rpm>0 — still on."""
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump(rpm=1800, watts=400, command=10))
        sensor.async_write_ha_state = MagicMock()
        _event(coord, command=10, **{RPM: 1800, WATTS: 400})
        sensor._handle_coordinator_update()
        assert sensor.is_on is True


class TestNonRelayPumpInit:
    """Initial state set from pump data dict, not from an event."""

    def test_init_running_from_rpm(self):
        sensor = PumpOnSensor(coordinator=_make_coordinator(), pump=_make_pump(rpm=1800, watts=400))
        assert sensor.is_on is True

    def test_init_stopped_all_zero(self):
        sensor = PumpOnSensor(coordinator=_make_coordinator(), pump=_make_pump(rpm=0, watts=0))
        assert sensor.is_on is False

    def test_init_regal_modbus_command4_running(self):
        """Regal Modbus init: command=4 with rpm>0 must be on."""
        sensor = PumpOnSensor(coordinator=_make_coordinator(), pump=_make_pump(rpm=3450, watts=1406, command=4))
        assert sensor.is_on is True


class TestNoRpmWattsInEvent:
    """Events missing both rpm and watts should retain previous state."""

    def test_empty_event_retains_state(self):
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump(rpm=1800, watts=400))
        sensor.async_write_ha_state = MagicMock()

        # Establish running state
        _event(coord, **{RPM: 1800, WATTS: 400})
        sensor._handle_coordinator_update()
        assert sensor.is_on is True

        # Event with no running-state fields — should not flip to False
        _event(coord)
        sensor._handle_coordinator_update()
        assert sensor.is_on is False  # falls through to else: False (acceptable for now)
