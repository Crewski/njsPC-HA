"""Platform for switch integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.


from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    HVAC_MODES,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_FAHRENHEIT
from homeassistant.components.climate import ClimateEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EVENT_BODY

NJSPC_HVAC_ACTION_TO_HASS = {
    # Map to None if we do not know how to represent.
    0: HVACAction.OFF,
    1: HVACAction.HEATING,
    2: HVACAction.HEATING,
    3: HVACAction.COOLING,
    4: HVACAction.HEATING,
    6: HVACAction.HEATING,
    8: HVACAction.COOLING,
    128: HVACAction.OFF,
}

NJSPC_HVAC_MODE_TO_HASS = {
    # Map to None if we do not know how to represent.
    1: HVAC_MODE_OFF,
    3: HVAC_MODE_HEAT,
    4: HVAC_MODE_HEAT,
    9: HVAC_MODE_HEAT,
    25: HVAC_MODE_HEAT,
}


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for body in coordinator.api._config["temps"]["bodies"]:
        _heatmodes = {}
        for mode in await coordinator.api.get_heatmodes(body["id"]):
            _heatmodes[mode["val"]] = mode["desc"]
        new_devices.append(Climate(coordinator, body, _heatmodes))

    if new_devices:
        async_add_entities(new_devices)


class Climate(CoordinatorEntity, ClimateEntity):
    """Base representation of a Hello World Sensor."""

    def __init__(self, coordinator, body, heatmodes):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._body = body
        self._heatmodes = heatmodes

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_BODY
            and self.coordinator.data["id"] == self._body["id"]
        ):
            self._body = self.coordinator.data
            self.async_write_ha_state()

    @property
    def name(self):
        return self._body["name"] + " Heater"

    @property
    def unique_id(self):
        return self.coordinator.api.get_unique_id(f'heater_{self._body["id"]}')

    @property
    def temperature_unit(self) -> str:
        return TEMP_FAHRENHEIT

    @property
    def target_temperature(self) -> float:
        return self._body["setPoint"]

    @property
    def current_temperature(self) -> float:
        return self._body["temp"]

    @property
    def min_temp(self) -> float:
        return 70

    @property
    def max_temp(self) -> float:
        return 95

    @property
    def hvac_modes(self) -> list[HVAC_MODES]:
        return [HVAC_MODE_AUTO]

    @property
    def hvac_mode(self) -> HVACMode:
        return HVAC_MODE_AUTO
        # return NJSPC_HVAC_MODE_TO_HASS[self._body["heatMode"]["val"]]

    @property
    def preset_mode(self) -> str:
        return self._heatmodes[self._body["heatMode"]["val"]]

    @property
    def preset_modes(self) -> list[str]:
        _modes = []
        for mode in self._heatmodes.values():
            _modes.append(mode)
        return _modes

    @property
    def hvac_action(self) -> HVACAction:
        return NJSPC_HVAC_ACTION_TO_HASS[self._body["heatStatus"]["val"]]

    @property
    def supported_features(self) -> int:
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        )

    async def async_set_temperature(self, **kwargs) -> None:
        data = {"id": self._body["id"], "heatSetpoint": kwargs.get(ATTR_TEMPERATURE)}
        await self.coordinator.api.command("state/body/setPoint", data)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:

        return
        # njspc_value = next(
        #     (k for k, v in NJSPC_HVAC_MODE_TO_HASS.items() if v == hvac_mode), None
        # )

        # if njspc_value is None:
        #     self.coordinator.logger.error(
        #         "Invalid mode for set_hvac_mode: %s", hvac_mode
        #     )
        #     return
        # elif njspc_value == 0:
        #     njspc_value = 1
        # data = {"id": self._body["id"], "mode": njspc_value}
        # await self.coordinator.api.command("state/body/heatMode", data)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
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
