"""Platform for light integration."""


from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant


from .const import (
    PoolEquipmentClass,
    DOMAIN,
)
from .features import LightCommandButton


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    config = coordinator.api.get_config()
    new_devices = []
    for circuit in config["circuits"]:
        try:
            if circuit["type"]["isLight"]:
                for command in await coordinator.api.get_lightcommands(
                    identifier=circuit["id"]
                ):
                    new_devices.append(
                        LightCommandButton(
                            coordinator=coordinator,
                            equipment_class=PoolEquipmentClass.LIGHT,
                            circuit=circuit,
                            command=command,
                        )
                    )
        except KeyError:
            pass

    for group in config["lightGroups"]:
        for command in await coordinator.api.get_lightcommands(identifier=group["id"]):
            new_devices.append(
                LightCommandButton(
                    coordinator=coordinator,
                    equipment_class=PoolEquipmentClass.LIGHT_GROUP,
                    circuit=group,
                    command=command,
                )
            )
    if new_devices:
        async_add_entities(new_devices)
