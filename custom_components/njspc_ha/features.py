"""Pool features implementation for njsPC-HA"""
from __future__ import annotations

from typing import Any

from .entity import PoolEquipmentEntity
from .__init__ import NjsPCHAdata


from homeassistant.components.switch import SwitchEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import (
    PoolEquipmentClass,
    API_CIRCUIT_SETSTATE,
    API_CIRCUITGROUP_SETSTATE,
    API_FEATURE_SETSTATE,
    API_LIGHT_RUNCOMMAND,
    API_LIGHTGROUP_SETSTATE,
    EVENT_AVAILABILITY,
    EVENT_CIRCUIT,
    EVENT_CIRCUITGROUP,
    EVENT_LIGHTGROUP,
    EVENT_FEATURE,
    EVENT_VIRTUAL_CIRCUIT,
)

class CircuitSwitch(PoolEquipmentEntity, SwitchEntity):
    """Circuit switch for njsPC-HA"""

    def __init__(
        self,
        coordinator: NjsPCHAdata,
        equipment_class: PoolEquipmentClass,
        circuit,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=equipment_class, data=circuit)
        self._event = None
        self._command = None
        self._value = None
        match equipment_class:
            case PoolEquipmentClass.AUX_CIRCUIT:
                self._event = EVENT_CIRCUIT
                self._command = API_CIRCUIT_SETSTATE
            case PoolEquipmentClass.CIRCUIT_GROUP:
                self._event = EVENT_CIRCUITGROUP
                self._command = API_CIRCUITGROUP_SETSTATE
            case PoolEquipmentClass.FEATURE:
                self._event = EVENT_FEATURE
                self._command = API_FEATURE_SETSTATE
            case PoolEquipmentClass.LIGHT_GROUP:
                self._event = EVENT_LIGHTGROUP
                self._command = API_LIGHTGROUP_SETSTATE
        self._attr_has_entity_name = False
        self._available = True
        self._value = False
        if "isOn" in circuit:
            self._value = circuit["isOn"]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self.equipment_id
        ):
            if "isOn" in self.coordinator.data:
                self._value = self.coordinator.data["isOn"]
            else:
                self._value = False
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.equipment_id, "state": True}
        await self.coordinator.api.command(url=self._command, data=data)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.equipment_id, "state": False}
        await self.coordinator.api.command(url=self._command, data=data)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        return self.equipment_name

    @property
    def unique_id(self) -> str:
        """Set unique device_id"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}"

    @property
    def is_on(self) -> str:
        return self._value

    @property
    def icon(self) -> str:
        return "mdi:toggle-switch-variant"

class LightCommandButton(PoolEquipmentEntity, ButtonEntity):
    """Light command button entity for njsPC-HA."""

    def __init__(self, coordinator:NjsPCHAdata, equipment_class: PoolEquipmentClass, circuit:Any, command:Any) -> None:
        """Initialize the button."""
        super().__init__(coordinator=coordinator, equipment_class=equipment_class, data=circuit)
        self._command = command

    async def async_press(self) -> None:
        """Button has been pressed"""

        data = {"id": self.equipment_id, "command": self._command["name"]}
        await self.coordinator.api.command(url=API_LIGHT_RUNCOMMAND, data=data)

    @property
    def name(self) -> str:
        """Name of button"""
        return self._command["desc"]

    @property
    def unique_id(self) -> str:
        """Set unique id"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_{self._command['name']}"

    @property
    def icon(self) -> str:
        match self._command["name"]:
            case "colorsync":
                return "mdi:cog-sync-outline"
            case "colorswim":
                return "mdi:palette-swatch-variant"
            case "colorhold":
                return "mdi:eyedropper"
            case "colorrecall":
                return "mdi:bookmark"
            case "lightthumper":
                return "mdi:gavel"
            case "thumper":
                return "mdi:gavel"
        return "mdi:palette"

class VirtualCircuit(PoolEquipmentEntity, BinarySensorEntity):
    """The current state for a virtual circuit"""

    def __init__(self, coordinator: NjsPCHAdata, virtual_circuit: Any) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, equipment_class=PoolEquipmentClass.CONTROL_PANEL, data={"model":coordinator.model})
        self._value = False
        self.circuit_id = virtual_circuit["id"]
        self.circuit_name = virtual_circuit["name"]
        if "isOn" in virtual_circuit:
            self._value = virtual_circuit["isOn"]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_VIRTUAL_CIRCUIT
            and self.coordinator.data["id"] == self.circuit_id
        ):
            if "isOn" in self.coordinator.data:
                self._value = self.coordinator.data["isOn"]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str | None:
        """Name of the sensor"""
        return self.circuit_name

    @property
    def unique_id(self) -> str | None:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.circuit_id}_ison"

    @property
    def native_value(self) -> bool | None:
        """Raw value of the sensor"""
        return self._value

    @property
    def is_on(self) -> bool:
        """Return if the pump is running."""
        return self._value

    @property
    def icon(self) -> str:
        if self._value is True:
            return "mdi:toggle-switch-outline"
        return "mdi:toggle-switch-off-outline"
