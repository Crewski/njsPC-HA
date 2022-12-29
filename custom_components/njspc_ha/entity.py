"""Base Entity for njsPC."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity
from . import NjsPCHAdata
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, EVENT_CONTROLLER, MANUFACTURER


class NjsPCEntity(CoordinatorEntity[NjsPCHAdata], Entity):
    """Defines a base njsPC entity."""

    def __init__(self, *, coordinator: NjsPCHAdata) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def device_info(self) -> DeviceInfo | None:
        """Device info"""
        if self.coordinator.data["event"] == EVENT_CONTROLLER:
            return DeviceInfo(
                identifiers={(DOMAIN, self.coordinator.data["model"])},
                name="nodejs-PoolController",
                manufacturer=MANUFACTURER,
                suggested_area="Pool",
                model=self.coordinator.data["model"],
                sw_version=f'{self.coordinator.data["appVersionState"]["installed"]} ({self.coordinator.data["appVersionState"]["gitLocalBranch"]}-{self.coordinator.data["appVersionState"]["gitLocalCommit"][-7:]})',
            )
