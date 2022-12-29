"""Platform for sensor integration."""

from homeassistant.helpers.entity import EntityCategory
from .entity import NjsPCEntity
from homeassistant.const import (
    MASS_POUNDS,
    POWER_WATT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from .const import (
    CURRENT_OUTPUT,
    DESC,
    DOMAIN,
    EVENT_AVAILABILITY,
    EVENT_CHLORINATOR,
    EVENT_PUMP,
    EVENT_TEMPS,
    FLOW,
    MAX_FLOW,
    MIN_FLOW,
    RPM,
    SALT_LEVEL,
    SALT_REQUIRED,
    SALT_TARGET,
    STATUS,
    TARGET_OUTPUT,
    WATTS,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    config = coordinator.api.get_config()
    for key in config["temps"]:
        if isinstance(config["temps"][key], int) or isinstance(
            config["temps"][key], float
        ):
            new_devices.append(
                TempSensor(
                    coordinator=coordinator,
                    key=key,
                    units=config["temps"]["units"]["name"],
                )
            )
    for pump in config["pumps"]:
        if RPM in pump:
            new_devices.append(RPMSensor(coordinator=coordinator, pump=pump))
        if WATTS in pump:
            new_devices.append(PowerSensor(coordinator=coordinator, pump=pump))
        if FLOW in pump:  # for pumps that have a flow reading
            new_devices.append(FlowSensor(coordinator=coordinator, pump=pump))
        if STATUS in pump:
            new_devices.append(
                StatusSensor(coordinator=coordinator, equipment=pump, event=EVENT_PUMP)
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
                StatusSensor(
                    coordinator=coordinator,
                    equipment=chlorinator,
                    event=EVENT_CHLORINATOR,
                )
            )
    if new_devices:
        async_add_entities(new_devices)


class TempSensor(NjsPCEntity, SensorEntity):
    """Temp Sensor for njsPC-HA"""

    def __init__(self, coordinator, key, units):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._key = key
        self._units = units
        self._value = round(coordinator.api._config["temps"][key], 1)
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_TEMPS
            and self._key in self.coordinator.data
        ):  # make sure the data we are looking for is in the coordinator data
            self._value = round(self.coordinator.data[self._key], 1)
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        return "njspc_" + self._key

    @property
    def unique_id(self):
        return self.coordinator.api.get_unique_id(f"temp_{self._key}")

    @property
    def state_class(self):
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self._value

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str:
        if self._units == "F":
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS


class RPMSensor(NjsPCEntity, SensorEntity):
    """RPM Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator, pump):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._pump = pump
        self._value = pump[RPM]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self._pump["id"]
            # make sure the data we are looking for is in the coordinator data
            and RPM in self.coordinator.data
        ):
            self._value = self.coordinator.data[RPM]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._pump["name"] + " RPM"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(f'pump_{self._pump["id"]}_rpm')

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        return self._value

    @property
    def native_unit_of_measurement(self):
        """Unit of measurement of the sensor"""
        return "RPM"

    @property
    def icon(self) -> str:
        return "mdi:speedometer"

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "min_speed": self._pump["minSpeed"],
            "max_speed": self._pump["maxSpeed"],
        }


class PowerSensor(NjsPCEntity, SensorEntity):
    """Watts Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator, pump):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._pump = pump
        self._value = pump[WATTS]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self._pump["id"]
            and WATTS
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[WATTS]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._pump["name"] + " Watts"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(f'pump_{self._pump["id"]}_watts')

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        return self._value

    @property
    def device_class(self):
        """Unit of measurement of the sensor"""
        # return DEVICE_CLASS_POWER
        return SensorDeviceClass.POWER

    @property
    def native_unit_of_measurement(self) -> str:
        return POWER_WATT


