"""Number platform for njsPC-HA"""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, POOL_SETPOINT, SPA_SETPOINT, SUPER_CHLOR_HOURS
from .chemistry import (
    ChlorinatorSetpoint,
    SuperChlorHours,
    ChemControllerSetpoint,
    ChemControllerIndex,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    config = coordinator.api.get_config()
    new_devices = []
    for chlorinator in config["chlorinators"]:
        try:
            if chlorinator["body"]["val"] == 0 or chlorinator["body"]["val"] == 32:
                # pool setpoint
                new_devices.append(
                    ChlorinatorSetpoint(coordinator, chlorinator, POOL_SETPOINT)
                )
        except KeyError:
            pass
        try:
            if chlorinator["body"]["val"] == 1 or chlorinator["body"]["val"] == 32:
                # spa setpoint
                new_devices.append(
                    ChlorinatorSetpoint(
                        coordinator=coordinator,
                        chlorinator=chlorinator,
                        setpoint=SPA_SETPOINT,
                    )
                )
        except KeyError:
            pass
        if SUPER_CHLOR_HOURS in chlorinator:
            new_devices.append(
                SuperChlorHours(coordinator=coordinator, chlorinator=chlorinator)
            )
    for chem_controller in config["chemControllers"]:
        try:
            if "ph" in chem_controller and chem_controller["ph"]["enabled"] is True:
                new_devices.append(
                    ChemControllerSetpoint(
                        coordinator=coordinator,
                        chem_controller=chem_controller,
                        chem_type="ph",
                    )
                )
            if "orp" in chem_controller and chem_controller["orp"]["enabled"] is True:
                new_devices.append(
                    ChemControllerSetpoint(
                        coordinator=coordinator,
                        chem_controller=chem_controller,
                        chem_type="orp",
                    )
                )
            new_devices.append(
                ChemControllerIndex(
                    coordinator=coordinator,
                    chem_controller=chem_controller,
                    index_name="alkalinity",
                )
            )
            new_devices.append(
                ChemControllerIndex(
                    coordinator=coordinator,
                    chem_controller=chem_controller,
                    index_name="cyanuricAcid",
                )
            )
            new_devices.append(
                ChemControllerIndex(
                    coordinator=coordinator,
                    chem_controller=chem_controller,
                    index_name="calciumHardness",
                )
            )
            new_devices.append(
                ChemControllerIndex(
                    coordinator=coordinator,
                    chem_controller=chem_controller,
                    index_name="borates",
                )
            )

        except KeyError:
            pass
    if new_devices:
        async_add_entities(new_devices)
