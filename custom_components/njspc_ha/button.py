"""Platform for light integration."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    API_LIGHT_RUNCOMMAND,
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for circuit in coordinator.api._config["circuits"]:
        try:
            if circuit["type"]["isLight"]:
                for theme in await coordinator.api.get_lightcommands(circuit["id"]):
                    new_devices.append(
                        LightCommandButton(coordinator, circuit["id"], theme["name"], f'{circuit["name"]} {theme[DESC]}')
                    )
        except KeyError:
            pass


    if new_devices:
        async_add_entities(new_devices)


class LightCommandButton(ButtonEntity):
    """Light command button entity for njsPC-HA."""


    def __init__(self, coordinator, id, command, name):
        """Initialize the button."""
        self.coordinator = coordinator
        self._command = command
        self._name = name
        self._id = id

    async def async_press(self):
        """Button has been pressed"""

        data = {"id": self._id, "command": self._command}
        await self.coordinator.api.command(API_LIGHT_RUNCOMMAND, data)


    @property
    def name(self):
        """Name of button"""
        return self._name

    @property
    def unique_id(self) -> str:
        """Set unique id"""
        return self.coordinator.api.get_unique_id(f'{self._name.lower().replace(" ", "")}_{self._id}')


