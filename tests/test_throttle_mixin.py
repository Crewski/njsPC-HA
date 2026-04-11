"""Tests for ThrottledSensorMixin across all throttled entity types."""

import sys
import time
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

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
_stub("homeassistant.components.sensor", {
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
    EVENT_FILTER,
    EVENT_TEMPS,
    EVENT_AVAILABILITY,
    THROTTLE_PUMP_SPEED_DELTA,
    THROTTLE_DEFAULT_INTERVAL,
    RPM,
    WATTS,
    FLOW,
)
from custom_components.njspc_ha.pumps import (
    PumpSpeedSensor,
    PumpPowerSensor,
    PumpFlowSensor,
    PumpOnSensor,
)
from custom_components.njspc_ha.bodies import (
    FilterOnSensor,
    FilterPressureSensor,
    FilterCleanSensor,
    BodyTempSensor,
)
from custom_components.njspc_ha.controller import TempProbeSensor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pump(rpm=1000, min_speed=450, max_speed=3450, pump_id=1, watts=100, flow=50):
    return {
        "id": pump_id,
        "name": "TestPump",
        "type": {"name": "vs"},
        RPM: rpm,
        "minSpeed": min_speed,
        "maxSpeed": max_speed,
        WATTS: watts,
        FLOW: flow,
        "minFlow": 10,
        "maxFlow": 100,
        "relay": 1,
        "command": 10,
    }


def _make_filter(filter_id=1, pressure=10.0, clean_pct=85, is_on=True):
    return {
        "id": filter_id,
        "name": "TestFilter",
        "pressure": pressure,
        "pressureUnits": {"name": "psi"},
        "cleanPercentage": clean_pct,
        "isOn": is_on,
    }


def _make_coordinator():
    """Return a minimal mock coordinator."""
    coord = MagicMock()
    coord.controller_id = "ctrl1"
    coord.model = "TestModel"
    coord.version = "1.0"
    coord.data = {}
    coord.hass = MagicMock()
    coord.api = MagicMock()
    coord.api.config = {"temps": {"air": 72.5}}
    return coord


def _set_event(coord, event, pump_id=1, **kwargs):
    """Set coordinator.data to simulate an event."""
    data = {"event": event, "id": pump_id, **kwargs}
    coord.data = data


# ===========================================================================
# PumpSpeedSensor Tests (numeric with delta > 0)
# ===========================================================================

class TestMaxSpeedScalar:
    """max_speed extra attribute must be a scalar, not a tuple."""

    def test_max_speed_is_scalar(self):
        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump(max_speed=3450))
        assert sensor.extra_state_attributes["max_speed"] == 3450
        assert not isinstance(sensor.extra_state_attributes["max_speed"], tuple)

    def test_min_speed_is_scalar(self):
        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump(min_speed=450))
        assert sensor.extra_state_attributes["min_speed"] == 450


class TestImmediateFirstPublish:
    """The very first event must be published with no delay."""

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

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_small_change_deferred(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

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

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_small_changes_do_not_reschedule(self, mock_time, mock_call_later):
        """Multiple small changes should not reschedule — only one timer."""
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1002)
        sensor._handle_coordinator_update()

        mock_time.monotonic.return_value = 110.0
        _set_event(coord, EVENT_PUMP, rpm=1004)
        sensor._handle_coordinator_update()

        assert mock_call_later.call_count == 1
        assert sensor._value == 1004


class TestSameValueSkipped:
    """Identical values should be skipped entirely — no write, no timer."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_same_rpm_skipped(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        # Same value 5 seconds later
        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        # Still only 1 write, no timer
        assert sensor.async_write_ha_state.call_count == 1
        assert mock_call_later.call_count == 0


class TestMeaningfulDelta:
    """A large RPM jump should publish immediately."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_large_delta_publishes_immediately(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        mock_time.monotonic.return_value = 102.0
        _set_event(coord, EVENT_PUMP, rpm=1000 + THROTTLE_PUMP_SPEED_DELTA)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 2


