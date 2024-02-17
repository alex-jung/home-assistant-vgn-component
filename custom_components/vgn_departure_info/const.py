from typing import Final

DOMAIN = "vgn_departure_info"

# Constants for "Haltestellen"
REST_API_VAG_NUMBER_TAG: Final = "VAGKennung"
REST_API_VGN_NUMBER_TAG: Final = "VGNKennung"
REST_API_BUS_STOP_NAME_TAG: Final = "Haltestellenname"
REST_API_VGN_PRODUCTS_TAG: Final = "Produkte"
REST_API_LONGITUDE_TAG: Final = "Longitude"
REST_API_LATITUDE_TAG: Final = "Latitude"
REST_API_BUS_STOPS_TAG: Final = "Haltestellen"
REST_API_BUS_STOP_TAG: Final = "Haltestelle"

# Constants for "Abfahrten"
REST_API_ABFAHRTEN_TAG: Final = "Abfahrten"
REST_API_LINE_NAME_TAG: Final = "Linienname"
REST_API_STOP_POINT_TAG: Final = "Haltepunkt"
REST_API_DIRECTION_TAG: Final = "Richtung"
REST_API_DIRECTION_TEXT_TAG: Final = "Richtungstext"
REST_API_DEPARTURE_MUST_TAG: Final = "AbfahrtszeitSoll"
REST_API_DEPARTURE_IS_TAG: Final = "AbfahrtszeitIst"
REST_API_PRODUCT_TAG: Final = "Produkt"
REST_API_TRIP_NUMBER_TAG: Final = "Fahrtnummer"
REST_API_OPERATION_DAY_TAG: Final = "Betriebstag"
REST_API_TRIP_ART_TAG: Final = "Fahrtartnummer"
REST_API_CAR_NUMBER_TAG: Final = "Fahrzeugnummer"
REST_API_OCCUPANCY_LEVEL_TAG: Final = "Besetzgrad"
REST_API_PROGNOSE_TAG: Final = "Prognose"
REST_API_STOP_POINT_TEXT_TAG: Final = "HaltesteigText"

# Config entry data
CONFIG_STOP_NAME: Final = "stop_name"
CONFIG_STOP_VGN_NUMBER: Final = "stop_vgn_number"
CONFIG_STOP_LIST: Final = "stop_list"

# fetch update interval
FETCH_UPDATE_INTERVAL = 60  # seconds

CONFIG_LINE_NAME: Final = "line_name"
CONFIG_PRODUCT_NAME: Final = "product_name"
CONFIG_DIRECTION: Final = "direction"
CONFIG_DIRECTION_TEXT: Final = "direction_text"
