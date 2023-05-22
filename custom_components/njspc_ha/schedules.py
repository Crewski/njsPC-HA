"""Platform for schedule integration."""
from __future__ import annotations

from typing import Any


from homeassistant.components.switch import SwitchEntity


from .entity import PoolEquipmentEntity
from .__init__ import NjsPCHAdata
from .const import (
    PoolEquipmentClass,
    EVENT_SCHEDULE,
    EVENT_AVAILABILITY,
    API_CONFIG_SCHEDULE,
)


class ScheduleSwitch(PoolEquipmentEntity, SwitchEntity):
    """Schedule switch for njsPC-HA"""

    def __init__(
        self,
        coordinator: NjsPCHAdata,
        equipment_class: PoolEquipmentClass,
        schedule,
        body=None,
    ) -> None:
        """Initialize the switch."""
        data = schedule["circuit"]
        if body is not None:
            data = body
        super().__init__(
            coordinator=coordinator,
            equipment_class=equipment_class,
            data=data,
        )

        self._available = True
        self._value = False
        self._attr_has_entity_name = False
        self.schedule_id = schedule["id"]
        self.schedule_name = schedule["circuit"]["name"]
        if "disabled" in schedule:
            self._value = schedule["disabled"]

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_SCHEDULE
            and self.coordinator.data["id"] == self.schedule_id
        ):
            if "disabled" in self.coordinator.data:
                self._value = self.coordinator.data["disabled"]
            else:
                self._value = False
            if (
                "circuit" in self.coordinator.data
                and "name" in self.coordinator.data["circuit"]
            ):
                self.schedule_name = self.coordinator.data["circuit"]["name"]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.schedule_id, "disabled": False}
        await self.coordinator.api.command(url=API_CONFIG_SCHEDULE, data=data)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data = {"id": self.schedule_id, "disabled": True}
        await self.coordinator.api.command(url=API_CONFIG_SCHEDULE, data=data)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._available

    @property
    def name(self) -> str:
        return f"{self.schedule_name} Schedule"

    @property
    def unique_id(self) -> str:
        """Set unique device_id"""
        return f"{self.coordinator.controller_id}_schedule_{self.schedule_id}_disabled"

    @property
    def is_on(self) -> bool:
        return not self._value

    @property
    def icon(self) -> str:
        return "mdi:calendar-clock"
