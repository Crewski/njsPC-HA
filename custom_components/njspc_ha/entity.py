"""Base Entity for njsPC."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity
from . import NjsPCHAdata
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, MANUFACTURER


class NjsPCEntity(CoordinatorEntity[NjsPCHAdata], Entity):
    """Defines a base njsPC entity."""

    def __init__(self, coordinator: NjsPCHAdata) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_info(self) -> DeviceInfo | None:
        """Device info"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.model)},
            name="nodejs-PoolController",
            manufacturer=MANUFACTURER,
            suggested_area="Pool",
            model=self.coordinator.model,
            sw_version=self.coordinator.version,
        )


class PoolEquipmentEntity(CoordinatorEntity[NjsPCHAdata], Entity):
    """Defines an Equipment Related Entity for njsPC"""

    def __init__(self, coordinator: NjsPCHAdata) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.equipment_class = None
        self.equipment_id = None
        self.equipment_name = None
        self.equipment_model = coordinator.model

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
