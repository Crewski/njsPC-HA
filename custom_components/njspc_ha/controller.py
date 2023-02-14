"""Main controller classes."""
from __future__ import annotations

from typing import Any
import logging


from homeassistant.helpers.entity import EntityCategory

from homeassistant.components.binary_sensor import (
    BinarySensorEntity
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass
)
from homeassistant.const import UnitOfTemperature
from .entity import PoolEquipmentEntity
from .__init__ import NjsPCHAdata
from .const import (
    PoolEquipmentModel,
    PoolEquipmentClass,
    EVENT_AVAILABILITY,
    EVENT_CONTROLLER,
    EVENT_TEMPS,
    STATUS,
    DESC
)


_LOGGER = logging.getLogger(__name__)


class FreezeProtectionSensor(PoolEquipmentEntity, BinarySensorEntity):
    """The current freeze protection status for the control panel"""

    def __init__(self, coordinator: NjsPCHAdata, data: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator = coordinator, equipment_class=PoolEquipmentClass.CONTROL_PANEL, data=data)
        if "freeze" in data:
            self._value = data["freeze"]
            self._available = True
        else:
            self._value = None
            self._available = False

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data["event"] == EVENT_CONTROLLER:
            if "freeze" in self.coordinator.data:
                self._available = True
                self._value = self.coordinator.data["freeze"]
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
    def name(self) -> str | None:
        """Name of the sensor"""
        return "Freeze Protection"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_freeze_protect"

    @property
    def native_value(self) -> bool | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def is_on(self) -> bool:
        """Return if motion is detected."""
        return self._value


    @property
    def icon(self) -> str:
        if self._value is True:
            return "mdi:snowflake-alert"
        return "mdi:snowflake-off"

class PanelModeSensor(PoolEquipmentEntity, SensorEntity):
    """The current dosing status for the chemical"""

    def __init__(
        self, coordinator: NjsPCHAdata, data: Any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator = coordinator, equipment_class=PoolEquipmentClass.CONTROL_PANEL, data = data)
        self._state_attributes: dict[str, Any] = dict([])
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._value = None
        if "mode" in data:
            self._value = data["mode"]["desc"]
            self._available = True
        else:
            self._value = None
            self._available = False

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data["event"] == EVENT_CONTROLLER:
            if "mode" in self.coordinator.data:
                self._value = self.coordinator.data["mode"]["desc"]
                self._available = True
            else:
                self._value = None
                self._available = False
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
        return "Panel Mode"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_panel_mode"

    @property
    def native_value(self) -> str | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self) -> str:
        match self._value:
            case "Auto":
                return "mdi:check-bold"
            case "Timeout":
                return "mdi:lock-clock"
            case "Service":
                return "mdi:mdi-lock"
            case _:
                return "mdi:lock-alert"

class TempProbeSensor(PoolEquipmentEntity, SensorEntity):
    """Temp Sensor for njsPC-HA"""

    def __init__(self, coordinator:NjsPCHAdata, key, units) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CONTROL_PANEL, data={"model":coordinator.model})
        self._key = key
        self._value = None
        self._units = units
        if "temps" in coordinator.api.config and key in coordinator.api.config["temps"]:
            self._value = round(coordinator.api.config["temps"][key], 1)
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_TEMPS
            and self._key in self.coordinator.data
        ):  # make sure the data we are looking for is in the coordinator data
            self._value = round(self.coordinator.data[self._key], 1)
            if "units" in self.coordinator.data:
                self._units = self.coordinator.data["units"]["name"]
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
        match self._key:
            case "waterSensor1":
                return "Water Sensor 1"
            case "waterSensor2":
                return "Water Sensor 2"
            case "waterSensor3":
                return "Water Sensor 3"
            case "waterSensor4":
                return "Water Senaor 4"
            case "air":
                return "Air Sensor"
            case "solar":
                return "Solar Sensor"
            case "solarSensor1":
                return "Solar Sensor 1"
            case "solarSensor2":
                return "Solar Sensor 2"
            case "solarSensor3":
                return "Solar Sensor 3"
            case "solarSensor4":
                return "Solar Sensor 4"
            case _:
                return self._key

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self._key}"

    @property
    def state_class(self) -> str:
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        return self._value

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str | UnitOfTemperature | None:
        if self._units == "F":
            return UnitOfTemperature.FAHRENHEIT
        return UnitOfTemperature.CELSIUS

class EquipmentStatusSensor(PoolEquipmentEntity, SensorEntity):
    """Equipment Status Sensor for njsPC-HA"""

    def __init__(
        self,
        coordinator: NjsPCHAdata,
        equipment_class: PoolEquipmentClass,
        equipment_model: PoolEquipmentModel,
        equipment: Any,
        event: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=equipment_class, data=equipment)
        self._value = None
        if STATUS in equipment and DESC in equipment[STATUS]:
            self._value = equipment[STATUS][DESC]
        self._event = event
        self._available = True
        self._attr_device_class = f"{self.equipment_name}_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if STATUS in self.coordinator.data and DESC in self.coordinator.data[STATUS]:
                self._value = self.coordinator.data[STATUS][DESC]
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
        return "Status"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_status"

    @property
    def native_value(self) -> str | None:
        return self._value

    @property
    def icon(self) -> str:
        if self._value != "Ok":
            return "mdi:alert-circle"
        return "mdi:check-circle"
