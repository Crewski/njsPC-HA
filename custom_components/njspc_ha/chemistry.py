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
from homeassistant.components.binary_sensor import (
    BinarySensorEntity
)
from homeassistant.components.number import (
    NumberEntity,
    NumberMode
)
from .const import (
    PoolEquipmentClass,
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
    API_CHEM_CONTROLLER_SETPOINT,
    API_SUPERCHLOR,
    POOL_SETPOINT,
    SUPER_CHLOR_HOURS,
    API_CONFIG_CHLORINATOR,
    SUPER_CHLOR
)

class FlowDetectedSensor(PoolEquipmentEntity, BinarySensorEntity):
    """The current freeze protection status for the control panel"""

    def __init__(self, coordinator: NjsPCHAdata, chem_controller) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator = coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        if "flowDetected" in chem_controller:
            self._value = chem_controller["flowDetected"]
            self._available = True
        else:
            self._value = None
            self._available = False

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER:
            if "flowDetected" in self.coordinator.data:
                self._available = True
                self._value = self.coordinator.data["flowDetected"]
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
        return "Flow Detected"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_flow_detected"

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
            return "mdi:waves-arrow-right"
        return "mdi:wave"

class WarningSensor(PoolEquipmentEntity, BinarySensorEntity):
    """The current freeze protection status for the control panel"""

    def __init__(self, coordinator: NjsPCHAdata, chem_controller) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator = coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self._state_attributes: dict[str, Any] = dict([])
        if "warnings" in chem_controller and chem_controller["warnings"]:
            warn = chem_controller["warnings"]

            self._available = True

            self._state_attributes["chlorinator_comm_err"] = warn["chlorinatorCommError"]["val"]
            self._state_attributes["chlorinator_comm_err_desc"] = warn["chlorinatorCommError"]["desc"]
            self._state_attributes["invalid_setup"] = warn["invalidSetup"]["val"]
            self._state_attributes["invalid_setup_desc"] = warn["invalidSetup"]["desc"]
            self._state_attributes["orp_daily_limit_reached"] = warn["orpDailyLimitReached"]["val"]
            self._state_attributes["orp_daily_limit_reached_desc"] = warn["orpDailyLimitReached"]["desc"]
            self._state_attributes["ph_daily_limit_reached"] = warn["pHDailyLimitReached"]["val"]
            self._state_attributes["ph_daily_limit_reached_desc"] = warn["pHDailyLimitReached"]["desc"]
            self._state_attributes["ph_lockout"] = warn["pHLockout"]["val"]
            self._state_attributes["ph_lockout_desc"] = warn["pHLockout"]["desc"]
            self._state_attributes["water_chemistry"] = warn["waterChemistry"]["val"]
            self._state_attributes["water_chemistry_desc"] = warn["waterChemistry"]["desc"]

            self._value = self._state_attributes["chlorinator_comm_err"] + self._state_attributes["invalid_setup"] + self._state_attributes["orp_daily_limit_reached"] + self._state_attributes["ph_daily_limit_reached"]  + self._state_attributes["ph_lockout"] + self._state_attributes["water_chemistry"]

        else:
            self._value = None
            self._available = False
            self._state_attributes["chlorinator_comm_err"] = 0
            self._state_attributes["chlorinator_comm_err_desc"] = ""
            self._state_attributes["invalid_setup"] = 0
            self._state_attributes["invalid_setup_desc"] = ""
            self._state_attributes["orp_daily_limit_reached"] = 0
            self._state_attributes["orp_daily_limit_reached_desc"] = ""
            self._state_attributes["ph_daily_limit_reached"] = 0
            self._state_attributes["ph_daily_limit_reached_desc"] = ""
            self._state_attributes["ph_lockout"] = 0
            self._state_attributes["ph_lockout_desc"] = ""
            self._state_attributes["water_chemistry"] = 0
            self._state_attributes["water_chemistry_desc"] = ""

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER:
            if "warnings" in self.coordinator.data:
                self._available = True
                warn = self.coordinator.data["warnings"]

                self._state_attributes["chlorinator_comm_err"] = warn["chlorinatorCommError"]["val"]
                self._state_attributes["chlorinator_comm_err_desc"] = warn["chlorinatorCommError"]["desc"]
                self._state_attributes["invalid_setup"] = warn["invalidSetup"]["val"]
                self._state_attributes["invalid_setup_desc"] = warn["invalidSetup"]["desc"]
                self._state_attributes["orp_daily_limit_reached"] = warn["orpDailyLimitReached"]["val"]
                self._state_attributes["orp_daily_limit_reached_desc"] = warn["orpDailyLimitReached"]["desc"]
                self._state_attributes["ph_daily_limit_reached"] = warn["pHDailyLimitReached"]["val"]
                self._state_attributes["ph_daily_limit_reached_desc"] = warn["pHDailyLimitReached"]["desc"]
                self._state_attributes["ph_lockout"] = warn["pHLockout"]["val"]
                self._state_attributes["ph_lockout_desc"] = warn["pHLockout"]["desc"]
                self._state_attributes["water_chemistry"] = warn["waterChemistry"]["val"]
                self._state_attributes["water_chemistry_desc"] = warn["waterChemistry"]["desc"]

                self._value = self._state_attributes["chlorinator_comm_err"] + self._state_attributes["invalid_setup"] + self._state_attributes["orp_daily_limit_reached"] + self._state_attributes["ph_daily_limit_reached"]  + self._state_attributes["ph_lockout"] + self._state_attributes["water_chemistry"]

            else:
                self._value = None
                self._available = False
                self._state_attributes["chlorinator_comm_err"] = 0
                self._state_attributes["chlorinator_comm_err_desc"] = ""
                self._state_attributes["invalid_setup"] = 0
                self._state_attributes["invalid_setup_desc"] = ""
                self._state_attributes["orp_daily_limit_reached"] = 0
                self._state_attributes["orp_daily_limit_reached_desc"] = ""
                self._state_attributes["ph_daily_limit_reached"] = 0
                self._state_attributes["ph_daily_limit_reached_desc"] = ""
                self._state_attributes["ph_lockout"] = 0
                self._state_attributes["ph_lockout_desc"] = ""
                self._state_attributes["water_chemistry"] = 0
                self._state_attributes["water_chemistry_desc"] = ""

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
        return "Chlorinator Warnings"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_warnings"

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
            return "mdi:waves-arrow-right"
        return "mdi:wave"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        return self._state_attributes

