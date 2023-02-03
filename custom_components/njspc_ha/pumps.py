"""Pump implementation for njsPC-HA"""
from __future__ import annotations

from typing import Any
from collections.abc import Mapping

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import UnitOfPower

from .entity import PoolEquipmentEntity, NjsPCHAdata

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)


from .const import (
    RPM,
    EVENT_PUMP,
    EVENT_AVAILABILITY,
    WATTS,
    FLOW,
    MIN_FLOW,
    MAX_FLOW,
    PoolEquipmentClass,
    PoolEquipmentModel,
)


class PumpSpeedSensor(PoolEquipmentEntity, SensorEntity):
    """RPM Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator: NjsPCHAdata, pump: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_id = pump["id"]
        self.equipment_class = PoolEquipmentClass.PUMP
        self.equipment_name = pump["name"]
        self.equipment_model = PoolEquipmentModel.PUMP
        self.coordinator_context = object()
        self._value = pump[RPM]
        self._available = True
        self._state_attributes: dict[str, Any] = dict([])
        if "minSpeed" in pump:
            self._state_attributes["min_speed"] = pump["minSpeed"]
        if "maxSpeed" in pump:
            self._state_attributes["max_speed"] = (pump["maxSpeed"],)
            # Below makes sure we have a name that makes sense for the entity.
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.equipment_class}_speed"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self.equipment_id
            and RPM in self.coordinator.data
        ):
            if RPM in self.coordinator.data:
                self._available = True
                self._value = self.coordinator.data[RPM]
            else:
                self._available = False
                self._value = None
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        """Name of the sensor"""
        return "Speed"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_speed"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        """Raw value of the sensor"""
        return self._value

    @property
    def native_unit_of_measurement(self) -> str:
        """Unit of measurement of the sensor"""
        return "RPM"

    @property
    def icon(self) -> str:
        return "mdi:speedometer"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        return self._state_attributes


class PumpPowerSensor(PoolEquipmentEntity, SensorEntity):
    """Watts Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator, pump):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_id = pump["id"]
        self.equipment_class = PoolEquipmentClass.PUMP
        self.equipment_name = pump["name"]
        self.equipment_model = PoolEquipmentModel.PUMP
        self.coordinator_context = object()
        self._value = pump[WATTS]
        self._available = True
        # Below makes sure we have a name that makes sense for the entity.
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.equipment_class}_power"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self.equipment_id
            and WATTS
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[WATTS]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        """Name of the sensor"""
        return "Watts"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_power"

    @property
    def state_class(self) -> str:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> str:
        """Raw value of the sensor"""
        return self._value

    @property
    def device_class(self) -> SensorDeviceClass:
        """The sensor device class for the sensor"""
        # return DEVICE_CLASS_POWER
        return SensorDeviceClass.POWER

    @property
    def native_unit_of_measurement(self) -> str:
        return UnitOfPower.WATT


class PumpFlowSensor(PoolEquipmentEntity, SensorEntity):
    """Flow Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator: NjsPCHAdata, pump: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.PUMP
        self.equipment_id = pump["id"]
        self.equipment_name = pump["name"]
        self.equipment_model = PoolEquipmentModel.PUMP
        self.coordinator_context = object()
        self._value = pump[FLOW]
        self._available = True
        self._state_attributes: dict[str, Any] = dict([])
        if MIN_FLOW in pump:
            self._state_attributes["min_flow"] = pump[MIN_FLOW]
        if MAX_FLOW in pump:
            self._state_attributes["max_flow"] = pump[MAX_FLOW]
            # Below makes sure we have a name that makes sense for the entity.
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.equipment_class}_flow"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self.equipment_id
            and FLOW
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[FLOW]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        """Name of the sensor"""
        return "Flow"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_flow"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        """Raw value of the sensor"""
        return self._value

    @property
    def native_unit_of_measurement(self) -> str:
        """Unit of measurement of the sensor"""
        # This can be LPM or GPM we will need to deal with this
        return "gpm"

    @property
    def icon(self) -> str:
        return "mdi:pump"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        return self._state_attributes


class PumpOnSensor(PoolEquipmentEntity, BinarySensorEntity):
    """The current running state for a pump"""

    def __init__(self, coordinator: NjsPCHAdata, pump: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.PUMP
        self.equipment_name = pump["name"]
        self.equipment_id = pump["id"]
        self.equipment_model = PoolEquipmentModel.PUMP
        if "relay" in pump:
            self._value = pump["relay"] > 0
        elif "command" in pump:
            self._value = pump["command"] == 10
        else:
            self._value = False
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.equipment_class}_ison"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if "relay" in self.coordinator.data:
                self._value = self.coordinator.data["relay"] > 0
            elif "command" in self.coordinator.data:
                self._value = self.coordinator.data["command"] == 10
            else:
                self._value = False
            self._available = True
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str | None:
        """Name of the sensor"""
        return "Running State"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_ison"

    @property
    def native_value(self) -> bool | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def is_on(self) -> bool:
        """Return if the pump is running."""
        return self._value

    @property
    def icon(self) -> str:
        if self._value is True:
            return "mdi:pump"
        return "mdi:pump-off"
