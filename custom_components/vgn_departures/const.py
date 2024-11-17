"""Constants for VGN Departures custom component."""

from typing import Final

DOMAIN = "vgn_departures"


# fetch update interval
FETCH_UPDATE_INTERVAL = 30  # seconds
REQUEST_TIME_SPAN = 60  # minutes
MAX_DEPARTURES = 5

# Config entry data
CFG_STOP_NAME: Final = "stop_name"
CFG_STOP: Final = "stop"
CFG_CONNECTIONS: Final = "connections"

CFG_ERROR_GTFS_NOT_FOUND = "error_gtfs_not_found"
CFG_ERROR_STOP_NOT_FOUND = "error_stop_not_found"
CFG_ERROR_NO_CHANGES_OPTIONS = "error_no_changes"
CFG_ERROR_ALREADY_CONFIGURED = "error_already_configured"

# Sensor attributes
ATTR_ATTRIBUTION = "Data provided by https://www.vgn.de"
ATTR_LINE_NAME: Final = "line_name"
ATTR_STOP_ID: Final = "stop_id"
ATTR_TRANSPORT_TYPE: Final = "transport"
ATTR_DIRECTION: Final = "direction"
ATTR_DIRECTION_TEXT: Final = "direction_text"
ATTR_DEPARTURES: Final = "departures"
ATTR_OCCUPANCY_LEVEL: Final = "occupancy_level"
ATTR_PLANNED_DEPARTURE_TIME: Final = "planned_departure_time"
ATTR_ACTUAL_DEPARTURE_TIME: Final = "actual_departure_time"
