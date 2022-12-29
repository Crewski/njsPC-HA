"""Platform for light integration."""

from .entity import NjsPCEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    API_LIGHT_RUNCOMMAND,
    DESC,
    DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    config = coordinator.api.get_config()
    new_devices = []
    for circuit in config["circuits"]:
        try:
            if circuit["type"]["isLight"]:
                for theme in await coordinator.api.get_lightcommands(
                    identifier=circuit["id"]
                ):
                    new_devices.append(
                        LightCommandButton(
                            coordinator=coordinator,
                            id=circuit["id"],
                            command=theme["name"],
                            name=f'{circuit["name"]} {theme[DESC]}',
                        )
                    )
        except KeyError:
            pass

    if new_devices:
        async_add_entities(new_devices)


class LightCommandButton(NjsPCEntity, ButtonEntity):
    """Light command button entity for njsPC-HA."""

    def __init__(self, coordinator, id, command, name):
        """Initialize the button."""
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._command = command
        self._name = name
        self._id = id

    async def async_press(self):
        """Button has been pressed"""

        data = {"id": self._id, "command": self._command}
        await self.coordinator.api.command(url=API_LIGHT_RUNCOMMAND, data=data)

    @property
    def name(self):
        """Name of button"""
        return self._name

    @property
    def unique_id(self) -> str:
        """Set unique id"""
        return self.coordinator.api.get_unique_id(
            name=f'{self._name.lower().replace(" ", "")}_{self._id}'
        )
