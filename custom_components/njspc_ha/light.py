"""Platform for light integration."""

from .entity import NjsPCEntity
from homeassistant.components.light import ATTR_EFFECT, LightEntity, LightEntityFeature

from .const import (
    API_CIRCUIT_SETSTATE,
    API_CIRCUIT_SETTHEME,
    API_LIGHTGROUP_SETSTATE,
    DESC,
    DOMAIN,
    EVENT_AVAILABILITY,
    EVENT_CIRCUIT,
    EVENT_LIGHTGROUP,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    config = coordinator.api.get_config()
    new_devices = []
    for circuit in config["circuits"]:
        try:
            if circuit["type"]["isLight"]:
                _lightthemes = {}
                for theme in await coordinator.api.get_lightthemes(circuit["id"]):
                    _lightthemes[theme["val"]] = theme[DESC]
                new_devices.append(
                    CircuitLight(
                        coordinator=coordinator,
                        circuit=circuit,
                        lightthemes=_lightthemes,
                        event=EVENT_CIRCUIT,
                        command=API_CIRCUIT_SETSTATE,
                    )
                )
        except KeyError:
            pass
    for group in config["lightGroups"]:
        _lightthemes = {}
        for theme in await coordinator.api.get_lightthemes(group["id"]):
            _lightthemes[theme["val"]] = theme[DESC]
        new_devices.append(
            CircuitLight(
                coordinator=coordinator,
                circuit=group,
                lightthemes=_lightthemes,
                event=EVENT_LIGHTGROUP,
                command=API_LIGHTGROUP_SETSTATE,
            )
        )

    if new_devices:
        async_add_entities(new_devices)


class CircuitLight(NjsPCEntity, LightEntity):
    """Light entity for njsPC-HA."""

    def __init__(self, coordinator, circuit, lightthemes, event, command):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._circuit = circuit
        self._lightthemes = lightthemes
        self._event = event
        self._command = command
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self._circuit["id"]
        ):
            self._circuit = self.coordinator.data
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        if ATTR_EFFECT in kwargs:

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
                await self.coordinator.api.command(url=API_CIRCUIT_SETTHEME, data=data)
                return

        data = {"id": self._circuit["id"], "state": True}
        await self.coordinator.api.command(url=self._command, data=data)

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._circuit["id"], "state": False}
        await self.coordinator.api.command(url=self._command, data=data)

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        return self._circuit["name"]

    @property
    def unique_id(self) -> str:
        """Set unique device_id"""
        return self.coordinator.api.get_unique_id(name=f'circuit_{self._circuit["id"]}')

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
        except KeyError:
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

    @property
    def supported_features(self) -> int:
        """See if light has effects"""
        if len(self._lightthemes) > 0:
            return LightEntityFeature.EFFECT
        return 0
