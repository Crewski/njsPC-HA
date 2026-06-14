"""Tests for PumpCircuitSpeedNumber entity — TDD: written before implementation."""

import sys
import asyncio
from types import ModuleType
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub out homeassistant modules (same pattern as test_throttle_mixin.py)
# ---------------------------------------------------------------------------

def _stub(name, attrs=None):
    mod = ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod

# Only stub if not already present (avoids conflict when running full suite)
if "homeassistant" not in sys.modules:
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

    class _NumberMode:
        BOX = "box"
        SLIDER = "slider"

    _stub("homeassistant.components.number", {
        "NumberEntity": type("NumberEntity", (), {}),
        "NumberMode": _NumberMode,
    })

    _stub("socketio")
    _stub("aiohttp")

# Now import our modules
from custom_components.njspc_ha.const import (
    EVENT_PUMP,
    EVENT_PUMP_EXT,
    EVENT_AVAILABILITY,
    API_PUMP_CIRCUIT,
    RPM,
    WATTS,
    FLOW,
)
from custom_components.njspc_ha.pumps import PumpCircuitSpeedNumber


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_circuit(circuit_id=6, circuit_name="Pool", speed=1800, flow=0, units_val=0, slot_id=1):
    """Build a single pump circuit dict matching getExtended() structure."""
    units_name = "rpm" if units_val == 0 else "gpm"
    units_desc = "RPM" if units_val == 0 else "GPM"
    return {
        "speed": speed,
        "flow": flow,
        "units": {"val": units_val, "name": units_name, "desc": units_desc},
        "id": slot_id,
        "circuit": {
            "id": circuit_id,
            "name": circuit_name,
            "type": {"val": 12, "name": "pool", "desc": "Pool"},
            "isOn": True,
        },
        "master": 1,
    }


def _make_pump(pump_id=50, pump_name="Pump 1", min_speed=1400, max_speed=3450,
               min_flow=0, max_flow=130, speed_step=10, flow_step=1,
               circuits=None, pump_type_name="regalmodbus"):
    """Build a pump dict matching /state/all getExtended() structure."""
    pump = {
        "id": pump_id,
        "name": pump_name,
        "type": {
            "val": 200,
            "name": pump_type_name,
            "desc": "Regal Modbus",
            "minSpeed": 450,
            "maxSpeed": 3450,
            "maxCircuits": 8,
            "hasAddress": True,
        },
        "isActive": True,
        "command": 10,
        RPM: 1800,
        WATTS: 191,
        FLOW: 0,
        "minSpeed": min_speed,
        "maxSpeed": max_speed,
        "minFlow": min_flow,
        "maxFlow": max_flow,
        "speedStepSize": speed_step,
        "flowStepSize": flow_step,
        "circuits": circuits or [
            _make_circuit(circuit_id=6, circuit_name="Pool", speed=1800, slot_id=1),
            _make_circuit(circuit_id=1, circuit_name="Spa", speed=3450, slot_id=2),
        ],
    }
    return pump


def _make_coordinator():
    """Return a minimal mock coordinator."""
    coord = MagicMock()
    coord.controller_id = "ctrl1"
    coord.model = "TestModel"
    coord.version = "1.0"
    coord.data = {}
    coord.hass = MagicMock()
    coord.api = MagicMock()
    coord.api.command = AsyncMock()
    return coord


def _make_entity(pump=None, circuit=None, coordinator=None):
    """Create a PumpCircuitSpeedNumber with sensible defaults."""
    coord = coordinator or _make_coordinator()
    p = pump or _make_pump()
    c = circuit or p["circuits"][0]
    entity = PumpCircuitSpeedNumber(coordinator=coord, pump=p, circuit=c)
    entity.async_write_ha_state = MagicMock()
    return entity, coord


# ===========================================================================
# Initialization Tests
# ===========================================================================

