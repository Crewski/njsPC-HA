"""Base Entity for njsPC."""
from __future__ import annotations

from typing import Any
from homeassistant.helpers.entity import DeviceInfo, Entity
from . import NjsPCHAdata
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, MANUFACTURER, PoolEquipmentClass, PoolEquipmentModel
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

    def __init1__(
        self,
        coordinator: NjsPCHAdata,
        equipment_class: PoolEquipmentClass,
        equipment_model: PoolEquipmentModel,
        data: Any,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.equipment_class = equipment_class
        self.equipment_id = 0
        self.equipment_name = None
        if "id" in data:
            self.equipment_id = data["id"]
        if equipment_model is None:
            self.equipment_model = coordinator.model
        else:
            self.equipment_model = equipment_model
        if "name" in data:
            self.equipment_name = data["name"]
        else:
            self.equipment_name = f"{self.equipment_class}{self.equipment_id}"
        self._attr_has_entity_name = True

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
