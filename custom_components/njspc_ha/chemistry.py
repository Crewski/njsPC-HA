"""Platform for chemistry integration."""
from __future__ import annotations

from typing import Any
from collections.abc import Mapping


from homeassistant.const import (
    UnitOfVolume,
    UnitOfMass,
    PERCENTAGE,
)

from .entity import PoolEquipmentEntity
from .__init__ import NjsPCHAdata
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.components.number import (
    NumberEntity,
    NumberMode
)
from .const import (
    PoolEquipmentClass,
    PoolEquipmentModel,
    EVENT_AVAILABILITY,
    EVENT_CHEM_CONTROLLER,
    EVENT_CHLORINATOR,
    SALT_LEVEL,
    SALT_TARGET,
    SALT_REQUIRED,
    TARGET_OUTPUT,
    CURRENT_OUTPUT,
    API_CHLORINATOR_POOL_SETPOINT,
    API_CHLORINATOR_SPA_SETPOINT,
    API_SUPERCHLOR,
    POOL_SETPOINT,
    SUPER_CHLOR_HOURS,
    API_CONFIG_CHLORINATOR,
    SUPER_CHLOR
)


class ChemistryDosingStatus(PoolEquipmentEntity, SensorEntity):
    """The current dosing status for the chemical"""

    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, chemical: Any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.CHEM_CONTROLLER
        self.equipment_name = chem_controller["name"]
        self.equipment_id = chem_controller["id"]
        self.equipment_model = PoolEquipmentModel.CHEM_CONTROLLER
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._state_attributes: dict[str, Any] = dict([])
        self.chem_type = chemical["type"]
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._value = None

        if "dosingStatus" in chemical:
            self._value = chemical["dosingStatus"]["desc"]
            self._available = True
            self._state_attributes["mix_time_remaining"] = chemical["mixTimeRemaining"]
            self._state_attributes["dose_time_remaining"] = chemical[
                "dosingTimeRemaining"
            ]
            self._state_attributes["dose_time"] = chemical["doseTime"]
            self._state_attributes["dose_volume"] = chemical["doseVolume"]
            self._state_attributes["dose_volume_remaining"] = chemical[
                "dosingVolumeRemaining"
            ]
        else:
            self._value = "Unknown"
            self._available = False
        # Below makes sure we have a name that makes sense for the entity.
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.chem_type}_dosing_status"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER
            and self.coordinator.data["id"] == self.equipment_id
            and self.chem_type in self.coordinator.data
        ):
            chemical = self.coordinator.data[self.chem_type]
            if "dosingStatus" in chemical:
                self._value = chemical["dosingStatus"]["desc"]
                self._available = True
                self._state_attributes["mix_time_remaining"] = chemical[
                    "mixTimeRemaining"
                ]
                self._state_attributes["dose_time_remaining"] = chemical[
                    "dosingTimeRemaining"
                ]
                self._state_attributes["dose_time"] = chemical["doseTime"]
                self._state_attributes["dose_volume"] = chemical["doseVolume"]
                self._state_attributes["dose_volume_remaining"] = chemical[
                    "dosingVolumeRemaining"
                ]
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
        return f"{self.chem_type} Dosing Status"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self.chem_type}_dosing_Status"

    @property
    def native_value(self) -> str | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self) -> str:
        match self._value:
            case "Mixing":
                return "mdi:bowl-mix-outline"
            case "Dosing":
                return "mdi:basket-fill"
            case "Monitoring":
                return "mdi:beaker-check"
            case _:
                return "mdi:beaker-alert"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._state_attributes