class TestInit:
    """Entity init from circuit data."""

    def test_rpm_circuit_initial_value(self):
        entity, _ = _make_entity()
        assert entity.native_value == 1800

    def test_flow_circuit_initial_value(self):
        circuit = _make_circuit(units_val=1, flow=30, speed=0)
        pump = _make_pump(circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.native_value == 30

    def test_stores_pump_id(self):
        entity, _ = _make_entity()
        assert entity._pump_id == 50

    def test_stores_circuit_id(self):
        """circuit_id is the equipment circuit id (e.g. 6 for Pool), not the slot."""
        entity, _ = _make_entity()
        assert entity._circuit_id == 6

    def test_stores_pump_circuit_id(self):
        """pump_circuit_id is the slot id (1-8) within the pump."""
        entity, _ = _make_entity()
        assert entity._pump_circuit_id == 1

    def test_is_rpm_flag_true(self):
        entity, _ = _make_entity()
        assert entity._is_rpm is True

    def test_is_rpm_flag_false_for_flow(self):
        circuit = _make_circuit(units_val=1, flow=30)
        pump = _make_pump(circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity._is_rpm is False


# ===========================================================================
# Property Tests
# ===========================================================================

class TestProperties:
    """NumberEntity properties."""

    def test_name_rpm_circuit(self):
        entity, _ = _make_entity()
        assert entity.name == "Pool Speed"

    def test_name_flow_circuit(self):
        circuit = _make_circuit(units_val=1, flow=30, circuit_name="Pool")
        pump = _make_pump(circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.name == "Pool Flow"

    def test_unique_id(self):
        entity, _ = _make_entity()
        assert entity.unique_id == "ctrl1_pump_50_circuit_6_speed"

    def test_unique_id_flow(self):
        circuit = _make_circuit(units_val=1, circuit_id=6)
        pump = _make_pump(circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.unique_id == "ctrl1_pump_50_circuit_6_flow"

    def test_native_min_rpm(self):
        entity, _ = _make_entity()
        assert entity.native_min_value == 1400

    def test_native_max_rpm(self):
        entity, _ = _make_entity()
        assert entity.native_max_value == 3450

    def test_native_step_rpm(self):
        entity, _ = _make_entity()
        assert entity.native_step == 10

    def test_native_min_flow(self):
        circuit = _make_circuit(units_val=1, flow=30)
        pump = _make_pump(min_flow=15, max_flow=130, flow_step=1, circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.native_min_value == 15

    def test_native_max_flow(self):
        circuit = _make_circuit(units_val=1, flow=30)
        pump = _make_pump(max_flow=130, circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.native_max_value == 130

    def test_native_step_flow(self):
        circuit = _make_circuit(units_val=1, flow=30)
        pump = _make_pump(flow_step=1, circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.native_step == 1

    def test_unit_of_measurement_rpm(self):
        entity, _ = _make_entity()
        assert entity.native_unit_of_measurement == "RPM"

    def test_unit_of_measurement_flow(self):
        circuit = _make_circuit(units_val=1, flow=30)
        pump = _make_pump(circuits=[circuit])
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.native_unit_of_measurement == "gpm"

    def test_mode_is_slider(self):
        entity, _ = _make_entity()
        assert entity.mode == "slider"

    def test_icon(self):
        entity, _ = _make_entity()
        assert entity.icon == "mdi:speedometer"

    def test_should_poll_false(self):
        entity, _ = _make_entity()
        assert entity.should_poll is False

    def test_available_default_true(self):
        entity, _ = _make_entity()
        assert entity.available is True

    def test_step_default_rpm_when_no_step_size(self):
        """If speedStepSize is missing from pump config, default to 10 for RPM."""
        pump = _make_pump()
        del pump["speedStepSize"]
        entity, _ = _make_entity(pump=pump)
        assert entity.native_step == 10

    def test_step_default_flow_when_no_step_size(self):
        """If flowStepSize is missing from pump config, default to 1 for GPM."""
        circuit = _make_circuit(units_val=1, flow=30)
        pump = _make_pump(circuits=[circuit])
        del pump["flowStepSize"]
        entity, _ = _make_entity(pump=pump, circuit=circuit)
        assert entity.native_step == 1


# ===========================================================================
# async_set_native_value Tests
# ===========================================================================

class TestSetNativeValue:
    """Setting the value calls the correct API endpoint."""

    def test_set_speed_rpm(self):
        entity, coord = _make_entity()
        asyncio.get_event_loop().run_until_complete(
            entity.async_set_native_value(2200)
        )
        coord.api.command.assert_called_once_with(
            url=API_PUMP_CIRCUIT,
            data={"pumpId": 50, "circuitId": 6, "speed": 2200},
        )

    def test_set_speed_flow(self):
        circuit = _make_circuit(units_val=1, flow=30, circuit_id=6)
        pump = _make_pump(circuits=[circuit])
        entity, coord = _make_entity(pump=pump, circuit=circuit)
        asyncio.get_event_loop().run_until_complete(
            entity.async_set_native_value(45)
        )
        coord.api.command.assert_called_once_with(
            url=API_PUMP_CIRCUIT,
            data={"pumpId": 50, "circuitId": 6, "flow": 45},
        )

    def test_set_value_converts_to_int(self):
        """HA number entities may pass float; API expects int."""
        entity, coord = _make_entity()
        asyncio.get_event_loop().run_until_complete(
            entity.async_set_native_value(2200.0)
        )
        call_data = coord.api.command.call_args[1]["data"]
        assert call_data["speed"] == 2200
        assert isinstance(call_data["speed"], int)

    def test_optimistic_update(self):
        """After set, native_value should reflect the new value optimistically."""
        entity, coord = _make_entity()
        asyncio.get_event_loop().run_until_complete(
            entity.async_set_native_value(2200)
        )
        assert entity.native_value == 2200


# ===========================================================================
# Coordinator Update Tests (pumpExt event)
# ===========================================================================

class TestCoordinatorUpdate:
    """Entity reacts to pumpExt events with circuit data."""

    def test_pump_ext_updates_speed(self):
        entity, coord = _make_entity()
        assert entity.native_value == 1800

        # Simulate pumpExt event with updated circuit data
        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 50,
            "circuits": [
                _make_circuit(circuit_id=6, circuit_name="Pool", speed=2200, slot_id=1),
                _make_circuit(circuit_id=1, circuit_name="Spa", speed=3450, slot_id=2),
            ],
        }
        entity._handle_coordinator_update()
        assert entity.native_value == 2200

    def test_pump_ext_updates_flow(self):
        circuit = _make_circuit(units_val=1, flow=30, circuit_id=6)
        pump = _make_pump(circuits=[circuit])
        entity, coord = _make_entity(pump=pump, circuit=circuit)
        assert entity.native_value == 30

        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 50,
            "circuits": [
                _make_circuit(units_val=1, flow=45, circuit_id=6, slot_id=1),
            ],
        }
        entity._handle_coordinator_update()
        assert entity.native_value == 45

    def test_pump_ext_wrong_pump_id_ignored(self):
        entity, coord = _make_entity()
        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 99,  # wrong pump
            "circuits": [
                _make_circuit(circuit_id=6, speed=9999, slot_id=1),
            ],
        }
        entity._handle_coordinator_update()
        assert entity.native_value == 1800  # unchanged

    def test_pump_ext_circuit_not_found_ignored(self):
        entity, coord = _make_entity()
        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 50,
            "circuits": [
                _make_circuit(circuit_id=99, speed=9999, slot_id=1),  # wrong circuit
            ],
        }
        entity._handle_coordinator_update()
        assert entity.native_value == 1800  # unchanged

    def test_regular_pump_event_ignored(self):
        """Regular pump events have no circuits — entity should not react."""
        entity, coord = _make_entity()
        coord.data = {
            "event": EVENT_PUMP,
            "id": 50,
            RPM: 2500,
            WATTS: 300,
        }
        entity._handle_coordinator_update()
        assert entity.native_value == 1800  # unchanged

    def test_pump_ext_no_circuits_key_ignored(self):
        """pumpExt without circuits key should not crash."""
        entity, coord = _make_entity()
        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 50,
        }
        entity._handle_coordinator_update()
        assert entity.native_value == 1800

    def test_availability_event(self):
        entity, coord = _make_entity()
        assert entity.available is True

        coord.data = {"event": EVENT_AVAILABILITY, "available": False}
        entity._handle_coordinator_update()
        assert entity.available is False

        coord.data = {"event": EVENT_AVAILABILITY, "available": True}
        entity._handle_coordinator_update()
        assert entity.available is True

    def test_pump_ext_calls_async_write_ha_state(self):
        entity, coord = _make_entity()
        entity.async_write_ha_state = MagicMock()

        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 50,
            "circuits": [
                _make_circuit(circuit_id=6, speed=2200, slot_id=1),
            ],
        }
        entity._handle_coordinator_update()
        entity.async_write_ha_state.assert_called_once()

    def test_second_circuit_entity_updates_independently(self):
        """Two entities for different circuits on the same pump update independently."""
        pump = _make_pump()
        coord = _make_coordinator()
        entity1 = PumpCircuitSpeedNumber(coordinator=coord, pump=pump, circuit=pump["circuits"][0])
        entity2 = PumpCircuitSpeedNumber(coordinator=coord, pump=pump, circuit=pump["circuits"][1])
        entity1.async_write_ha_state = MagicMock()
        entity2.async_write_ha_state = MagicMock()

        assert entity1.native_value == 1800  # Pool
        assert entity2.native_value == 3450  # Spa

        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 50,
            "circuits": [
                _make_circuit(circuit_id=6, circuit_name="Pool", speed=2000, slot_id=1),
                _make_circuit(circuit_id=1, circuit_name="Spa", speed=3000, slot_id=2),
            ],
        }
        entity1._handle_coordinator_update()
        entity2._handle_coordinator_update()
        assert entity1.native_value == 2000
        assert entity2.native_value == 3000


# ===========================================================================
# Edge Cases
# ===========================================================================

class TestEdgeCases:
    """Guard rails and boundary conditions."""

    def test_circuit_missing_circuit_key(self):
        """A circuit dict without circuit.id should not crash init."""
        bad_circuit = {
            "speed": 1800,
            "units": {"val": 0, "name": "rpm"},
            "id": 1,
            "circuit": {},
            "master": 1,
        }
        pump = _make_pump(circuits=[bad_circuit])
        # Should not raise — entity just uses fallback values
        entity = PumpCircuitSpeedNumber(
            coordinator=_make_coordinator(), pump=pump, circuit=bad_circuit
        )
        entity.async_write_ha_state = MagicMock()
        # circuit_id should be None or 0 — as long as it doesn't crash
        assert entity is not None

    def test_pump_ext_with_empty_circuits_array(self):
        """pumpExt with empty circuits array should not crash."""
        entity, coord = _make_entity()
        coord.data = {
            "event": EVENT_PUMP_EXT,
            "id": 50,
            "circuits": [],
        }
        entity._handle_coordinator_update()
        assert entity.native_value == 1800  # unchanged
