"""Platform for sensor integration."""

from homeassistant.const import (
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    POWER_WATT,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
    PERCENTAGE
)
from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT, SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, EVENT_AVAILABILITY, EVENT_CHLORINATOR, EVENT_PUMP, EVENT_TEMPS


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
        new_devices.append(RPMSensor(coordinator, pump))
        new_devices.append(PowerSensor(coordinator, pump))
        new_devices.append(StatusSensor(coordinator, pump, EVENT_PUMP))
    for chlorinator in coordinator.api._config["chlorinators"]:
        new_devices.append(SaltSensor(coordinator, chlorinator))
        new_devices.append(StatusSensor(coordinator, chlorinator, EVENT_CHLORINATOR))
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
        if self.coordinator.data["event"] == EVENT_TEMPS:
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
        self._value = pump["rpm"]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self._pump["id"]
        ):
            self._value = self.coordinator.data["rpm"]
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
        self._value = pump["watts"]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_PUMP
            and self.coordinator.data["id"] == self._pump["id"]
        ):
            self._value = self.coordinator.data["watts"]
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


class SaltSensor(CoordinatorEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._value = chlorinator["saltLevel"]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
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
        return self._chlorinator["saltLevel"]

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
            "salt_target": self._chlorinator["saltTarget"],
            "salt_required": self._chlorinator["saltRequired"],
        }


class StatusSensor(CoordinatorEntity, SensorEntity):
    """Equipment Status Sensor for njsPC-HA"""

    def __init__(self, coordinator, equipment, event):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._equipment = equipment
        self._event = event
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == self._event
            and self.coordinator.data["id"] == self._equipment["id"]
        ):
            self._equipment = self.coordinator.data
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
        return self._equipment["status"]["desc"]

    @property
    def icon(self):
        if self._equipment["status"]["desc"] != "Ok":
            return "mdi:alert-circle"
        return "mdi:check-circle"



class TargetSensor(CoordinatorEntity, SensorEntity):
    """SWG Salt Sensor for njsPC-HA"""

    def __init__(self, coordinator, chlorinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._chlorinator = chlorinator
        self._value = chlorinator["currentOutput"]
        self._available = True

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (
            self.coordinator.data["event"] == EVENT_CHLORINATOR
            and self.coordinator.data["id"] == self._chlorinator["id"]
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
        return self._chlorinator["currentOutput"]

    @property
    def icon(self):
        return "mdi:atom"

    @property
    def native_unit_of_measurement(self) -> str:
        return PERCENTAGE

    @property
    def extra_state_attributes(self):
        """Return entity specific state attributes."""
        return {
            "target_output": self._chlorinator["targetOutput"]
        }