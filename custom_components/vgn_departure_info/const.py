from typing import Final

DOMAIN = "vgn_departure_info"

# fetch update interval
FETCH_UPDATE_INTERVAL = 30  # seconds
REQUEST_TIME_SPAN = 60  # minutes
MAX_DEPARTURES = 5

ERROR_GTFS_NOT_FOUND = "gtfs_not_found"

# Config entry data
CONFIG_TRANSPORT_TYPE: Final = "transport_type"
CONFIG_STATION_NAME: Final = "stop_name"
CONFIG_STATION_ID: Final = "stop_id"
CONFIG_CONNECTIONS: Final = "connections"
CONFIG_SENSORS_DATA: Final = "sensor_data"

CONFIG_DEPARTURE_LIST: Final = "stop_list"
CONFIG_LINE_NAME: Final = "line_name"
CONFIG_PRODUCT_NAME: Final = "product_name"
CONFIG_DIRECTION: Final = "direction"
CONFIG_DIRECTION_TEXT: Final = "direction_text"

# Sensor attributes
ATTR_LINE_NAME: Final = "line_name"
ATTR_STOP_ID: Final = "stop_id"
ATTR_TRANSPORT_TYPE: Final = "transport"
ATTR_DIRECTION: Final = "direction"
ATTR_DIRECTION_TEXT: Final = "direction_text"
ATTR_DEPARTURES: Final = "departures"
