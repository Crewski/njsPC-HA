"""Platform for switch integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.


from homeassistant.components.light import ATTR_EFFECT, LightEntity, LightEntityFeature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    API_CIRCUIT_SETSTATE,
    API_CIRCUIT_SETTHEME,
    DOMAIN,
    EVENT_CIRCUIT,
    EVENT_LIGHTGROUP,
)

# COLORLOGIC_THEMES = {
#     20: "Cloud White",
#     21: "Deep Sea",
#     22: "Royal Blue",
#     23: "Afternoon Skies",
#     24: "Aqua Green",
#     25: "Emerald",
#     26: "Warm Red",
#     27: "Flamingo",
#     28: "Vivid Violet",
#     29: "Sangria",
#     30: "Voodoo Lounge",
#     31: "Twilight",
#     32: "Tranquility",
#     33: "Gemstone",
#     34: "USA",
#     35: "Mardi Gras",
#     36: "Cabaret",
# }

# INTELLIBRITE_THEMES = {
#     0: "White",
#     1: "Green",
#     2: "Blue",
#     3: "Magenta",
#     4: "Red",
#     5: "SAm Mode",
#     6: "Party",
#     7: "Romance",
#     8: "Caribbean",
#     9: "American",
#     10: "Sunset",
#     11: "Royal",
# }


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for circuit in coordinator.api._config["circuits"]:
        try:
            if circuit["type"]["isLight"]:
                _lightthemes = {}
                for theme in await coordinator.api.get_lightthemes(circuit["id"]):
                    _lightthemes[theme["val"]] = theme["desc"]
                new_devices.append(
                    CircuitLight(coordinator, circuit, _lightthemes, EVENT_CIRCUIT)
                )
        except KeyError:
            pass
    for group in coordinator.api._config["lightGroups"]:
        _lightthemes = {}
        for theme in await coordinator.api.get_lightthemes(group["id"]):
            _lightthemes[theme["val"]] = theme["desc"]
        new_devices.append(
            CircuitLight(coordinator, group, _lightthemes, EVENT_LIGHTGROUP)
        )

    if new_devices:
        async_add_entities(new_devices)


# This base class shows the common properties and methods for a sensor as used in this
# example. See each sensor for further details about properties and methods that
# have been overridden.
class CircuitLight(CoordinatorEntity, LightEntity):
    """Base representation of a Hello World Sensor."""

    def __init__(self, coordinator, circuit, lightthemes, event):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._circuit = circuit
        self._lightthemes = lightthemes
        self._event = event

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self._circuit["id"]
        ):
            self._circuit = self.coordinator.data
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        if ATTR_EFFECT in kwargs:
            # effect_list = None
            # if self._circuit["type"]["theme"] == "colorlogic":
            #     effect_list = COLORLOGIC_THEMES
            # elif self._circuit["type"]["theme"] == "intellibrite":
            #     effect_list = INTELLIBRITE_THEMES

            if len(self._lightthemes) > 0:

                njspc_value = next(
                    (
                        k
                        for k, v in self._lightthemes.items()
                        if v == kwargs[ATTR_EFFECT]
                    ),
                    None,
                )
                if njspc_value is None:
                    self.coordinator.logger.error(
                        "Invalid theme for colorlogic light: %s", kwargs[ATTR_EFFECT]
                    )
                    return
                data = {"id": self._circuit["id"], "theme": njspc_value}
                await self.coordinator.api.command(API_CIRCUIT_SETTHEME, data)
                return

        data = {"id": self._circuit["id"], "state": True}
        await self.coordinator.api.command(API_CIRCUIT_SETSTATE, data)

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._circuit["id"], "state": False}
        await self.coordinator.api.command(API_CIRCUIT_SETSTATE, data)

    @property
    def name(self):
        return self._circuit["name"]

    @property
    def unique_id(self) -> str:
        """Set unique device_id"""
        return self.coordinator.api.get_unique_id(f'circuit_{self._circuit["id"]}')

    @property
    def is_on(self):
        try:
            return self._circuit["isOn"]
        except KeyError:
            return False

    @property
    def effect(self) -> str:
        """Which effect is active"""
        try:
            theme_value = self._circuit["lightingTheme"]["val"]
            return self._lightthemes[theme_value]
        except:
            return None

    @property
    def effect_list(self) -> list[str]:
        """Get list of effects"""
        if len(self._lightthemes) > 0:
            _effects = []
            for effect in self._lightthemes.values():
                _effects.append(effect)
            return _effects
        return None
        # try:
        #     _effects = []
        #     _list = None
        #     theme = self._circuit["type"]["theme"]
        #     if theme == "colorlogic":
        #         _list = COLORLOGIC_THEMES
        #     elif theme == "intellibrite":
        #         _list = INTELLIBRITE_THEMES

        #     if _list is not None:
        #         for effect in _list.values():
        #             _effects.append(effect)
        #         return _effects

        #     return None
        # except:
        #     return None

    @property
    def supported_features(self) -> int:
        """See if light has effects"""
        if len(self._lightthemes) > 0:
            return LightEntityFeature.EFFECT

        return 0
        # try:
        #     theme = self._circuit["type"]["theme"]
        #     if theme in ("colorlogic", "intellibrite"):
        #         return LightEntityFeature.EFFECT

        #     return 0
        # except:
        #     return 0
