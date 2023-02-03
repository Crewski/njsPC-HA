"""Platform for body integration."""
from __future__ import annotations

from typing import Any


from homeassistant.const import UnitOfTemperature, UnitOfPressure, ATTR_TEMPERATURE, PERCENTAGE

from homeassistant.components.switch import SwitchEntity
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import PoolEquipmentEntity
from .__init__ import NjsPCHAdata
from .const import (
    PoolEquipmentClass,
    PoolEquipmentModel,
    EVENT_TEMPS,
    EVENT_AVAILABILITY,
    EVENT_BODY,
    EVENT_FILTER,
    API_CIRCUIT_SETSTATE,
    API_TEMPERATURE_SETPOINT,
    API_SET_HEATMODE,
)

NJSPC_HVAC_ACTION_TO_HASS = {
    # Map to None if we do not know how to represent.
    "off": HVACAction.OFF,
    "heater": HVACAction.HEATING,
    "solar": HVACAction.HEATING,
    "hpheat": HVACAction.HEATING,
    "hybheat": HVACAction.HEATING,
    "mtheat": HVACAction.HEATING,
    "cooling": HVACAction.COOLING,
    "hpcool": HVACAction.COOLING,
    "cooldown": HVACAction.OFF,
}
class FilterOnSensor(PoolEquipmentEntity, BinarySensorEntity):
    """The current running state for a pump"""

    def __init__(self, coordinator: NjsPCHAdata, pool_filter: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.FILTER
        self.equipment_name = pool_filter["name"]
        self.equipment_id = pool_filter["id"]
        self.equipment_model = PoolEquipmentModel.FILTER
        self._value = pool_filter["isOn"]
        self._available = True
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.equipment_class}_ison"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_FILTER
            and self.coordinator.data["id"] == self.equipment_id
        ):
            self._value = self.coordinator.data["isOn"]
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
        return "Filter State"

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
            return "mdi:filter"
        return "mdi:filter-off"

class FilterCleanSensor(PoolEquipmentEntity, SensorEntity):
    """Sensor for filter clean percentage"""

    def __init__(self, coordinator: NjsPCHAdata, pool_filter: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.FILTER
        self.equipment_id = pool_filter["id"]
        self.equipment_name = pool_filter["name"]
        self.equipment_model = PoolEquipmentModel.FILTER
        self.coordinator_context = object()
        self._value = pool_filter["cleanPercentage"]
        self._available = True
        # Give us a good entity id
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.equipment_class}_cleanpercent"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if (
            self.coordinator.data["event"] == EVENT_FILTER
            and "id" in self.coordinator.data
            and self.coordinator.data["id"] == self.equipment_id
        ):
            self._value = self.coordinator.data["cleanPercentage"]
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
        return "Clean Percentage"

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_cleanpercent"

    @property
    def state_class(self) -> str:
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        return self._value

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.POWER_FACTOR

    @property
    def native_unit_of_measurement(self) -> str | UnitOfTemperature | None:
        return PERCENTAGE

class FilterPressureSensor(PoolEquipmentEntity, SensorEntity):
    """Sensor for filter pressure"""

    def __init__(self, coordinator: NjsPCHAdata, pool_filter: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.FILTER
        self.equipment_id = pool_filter["id"]
        self.equipment_name = pool_filter["name"]
        self.equipment_model = PoolEquipmentModel.FILTER
        self.coordinator_context = object()
        self._value = pool_filter["pressure"]
        self._units = pool_filter["pressureUnits"]["name"]
        self._available = True
        # Give us a good entity id
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{self.equipment_class}_pressure"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if (
            self.coordinator.data["event"] == EVENT_FILTER
            and "id" in self.coordinator.data
            and self.coordinator.data["id"] == self.equipment_id
        ):
            self._value = self.coordinator.data["pressure"]
            self._units = self.coordinator.data["pressureUnits"]["name"]
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
        return "Pressure"

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_pressure"

    @property
    def state_class(self) -> str:
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> float:
        return self._value

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.PRESSURE

    @property
    def native_unit_of_measurement(self) -> str | UnitOfTemperature | None:
        match self._units:
            case "psi":
                return UnitOfPressure.PSI
            case "kPa":
                return UnitOfPressure.KPA
            case "Pa":
                return UnitOfPressure.PA
            case "atm":
                return UnitOfPressure.INHG
            case "bar":
                return UnitOfPressure.BAR
            case _:
                return UnitOfPressure.PSI

