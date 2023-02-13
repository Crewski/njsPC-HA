"""Platform for switch integration."""
from __future__ import annotations


from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant


from .const import (
    PoolEquipmentClass,
    DOMAIN,
    SUPER_CHLOR,
)
from .features import CircuitSwitch
from .chemistry import SuperChlorSwitch
from .bodies import BodyCircuitSwitch


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    config = coordinator.api.get_config()

    for circuit in config["circuits"]:
        try:
            # For the body circuits we will be associating them with
            # the body circuit.  However this is a bit of a dance since
            # we need to do this from the temps array so we can get
            # the body name differently.  These can be mixed up because
            # of the ability to assign different functions in the i10D models
            if circuit["id"] == 1 or circuit["id"] == 6:
                for body in config["temps"]["bodies"]:
                    if body["circuit"] == circuit["id"] and "name" in circuit:
                        new_devices.append(
                            BodyCircuitSwitch(
                                coordinator=coordinator, circuit=circuit, body=body
                            )
                        )

            elif not circuit["type"]["isLight"]:
                new_devices.append(
                    CircuitSwitch(
                        coordinator=coordinator,
                        equipment_class=PoolEquipmentClass.AUX_CIRCUIT,
                        circuit=circuit,
                    )
                )
        except KeyError:
            new_devices.append(
                CircuitSwitch(
                    coordinator=coordinator,
                    equipment_class=PoolEquipmentClass.AUX_CIRCUIT,
                    circuit=circuit,
                )
            )

    for circuit in config["circuitGroups"]:
        new_devices.append(
            CircuitSwitch(
                coordinator=coordinator,
                equipment_class=PoolEquipmentClass.CIRCUIT_GROUP,
                circuit=circuit,
            )
        )

    for feature in config["features"]:
        new_devices.append(
            CircuitSwitch(
                coordinator=coordinator,
                equipment_class=PoolEquipmentClass.FEATURE,
                circuit=feature,
            )
        )

    for chlorinator in config["chlorinators"]:
        if SUPER_CHLOR in chlorinator:
            new_devices.append(
                SuperChlorSwitch(coordinator=coordinator, chlorinator=chlorinator)
            )

    if new_devices:
        async_add_entities(new_devices)
