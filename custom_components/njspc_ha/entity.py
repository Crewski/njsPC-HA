"""Base Entity for njsPC."""
from __future__ import annotations

import time

from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import NjsPCHAdata
from .const import (
    DOMAIN,
    MANUFACTURER,
    PoolEquipmentClass,
    PoolEquipmentModel,
    THROTTLE_DEFAULT_INTERVAL,
)
from dataclasses import dataclass


@dataclass
class PoolEquipmentDescription:
    """A class that describes pool equipment devices."""

    equipment_class: PoolEquipmentClass | None = None
    equipment_model: PoolEquipmentModel | None = None
    label: str | None = None
    id_key: str | None = "id"
    name_key: str | None = "name"


DEVICE_MAPPING: dict[PoolEquipmentClass, PoolEquipmentDescription] = {
    PoolEquipmentClass.CONTROL_PANEL: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.CONTROL_PANEL,
        equipment_model=PoolEquipmentModel.CONTROL_PANEL,
        label="Outdoor Control Panel",
        id_key=None,
        name_key="model",
    ),
    PoolEquipmentClass.PUMP: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.PUMP,
        equipment_model=PoolEquipmentModel.PUMP,
        label="Pump",
    ),
    PoolEquipmentClass.BODY: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.BODY,
        equipment_model=PoolEquipmentModel.BODY,
        label="Body",
    ),
    PoolEquipmentClass.FILTER: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.FILTER,
        equipment_model=PoolEquipmentModel.FILTER,
        label="Filter",
    ),
    PoolEquipmentClass.CHLORINATOR: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.CHLORINATOR,
        equipment_model=PoolEquipmentModel.CHLORINATOR,
        label="Chlorinator",
    ),
    PoolEquipmentClass.CHEM_CONTROLLER: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.CHEM_CONTROLLER,
        equipment_model=PoolEquipmentModel.CHEM_CONTROLLER,
        label="Chem Controller",
    ),
    PoolEquipmentClass.AUX_CIRCUIT: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.AUX_CIRCUIT,
        equipment_model=PoolEquipmentModel.AUX_CIRCUIT,
        label="Circuit",
    ),
    PoolEquipmentClass.LIGHT: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.LIGHT,
        equipment_model=PoolEquipmentModel.LIGHT,
    ),
    PoolEquipmentClass.FEATURE: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.FEATURE,
        equipment_model=PoolEquipmentModel.FEATURE,
        label="Feature",
    ),
    PoolEquipmentClass.CIRCUIT_GROUP: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.CIRCUIT_GROUP,
        equipment_model=PoolEquipmentModel.CIRCUIT_GROUP,
        label="Circuit Group",
    ),
    PoolEquipmentClass.LIGHT_GROUP: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.LIGHT_GROUP,
        equipment_model=PoolEquipmentModel.LIGHT_GROUP,
        label="Light Group",
    ),
    PoolEquipmentClass.HEATER: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.HEATER,
        equipment_model=PoolEquipmentModel.HEATER,
        label="Heater",
    ),
    PoolEquipmentClass.VALVE: PoolEquipmentDescription(
        equipment_class=PoolEquipmentClass.VALVE,
        equipment_model=PoolEquipmentModel.VALVE,
        label="Valve",
    ),
}