class TestDelayedFlush:
    """A pending value must flush when the timer fires."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_flush_publishes_pending_value(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1003)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        # Simulate the timer firing
        mock_time.monotonic.return_value = 130.0
        sensor._on_throttle_flush(None)
        assert sensor.async_write_ha_state.call_count == 2
        assert sensor._throttle_last_published_value == 1003
        assert sensor._throttle_flush_unsub is None


class TestAvailabilityImmediate:
    """Availability events must always publish immediately and cancel timers."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_availability_publishes_immediately(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        unsub = MagicMock()
        mock_call_later.return_value = unsub

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1002)
        sensor._handle_coordinator_update()
        assert mock_call_later.call_count == 1

        coord.data = {"event": EVENT_AVAILABILITY, "available": False}
        sensor._handle_coordinator_update()

        unsub.assert_called_once()
        assert sensor._throttle_flush_unsub is None
        assert sensor.async_write_ha_state.call_count == 2
        assert sensor.available is False


class TestCleanupOnRemoval:
    """Pending timers must be cleaned up on entity removal."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    @pytest.mark.asyncio
    async def test_removal_cancels_timer(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        unsub = MagicMock()
        mock_call_later.return_value = unsub

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()
        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, rpm=1002)
        sensor._handle_coordinator_update()

        assert sensor._throttle_flush_unsub is not None
        await sensor.async_will_remove_from_hass()
        unsub.assert_called_once()
        assert sensor._throttle_flush_unsub is None


class TestIntervalExpired:
    """After the full interval, the next small change should publish immediately."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_publish_after_interval(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0

        coord = _make_coordinator()
        sensor = PumpSpeedSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, rpm=1000)
        sensor._handle_coordinator_update()

        mock_time.monotonic.return_value = 100.0 + THROTTLE_DEFAULT_INTERVAL + 1
        _set_event(coord, EVENT_PUMP, rpm=1003)
        sensor._handle_coordinator_update()

        assert sensor.async_write_ha_state.call_count == 2
        assert mock_call_later.call_count == 0


# ===========================================================================
# PumpOnSensor Tests (binary with delta = 0)
# ===========================================================================

class TestBinarySensorSameValueSkipped:
    """Binary sensors with delta=0 should skip writes when value is unchanged."""

    def test_same_boolean_skipped(self):
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # First event — pump on
        _set_event(coord, EVENT_PUMP, relay=1)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1
        assert sensor.is_on is True

        # Same state again — should skip
        _set_event(coord, EVENT_PUMP, relay=2)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1  # still 1

    def test_boolean_change_publishes(self):
        coord = _make_coordinator()
        sensor = PumpOnSensor(coordinator=coord, pump=_make_pump())
        sensor.async_write_ha_state = MagicMock()

        # On
        _set_event(coord, EVENT_PUMP, relay=1)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        # Off — value changed, immediate publish
        _set_event(coord, EVENT_PUMP, relay=0)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 2
        assert sensor.is_on is False


class TestFilterOnSameValueSkipped:
    """FilterOnSensor should also skip unchanged boolean writes."""

    def test_filter_on_same_skipped(self):
        coord = _make_coordinator()
        sensor = FilterOnSensor(coordinator=coord, pool_filter=_make_filter(is_on=True))
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_FILTER, isOn=True)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        _set_event(coord, EVENT_FILTER, isOn=True)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1  # skipped


# ===========================================================================
# PumpPowerSensor Tests (numeric with delta > 0)
# ===========================================================================