class AlarmSensor(PoolEquipmentEntity, BinarySensorEntity):
    """The current freeze protection status for the control panel"""

    def __init__(self, coordinator: NjsPCHAdata, chem_controller) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator = coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self._state_attributes: dict[str, Any] = dict([])
        if "alarms" in chem_controller and chem_controller["alarms"]:
            alarms = chem_controller["alarms"]

            self._available = True

            self._state_attributes["body_fault"] = alarms["bodyFault"]["val"]
            self._state_attributes["body_fault_desc"] = alarms["bodyFault"]["desc"]
            self._state_attributes["chlor_fault"] = alarms["chlorFault"]["val"]
            self._state_attributes["chlor_fault_desc"] = alarms["chlorFault"]["desc"]
            self._state_attributes["comms"] = alarms["comms"]["val"]
            self._state_attributes["comms_desc"] = alarms["comms"]["desc"]
            self._state_attributes["flow"] = alarms["flow"]["val"]
            self._state_attributes["flow_desc"] = alarms["flow"]["desc"]
            self._state_attributes["flow_sensor_fault"] = alarms["flowSensorFault"]["val"]
            self._state_attributes["flow_sensor_fault_desc"] = alarms["flowSensorFault"]["desc"]
            self._state_attributes["freeze_protect"] = alarms["freezeProtect"]["val"]
            self._state_attributes["freeze_protect_desc"] = alarms["freezeProtect"]["desc"]

            self._state_attributes["orp"] = alarms["orp"]["val"]
            self._state_attributes["orp_desc"] = alarms["orp"]["desc"]
            self._state_attributes["orp_probe_fault"] = alarms["orpProbeFault"]["val"]
            self._state_attributes["orp_probe_fault_desc"] = alarms["orpProbeFault"]["desc"]
            self._state_attributes["orp_pump_fault"] = alarms["orpPumpFault"]["val"]
            self._state_attributes["orp_pump_fault_desc"] = alarms["orpPumpFault"]["desc"]
            self._state_attributes["orp_tank"] = alarms["orpTank"]["val"]
            self._state_attributes["orp_tank_desc"] = alarms["orpTank"]["desc"]

            self._state_attributes["ph"] = alarms["pH"]["val"]
            self._state_attributes["ph_desc"] = alarms["pH"]["desc"]
            self._state_attributes["ph_probe_fault"] = alarms["pHProbeFault"]["val"]
            self._state_attributes["ph_probe_fault_desc"] = alarms["pHProbeFault"]["desc"]
            self._state_attributes["ph_pump_fault"] = alarms["pHPumpFault"]["val"]
            self._state_attributes["ph_pump_fault_desc"] = alarms["pHPumpFault"]["desc"]
            self._state_attributes["ph_tank"] = alarms["pHTank"]["val"]
            self._state_attributes["ph_tank_desc"] = alarms["pHTank"]["desc"]

            self._state_attributes["probe_fault"] = alarms["probeFault"]["val"]
            self._state_attributes["probe_fault_desc"] = alarms["probeFault"]["desc"]

            self._value = self._state_attributes["body_fault"] + \
                self._state_attributes["chlor_fault"] + \
                self._state_attributes["comms"] + \
                self._state_attributes["flow"]  + \
                self._state_attributes["flow_sensor_fault"] + \
                self._state_attributes["freeze_protect"] + \
                self._state_attributes["orp"] + \
                self._state_attributes["orp_probe_fault"] + \
                self._state_attributes["orp_pump_fault"]  + \
                self._state_attributes["orp_tank"] + \
                self._state_attributes["ph"] + \
                self._state_attributes["ph_probe_fault"] + \
                self._state_attributes["ph_pump_fault"]  + \
                self._state_attributes["ph_tank"] + \
                self._state_attributes["probe_fault"]
        else:
            self._value = None
            self._available = False
            self._state_attributes["body_fault"] = 0
            self._state_attributes["body_fault_desc"] = ""
            self._state_attributes["chlor_fault"] = 0
            self._state_attributes["chlor_fault_desc"] = ""
            self._state_attributes["comms"] = 0
            self._state_attributes["comms_desc"] = ""
            self._state_attributes["flow"] = 0
            self._state_attributes["flow_desc"] = ""
            self._state_attributes["flow_sensor_fault"] = 0
            self._state_attributes["flow_sensor_fault_desc"] = ""
            self._state_attributes["freeze_protect"] = 0
            self._state_attributes["freeze_protect_desc"] = ""

            self._state_attributes["orp"] = 0
            self._state_attributes["orp_desc"] = ""
            self._state_attributes["orp_probe_fault"] = 0
            self._state_attributes["orp_probe_fault_desc"] = ""
            self._state_attributes["orp_pump_fault"] = 0
            self._state_attributes["orp_pump_fault_desc"] = ""
            self._state_attributes["orp_tank"] = 0
            self._state_attributes["orp_tank_desc"] = ""

            self._state_attributes["ph"] = 0
            self._state_attributes["ph_desc"] = ""
            self._state_attributes["ph_probe_fault"] = 0
            self._state_attributes["ph_probe_fault_desc"] = ""
            self._state_attributes["ph_pump_fault"] = 0
            self._state_attributes["ph_pump_fault_desc"] = ""
            self._state_attributes["ph_tank"] = 0
            self._state_attributes["ph_tank_desc"] = ""

            self._state_attributes["probe_fault"] = 0
            self._state_attributes["probe_fault_desc"] = ""

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER:
            if "alarms" in self.coordinator.data:
                self._available = True
                alarms = self.coordinator.data["alarms"]

                self._state_attributes["body_fault"] = alarms["bodyFault"]["val"]
                self._state_attributes["body_fault_desc"] = alarms["bodyFault"]["desc"]
                self._state_attributes["chlor_fault"] = alarms["chlorFault"]["val"]
                self._state_attributes["chlor_fault_desc"] = alarms["chlorFault"]["desc"]
                self._state_attributes["comms"] = alarms["comms"]["val"]
                self._state_attributes["comms_desc"] = alarms["comms"]["desc"]
                self._state_attributes["flow"] = alarms["flow"]["val"]
                self._state_attributes["flow_desc"] = alarms["flow"]["desc"]
                self._state_attributes["flow_sensor_fault"] = alarms["flowSensorFault"]["val"]
                self._state_attributes["flow_sensor_fault_desc"] = alarms["flowSensorFault"]["desc"]
                self._state_attributes["freeze_protect"] = alarms["freezeProtect"]["val"]
                self._state_attributes["freeze_protect_desc"] = alarms["freezeProtect"]["desc"]

                self._state_attributes["orp"] = alarms["orp"]["val"]
                self._state_attributes["orp_desc"] = alarms["orp"]["desc"]
                self._state_attributes["orp_probe_fault"] = alarms["orpProbeFault"]["val"]
                self._state_attributes["orp_probe_fault_desc"] = alarms["orpProbeFault"]["desc"]
                self._state_attributes["orp_pump_fault"] = alarms["orpPumpFault"]["val"]
                self._state_attributes["orp_pump_fault_desc"] = alarms["orpPumpFault"]["desc"]
                self._state_attributes["orp_tank"] = alarms["orpTank"]["val"]
                self._state_attributes["orp_tank_desc"] = alarms["orpTank"]["desc"]

                self._state_attributes["ph"] = alarms["pH"]["val"]
                self._state_attributes["ph_desc"] = alarms["pH"]["desc"]
                self._state_attributes["ph_probe_fault"] = alarms["pHProbeFault"]["val"]
                self._state_attributes["ph_probe_fault_desc"] = alarms["pHProbeFault"]["desc"]
                self._state_attributes["ph_pump_fault"] = alarms["pHPumpFault"]["val"]
                self._state_attributes["ph_pump_fault_desc"] = alarms["pHPumpFault"]["desc"]
                self._state_attributes["ph_tank"] = alarms["pHTank"]["val"]
                self._state_attributes["ph_tank_desc"] = alarms["pHTank"]["desc"]

                self._state_attributes["probe_fault"] = alarms["probeFault"]["val"]
                self._state_attributes["probe_fault_desc"] = alarms["probeFault"]["desc"]

                self._value = self._state_attributes["body_fault"] + \
                    self._state_attributes["chlor_fault"] + \
                    self._state_attributes["comms"] + \
                    self._state_attributes["flow"]  + \
                    self._state_attributes["flow_sensor_fault"] + \
                    self._state_attributes["freeze_protect"] + \
                    self._state_attributes["orp"] + \
                    self._state_attributes["orp_probe_fault"] + \
                    self._state_attributes["orp_pump_fault"]  + \
                    self._state_attributes["orp_tank"] + \
                    self._state_attributes["ph"] + \
                    self._state_attributes["ph_probe_fault"] + \
                    self._state_attributes["ph_pump_fault"]  + \
                    self._state_attributes["ph_tank"] + \
                    self._state_attributes["probe_fault"]
            else:
                self._value = None
                self._available = False
                self._state_attributes["body_fault"] = 0
                self._state_attributes["body_fault_desc"] = ""
                self._state_attributes["chlor_fault"] = 0
                self._state_attributes["chlor_fault_desc"] = ""
                self._state_attributes["comms"] = 0
                self._state_attributes["comms_desc"] = ""
                self._state_attributes["flow"] = 0
                self._state_attributes["flow_desc"] = ""
                self._state_attributes["flow_sensor_fault"] = 0
                self._state_attributes["flow_sensor_fault_desc"] = ""
                self._state_attributes["freeze_protect"] = 0
                self._state_attributes["freeze_protect_desc"] = ""

                self._state_attributes["orp"] = 0
                self._state_attributes["orp_desc"] = ""
                self._state_attributes["orp_probe_fault"] = 0
                self._state_attributes["orp_probe_fault_desc"] = ""
                self._state_attributes["orp_pump_fault"] = 0
                self._state_attributes["orp_pump_fault_desc"] = ""
                self._state_attributes["orp_tank"] = 0
                self._state_attributes["orp_tank_desc"] = ""

                self._state_attributes["ph"] = 0
                self._state_attributes["ph_desc"] = ""
                self._state_attributes["ph_probe_fault"] = 0
                self._state_attributes["ph_probe_fault_desc"] = ""
                self._state_attributes["ph_pump_fault"] = 0
                self._state_attributes["ph_pump_fault_desc"] = ""
                self._state_attributes["ph_tank"] = 0
                self._state_attributes["ph_tank_desc"] = ""

                self._state_attributes["probe_fault"] = 0
                self._state_attributes["probe_fault_desc"] = ""

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
        return "Chlorinator Alarms"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_alarms"

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
            return "mdi:waves-arrow-right"
        return "mdi:wave"

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        return self._state_attributes