class ChemistryDemandSensor(PoolEquipmentEntity, SensorEntity):
    """Chemical demand for a chemistry controller"""

    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, chemical: Any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.CHEM_CONTROLLER
        self.equipment_name = chem_controller["name"]
        self.equipment_id = chem_controller["id"]
        self.equipment_model = PoolEquipmentModel.CHEM_CONTROLLER
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._state_attributes: dict[str, Any] = dict([])
        self.chem_type = chemical["type"]
        self._value = None
        # Below makes sure we have a name that makes sense for the entity.
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.chem_type}_demand"

        if "demand" in chemical:
            self._value = chemical["demand"]
            if "dailyVolumeDosed" in chemical:
                self._state_attributes["dosed_last_24hrs"] = chemical[
                    "dailyVolumeDosed"
                ]
            self._available = True
        else:
            self._available = False
            self._value = None

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER
            and self.coordinator.data["id"] == self.equipment_id
            and self.chem_type in self.coordinator.data
        ):
            chemical = self.coordinator.data[self.chem_type]
            if "demand" in chemical:
                self._value = chemical["demand"]
                if "dailyVolumeDosed" in chemical:
                    self._state_attributes["dosed_last_24hrs"] = chemical[
                        "dailyVolumeDosed"
                    ]
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
        return f"{self.chem_type} Demand"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self.chem_type}_demand"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | float | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:sine-wave"

    @property
    def native_unit_of_measurement(self) -> str:
        if self.chem_type == "orp":
            return "mV"
        return UnitOfVolume.MILLILITERS

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._state_attributes

class ChemistryTankLevel(PoolEquipmentEntity, SensorEntity):
    """Tank level for a chemistry tank"""

    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, chemical: Any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.CHEM_CONTROLLER
        self.equipment_name = chem_controller["name"]
        self.equipment_id = chem_controller["id"]
        self.equipment_model = PoolEquipmentModel.CHEM_CONTROLLER
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._state_attributes: dict[str, Any] = dict([])
        self.chem_type = chemical["chemType"]
        self._value = None
        if "tank" in chem_controller[self.chem_type]:
            tank = chem_controller[self.chem_type]["tank"]
            if "capacity" in tank:
                self._state_attributes["capacity"] = tank["capacity"]
            if "units" in tank:
                self._state_attributes["units"] = tank["units"]["name"]

            if "level" in tank:
                self._state_attributes["level"] = tank["level"]
                if "capacity" in tank:
                    self._value = round(tank["level"] / tank["capacity"], 2) * 100
                else:
                    self._value = 0
            self._available = True
        else:
            self._available = False
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.chem_type}_tanklevel"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER
            and self.coordinator.data["id"] == self.equipment_id
            and self.chem_type in self.coordinator.data
        ):
            chemical = self.coordinator.data[self.chem_type]
            if "tank" in chemical:
                tank = chemical["tank"]
                if "capacity" in tank:
                    self._state_attributes["capacity"] = tank["capacity"]
                if "units" in tank:
                    self._state_attributes["units"] = tank["units"]["name"]

                if "level" in tank:
                    self._state_attributes["level"] = tank["level"]
                    if "capacity" in tank:
                        self._value = round(tank["level"] / tank["capacity"], 2) * 100
                    else:
                        self._value = 0
                self._available = True
            else:
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
        return f"{self.chem_type} Tank Level"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self.chem_type}_tanklevel"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | float | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:car-coolant-level"

    @property
    def native_unit_of_measurement(self) -> str:
        return PERCENTAGE

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._state_attributes

