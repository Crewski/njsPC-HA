"""Pool features implementation for njsPC-HA"""
from __future__ import annotations

from typing import Any

from .entity import PoolEquipmentEntity
from .__init__ import NjsPCHAdata


from homeassistant.components.switch import SwitchEntity
from homeassistant.components.button import ButtonEntity

from .const import (
    PoolEquipmentClass,
    PoolEquipmentModel,
    API_CIRCUIT_SETSTATE,
    API_CIRCUITGROUP_SETSTATE,
    API_FEATURE_SETSTATE,
    API_LIGHT_RUNCOMMAND,
    EVENT_AVAILABILITY,
    EVENT_CIRCUIT,
    EVENT_CIRCUITGROUP,
    EVENT_LIGHTGROUP,
    EVENT_FEATURE,
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
        super().__init__(coordinator)
        self.equipment_class = equipment_class
        self.equipment_name = circuit["name"]
        self.equipment_id = circuit["id"]
        self.equipment_model = PoolEquipmentModel.AUX_CIRCUIT
        self._event = None
        self._command = None
        match equipment_class:
            case PoolEquipmentClass.AUX_CIRCUIT:
                self._event = EVENT_CIRCUIT
                self._command = API_CIRCUIT_SETSTATE
                self.equipment_model = PoolEquipmentModel.AUX_CIRCUIT
            case PoolEquipmentClass.CIRCUIT_GROUP:
                self._event = EVENT_CIRCUITGROUP
                self._command = API_CIRCUITGROUP_SETSTATE
                self.equipment_model = PoolEquipmentModel.CIRCUIT_GROUP
            case PoolEquipmentClass.FEATURE:
                self._event = EVENT_FEATURE
                self._command = API_FEATURE_SETSTATE
                self.equipment_model = PoolEquipmentModel.FEATURE
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
        super().__init__(coordinator)
        self.equipment_class = equipment_class
        self.equipment_id = circuit["id"]
        self.equipment_name = circuit["name"]
        self._command = command
        if equipment_class == PoolEquipmentClass.LIGHT_GROUP:
            self.equipment_model = PoolEquipmentModel.LIGHT_GROUP
        else:
            self.equipment_model = PoolEquipmentModel.LIGHT
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_{command['name']}"

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
