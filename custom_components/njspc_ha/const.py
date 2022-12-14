"""Constants for the njsPC-HA integration."""

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
APT_SET_HEATMODE = "state/body/heatMode"

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
