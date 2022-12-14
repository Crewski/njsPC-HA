"""Platform for switch integration."""
from __future__ import annotations
from .entity import NjsPCEntity

from homeassistant.components.switch import SwitchEntity

from .const import (
    API_CIRCUIT_SETSTATE,
    API_CIRCUITGROUP_SETSTATE,
    API_FEATURE_SETSTATE,
    API_SUPERCHLOR,
    DOMAIN,
    EVENT_AVAILABILITY,
    EVENT_CHLORINATOR,
    EVENT_CIRCUIT,
    EVENT_CIRCUITGROUP,
    EVENT_FEATURE,
    SUPER_CHLOR,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    config = coordinator.api.get_config()
    for circuit in config["circuits"]:
        try:
            if not circuit["type"]["isLight"]:
                new_devices.append(
                    CircuitSwitch(
                        coordinator=coordinator,
                        circuit=circuit,
                        event=EVENT_CIRCUIT,
                        command=API_CIRCUIT_SETSTATE,
                    )
                )
        except KeyError:
            new_devices.append(
                CircuitSwitch(
                    coordinator=coordinator,
                    circuit=circuit,
                    event=EVENT_CIRCUIT,
                    command=API_CIRCUIT_SETSTATE,
                )
            )

    for circuit in config["circuitGroups"]:
        new_devices.append(
            CircuitSwitch(
                coordinator=coordinator,
                circuit=circuit,
                event=EVENT_CIRCUITGROUP,
                command=API_CIRCUITGROUP_SETSTATE,
            )
        )

    for feature in config["features"]:
        new_devices.append(
            CircuitSwitch(
                coordinator=coordinator,
                circuit=feature,
                event=EVENT_FEATURE,
                command=API_FEATURE_SETSTATE,
            )
        )

    for chlorinator in config["chlorinators"]:
        if SUPER_CHLOR in chlorinator:
            new_devices.append(
                SuperChlorSwitch(coordinator=coordinator, chlorinator=chlorinator)
            )

    if new_devices:
        async_add_entities(new_devices)


class CircuitSwitch(NjsPCEntity, SwitchEntity):
    """Circuit switch for njsPC-HA"""

    def __init__(self, coordinator, circuit, event, command):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._circuit = circuit
        self._event = event
        self._command = command
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self._circuit["id"]
        ):
            self._circuit = self.coordinator.data
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._circuit["id"], "state": True}
        await self.coordinator.api.command(url=self._command, data=data)

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._circuit["id"], "state": False}
        await self.coordinator.api.command(url=self._command, data=data)

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        return self._circuit["name"]

    @property
    def unique_id(self) -> str:
        """Set unique device_id"""
        return self.coordinator.api.get_unique_id(name=f'circuit_{self._circuit["id"]}')

    @property
    def is_on(self):
        try:
            return self._circuit["isOn"]
        except KeyError:
            return False

    @property
    def icon(self) -> str:
        if self._circuit["type"]["val"] == 12 or self._circuit["type"]["val"] == 2:
            return "mdi:pool"
        elif self._circuit["type"]["val"] == 13 or self._circuit["type"]["val"] == 1:
            return "mdi:hot-tub"
        else:
            return "mdi:toggle-switch-variant"


class SuperChlorSwitch(NjsPCEntity, SwitchEntity):
    """Super Chlorinate switch for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = self._chlorinator[SUPER_CHLOR]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and SUPER_CHLOR in self.coordinator.data
        ):
            self._value = self.coordinator.data[SUPER_CHLOR]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._chlorinator["id"], "superChlorinate": True}
        await self.coordinator.api.command(url=API_SUPERCHLOR, data=data)

    async def async_turn_off(self, **kwargs):
        """Turn the entity on."""
        data = {"id": self._chlorinator["id"], "superChlorinate": False}
        await self.coordinator.api.command(url=API_SUPERCHLOR, data=data)

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        return self._chlorinator["name"] + " Super Chlorinate"

    @property
    def unique_id(self):
        return self.coordinator.api.get_unique_id(
            name=f'superchlorinate_{self._chlorinator["id"]}'
        )

    @property
    def is_on(self):
        # return self._chlorinator["superChlor"]
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:atom-variant"
