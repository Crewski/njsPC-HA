"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant


from .controller import FreezeProtectionSensor
from .chemistry import FlowDetectedSensor, WarningSensor, AlarmSensor
from .pumps import PumpOnSensor
from .bodies import FilterOnSensor, BodyCoveredSensor
from .features import VirtualCircuit

from .const import (
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for past config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    config = coordinator.api.get_config()

    new_devices.append(FreezeProtectionSensor(coordinator, config))
    # Add in a binary sensor for all pumps.
    for pump in config["pumps"]:
        new_devices.append(PumpOnSensor(coordinator=coordinator, pump=pump))

    for pool_filter in config["filters"]:
        new_devices.append(
            FilterOnSensor(coordinator=coordinator, pool_filter=pool_filter)
        )
    if "virtualCircuits" in config:
        for virtual_circuit in config["virtualCircuits"]:
            if "id" in virtual_circuit and "name" in virtual_circuit:
                new_devices.append(
                    VirtualCircuit(
                        coordinator=coordinator, virtual_circuit=virtual_circuit
                    )
                )

    if "bodies" in config["temps"]:  # We can have Nobody Nixie systems (equipment only)
        for body in list(config["temps"]["bodies"]):
            if "isCovered" in body:
                new_devices.append(
                    BodyCoveredSensor(coordinator=coordinator, body=body)
                )

    for chem_controller in config["chemControllers"]:
        if (
            "name" in chem_controller
            and "type" in chem_controller
            and "name" in chem_controller["type"]
            and chem_controller["type"]["name"] != "none"
        ):
            new_devices.append(
                FlowDetectedSensor(
                    coordinator=coordinator,
                    chem_controller=chem_controller
                )
            )
            if (
                "warnings" in chem_controller
            ):
                new_devices.append(
                    WarningSensor(
                        coordinator=coordinator,
                        chem_controller=chem_controller
                    )
                )
            if (
                "alarms" in chem_controller
            ):
                new_devices.append(
                    AlarmSensor(
                        coordinator=coordinator,
                        chem_controller=chem_controller
                    )
                )
    if new_devices:
        async_add_entities(new_devices)