class TestPumpPowerThrottled:
    """PumpPowerSensor uses the mixin with THROTTLE_PUMP_POWER_DELTA=5."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_small_watt_change_deferred(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = PumpPowerSensor(coordinator=coord, pump=_make_pump(watts=100))
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, watts=100)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_PUMP, watts=102)
        sensor._handle_coordinator_update()
        # Small change deferred
        assert sensor.async_write_ha_state.call_count == 1
        assert mock_call_later.call_count == 1

    def test_large_watt_change_immediate(self):
        coord = _make_coordinator()
        sensor = PumpPowerSensor(coordinator=coord, pump=_make_pump(watts=100))
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_PUMP, watts=100)
        sensor._handle_coordinator_update()

        _set_event(coord, EVENT_PUMP, watts=110)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 2


# ===========================================================================
# TempProbeSensor Tests (numeric with THROTTLE_TEMP_DELTA=0.1)
# ===========================================================================

class TestTempProbeThrottled:
    """TempProbeSensor should throttle small temperature changes."""

    def test_same_temp_skipped(self):
        coord = _make_coordinator()
        sensor = TempProbeSensor(coordinator=coord, key="air", units="F")
        sensor.async_write_ha_state = MagicMock()

        coord.data = {"event": EVENT_TEMPS, "air": 72.5}
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        # Same temp
        coord.data = {"event": EVENT_TEMPS, "air": 72.5}
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

    def test_meaningful_temp_change_publishes(self):
        coord = _make_coordinator()
        sensor = TempProbeSensor(coordinator=coord, key="air", units="F")
        sensor.async_write_ha_state = MagicMock()

        coord.data = {"event": EVENT_TEMPS, "air": 72.5}
        sensor._handle_coordinator_update()

        coord.data = {"event": EVENT_TEMPS, "air": 72.7}
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 2


# ===========================================================================
# FilterPressureSensor Tests
# ===========================================================================

class TestFilterPressureThrottled:
    """FilterPressureSensor should throttle small pressure changes."""

    @patch("custom_components.njspc_ha.entity.async_call_later")
    @patch("custom_components.njspc_ha.entity.time")
    def test_small_pressure_deferred(self, mock_time, mock_call_later):
        mock_time.monotonic.return_value = 100.0
        mock_call_later.return_value = MagicMock()

        coord = _make_coordinator()
        sensor = FilterPressureSensor(coordinator=coord, pool_filter=_make_filter(pressure=10.0))
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_FILTER, pressure=10.0)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        mock_time.monotonic.return_value = 105.0
        _set_event(coord, EVENT_FILTER, pressure=10.2)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1  # deferred

    def test_large_pressure_change_immediate(self):
        coord = _make_coordinator()
        sensor = FilterPressureSensor(coordinator=coord, pool_filter=_make_filter(pressure=10.0))
        sensor.async_write_ha_state = MagicMock()

        _set_event(coord, EVENT_FILTER, pressure=10.0)
        sensor._handle_coordinator_update()

        _set_event(coord, EVENT_FILTER, pressure=10.5)
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 2


# ===========================================================================
# BodyTempSensor Tests
# ===========================================================================

class TestBodyTempThrottled:
    """BodyTempSensor should throttle small temperature changes."""

    def test_same_body_temp_skipped(self):
        coord = _make_coordinator()
        body = {"id": 1, "name": "Pool", "temp": 82.0}
        sensor = BodyTempSensor(coordinator=coord, units="F", body=body)
        sensor.async_write_ha_state = MagicMock()

        coord.data = {"event": EVENT_TEMPS, "bodies": [{"id": 1, "temp": 82.0}]}
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1

        coord.data = {"event": EVENT_TEMPS, "bodies": [{"id": 1, "temp": 82.0}]}
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 1  # skipped

    def test_meaningful_body_temp_publishes(self):
        coord = _make_coordinator()
        body = {"id": 1, "name": "Pool", "temp": 82.0}
        sensor = BodyTempSensor(coordinator=coord, units="F", body=body)
        sensor.async_write_ha_state = MagicMock()

        coord.data = {"event": EVENT_TEMPS, "bodies": [{"id": 1, "temp": 82.0}]}
        sensor._handle_coordinator_update()

        coord.data = {"event": EVENT_TEMPS, "bodies": [{"id": 1, "temp": 82.2}]}
        sensor._handle_coordinator_update()
        assert sensor.async_write_ha_state.call_count == 2
"""Tests for PumpSpeedSensor throttling and max_speed scalar fix."""
