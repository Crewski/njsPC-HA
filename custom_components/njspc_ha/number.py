from .const import API_SWG_POOL_SETPOINT, DOMAIN, EVENT_CHLORINATOR
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.number import NumberEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for chlorinator in coordinator.api._config["chlorinators"]:
        new_devices.append(SWGNumber(coordinator, chlorinator))
    if new_devices:
        async_add_entities(new_devices)


class SWGNumber(CoordinatorEntity, NumberEntity):
    """Base representation of a Hello World Sensor."""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._attr_value = chlorinator["poolSetpoint"]
        self._attr_unit_of_measurement = PERCENTAGE
        self._attr_step = 1

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
        ):
            self._attr_value = self.coordinator.data["poolSetpoint"]
            self.async_write_ha_state()

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        new_value = int(value)
        print(new_value)
        # self._attr_value = new_value
        data = {"id": self._chlorinator["id"], "poolSetpoint": new_value}
        await self.coordinator.api.command(API_SWG_POOL_SETPOINT, data)
        # self.async_write_ha_state()

    @property
    def name(self):
        """Name of the sensor"""
        return self._chlorinator["name"] + " Setpoint"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'swgsetpointnumber_{self._chlorinator["id"]}'
        )

    @property
    def icon(self):
        return "mdi:creation"