class ChemistrySensor(PoolEquipmentEntity, SensorEntity):
    """Chemistry Sensor for njsPC-HA"""

    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, chemical: Any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.CHEM_CONTROLLER
        self.equipment_name = chem_controller["name"]
        self.equipment_id = chem_controller["id"]
        self.equipment_model = PoolEquipmentModel.CHEM_CONTROLLER
        self.coordinator = coordinator
        self.coordinator_context = object()
        # self.chemical = chemical
        self._state_attributes: dict[str, str] = dict([])
        self.chem_type = chemical["chemType"]

        # self._controller_id = chem_controller["id"]
        # self._controller_name = chem_controller["name"]
        probe = chem_controller[self.chem_type]["probe"]
        if "temperature" in probe:
            self._state_attributes["temperature"] = probe["temperature"]
        if "tempUnits" in probe:
            self._state_attributes["temp_units"] = probe["tempUnits"]["name"]
        self._value = None
        if "level" in chemical:
            self._value = chemical["level"]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.chem_type}_level"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER
            and self.coordinator.data["id"] == self.equipment_id
            and self.chem_type in self.coordinator.data
        ):
            chemical = self.coordinator.data[self.chem_type]
            if "probe" in chemical:
                probe = chemical["probe"]
                self._state_attributes["probe_reading"] = probe["level"]
                if "temperature" in probe:
                    self._state_attributes["temperature"] = probe["temperature"]
                if "tempUnits" in probe:
                    self._state_attributes["temp_units"] = probe["tempUnits"]["name"]
            self._value = chemical["level"]
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
        return f"{self.chem_type} Level"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        # return self.coordinator.api.get_unique_id(f"ph_probe_{self._controller_id}_")
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self.chem_type}_level"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | float | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:test-tube"

    @property
    def native_unit_of_measurement(self) -> str | None:
        if self.chem_type == "orp":
            return "mV"
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        return self._state_attributes