class FlowSensor(NjsPCEntity, SensorEntity):
    """Flow Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator, pump):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._pump = pump
        self._value = pump[FLOW]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self._pump["id"]
            and FLOW
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[FLOW]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._pump["name"] + " Flow"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(f'pump_{self._pump["id"]}_gpm')

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        return self._value

    @property
    def native_unit_of_measurement(self):
        """Unit of measurement of the sensor"""
        return "GPM"

    @property
    def icon(self) -> str:
        return "mdi:pump"

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        attrs = {}
        if MIN_FLOW in self._pump:
            attrs[MIN_FLOW] = self._pump[MIN_FLOW]
        if MAX_FLOW in self._pump:
            attrs[MAX_FLOW] = self._pump[MAX_FLOW]
        return attrs if len(attrs) > 0 else None
        # return {
        #     "min_flow": self._pump["minFlow"],
        #     "max_flow": self._pump["maxFlow"],
        # }


class SaltSensor(NjsPCEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_LEVEL]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and SALT_LEVEL
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            # self._chlorinator = self.coordinator.data
            self._value = self.coordinator.data[SALT_LEVEL]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._chlorinator["name"] + " Salt Level"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'saltlevel_{self._chlorinator["id"]}'
        )

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        # return self._chlorinator[SALT_LEVEL]
        return self._value

    @property
    def icon(self):
        return "mdi:shaker-outline"

    @property
    def native_unit_of_measurement(self) -> str:
        return "PPM"

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "salt_target": self._chlorinator[SALT_TARGET],
            "salt_required": self._chlorinator[SALT_REQUIRED],
        }


class SaltTargetSensor(NjsPCEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_TARGET]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and SALT_TARGET
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._chlorinator = self.coordinator.data
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._chlorinator["name"] + " Salt Target"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'salttarget_{self._chlorinator["id"]}'
        )

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        # return self._chlorinator[SALT_TARGET]
        return self._value

    @property
    def icon(self):
        return "mdi:target-variant"

    @property
    def native_unit_of_measurement(self) -> str:
        return "PPM"


class SaltRequiredSensor(NjsPCEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_REQUIRED]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and SALT_REQUIRED
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[SALT_REQUIRED]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._chlorinator["name"] + " Salt Required"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'saltrequired_{self._chlorinator["id"]}'
        )

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        # return self._chlorinator[SALT_REQUIRED]
        return self._value

    @property
    def icon(self):
        return "mdi:plus-box"

    @property
    def native_unit_of_measurement(self) -> str:
        return MASS_POUNDS


class StatusSensor(NjsPCEntity, SensorEntity):
    """Equipment Status Sensor for njsPC-HA"""

    def __init__(self, coordinator, equipment, event):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._equipment = equipment
        self._value = self._equipment[STATUS][DESC]
        self._event = event
        self._available = True
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self._equipment["id"]
        ):
            self._value = self.coordinator.data[STATUS][DESC]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._equipment["name"] + " Status"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(f'status_{self._equipment["id"]}')

    @property
    def native_value(self):
        # return self._equipment[STATUS][DESC]
        return self._value

    @property
    def icon(self):
        if self._value != "Ok":
            return "mdi:alert-circle"
        return "mdi:check-circle"


class CurrentOutputSensor(NjsPCEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[CURRENT_OUTPUT]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and CURRENT_OUTPUT
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[CURRENT_OUTPUT]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._chlorinator["name"] + " Current Output"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'saltoutput_{self._chlorinator["id"]}'
        )

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        # return self._chlorinator[CURRENT_OUTPUT]
        return self._value

    @property
    def icon(self):
        return "mdi:atom"

    @property
    def native_unit_of_measurement(self) -> str:
        return PERCENTAGE

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {"target_output": self._chlorinator[TARGET_OUTPUT]}


class TargetOutputSensor(NjsPCEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        # super().__init__(coordinator)
        self.coordinator = coordinator
        self.coordinator_context = object()
        self._chlorinator = chlorinator
        self._value = chlorinator[TARGET_OUTPUT]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and TARGET_OUTPUT
            in self.coordinator.data  # make sure the data we are looking for is in the coordinator data
        ):
            self._value = self.coordinator.data[TARGET_OUTPUT]
            self.async_write_ha_state()
        elif self.coordinator.data["event"] == EVENT_AVAILABILITY:
            self._available = self.coordinator.data["available"]
            self.async_write_ha_state()

    @property
    def should_poll(self):
        return False

    @property
    def available(self):
        return self._available

    @property
    def name(self):
        """Name of the sensor"""
        return self._chlorinator["name"] + " Target Output"

    @property
    def unique_id(self):
        """ID of the sensor"""
        return self.coordinator.api.get_unique_id(
            f'salttargetoutput_{self._chlorinator["id"]}'
        )

    @property
    def state_class(self):
        """State class of the sensor"""
        return SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        return self._value

    @property
    def icon(self):
        return "mdi:target"

    @property
    def native_unit_of_measurement(self) -> str:
        return PERCENTAGE
