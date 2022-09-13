"""Platform for climate integration."""

from homeassistant.components.climate.const import (
    HVAC_MODES,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_FAHRENHEIT, TEMP_CELSIUS
from homeassistant.components.climate import ClimateEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EVENT_AVAILABILITY, EVENT_BODY

NJSPC_HVAC_ACTION_TO_HASS = {
    # Map to None if we do not know how to represent.
    'off':      HVACAction.OFF,
    'heater':   HVACAction.HEATING,
    'solar':    HVACAction.HEATING,
    'hpheat':   HVACAction.HEATING,
    'hybheat':  HVACAction.HEATING,
    'mtheat':   HVACAction.HEATING,
    'cooling':  HVACAction.COOLING,
    'hpcool':   HVACAction.COOLING,
    'cooldown': HVACAction.OFF,
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add climates for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    if len(coordinator.api._config["heaters"]) == 0:
        # no heaters are available
        return

    new_devices = []
    _units = coordinator.api._config["temps"]["units"]["val"]
    for body in coordinator.api._config["temps"]["bodies"]:
        _heatmodes = {}
        for mode in await coordinator.api.get_heatmodes(body["id"]):
            _heatmodes[mode["val"]] = mode["desc"]
        _has_cooling = await coordinator.api.has_cooling(body["type"]["val"])
        new_devices.append(Climate(coordinator, body, _heatmodes, _units, _has_cooling))

    if new_devices:
        async_add_entities(new_devices)


class Climate(CoordinatorEntity, ClimateEntity):
    """Climate entity for njsPC-HA"""

    def __init__(self, coordinator, body, heatmodes, units, has_cooling):
        """Initialize the climate."""
        super().__init__(coordinator)
        self._body = body
        self._heatmodes = heatmodes
        self._units = units
        self._available = True
        self._has_cooling = has_cooling

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_BODY
            and self.coordinator.data["id"] == self._body["id"]
        ):
            self._body = self.coordinator.data
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        """Do not need to poll"""
        return False

    @property
    def available(self):
        """Entity availability"""
        return self._available

    @property
    def name(self):
        """Set name of entity"""
        return self._body["name"] + " Heater"

    @property
    def unique_id(self):
        """Set unique id"""
        return self.coordinator.api.get_unique_id(f'heater_{self._body["id"]}')

    @property
    def temperature_unit(self) -> str:
        """Set temperature units"""
        return TEMP_FAHRENHEIT if self._units == 0 else TEMP_CELSIUS

    @property
    def target_temperature(self) -> float:
        """Set target temp if cooling isn't enabled"""
        return self._body["setPoint"] if self._has_cooling is False else None

    @property
    def target_temperature_high(self) -> float:
        """Set cooling temp if cooling is enabled"""
        return self._body["coolSetpoint"] if self._has_cooling is True else None

    @property
    def target_temperature_low(self) -> float:
        """Set heating temp if cooling is enabled"""
        return self._body["setPoint"] if self._has_cooling is True else None

    @property
    def current_temperature(self) -> float:
        """Get current temp"""
        return self._body["temp"]

    @property
    def min_temp(self) -> float:
        """Set min temp specific to body type"""
        try:
            if self._body["type"]["val"] == 0:
                # pool setpoint
                return 70 if self._units == 0 else 21
            else:
                # spa setpoint
                return 90 if self._units == 0 else 32
        except:
            # default to pool
            return 70 if self._units == 0 else 21

    @property
    def max_temp(self) -> float:
        """Set max temp specific to body type"""
        try:
            if self._body["type"]["val"] == 0:
                # pool setpoint
                return 95 if self._units == 0 else 35
            else:
                # spa setpoint
                return 104 if self._units == 0 else 40
        except:
            # default to pool
            return 95 if self._units == 0 else 35

    @property
    def hvac_modes(self) -> list[HVAC_MODES]:
        """if only off and heat are options, add them as modes, else use presets"""
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
            return HVACMode.OFF if self._body["heatMode"]["val"] <= 1 else _on
        return HVACMode.AUTO

    @property
    def preset_mode(self) -> str:
        if len(self._heatmodes) <= 2:
            return None
        try:
            return self._heatmodes[self._body["heatMode"]["val"]]
        except:
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
            return NJSPC_HVAC_ACTION_TO_HASS[self._body["heatStatus"]["name"]]
        except:
            return HVACAction.OFF

    @property
    def supported_features(self) -> int:
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

    async def async_set_temperature(self, **kwargs) -> None:
        data = {"id": self._body["id"]}
        if "target_temp_low" in kwargs:
            data["heatSetpoint"] = kwargs.get("target_temp_low")
        if "target_temp_high" in kwargs:
            data["coolSetpoint"] = kwargs.get("target_temp_high")
        if ATTR_TEMPERATURE in kwargs:
            data["heatSetpoint"] = kwargs.get(ATTR_TEMPERATURE)
        # data = {"id": self._body["id"], "heatSetpoint": kwargs.get(ATTR_TEMPERATURE)}
        await self.coordinator.api.command("state/body/setPoint", data)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if len(self._heatmodes) <= 2:
            njspc_value = None
            if hvac_mode == HVACMode.OFF:
                njspc_value = 1
            else:
                njspc_value = next(
                    (k for k, v in self._heatmodes.items() if k > 1), None
                )
            if njspc_value is None:
                self.coordinator.logger.error(
                    "Invalid mode for set_hvac_mode: %s", hvac_mode
                )
                return
            data = {"id": self._body["id"], "mode": njspc_value}
            await self.coordinator.api.command("state/body/heatMode", data)
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
        data = {"id": self._body["id"], "mode": njspc_value}
        await self.coordinator.api.command("state/body/heatMode", data)