class ChemControllerSetpoint(PoolEquipmentEntity, NumberEntity):
    """Chemistry setpoint for ORP or pH"""
    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, chem_type: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self.chem_type = chem_type
        self.coordinator_context = object()
        self._state_attributes: dict[str, Any] = dict([])
        self._value = None
        self._available = True
        if self.chem_type in chem_controller and chem_controller[self.chem_type]["setpoint"]:
            self._value = chem_controller[self.chem_type]["setpoint"]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER
            and self.coordinator.data["id"] == self.equipment_id
            and self.chem_type in self.coordinator.data
        ):
            if "setpoint" in self.coordinator.data[self.chem_type]:
                self._value = self.coordinator.data[self.chem_type]["setpoint"]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        new_value = value
        if self.chem_type == "orp":
            new_value = int(value)
        data = {"id": self.equipment_id, self.chem_type: {"setpoint": new_value}}
        await self.coordinator.api.command(url=API_CHEM_CONTROLLER_SETPOINT, data=data)

    @property
    def mode(self) -> NumberMode:
        return NumberMode.BOX

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        """Name of the Setpoint"""
        name = "ORP" if self.chem_type == "orp" else "pH"
        return f"{name} Setpoint"

    @property
    def unique_id(self) -> str:
        """ID of the setpoint"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self.chem_type}_setpoint"

    @property
    def icon(self) -> str:
        return "mdi:creation"

    @property
    def native_value(self):
        """value"""
        return self._value

    @property
    def native_step(self) -> float:
        match(self.chem_type):
            case "ph":
                return .1
            case "orp":
                return 10
        return 0

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "mV" if self.chem_type == "orp" else None

    @property
    def native_min_value(self) -> float:
        match(self.chem_type):
            case "ph":
                return 6.8
            case "orp":
                return 400
        return 0

    @property
    def native_max_value(self) -> float:
        match(self.chem_type):
            case "ph":
                return 8.0
            case "orp":
                return 800
        return 1000

class ChemControllerIndex(PoolEquipmentEntity, NumberEntity):
    """Index values for Chem Controllers"""
    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, index_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self.index_name = index_name
        self.coordinator_context = object()
        self._state_attributes: dict[str, Any] = dict([])
        self._value = None
        self._available = True
        if self.index_name in chem_controller:
            self._value = chem_controller[self.index_name]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER
            and self.coordinator.data["id"] == self.equipment_id
            and self.index_name in self.coordinator.data
        ):
            self._value = self.coordinator.data[self.index_name]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        new_value = int(value)
        data = {"id": self.equipment_id, self.index_name: new_value}
        await self.coordinator.api.command(url=API_CHEM_CONTROLLER_SETPOINT, data=data)

    @property
    def mode(self) -> NumberMode:
        return NumberMode.BOX

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        """Name of the Setpoint"""
        match(self.index_name):
            case "calciumHardness":
                return "Calcium Hardness"
            case "borates":
                return "Borates"
            case "cyanuricAcid":
                return "Cyanuric Acid"
            case "alkalinity":
                return "Total Alkalinity"
            case _:
                return self.index_name

    @property
    def unique_id(self) -> str:
        """ID of the setpoint"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self.index_name}_setpoint"

    @property
    def icon(self) -> str:
        return "mdi:test-tube"

    @property
    def native_value(self):
        """value"""
        return self._value

    @property
    def native_step(self) -> int:
        return 1

    @property
    def native_min_value(self) -> int:
        match(self.index_name):
            case "borates":
                return 0
            case "calciumHardness":
                return 25
            case "alkalinity":
                return 25
            case "cyanuricAcid":
                return 0
        return 0

    @property
    def native_max_value(self) -> int:
        match(self.index_name):
            case "borates":
                return 201
            case "calciumHardness":
                return 800
            case "alkalinity":
                return 800
            case "cyanuricAcid":
                return 201
        return 0

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "ppm"

