"""Constants for the njsPC-HA integration."""

# from homeassistant.components.radarr.sensor import ENDPOINTS


DOMAIN = "njspc_ha"

# API ENDPOINTS
API_STATE_ALL = "state/all"
API_CIRCUIT_SETSTATE = "state/circuit/setState"
API_CIRCUITGROUP_SETSTATE = "state/circuitGroup/setState"
API_LIGHTGROUP_SETSTATE = "state/lightGroup/setState"
API_FEATURE_SETSTATE = "state/feature/setState"
API_CHLORINATOR_POOL_SETPOINT = "state/chlorinator/poolSetpoint"
API_CHLORINATOR_SPA_SETPOINT = "state/chlorinator/spaSetpoint"
API_SUPERCHLOR = "state/chlorinator/superChlorinate"
API_SWG_POOL_SETPOINT = "config/chlorinator"
API_CIRCUIT_SETTHEME = "state/circuit/setTheme"
API_CONFIG_BODY = "config/body"
API_HEATMODES = "heatModes"
API_CONFIG_CIRCUIT = "config/circuit"
API_LIGHTTHEMES = "lightThemes"


# SOCKETIO EVENTS
EVENT_CIRCUIT = "circuit"
EVENT_BODY = "body"
EVENT_TEMPS = "temps"
EVENT_CHLORINATOR = "chlorinator"
EVENT_PUMP = "pump"
EVENT_LIGHTGROUP = "lightGroup"
EVENT_CIRCUITGROUP = "circuitGroup"
EVENT_FEATURE = "feature"

POOL_SETPOINT = "poolSetpoint"
SPA_SETPOINT = "spaSetpoint"