class ThrottledSensorMixin:
    """Mixin that reduces HA state writes for push-driven entities.

    Class attributes (override per-entity):
        _throttle_interval: seconds between writes (default: THROTTLE_DEFAULT_INTERVAL)
        _throttle_delta: minimum change for immediate publish (default: 0)
            0 = any value change publishes immediately; unchanged values are skipped.
            >0 = small changes are deferred and coalesced up to _throttle_interval.

    Usage:
        __init__: call self._init_throttle() after super().__init__().
        data events: update self._value, then call self._throttled_update(self._value).
        availability events: update self._available, then call self._immediate_update().
    """

    _throttle_interval: float = THROTTLE_DEFAULT_INTERVAL
    _throttle_delta: float = 0

    def _init_throttle(self) -> None:
        """Initialize throttle state. Call at the end of __init__."""
        self._throttle_last_published_value = None
        self._throttle_last_publish_time: float = 0.0
        self._throttle_flush_unsub: CALLBACK_TYPE | None = None
        self._throttle_pending_value = None

    def _throttled_update(self, new_value) -> None:
        """Evaluate whether to publish now or defer a state write."""
        now = time.monotonic()

        # First update ever → publish immediately
        if self._throttle_last_published_value is None:
            self._do_throttled_publish(now, new_value)
            return

        # Exactly the same as last published → cancel any pending flush, skip
        if new_value == self._throttle_last_published_value:
            self._cancel_throttle_flush()
            return

        # Check if the change is significant enough for immediate publish
        significant = self._throttle_delta <= 0
        if not significant:
            try:
                significant = (
                    abs(new_value - self._throttle_last_published_value)
                    >= self._throttle_delta
                )
            except TypeError:
                significant = True

        if significant:
            self._cancel_throttle_flush()
            self._do_throttled_publish(now, new_value)
            return

        # Small numeric change — defer to interval
        elapsed = now - self._throttle_last_publish_time
        if elapsed >= self._throttle_interval:
            self._cancel_throttle_flush()
            self._do_throttled_publish(now, new_value)
            return

        # Store pending and schedule flush if not already pending
        self._throttle_pending_value = new_value
        if self._throttle_flush_unsub is None:
            delay = self._throttle_interval - elapsed
            self._throttle_flush_unsub = async_call_later(
                self.coordinator.hass, delay, self._on_throttle_flush
            )

    @callback
    def _on_throttle_flush(self, _now) -> None:
        """Flush pending value when throttle interval expires."""
        self._throttle_flush_unsub = None
        self._do_throttled_publish(
            time.monotonic(), self._throttle_pending_value
        )

    def _do_throttled_publish(self, now: float, value) -> None:
        """Write state and record publish metadata."""
        self._throttle_last_published_value = value
        self._throttle_last_publish_time = now
        self.async_write_ha_state()

    def _cancel_throttle_flush(self) -> None:
        """Cancel any pending flush timer."""
        if self._throttle_flush_unsub is not None:
            self._throttle_flush_unsub()
            self._throttle_flush_unsub = None

    def _immediate_update(self) -> None:
        """Publish immediately, bypassing throttle. Use for availability."""
        self._cancel_throttle_flush()
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up throttle timer on entity removal."""
        self._cancel_throttle_flush()
        await super().async_will_remove_from_hass()


class PoolEquipmentEntity(CoordinatorEntity[NjsPCHAdata], Entity):
    """Defines an Equipment Related Entity for njsPC"""

    def __init__(
        self, coordinator: NjsPCHAdata, equipment_class: PoolEquipmentClass, data: any
    ) -> None:
        super().__init__(coordinator)
        self.equipment_class = equipment_class
        self.equipment_model = None
        self.equipment_id = 0
        if equipment_class in DEVICE_MAPPING:
            dev = DEVICE_MAPPING[equipment_class]
            self.equipment_model = dev.equipment_model
            if dev.id_key is not None and dev.id_key in data:
                self.equipment_id = data[dev.id_key]
            if dev.name_key is not None and dev.name_key in data:
                self.equipment_name = data[dev.name_key]
            elif self.equipment_id != 0:
                self.equipment_name = f"{dev.label}{self.equipment_id}"
            else:
                self.equipment_name = dev.label
        self._attr_has_entity_name = True
        self._available = True

    def format_duration(self, secs: int) -> str:
        """Format a number of seconds into an output string"""
        days = secs // 86400
        hrs = (secs - (days * 86400)) // 3600
        mins = (secs - (days * 86400) - (hrs * 3600)) // 60
        sec = secs - (days * 86000) - (hrs * 3600) - (mins * 60)
        formatted = ""
        if days > 0:
            formatted = f"{days}days"
        if hrs > 0:
            formatted = f"{formatted} {hrs}hrs"
        if mins > 0:
            formatted = f"{formatted} {mins}min"
        if sec > 0:
            formatted = f"{formatted} {sec}sec"
        return formatted

            




    @property
    def device_info(self) -> DeviceInfo | None:
        """Device info"""
        return DeviceInfo(
            # Below assigns the entity to the overall device
            identifiers={
                (
                    DOMAIN,
                    self.coordinator.model,
                    self.equipment_class,
                    self.equipment_id,
                ),
            },
            name=self.equipment_name,
            manufacturer=MANUFACTURER,
            suggested_area="Pool",
            model=self.equipment_model,
            sw_version=self.coordinator.version,
        )
