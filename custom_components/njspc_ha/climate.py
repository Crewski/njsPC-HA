"""Platform for climate integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant

from .bodies import BodyHeater
from .const import DESC, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add climates for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    config = coordinator.api.get_config()
    if len(config["heaters"]) == 0:
        # no heaters are available
        return

    new_devices = []
    _units = config["temps"]["units"]["val"]
    for body in config["temps"]["bodies"]:
        # Only include body heaters that are selected into the body. These are from
        # the heater definition where the body selection is included.
        if "heaterOptions" in body:
            if body["heaterOptions"]["total"] == 0:
                continue
        else:
            continue
        _has_cooling = False
        if "hasCoolSetpoint" in body["heaterOptions"]:
            _has_cooling = body["heaterOptions"]["hasCoolSetpoint"]
        _heatmodes = {}
        for mode in await coordinator.api.get_heatmodes(identifier=body["id"]):
            _heatmodes[mode["val"]] = mode[DESC]
        # Below is not needed the heater options will tell us if the cooling setpoint
        # should be available and we should not have to round trip.
        # _has_cooling = await coordinator.api.has_cooling(body=body["type"]["val"])
        new_devices.append(
            BodyHeater(
                coordinator=coordinator,
                body=body,
                heatmodes=_heatmodes,
                units=_units,
                has_cooling=_has_cooling,
            )
        )

    if new_devices:
        async_add_entities(new_devices)
