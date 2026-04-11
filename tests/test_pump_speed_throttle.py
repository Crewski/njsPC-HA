"""Tests for PumpSpeedSensor throttling and max_speed scalar fix."""

import sys
import time
from types import ModuleType
from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Stub out homeassistant and related modules so we can import pumps.py
# without a real HA installation.
# ---------------------------------------------------------------------------

def _stub(name, attrs=None):
    mod = ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod

# Core HA stubs
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

# Sensor platform stubs
_sensor = _stub("homeassistant.components.sensor", {
    "SensorEntity": type("SensorEntity", (), {}),
    "SensorStateClass": MagicMock(),
    "SensorDeviceClass": MagicMock(),
})
_stub("homeassistant.components.binary_sensor", {
    "BinarySensorEntity": type("BinarySensorEntity", (), {}),
    "BinarySensorDeviceClass": MagicMock(),
})
_stub("homeassistant.components.switch", {"SwitchEntity": type("SwitchEntity", (), {})})
_stub("homeassistant.components.climate", {
    "ClimateEntity": type("ClimateEntity", (), {}),
    "ClimateEntityFeature": MagicMock(),
    "HVACAction": MagicMock(),
    "HVACMode": MagicMock(),
})
_stub("homeassistant.components.light", {
    "LightEntity": type("LightEntity", (), {}),
    "LightEntityFeature": MagicMock(),
    "ColorMode": MagicMock(),
    "ATTR_EFFECT": "effect",
})
_stub("homeassistant.components.button", {"ButtonEntity": type("ButtonEntity", (), {})})
_stub("homeassistant.components.number", {"NumberEntity": type("NumberEntity", (), {}), "NumberMode": MagicMock()})

_stub("socketio")
_stub("aiohttp")

# Now import our modules
from custom_components.njspc_ha.const import (
    EVENT_PUMP,
    EVENT_AVAILABILITY,
    PUMP_SPEED_MIN_DELTA,
    PUMP_SPEED_MIN_INTERVAL,
    RPM,
)
from custom_components.njspc_ha.pumps import PumpSpeedSensor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pump(rpm=1000, min_speed=450, max_speed=3450, pump_id=1):
    return {
        "id": pump_id,
        "name": "TestPump",
        "type": {"name": "vs"},
        RPM: rpm,
        "minSpeed": min_speed,
        "maxSpeed": max_speed,
    }


def _make_coordinator(pump_id=1):
    """Return a minimal mock coordinator."""
    coord = MagicMock()
    coord.controller_id = "ctrl1"
    coord.model = "TestModel"
    coord.version = "1.0"
    coord.data = {}
    # async_call_later is patched at the module level, hass just needs to exist
    coord.hass = MagicMock()
    return coord


def _set_event(coord, event, pump_id=1, **kwargs):
    """Set coordinator.data to simulate an event."""
    data = {"event": event, "id": pump_id, **kwargs}
    coord.data = data


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMaxSpeedScalar:
    """max_speed extra attribute must be a scalar, not a tuple."""

    def test_max_speed_is_scalar(self):
        coord = _make_coordinator()
        pump = _make_pump(max_speed=3450)
        sensor = PumpSpeedSensor(coordinator=coord, pump=pump)
        attrs = sensor.extra_state_attributes
        assert attrs["max_speed"] == 3450
        assert not isinstance(attrs["max_speed"], tuple)

    def test_min_speed_is_scalar(self):
        coord = _make_coordinator()
        pump = _make_pump(min_speed=450)
        sensor = PumpSpeedSensor(coordinator=coord, pump=pump)
        assert sensor.extra_state_attributes["min_speed"] == 450


class TestImmediateFirstPublish:
    """The very first RPM event must be published with no delay."""

    def test_first_rpm_publishes_immediately(self):
        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1005)
        sensor._handle_coordinator_update()

        sensor.async_write_ha_state.assert_called_once()
        assert sensor.native_value == 1005