class ChemistryDosingStatus(PoolEquipmentEntity, SensorEntity):
    """The current dosing status for the chemical"""

    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, chemical: Any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self._state_attributes: dict[str, Any] = dict([])
        self.chem_type = chemical["type"]
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._value = None

        if "dosingStatus" in chemical:
            self._value = chemical["dosingStatus"]["desc"]
            self._available = True
            self._state_attributes["mix_time_remaining"] = self.format_duration(chemical["mixTimeRemaining"])
            self._state_attributes["dose_time_remaining"] = self.format_duration(chemical[
                "dosingTimeRemaining"
            ])
            self._state_attributes["dose_time"] = self.format_duration(chemical["doseTime"])
            self._state_attributes["dose_volume"] = chemical["doseVolume"]
            self._state_attributes["volume_dosed"] = chemical["volumeDosed"]
            self._state_attributes["dose_volume_remaining"] = chemical[
                "dosingVolumeRemaining"
            ]
        else:
            self._value = "Unknown"
            self._available = False


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
                self._state_attributes["mix_time_remaining"] = self.format_duration(chemical[
                    "mixTimeRemaining"
                ])
                self._state_attributes["dose_time_remaining"] = self.format_duration(chemical[
                    "dosingTimeRemaining"
                ])
                self._state_attributes["dose_time"] = self.format_duration(chemical["doseTime"])
                self._state_attributes["dose_volume"] = chemical["doseVolume"]
                self._state_attributes["volume_dosed"] = chemical["volumeDosed"]
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
        match(self.chem_type):
            case "ph":
                return "pH Dosing Status"
            case "orp":
                return "ORP Dosing Status"
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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self._state_attributes: dict[str, Any] = dict([])
        self.chem_type = chemical["type"]
        self._value = None

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
        match(self.chem_type):
            case "ph":
                return "Acid Demand"
            case "orp":
                return "ORP Demand"
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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
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
        match(self.chem_type):
            case "ph":
                return "Acid Tank Level"
            case "orp":
                return "Chlorine Tank Level"
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

