from .const import (
    API_CHLORINATOR_POOL_SETPOINT,
    API_CHLORINATOR_SPA_SETPOINT,
    DOMAIN,
    EVENT_AVAILABILITY,
    EVENT_CHLORINATOR,
    POOL_SETPOINT,
    SPA_SETPOINT,
    API_CONFIG_CHLORINATOR,
    SUPER_CHLOR_HOURS
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.number import NumberEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for chlorinator in coordinator.api._config["chlorinators"]:
        try:
            if chlorinator["body"]["val"] == 0 or chlorinator["body"]["val"] == 32:
                # pool setpoint
                new_devices.append(
                    SWGNumber(
                        coordinator,
                        chlorinator,
                        POOL_SETPOINT,
                        API_CHLORINATOR_POOL_SETPOINT,
                    )
                )
        except KeyError:
            pass
        try:
            if chlorinator["body"]["val"] == 1 or chlorinator["body"]["val"] == 32:
                # spa setpoint
                new_devices.append(
                    SWGNumber(
                        coordinator, chlorinator, SPA_SETPOINT, API_CHLORINATOR_SPA_SETPOINT
                    )
                )
        except KeyError:
            pass
        if SUPER_CHLOR_HOURS in chlorinator:
            new_devices.append(HoursNumber(coordinator, chlorinator, API_CONFIG_CHLORINATOR))

    if new_devices:
        async_add_entities(new_devices)


class SWGNumber(CoordinatorEntity, NumberEntity):
    """Number for setting SWG Setpoint in njsPC-HA."""

    def __init__(self, coordinator, chlorinator, setpoint, command):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._type = setpoint
        self._command = command
        # self._value = chlorinator[setpoint]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
        ):
            self._chlorinator = self.coordinator.data
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        new_value = int(value)
        data = {"id": self._chlorinator["id"], "setPoint": new_value}
        await self.coordinator.api.command(self._command, data)

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        name = "Pool" if self._type == POOL_SETPOINT else "Spa"
        return f'{self._chlorinator["name"]} {name} Setpoint'

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'swg{self._type.lower()}_{self._chlorinator["id"]}'
        )

    @property
    def icon(self):
        return "mdi:creation"

    @property
    def native_value(self):
        """value"""
        return self._chlorinator[self._type]

    @property
    def native_step(self):
        return 1

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

class HoursNumber(CoordinatorEntity, NumberEntity):
    """Number for setting SWG Setpoint in njsPC-HA."""

    def __init__(self, coordinator, chlorinator, command):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._command = command
        self._value = chlorinator[SUPER_CHLOR_HOURS]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
        ):
            self._chlorinator = self.coordinator.data
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        new_value = int(value)
        data = {"id": self._chlorinator["id"], "superChlorHours": new_value}
        await self.coordinator.api.command(self._command, data)

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return f'{self._chlorinator["name"]} SuperChlor Hours'

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'swgsuperchlorhours_{self._chlorinator["id"]}'
        )

    @property
    def icon(self):
        return "mdi:timer"

    @property
    def native_value(self):
        """value"""
        return self._chlorinator["superChlorHours"]

    @property
    def native_step(self):
        return 1

    @property
    def native_unit_of_measurement(self):
        return "H"

    @property
    def native_min_value(self):
        return 1

    @property
    def native_max_value(self):
        return 24
