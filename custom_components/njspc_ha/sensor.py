"""Platform for sensor integration."""

from homeassistant.const import (
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    MASS_POUNDS,
    POWER_WATT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
)
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CURRENT_OUTPUT,
    DESC,
    DOMAIN,
    EVENT_AVAILABILITY,
    EVENT_CHLORINATOR,
    EVENT_PUMP,
    EVENT_TEMPS,
    FLOW,
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
    for key in coordinator.api._config["temps"]:
        if isinstance(coordinator.api._config["temps"][key], int) or isinstance(
            coordinator.api._config["temps"][key], float
        ):
            new_devices.append(
                TempSensor(
                    coordinator, key, coordinator.api._config["temps"]["units"]["name"]
                )
            )
    for pump in coordinator.api._config["pumps"]:
        if RPM in pump:
            new_devices.append(RPMSensor(coordinator, pump))
        if WATTS in pump:
            new_devices.append(PowerSensor(coordinator, pump))
        if FLOW in pump:  # for pumps that have a flow reading
            new_devices.append(FlowSensor(coordinator, pump))
        new_devices.append(StatusSensor(coordinator, pump, EVENT_PUMP))
    for chlorinator in coordinator.api._config["chlorinators"]:
        if SALT_LEVEL in chlorinator:
            new_devices.append(SaltSensor(coordinator, chlorinator))
        if CURRENT_OUTPUT in chlorinator:
            new_devices.append(CurrentOutputSensor(coordinator, chlorinator))
        if TARGET_OUTPUT in chlorinator:
            new_devices.append(TargetOutputSensor(coordinator, chlorinator))
        if SALT_REQUIRED in chlorinator:
            new_devices.append(SaltRequiredSensor(coordinator, chlorinator))
        if SALT_TARGET in chlorinator:
            new_devices.append(SaltTargetSensor(coordinator, chlorinator))
        new_devices.append(StatusSensor(
            coordinator, chlorinator, EVENT_CHLORINATOR))
    if new_devices:
        async_add_entities(new_devices)


class TempSensor(CoordinatorEntity, SensorEntity):
    """Temp Sensor for njsPC-HA"""

    def __init__(self, coordinator, key, units):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._key = key
        self._units = units
        self._value = round(coordinator.api._config["temps"][key], 1)
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (self.coordinator.data["event"] == EVENT_TEMPS and self._key in self.coordinator.data):    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

    @property
    def native_value(self):
        return self._value

    @property
    def device_class(self):
        return DEVICE_CLASS_TEMPERATURE

    @property
    def native_unit_of_measurement(self) -> str:
        if self._units == "F":
            return TEMP_FAHRENHEIT
        return TEMP_CELSIUS


class RPMSensor(CoordinatorEntity, SensorEntity):
    """RPM Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator, pump):
        """Initialize the sensor."""
        super().__init__(coordinator)
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
        return STATE_CLASS_MEASUREMENT

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


class PowerSensor(CoordinatorEntity, SensorEntity):
    """Watts Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator, pump):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._pump = pump
        self._value = pump[WATTS]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self._pump["id"]
            and WATTS in self.coordinator.data    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

    @property
    def native_value(self):
        """Raw value of the sensor"""
        return self._value

    @property
    def device_class(self):
        """Unit of measurement of the sensor"""
        return DEVICE_CLASS_POWER

    @property
    def native_unit_of_measurement(self) -> str:
        return POWER_WATT


class FlowSensor(CoordinatorEntity, SensorEntity):
    """Flow Pump Sensor for njsPC-HA"""

    def __init__(self, coordinator, pump):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._pump = pump
        self._value = pump[FLOW]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self._pump["id"]
            and FLOW in self.coordinator.data    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

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
        return {
            "min_flow": self._pump["minFlow"],
            "max_flow": self._pump["maxFlow"],
        }


class SaltSensor(CoordinatorEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_LEVEL]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and SALT_LEVEL in self.coordinator.data    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

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


class SaltTargetSensor(CoordinatorEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_TARGET]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and SALT_TARGET in self.coordinator.data    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

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


class SaltRequiredSensor(CoordinatorEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._value = chlorinator[SALT_REQUIRED]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
            and SALT_REQUIRED in self.coordinator.data    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

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


class StatusSensor(CoordinatorEntity, SensorEntity):
    """Equipment Status Sensor for njsPC-HA"""

    def __init__(self, coordinator, equipment, event):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._equipment = equipment
        self._value = self._equipment[STATUS][DESC]
        self._event = event
        self._available = True

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


class CurrentOutputSensor(CoordinatorEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._value = chlorinator[CURRENT_OUTPUT]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]            
            and CURRENT_OUTPUT in self.coordinator.data    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

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

class TargetOutputSensor(CoordinatorEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._value = chlorinator[TARGET_OUTPUT]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]            
            and TARGET_OUTPUT in self.coordinator.data    # make sure the data we are looking for is in the coordinator data
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
        return STATE_CLASS_MEASUREMENT

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