class SaltSensor(PoolEquipmentEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.equipment_model = PoolEquipmentModel.CHLORINATOR

        self.coordinator = coordinator
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_LEVEL]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_saltlevel"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.entity_id
            and SALT_LEVEL
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            # self._chlorinator = self.coordinator.data
            self._value = self.coordinator.data[SALT_LEVEL]
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
        return "Salt Level"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_saltlevel"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        """Raw value of the sensor"""
        # return self._chlorinator[SALT_LEVEL]
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:shaker-outline"

    @property
    def native_unit_of_measurement(self) -> str:
        return "PPM"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        return {
            "salt_target": self._chlorinator[SALT_TARGET],
            "salt_required": self._chlorinator[SALT_REQUIRED],
        }

class SaltTargetSensor(PoolEquipmentEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.equipment_model = PoolEquipmentModel.CHLORINATOR
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_TARGET]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_salttarget"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
            and SALT_TARGET
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._chlorinator = self.coordinator.data
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
        return "Salt Target"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_salttarget"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        """Raw value of the sensor"""
        # return self._chlorinator[SALT_TARGET]
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:target-variant"

    @property
    def native_unit_of_measurement(self) -> str:
        return "PPM"

class SaltRequiredSensor(PoolEquipmentEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.equipment_model = PoolEquipmentModel.CHLORINATOR
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_REQUIRED]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_saltrequired"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
            and SALT_REQUIRED
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[SALT_REQUIRED]
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
        return "Salt Required"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_saltrequired"

    @property
    def state_class(self) -> SensorStateClass | str:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:plus-box"

    @property
    def native_unit_of_measurement(self) -> str | None:
        return UnitOfMass.POUNDS

class CurrentOutputSensor(PoolEquipmentEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[CURRENT_OUTPUT]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_currentoutput"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and CURRENT_OUTPUT
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[CURRENT_OUTPUT]
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
        return "Current Output"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_currentoutput"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        """Raw value of the sensor"""
        # return self._chlorinator[CURRENT_OUTPUT]
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:atom"

    @property
    def native_unit_of_measurement(self) -> str:
        return PERCENTAGE

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        return {"target_output": self._chlorinator[TARGET_OUTPUT]}

class TargetOutputSensor(PoolEquipmentEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.equipment_model = PoolEquipmentModel.CHLORINATOR

        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[TARGET_OUTPUT]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_targetoutput"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and TARGET_OUTPUT
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[TARGET_OUTPUT]
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
        return "Target Output"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_targetoutput"

    @property
    def state_class(self) -> SensorStateClass:
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:target"

    @property
    def native_unit_of_measurement(self) -> str:
        return PERCENTAGE

class ChlorinatorSetpoint(PoolEquipmentEntity, NumberEntity):
    """Number for setting SWG Setpoint in njsPC-HA."""

    def __init__(self, coordinator:NjsPCHAdata, chlorinator: Any, setpoint) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.equipment_model = PoolEquipmentModel.CHLORINATOR
        self.coordinator_context = object()
        self._type = setpoint
        self._available = True
        self._value = chlorinator[setpoint]
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_class}_{setpoint}setpoint"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if self._type in self.coordinator.data:
                self._value = self.coordinator.data[self._type]
                self._available = True
            else:
                self._available = False
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        new_value = int(value)
        data = {"id": self.equipment_id, "setPoint": new_value}
        if self._type == POOL_SETPOINT:
            await self.coordinator.api.command(url=API_CHLORINATOR_POOL_SETPOINT, data=data)
        else:
            await self.coordinator.api.command(url=API_CHLORINATOR_SPA_SETPOINT, data=data)

    @property
    def mode(self) -> NumberMode:
        return NumberMode.AUTO

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        """Name of the sensor"""
        name = "Pool" if self._type == POOL_SETPOINT else "Spa"
        return f"{name} Setpoint"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self._type}setpoint"

    @property
    def icon(self) -> str:
        return "mdi:creation"

    @property
    def native_value(self):
        """value"""
        return self._value

    @property
    def native_step(self) -> int:
        return 1

    @property
    def native_unit_of_measurement(self) -> str:
        return PERCENTAGE

class SuperChlorHours(PoolEquipmentEntity, NumberEntity):
    """Number for setting SWG SuperChlorinate Hours in njsPC-HA."""

    def __init__(self, coordinator:NjsPCHAdata, chlorinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.equipment_model = PoolEquipmentModel.CHLORINATOR
        self.coordinator_context = object()
        self._value = chlorinator[SUPER_CHLOR_HOURS]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_superchlor_hours"


    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if SUPER_CHLOR_HOURS in self.coordinator.data:
                self._value = self.coordinator.data[SUPER_CHLOR_HOURS]
                self._available = True
            else:
                self._value = None
                self._available = False
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        new_value = int(value)
        data = {"id": self.equipment_id, "superChlorHours": new_value}
        await self.coordinator.api.command(url=API_CONFIG_CHLORINATOR, data=data)

    @property
    def mode(self) -> NumberMode:
        return NumberMode.AUTO

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        """Name of the sensor"""
        return "SuperChlor Hours"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_superchlor_hours"

    @property
    def icon(self) -> str:
        return "mdi:timer"

    @property
    def native_value(self) -> int:
        """value"""
        return self._value

    @property
    def native_step(self) -> int:
        return 1

    @property
    def native_unit_of_measurement(self) -> str:
        return "H"

    @property
    def native_min_value(self) -> int:
        return 1

    @property
    def native_max_value(self) -> int:
        return 24

class SuperChlorSwitch(PoolEquipmentEntity, SwitchEntity):
    """Super Chlorinate switch for njsPC-HA"""

    def __init__(self, coordinator, chlorinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.CHLORINATOR
        self.equipment_id = chlorinator["id"]
        self.equipment_name = chlorinator["name"]
        self.equipment_model = PoolEquipmentModel.CHLORINATOR
        self.coordinator_context = object()
        self._value = chlorinator[SUPER_CHLOR]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_superchlorinate"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
            and SUPER_CHLOR in self.coordinator.data
        ):
            self._value = self.coordinator.data[SUPER_CHLOR]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.equipment_id, "superChlorinate": True}
        await self.coordinator.api.command(url=API_SUPERCHLOR, data=data)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.equipment_id, "superChlorinate": False}
        await self.coordinator.api.command(url=API_SUPERCHLOR, data=data)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        return "Super Chlorinate"

    @property
    def unique_id(self) -> str:
        """Unique identifier for the entity"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_superchlorinate"

    @property
    def is_on(self) -> bool:
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:atom-variant"