class TestSmallChangeSuppressed:
    """Rapid small RPM changes within the throttle window should not
    trigger repeated state writes."""

    @patch("custom_components.njspc_ha.pumps.async_call_later")
    @patch("custom_components.njspc_ha.pumps.time")
    def test_small_change_deferred(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()  # unsub callback

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First event — publishes immediately
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        # Advance 5 seconds — small change
        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1003)
        sensor._handle_coordinator_update()

        # Should NOT have published again
        assert sensor.async_write_ha_state.call_count == 1
        # Should have scheduled a flush
        mock_call_later.assert_called_once()

    @patch("custom_components.njspc_ha.pumps.async_call_later")
    @patch("custom_components.njspc_ha.pumps.time")
    def test_small_changes_do_not_reschedule(self, mock_time, mock_call_later):
        """Multiple small changes should not reschedule — only one timer."""
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First publish
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        # Two small changes
        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1002)
        sensor._handle_coordinator_update()

        mock_time.monotonic.return_value = 110.0
        _set_event(coord, EVENT_PUMP, rpm=1004)
        sensor._handle_coordinator_update()

        # Only one timer scheduled
        assert mock_call_later.call_count == 1
        # Value is updated internally
        assert sensor._value == 1004


class TestMeaningfulDelta:
    """A large RPM jump should publish immediately regardless of window."""

    @patch("custom_components.njspc_ha.pumps.async_call_later")
    @patch("custom_components.njspc_ha.pumps.time")
    def test_large_delta_publishes_immediately(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First publish
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        # 2 seconds later, RPM jumps by more than PUMP_SPEED_MIN_DELTA
        mock_time.monotonic.return_value = 102.0
        _set_event(coord, EVENT_PUMP, rpm=1000 + PUMP_SPEED_MIN_DELTA)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 2


class TestDelayedFlush:
    """A pending RPM update must flush when the timer fires."""

    @patch("custom_components.njspc_ha.pumps.async_call_later")
    @patch("custom_components.njspc_ha.pumps.time")
    def test_flush_publishes_pending_value(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First publish
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        # Small change — deferred
        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1003)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        # Simulate the timer firing
        mock_time.monotonic.return_value = 130.0
        sensor._flush_callback(None)
        assert sensor.async_write_ha_state.call_count == 2
        assert sensor._last_published_value == 1003
        assert sensor._flush_unsub is None


class TestAvailabilityImmediate:
    """Availability events must always publish immediately and cancel timers."""

    @patch("custom_components.njspc_ha.pumps.async_call_later")
    @patch("custom_components.njspc_ha.pumps.time")
    def test_availability_publishes_immediately(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        unsub = MagicMock()
        mock_call_later.return_value = unsub

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First publish
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        # Small change → deferred, timer scheduled
        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1002)
        sensor._handle_coordinator_update()
        assert mock_call_later.call_count == 1

        # Availability event
        coord.data = {"event": EVENT_AVAILABILITY, "available": False}
        sensor._handle_coordinator_update()

        # Timer must have been cancelled
        unsub.assert_called_once()
        assert sensor._flush_unsub is None
        # Availability write happened
        assert sensor.async_write_ha_state.call_count == 2
        assert sensor.available is False


class TestCleanupOnRemoval:
    """Pending timers/tasks must be cleaned up on entity removal."""

    @patch("custom_components.njspc_ha.pumps.async_call_later")
    @patch("custom_components.njspc_ha.pumps.time")
    @pytest.mark.asyncio
    async def test_removal_cancels_timer(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        unsub = MagicMock()
        mock_call_later.return_value = unsub

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First publish, then deferred update
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()
        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1002)
        sensor._handle_coordinator_update()

        # Timer is pending
        assert sensor._flush_unsub is not None

        await sensor.async_will_remove_from_hass()

        unsub.assert_called_once()
        assert sensor._flush_unsub is None


class TestIntervalExpired:
    """After the full interval has elapsed, the next small change should
    publish immediately without scheduling a timer."""

    @patch("custom_components.njspc_ha.pumps.async_call_later")
    @patch("custom_components.njspc_ha.pumps.time")
    def test_publish_after_interval(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First publish
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        # Well past the throttle window
        mock_time.monotonic.return_value = 100.0 + PUMP_SPEED_MIN_INTERVAL + 1
        _set_event(coord, EVENT_PUMP, rpm=1003)
        sensor._handle_coordinator_update()

        # Should have published immediately (count=2), no timer
        assert sensor.async_write_ha_state.call_count == 2
        assert mock_call_later.call_count == 0
