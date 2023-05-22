"""Platform for schedule integration."""
from __future__ import annotations

from typing import Any
from collections.abc import Mapping


from homeassistant.components.switch import SwitchEntity


from .entity import PoolEquipmentEntity
from .__init__ import NjsPCHAdata
from .const import (
    PoolEquipmentClass,
    EVENT_SCHEDULE,
    EVENT_AVAILABILITY,
    API_CONFIG_SCHEDULE,
)

DAY_ABBREVIATIONS = {
    "sun": "U",
    "sat": "S",
    "fri": "F",
    "thu": "H",
    "wed": "W",
    "tue": "T",
    "mon": "M",
}


class ScheduleSwitch(PoolEquipmentEntity, SwitchEntity):
    """Schedule switch for njsPC-HA"""

    def __init__(
        self,
        coordinator: NjsPCHAdata,
        equipment_class: PoolEquipmentClass,
        schedule,
        clockMode: int = 12,
        body=None,
    ) -> None:
        """Initialize the switch."""
        data = schedule["circuit"]
        if body is not None:
            # change it over to body if provided
            data = body
        super().__init__(
            coordinator=coordinator,
            equipment_class=equipment_class,
            data=data,
        )

        self._available = True
        self._value = False
        self._clock_mode = clockMode

        self._attr_has_entity_name = False
        self.schedule_id = schedule["id"]
        self.schedule_name = schedule["circuit"]["name"]
        if "disabled" in schedule:
            self._value = schedule["disabled"]

        self._state_attributes: dict[str, Any] = dict([])
        if "scheduleDays" in schedule:
            self._state_attributes["days"] = self.format_schedule_days(
                schedule_days=schedule["scheduleDays"]
            )
        if "startTime" in schedule and "startTimeType" in schedule:
            self._state_attributes["start_time"] = self.format_start_stop_times(
                time=schedule["startTime"], time_type=schedule["startTimeType"]["val"]
            )
        if "endTime" in schedule and "endTimeType" in schedule:
            self._state_attributes["end_time"] = self.format_start_stop_times(
                time=schedule["endTime"], time_type=schedule["endTimeType"]["val"]
            )

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

            if (
                "startTime" in self.coordinator.data
                and "startTimeType" in self.coordinator.data
            ):
                self._state_attributes["start_time"] = self.format_start_stop_times(
                    time=self.coordinator.data["startTime"],
                    time_type=self.coordinator.data["startTimeType"]["val"],
                )
            if (
                "endTime" in self.coordinator.data
                and "endTimeType" in self.coordinator.data
            ):
                self._state_attributes["end_time"] = self.format_start_stop_times(
                    time=self.coordinator.data["endTime"],
                    time_type=self.coordinator.data["endTimeType"]["val"],
                )
            if "scheduleDays" in self.coordinator.data:
                self._state_attributes["days"] = self.format_schedule_days(
                    schedule_days=self.coordinator.data["scheduleDays"]
                )
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

    def format_start_stop_times(self, time: int, time_type: int) -> str:
        """Format the minutes time to human readable"""
        formatted = ""
        if time_type == 1:
            return "Sunrise"
        elif time_type == 2:
            return "Sunset"
        elif time_type == 0:
            hrs = time // 60
            mins = time - (hrs * 60)
            if self._clock_mode == 24:
                formatted = f"{hrs:02}:{mins:02}"
            else:
                ampm = "am"
                if hrs > 12:
                    hrs = hrs - 12
                    ampm = "pm"
                formatted = f"{hrs}:{mins:02} {ampm}"
        else:
            formatted = "Unknown"
        return formatted

    def format_schedule_days(self, schedule_days) -> str:
        """Format the scheduled days into a string"""
        formatted = ""
        if schedule_days["val"] == 127:
            formatted = "Every Day"
        elif schedule_days["val"] == 31:
            formatted = "Weekdays"
        elif schedule_days["val"] == 96:
            formatted = "Weekends"
        else:
            day_list = []
            idx = 0
            for day in schedule_days["days"]:
                if day["name"] == "sun":
                    # we need to change the insert index if Sunday is in the list so that it stays at the beginning
                    idx = 1
                day_list.insert(idx, DAY_ABBREVIATIONS[day["name"]])
            formatted = "-".join(day_list)
        return formatted

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
        if self._value:
            return "mdi:calendar-remove"
        else:
            return "mdi:calendar-clock"

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""

        return self._state_attributes