class BodyTempSensor(PoolEquipmentEntity, SensorEntity):
    """Body Temp Sensor for njsPC-HA"""

    def __init__(self, coordinator: NjsPCHAdata, units: str, body: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = PoolEquipmentClass.BODY
        self.equipment_id = body["id"]
        self.equipment_name = body["name"]
        self.equipment_model = PoolEquipmentModel.BODY
        self.coordinator_context = object()
        self._units = units
        self._value = body["temp"]
        self._available = True
        # Give us a good entity id
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_temperature"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        if (
            self.coordinator.data["event"] == EVENT_TEMPS
            and "bodies" in self.coordinator.data
        ):
            body = None
            for b in list(self.coordinator.data["bodies"]):
                if b["id"] == self.equipment_id:
                    body = b
                    break
            if body is not None:
                if "temp" in body:
                    self._value = round(body["temp"], 2)
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
        return "Temperature"

    @property
    def unique_id(self) -> str:
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_temperature"

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


class BodyCircuitSwitch(PoolEquipmentEntity, SwitchEntity):
    """Body Circuit switch for njsPC-HA"""

    def __init__(
        self,
        coordinator: NjsPCHAdata,
        circuit,
        body,
    ) -> None:
        """Initialize the sensor."""
        # Need to add delays to this at some point.  We will get
        # delay messages when this happens
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.BODY
        self.equipment_name = body["name"]
        self.equipment_id = body["id"]
        self.equipment_model = PoolEquipmentModel.BODY
        self.body_type = body["type"]["name"]
        self._event = None
        self._command = None
        self._available = True
        self._value = False
        self.circuit_id = circuit["id"]
        self.circuit_name = circuit["name"]
        if "isOn" in circuit:
            self._value = circuit["isOn"]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self.circuit_id
        ):
            if "isOn" in self.coordinator.data:
                self._value = self.coordinator.data["isOn"]
            else:
                self._value = False
            if "name" in self.coordinator.data:
                self.circuit_name = self.coordinator.data["name"]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.circuit_id, "state": True}
        await self.coordinator.api.command(url=API_CIRCUIT_SETSTATE, data=data)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.circuit_id, "state": False}
        await self.coordinator.api.command(url=API_CIRCUIT_SETSTATE, data=data)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        return self.circuit_name

    @property
    def unique_id(self) -> str:
        """Set unique device_id"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_state"

    @property
    def is_on(self) -> str:
        return self._value

    @property
    def icon(self) -> str:
        if self.body_type == "pool":
            return "mdi:pool"
        elif self.body_type == "spa":
            return "mdi:hot-tub"
        else:
            return "mdi:toggle-switch-variant"


class BodyHeater(PoolEquipmentEntity, ClimateEntity):
    """Climate entity for njsPC-HA"""

    # When thinking about heaters for pool/spa you need to not think of it so much
    # like a home thermostat.  While a home thermostat can be made to work
    # the difference become a struggle to overcome.
    # Home Thermostats typical assume only two heat/cool sources that are tied
    # directly to the mode.  For instance, if it is heating the furnace is on and
    # if it is cooling the air conditioner is on.  Finally, (and of no use to us),
    # the blower can be on at different speeds to enhance the distribution.
    #
    # For Pool thermostats the heat source can and will be varied depending on how
    # many are installed and which combination is the most efficient.  On a simple
    # heater/solar installation both heat sources can fill the potential for heating
    # and the solar can be be used for cooling depending on the conditions.  When you
    # throw hybrid heaters or heat pumps with cooling options into the mix the
    # calculation for which component of the heater is active becomes a bit goofier.
    #
    # Finally, we must not forget that in shared body systems one heater will act
    # like two devices and be mutually exclusive to the particular body.  Our
    # representation here reflects this by attaching the heater to the body device.
    # This is not the heater device and we may add it later to show diagnostic data.
    def __init__(self, coordinator, body, heatmodes, units, has_cooling) -> None:
        """Initialize the body heater."""
        super().__init__(coordinator)
        self.equipment_class = PoolEquipmentClass.BODY
        self.equipment_id = body["id"]
        self.equipment_name = body["name"]
        self.equipment_model = PoolEquipmentModel.BODY
        self._heatmodes = heatmodes
        self._units = units
        self._available = True
        self._has_cooling = has_cooling
        self.heat_setpoint = body["setPoint"]
        self.cool_setpoint = body["coolSetpoint"]
        self.heat_mode = None
        self.heat_status = None
        self.body_temperature = None
        if "temp" in body:
            self.body_temperature = body["temp"]
        if "heatMode" in body:
            self.heat_mode = body["heatMode"]
        if "heatStatus" in body:
            self.heat_status = body["heatStatus"]
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{body['name']}_heater"

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_BODY
            and self.coordinator.data["id"] == self.equipment_id
        ):
            body = self.coordinator.data
            # Because of the way Pentair reports these they may
            # not yet be set so always check for the value
            # in the event
            if "temp" in body:
                self.body_temperature = body["temp"]
            if "setPoint" in body:
                self.heat_setpoint = body["setPoint"]
            if "coolSetpoint" in body:
                self.cool_setpoint = body["coolSetpoint"]
            if "heatStatus" in body:
                self.heat_status = body["heatStatus"]
            if "heatMode" in body:
                self.heat_mode = body["heatMode"]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        """Do not need to poll"""
        return False

    @property
    def available(self) -> bool:
        """Entity availability"""
        return self._available

    @property
    def name(self) -> str:
        """Set name of entity"""
        return "Heater"

    @property
    def unique_id(self) -> str:
        """Set unique id"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_heater"

    @property
    def temperature_unit(self) -> str:
        """Set temperature units"""
        return (
            UnitOfTemperature.FAHRENHEIT
            if self._units == 0
            else UnitOfTemperature.CELSIUS
        )

    @property
    def target_temperature(self) -> float | None:
        """Set target temp if cooling isn't enabled"""
        return self.heat_setpoint if self._has_cooling is False else None

    @property
    def target_temperature_high(self) -> float | None:
        """Set cooling temp if cooling is enabled"""
        return self.cool_setpoint if self._has_cooling is True else None

    @property
    def target_temperature_low(self) -> float | None:
        """Set heating temp if cooling is enabled"""
        return self.heat_setpoint if self._has_cooling is True else None

    @property
    def current_temperature(self) -> float | None:
        """Get current temp"""
        return self.body_temperature

    @property
    def min_temp(self) -> float:
        """Set min temp specific to body type"""
        return 40 if self._units == 0 else 21
        # try:
        #     if self._body["type"]["val"] == 0:
        #         # pool setpoint
        #         return 70 if self._units == 0 else 21
        #     else:
        #         # spa setpoint
        #         return 90 if self._units == 0 else 32
        # except:
        #     # default to pool
        #     return 70 if self._units == 0 else 21

    @property
    def max_temp(self) -> float:
        """Set max temp specific to body type"""
        return 104 if self._units == 0 else 40
        # try:
        #     if self._body["type"]["val"] == 0:
        #         # pool setpoint
        #         return 95 if self._units == 0 else 35
        #     else:
        #         # spa setpoint
        #         return 104 if self._units == 0 else 40
        # except:
        #     # default to pool
        #     return 95 if self._units == 0 else 35

    @property
    def hvac_modes(self) -> list[HVACMode] | list[str]:
        """if only off and heat are options, add them as modes, else use presets"""
        # The typical list of heat modes are:
        # off
        # gas only
        # solar only
        # solar preferred
        # heatpump only
        # heatpump preferred
        # hybrid
        # dual heat
        _on: HVACMode = (
            HVACMode.HEAT_COOL if self._has_cooling is True else HVACMode.HEAT
        )
        return [HVACMode.OFF, _on] if len(self._heatmodes) <= 2 else [HVACMode.AUTO]

    @property
    def hvac_mode(self) -> HVACMode:
        if len(self._heatmodes) <= 2:
            # if heatMode is 0/1 it is off, anything else is heat
            _on: HVACMode = (
                HVACMode.HEAT_COOL if self._has_cooling is True else HVACMode.HEAT
            )
            return HVACMode.OFF if self.heat_mode["name"] == "off" else _on
        return HVACMode.AUTO

    @property
    def preset_mode(self) -> str:
        if len(self._heatmodes) <= 2:
            return None
        try:
            return self._heatmodes[self.heat_mode["val"]]
        except KeyError:
            return "Off"

    @property
    def preset_modes(self) -> list[str]:
        if len(self._heatmodes) <= 2:
            return None
        _modes = []
        for mode in self._heatmodes.values():
            _modes.append(mode)
        return _modes

    @property
    def hvac_action(self) -> HVACAction:
        try:
            return NJSPC_HVAC_ACTION_TO_HASS[self.heat_status["name"]]
        except KeyError:
            return HVACAction.OFF

    @property
    def supported_features(self) -> ClimateEntityFeature:
        if len(self._heatmodes) <= 2 and self._has_cooling is True:
            # only 1 heater that supports cooling
            return ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        elif len(self._heatmodes) <= 2:
            # only 1 heater that doesn't support cooling
            return ClimateEntityFeature.TARGET_TEMPERATURE
        elif self._has_cooling is True:
            # multiple heaters that support cooling
            return (
                ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
                | ClimateEntityFeature.PRESET_MODE
            )
        else:
            # multiple heaters that don't support cooling
            return (
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.PRESET_MODE
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        data = {"id": self.equipment_id}
        if "target_temp_low" in kwargs:
            data["heatSetpoint"] = kwargs.get("target_temp_low")
        if "target_temp_high" in kwargs:
            data["coolSetpoint"] = kwargs.get("target_temp_high")
        if ATTR_TEMPERATURE in kwargs:
            data["heatSetpoint"] = kwargs.get(ATTR_TEMPERATURE)
        # data = {"id": self._body["id"], "heatSetpoint": kwargs.get(ATTR_TEMPERATURE)}
        await self.coordinator.api.command(url=API_TEMPERATURE_SETPOINT, data=data)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if len(self._heatmodes) <= 2:
            njspc_value = None
            if hvac_mode == HVACMode.OFF:
                njspc_value = next(
                    (k for k, v in self._heatmodes.items() if v.lower() == "off"), None
                )
            else:
                njspc_value = next(
                    (k for k, v in self._heatmodes.items() if v.lower() != "off"), None
                )
            if njspc_value is None:
                self.coordinator.logger.error(
                    "Invalid mode for set_hvac_mode: %s", hvac_mode
                )
                return
            data = {"id": self.equipment_id, "mode": njspc_value}
            await self.coordinator.api.command(url=API_SET_HEATMODE, data=data)
        return

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if len(self._heatmodes) <= 2:
            return None

        njspc_value = next(
            (k for k, v in self._heatmodes.items() if v == preset_mode), None
        )

        if njspc_value is None:
            self.coordinator.logger.error(
                "Invalid mode for set_hvac_mode: %s", preset_mode
            )
            return
        data = {"id": self.equipment_id, "mode": njspc_value}
        await self.coordinator.api.command(url=API_SET_HEATMODE, data=data)
