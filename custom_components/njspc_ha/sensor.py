"""Platform for sensor integration."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant

from .entity import PoolEquipmentEntity, NjsPCHAdata

from homeassistant.components.sensor import SensorEntity

from .chemistry import (
    ChemistryDemandSensor,
    ChemistrySensor,
    ChemistryTankLevel,
    ChemistryDosingStatus,
    SaltSensor,
    SaltRequiredSensor,
    SaltTargetSensor,
    CurrentOutputSensor,
    TargetOutputSensor,
)
from .pumps import PumpPowerSensor, PumpFlowSensor, PumpSpeedSensor
from .controller import PanelModeSensor, TempProbeSensor
from .bodies import BodyTempSensor, FilterPressureSensor, FilterCleanSensor
from .const import (
    PoolEquipmentClass,
    PoolEquipmentModel,
    CURRENT_OUTPUT,
    DESC,
    DOMAIN,
    EVENT_AVAILABILITY,
    EVENT_CHLORINATOR,
    EVENT_PUMP,
    SALT_LEVEL,
    SALT_REQUIRED,
    SALT_TARGET,
    STATUS,
    TARGET_OUTPUT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for past config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    config = coordinator.api.get_config()

    new_devices.append(PanelModeSensor(coordinator, config))
    if "temps" in config:
        units = config["temps"]["units"]["name"]
        for key in config["temps"]:
            if (
                key == "air"
                or key == "solar"
                or key.startswith("solarSensor")
                or key.startswith("waterSensor")
            ):
                new_devices.append(
                    TempProbeSensor(
                        coordinator=coordinator,
                        key=key,
                        units=units,
                    )
                )
        if (
            "bodies" in config["temps"]
        ):  # We can have Nobody Nixie systems (equipment only)
            for body in list(config["temps"]["bodies"]):
                new_devices.append(
                    BodyTempSensor(coordinator=coordinator, units=units, body=body)
                )

    for pump in config["pumps"]:
        # Pump sensors vary by type. This may need a re-visit for pump types that use a
        # number for their speed or High/Low.  Such are the dual speed, superflo, and relay pumps
        if "type" in pump:
            pump_type = pump["type"]
            if "maxSpeed" in pump_type:
                new_devices.append(PumpSpeedSensor(coordinator=coordinator, pump=pump))
            if "maxFlow" in pump_type:
                new_devices.append(PumpFlowSensor(coordinator=coordinator, pump=pump))
            if "maxSpeed" in pump_type or "maxFlow" in pump_type:
                new_devices.append(PumpPowerSensor(coordinator=coordinator, pump=pump))
            if STATUS in pump:
                new_devices.append(
                    EquipmentStatusSensor(
                        coordinator=coordinator,
                        equipment_class=PoolEquipmentClass.PUMP,
                        equipment_model=PoolEquipmentModel.PUMP,
                        equipment=pump,
                        event=EVENT_PUMP,
                    )
                )
    for chlorinator in config["chlorinators"]:
        if SALT_LEVEL in chlorinator:
            new_devices.append(
                SaltSensor(coordinator=coordinator, chlorinator=chlorinator)
            )
        if CURRENT_OUTPUT in chlorinator:
            new_devices.append(
                CurrentOutputSensor(coordinator=coordinator, chlorinator=chlorinator)
            )
        if TARGET_OUTPUT in chlorinator:
            new_devices.append(
                TargetOutputSensor(coordinator=coordinator, chlorinator=chlorinator)
            )
        if SALT_REQUIRED in chlorinator:
            new_devices.append(
                SaltRequiredSensor(coordinator=coordinator, chlorinator=chlorinator)
            )
        if SALT_TARGET in chlorinator:
            new_devices.append(
                SaltTargetSensor(coordinator=coordinator, chlorinator=chlorinator)
            )
        if STATUS in chlorinator:
            new_devices.append(
                EquipmentStatusSensor(
                    coordinator=coordinator,
                    equipment_class=PoolEquipmentClass.CHLORINATOR,
                    equipment_model=PoolEquipmentModel.CHLORINATOR,
                    equipment=chlorinator,
                    event=EVENT_CHLORINATOR,
                )
            )
    for chem_controller in config["chemControllers"]:
        if (
            "name" in chem_controller
            and "type" in chem_controller
            and "name" in chem_controller["type"]
            and chem_controller["type"]["name"] != "none"
        ):
            if "ph" in chem_controller:
                chemical = chem_controller["ph"]
                if chemical["enabled"] is True:
                    new_devices.append(
                        ChemistryDosingStatus(
                            coordinator=coordinator,
                            chem_controller=chem_controller,
                            chemical=chemical,
                        )
                    )
                    new_devices.append(
                        ChemistrySensor(
                            coordinator=coordinator,
                            chem_controller=chem_controller,
                            chemical=chemical,
                        )
                    )
                    new_devices.append(
                        ChemistryDemandSensor(
                            coordinator=coordinator,
                            chem_controller=chem_controller,
                            chemical=chemical,
                        )
                    )
                    if "tank" in chemical:
                        new_devices.append(
                            ChemistryTankLevel(
                                coordinator=coordinator,
                                chem_controller=chem_controller,
                                chemical=chemical,
                            )
                        )

            if "orp" in chem_controller:
                chemical = chem_controller["orp"]
                if chemical["enabled"] is True:
                    new_devices.append(
                        ChemistryDosingStatus(
                            coordinator=coordinator,
                            chem_controller=chem_controller,
                            chemical=chemical,
                        )
                    )
                    new_devices.append(
                        ChemistrySensor(
                            coordinator=coordinator,
                            chem_controller=chem_controller,
                            chemical=chem_controller["orp"],
                        )
                    )
                    new_devices.append(
                        ChemistryDemandSensor(
                            coordinator=coordinator,
                            chem_controller=chem_controller,
                            chemical=chemical,
                        )
                    )
                    if (
                        "tank" in chemical
                        and chemical["doserType"]["name"] != "chlorinator"
                    ):
                        new_devices.append(
                            ChemistryTankLevel(
                                coordinator=coordinator,
                                chem_controller=chem_controller,
                                chemical=chemical,
                            )
                        )
    for pool_filter in config["filters"]:
        new_devices.append(
            FilterPressureSensor(coordinator=coordinator, pool_filter=pool_filter)
        )
        new_devices.append(
            FilterCleanSensor(coordinator=coordinator, pool_filter=pool_filter)
        )

    if new_devices:
        async_add_entities(new_devices)


class EquipmentStatusSensor(PoolEquipmentEntity, SensorEntity):
    """Equipment Status Sensor for njsPC-HA"""

    def __init__(
        self,
        coordinator: NjsPCHAdata,
        equipment_class: PoolEquipmentClass,
        equipment_model: PoolEquipmentModel,
        equipment: Any,
        event: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.equipment_class = equipment_class
        self.equipment_id = equipment["id"]
        self.equipment_name = equipment["name"]
        self.equipment_model = equipment_model
        self.coordinator_context = object()
        self._value = equipment[STATUS][DESC]
        self._event = event
        self._available = True
        # Below makes sure we have a name that makes sense for the entity.
        self._attr_has_entity_name = True
        self._attr_device_class = f"{self.equipment_name}_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self.equipment_id
        ):
            self._value = self.coordinator.data[STATUS][DESC]
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
    def name(self) -> str:
        """Name of the sensor"""
        return "Status"

    @property
    def unique_id(self) -> str:
        """ID of the sensor"""
        return f"{self.coordinator.controller_id}_{self.equipment_class}_{self.equipment_id}_status"

    @property
    def native_value(self) -> str | None:
        return self._value

    @property
    def icon(self) -> str:
        if self._value != "Ok":
            return "mdi:alert-circle"
        return "mdi:check-circle"