class SaturationIndexSensor(PoolEquipmentEntity, SensorEntity):
    """Saturation Index Sensor for njsPC-HA"""

    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, index_name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self._state_attributes: dict[str, str] = dict([])
        self.index_name = index_name
        self._available = True
        self._value = None
        if self.index_name in chem_controller:
            self._value = chem_controller[self.index_name]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHEM_CONTROLLER
            and self.coordinator.data["id"] == self.equipment_id
            and self.index_name in self.coordinator.data
        ):
            self._value = self.coordinator.data[self.index_name]
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
        match(self.index_name):
            case "lsi":
                return "LSI"
            case "csi":
                return "CSI"
        return f"{self.index_name} Index"

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        # return self.coordinator.api.get_unique_id(f"ph_probe_{self._controller_id}_")
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self.index_name}_level"

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
        return "mdi:atom-variant"

    @property
    def native_unit_of_measurement(self) -> str | None:
        return None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return the state attributes."""
        return self._state_attributes

class ChemistrySensor(PoolEquipmentEntity, SensorEntity):
    """Chemistry Sensor for njsPC-HA"""

    def __init__(
        self, coordinator: NjsPCHAdata, chem_controller, chemical: Any
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHEM_CONTROLLER, data=chem_controller)
        self._state_attributes: dict[str, str] = dict([])
        self.chem_type = chemical["chemType"]
        probe = chem_controller[self.chem_type]["probe"]
        if "temperature" in probe:
            self._state_attributes["temperature"] = probe["temperature"]
        if "tempUnits" in probe:
            self._state_attributes["temp_units"] = probe["tempUnits"]["name"]
        self._value = None
        if "level" in chemical:
            self._value = chemical["level"]
        self._available = True

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
        match(self.chem_type):
            case "ph":
                return "pH Level"
            case "orp":
                return "ORP Level"
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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._value = None
        if SALT_LEVEL in chlorinator:
            self._value = chlorinator[SALT_LEVEL]
        self._available = True
        self.salt_target = None
        self.salt_required = None
        if SALT_REQUIRED in chlorinator:
            self.salt_required = chlorinator[SALT_REQUIRED]
        if SALT_TARGET in chlorinator:
            self.salt_target = chlorinator[SALT_TARGET]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
        ):
            # self._chlorinator = self.coordinator.data
            
            if SALT_LEVEL in self.coordinator.data:
                self._value = self.coordinator.data[SALT_LEVEL]
            if SALT_TARGET in self.coordinator.data:
                self.salt_target = self.coordinator.data[SALT_TARGET]
            if SALT_REQUIRED in self.coordinator.data:
                self.salt_required = self.coordinator.data[SALT_REQUIRED]
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
            "salt_target": self.salt_target,
            "salt_required": self.salt_required,
        }

class SaltTargetSensor(PoolEquipmentEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._value = None
        if SALT_TARGET in chlorinator:
            self._value = chlorinator[SALT_TARGET]
        self._available = True
        self._attr_has_entity_name = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
            and SALT_TARGET
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[SALT_TARGET]
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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._value = None
        if SALT_REQUIRED in chlorinator:
            self._value = chlorinator[SALT_REQUIRED]
        self._available = True

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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._value = None
        self.target_output = None
        if CURRENT_OUTPUT in chlorinator:
            self._value = chlorinator[CURRENT_OUTPUT]
        if TARGET_OUTPUT in chlorinator:
            self.target_output = chlorinator[TARGET_OUTPUT]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if CURRENT_OUTPUT in self.coordinator.data:
                self._value = self.coordinator.data[CURRENT_OUTPUT]
            if TARGET_OUTPUT in self.coordinator.data:
                self.target_output = self.coordinator.data[TARGET_OUTPUT]
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
        return {TARGET_OUTPUT: self.target_output}

class TargetOutputSensor(PoolEquipmentEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._value = None
        self.current_output = None
        if TARGET_OUTPUT in chlorinator:
            self._value = chlorinator[TARGET_OUTPUT]
        if CURRENT_OUTPUT in chlorinator:
            self.current_output = chlorinator[CURRENT_OUTPUT]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if TARGET_OUTPUT in self.coordinator.data:
                self._value = self.coordinator.data[TARGET_OUTPUT]
            if CURRENT_OUTPUT in self.coordinator.data:
                self.current_output = self.coordinator.data[CURRENT_OUTPUT]
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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._type = setpoint
        self._available = True
        self._value = None
        if setpoint in chlorinator:
            self._value = chlorinator[setpoint]

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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._value = None
        if SUPER_CHLOR_HOURS in chlorinator:
            self._value = chlorinator[SUPER_CHLOR_HOURS]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if SUPER_CHLOR_HOURS in self.coordinator.data:
                self._value = self.coordinator.data[SUPER_CHLOR_HOURS]
                self._available = True
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
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CHLORINATOR, data=chlorinator)
        self._value = None
        if SUPER_CHLOR in chlorinator:
            self._value = chlorinator[SUPER_CHLOR]
        self._available = True

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
