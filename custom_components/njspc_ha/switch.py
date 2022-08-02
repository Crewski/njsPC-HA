"""Platform for switch integration."""


from homeassistant.const import DEVICE_CLASS_POWER, DEVICE_CLASS_TEMPERATURE
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    API_CIRCUIT_SETSTATE,
    API_CIRCUITGROUP_SETSTATE,
    API_FEATURE_SETSTATE,
    API_SUPERCHLOR,
    DOMAIN,
    EVENT_CHLORINATOR,
    EVENT_CIRCUIT,
    EVENT_CIRCUITGROUP,
    EVENT_FEATURE,
)



async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for circuit in coordinator.api._config["circuits"]:
        try:
            if not circuit["type"]["isLight"]:
                new_devices.append(CircuitSwitch(coordinator, circuit, EVENT_CIRCUIT, API_CIRCUIT_SETSTATE))
        except KeyError:
            new_devices.append(CircuitSwitch(coordinator, circuit, EVENT_CIRCUIT, API_CIRCUIT_SETSTATE))

    for circuit in coordinator.api._config["circuitGroups"]:
        new_devices.append(CircuitSwitch(coordinator, circuit, EVENT_CIRCUITGROUP, API_CIRCUITGROUP_SETSTATE))

    for feature in coordinator.api._config["features"]:
        new_devices.append(CircuitSwitch(coordinator, feature, EVENT_FEATURE, API_FEATURE_SETSTATE))   

    for chlorinator in coordinator.api._config["chlorinators"]:
        new_devices.append(SuperChlorSwitch(coordinator, chlorinator))

    if new_devices:
        async_add_entities(new_devices)


class CircuitSwitch(CoordinatorEntity, SwitchEntity):
    """Base representation of a Hello World Sensor."""

    def __init__(self, coordinator, circuit, event, command):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._circuit = circuit
        self._event = event
        self._command = command

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self._circuit["id"]
        ):
            self._circuit = self.coordinator.data
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._circuit["id"], "state": True}
        await self.coordinator.api.command(self._command, data)

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._circuit["id"], "state": False}
        await self.coordinator.api.command(self._command, data)

    @property
    def name(self):
        return self._circuit["name"]

    @property
    def unique_id(self) -> str:
        """Set unique device_id"""
        return self.coordinator.api.get_unique_id(f'circuit_{self._circuit["id"]}')

    @property
    def is_on(self):
        try:
            return self._circuit["isOn"]
        except:
            return False

    @property
    def icon(self) -> str:
        if self._circuit["type"]["val"] == 12 or self._circuit["type"]["val"] == 2:
            return "mdi:pool"
        elif self._circuit["type"]["val"] == 13 or self._circuit["type"]["val"] == 1:
            return "mdi:hot-tub"
        else:
            return "mdi:toggle-switch-variant"


class SuperChlorSwitch(CoordinatorEntity, SwitchEntity):
    """Base representation of a Hello World Sensor."""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
        ):
            self._chlorinator = self.coordinator.data
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._chlorinator["id"], "superChlorinate": True}
        await self.coordinator.api.command(API_SUPERCHLOR, data)

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._chlorinator["id"], "superChlorinate": False}
        await self.coordinator.api.command(API_SUPERCHLOR, data)

    @property
    def name(self):
        return self._chlorinator["name"] + " Super Chlorinate"

    @property
    def unique_id(self):
        return self.coordinator.api.get_unique_id(
            f'superchlorinate_{self._chlorinator["id"]}'
        )

    @property
    def is_on(self):
        return self._chlorinator["superChlor"]

    @property
    def icon(self) -> str:
        return "mdi:atom-variant"
