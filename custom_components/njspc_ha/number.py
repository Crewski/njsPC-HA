from .const import API_CHLORINATOR_POOL_SETPOINT, API_CHLORINATOR_SPA_SETPOINT, DOMAIN, EVENT_CHLORINATOR, POOL_SETPOINT, SPA_SETPOINT
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.number import NumberEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for chlorinator in coordinator.api._config["chlorinators"]:
        if chlorinator["body"]["val"] == 0 or chlorinator["body"]["val"] == 32:
            # pool setpoint
            new_devices.append(SWGNumber(coordinator, chlorinator, POOL_SETPOINT, API_CHLORINATOR_POOL_SETPOINT))
        if chlorinator["body"]["val"] == 1 or chlorinator["body"]["val"] == 32:
            # spa setpoint
            new_devices.append(SWGNumber(coordinator, chlorinator, SPA_SETPOINT, API_CHLORINATOR_SPA_SETPOINT))

    if new_devices:
        async_add_entities(new_devices)


class SWGNumber(CoordinatorEntity, NumberEntity):
    """Number for setting SWG Setpoint in njsPC-HA."""

    def __init__(self, coordinator, chlorinator, type, command):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._type = type
        self._attr_value = chlorinator[type]
        self._attr_unit_of_measurement = PERCENTAGE
        self._attr_step = 1
        self._command = command
        

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
        ):
            self._attr_value = self.coordinator.data[self._type]
            self.async_write_ha_state()

    async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        new_value = int(value)
        data = {"id": self._chlorinator["id"], "setPoint": new_value}
        await self.coordinator.api.command(self._command, data)

    @property
    def name(self):
        """Name of the sensor"""
        return self._chlorinator["name"] + " Setpoint"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'swg{self._type.lower()}_{self._chlorinator["id"]}'
        )

    @property
    def icon(self):
        return "mdi:creation"
