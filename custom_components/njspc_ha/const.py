"""Constants for the njsPC-HA integration."""

from homeassistant.backports.enum import StrEnum


DOMAIN = "njspc_ha"
MANUFACTURER = "nodejs-PoolController"

# API ENDPOINTS
API_STATE_ALL = "state/all"
API_CIRCUIT_SETSTATE = "state/circuit/setState"
API_CIRCUITGROUP_SETSTATE = "state/circuitGroup/setState"
API_LIGHTGROUP_SETSTATE = "state/lightGroup/setState"
API_FEATURE_SETSTATE = "state/feature/setState"
API_CHLORINATOR_POOL_SETPOINT = "state/chlorinator/poolSetpoint"
API_CHLORINATOR_SPA_SETPOINT = "state/chlorinator/spaSetpoint"
API_SUPERCHLOR = "state/chlorinator/superChlorinate"
API_CIRCUIT_SETTHEME = "state/circuit/setTheme"
API_CONFIG_BODY = "config/body"
API_HEATMODES = "heatModes"
API_CONFIG_CIRCUIT = "config/circuit"
API_LIGHTTHEMES = "lightThemes"
API_CONFIG_HEATERS = "config/options/heaters"
API_CONFIG_CHLORINATOR = "config/chlorinator"
API_LIGHTCOMMANDS = "lightCommands"
API_LIGHT_RUNCOMMAND = "state/light/runCommand"
API_TEMPERATURE_SETPOINT = "state/body/setPoint"
API_SET_HEATMODE = "state/body/heatMode"

# SOCKETIO EVENTS
EVENT_CIRCUIT = "circuit"
EVENT_BODY = "body"
EVENT_TEMPS = "temps"
EVENT_CHLORINATOR = "chlorinator"
EVENT_PUMP = "pump"
EVENT_LIGHTGROUP = "lightGroup"
EVENT_CIRCUITGROUP = "circuitGroup"
EVENT_FEATURE = "feature"
EVENT_AVAILABILITY = "availability"
EVENT_CONTROLLER = "controller"
EVENT_CHEM_CONTROLLER = "chemController"
EVENT_FILTER = "filter"

POOL_SETPOINT = "poolSetpoint"
SPA_SETPOINT = "spaSetpoint"

# KEYS
SALT_TARGET = "saltTarget"
SALT_LEVEL = "saltLevel"
SALT_REQUIRED = "saltRequired"
RPM = "rpm"
WATTS = "watts"
FLOW = "flow"
STATUS = "status"
DESC = "desc"
CURRENT_OUTPUT = "currentOutput"
TARGET_OUTPUT = "targetOutput"
SUPER_CHLOR = "superChlor"
SUPER_CHLOR_HOURS = "superChlorHours"
MIN_FLOW = "minFlow"
MAX_FLOW = "maxFlow"


class PoolEquipmentClass(StrEnum):
    """Class for pool equipment."""

    CONTROL_PANEL = "control_panel"
    """Outdoor Control panel for the pool"""

    BODY = "body"
    """Identifies a body associated with the control system"""

    AUX_CIRCUIT = "circuit"
    """AUX Circuit that is associated with a relay"""

    FEATURE = "feature"
    """A feature that defined for the pool"""

    CIRCUIT_GROUP = "circuitGroup"
    """Group or macro circuits"""

    LIGHT = "light"
    """A light attached to an Aux Circuit"""

    LIGHT_GROUP = "lightGroup"
    """Light groupings"""

    PUMP = "pump"
    """Filter or feature pump"""

    HEATER = "heater"
    """Defines a heater"""

    VALVE = "valve"
    """Valve"""

    CHLORINATOR = "chlorinator"
    """Clorinators that are RS485 controlled"""

    CHEM_CONTROLLER = "chemController"
    """Chemistry controller such as REM Chem or IntelliChem"""

    FILTER = "filter"
    """A pool equipment filter"""


class PoolEquipmentModel(StrEnum):
    """Model descriptions for pool equipment."""

    CONTROL_PANEL = "Control Panel"
    """Outdoor Control panel for the pool"""

    BODY = "Pool Body"
    """Identifies a body associated with the control system"""

    AUX_CIRCUIT = "Pool Circuit"
    """AUX Circuit that is associated with a relay"""

    FEATURE = "Pool Feature"
    """A feature that defined for the pool"""

    CIRCUIT_GROUP = "Pool Circuit Group"
    """Group or macro circuits"""

    LIGHT = "Pool Light"
    """A light attached to an Aux Circuit"""

    LIGHT_GROUP = "Pool Light Group"
    """Light groupings"""

    PUMP = "Pool Pump"
    """Filter or feature pump"""

    HEATER = "Pool Heater"
    """Defines a heater"""

    VALVE = "Pool Valve"
    """Valve"""

    CHLORINATOR = "Pool Chlorinator"
    """Clorinators that are RS485 controlled"""

    CHEM_CONTROLLER = "Pool Chemistry Controller"
    """Chemistry controller such as REM Chem or IntelliChem"""

    FILTER = "Pool Filter"
    """Equipment filter for the pool"""
