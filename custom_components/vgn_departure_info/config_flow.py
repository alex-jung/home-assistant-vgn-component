"""ToDo."""

import logging
from typing import Any

from pandas import DataFrame
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector
from homeassistant.util import slugify

from .const import (
    CONFIG_CONNECTIONS,
    CONFIG_SENSORS_DATA,
    CONFIG_STATION_ID,
    CONFIG_STATION_NAME,
    CONFIG_TRANSPORT_TYPE,
    DOMAIN,
)
from .vgn.data_classes import SensorData, TransportType
from .vgn.gtfs_client import VGNGtfsClient

_LOGGER = logging.getLogger(__name__)


async def convert_connection_to_options(station_name, group_head, frame):
    """Prepare options for connections config flow."""
    stop_id = frame.iloc[0]["stop_id"]
    transport = TransportType(frame.iloc[0]["route_type"])
    line_name = group_head[1]
    direction_text = group_head[0]
    direction = frame.iloc[0]["direction_id"]

    label = f'{transport.value} "{line_name}" - {direction_text}'

    value = f"{station_name}#{stop_id}#{transport.index}#{line_name}#{direction_text}#{direction}"

    return (label, value)


async def convert_to_sensor_data(option_value: str):
    """Convert connnection data from input string provided by user."""
    split = option_value.split("#")

    station_name = split[0]
    stop_id = split[1]
    transport = int(split[2])
    line_name = split[3]
    direction_text = split[4]
    direction = int(split[5])

    return {
        "station_name": station_name,
        "stop_id": stop_id,
        "transport": transport,
        "line_name": line_name,
        "direction_text": direction_text,
        "direction": direction,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ToDo."""

    VERSION = 2
    MINOR_VERSION = 0

    async def _get_stops(self, stop_name: str):
        return self._api.stops(stop_name)

    def __init__(self) -> None:
        """ToDo."""
        super().__init__()

        self._entry_data: dict[str, Any] = {
            # station name. e.g. "Frankenstr"
            CONFIG_STATION_NAME: None,
            # station id. e.g. 1976
            CONFIG_STATION_ID: None,
            # list of direction(s) choosen by user
            CONFIG_SENSORS_DATA: [],
        }

        self._cf: DataFrame = None
        self._api: VGNGtfsClient | None = None
        self._stop_name: str | None = None
        self._stop_id: str | None = None
        self._transport_types: list[TransportType] = []

        _LOGGER.info("Start configuration flow for VGN departure entry")

    async def async_step_user(self, user_input=None):
        """Step to provide stop name."""
        errors = {}

        # initialize api
        self._api = await self.hass.async_add_executor_job(VGNGtfsClient.instance)

        _LOGGER.debug("Start step_user")
        _LOGGER.debug("- user_input: %s", user_input)

        if user_input is not None:
            _LOGGER.debug("Fetching VGN stops")

            self._cf = await self.hass.async_add_executor_job(
                self._api.stops, user_input[CONFIG_STATION_NAME]
            )

            # self._cf = await self._api.stops(user_input[CONFIG_STATION_NAME])

            _LOGGER.debug(
                'Found %s stop(s) for input "%s"',
                len(self._cf.index),
                user_input[CONFIG_STATION_NAME],
            )

            if len(self._cf.index) == 0:
                errors[CONFIG_STATION_NAME] = "error_no_stop_found"

            if not errors:
                return await self.async_step_station()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_STATION_NAME): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_station(self, user_input=None):
        """Step to choose the station."""
        errors = {}

        _LOGGER.debug("Start 'step_station'")
        _LOGGER.debug("- user_input: %s", user_input)

        if user_input is not None:
            self._stop_name = user_input[CONFIG_STATION_NAME]
            self._transport_types = [
                TransportType(int(x)) for x in user_input[CONFIG_TRANSPORT_TYPE]
            ]

            _LOGGER.debug("Filter stop(s) selected by user: %s", self._stop_name)

            # removed all other not relevant stations
            df = self._cf
            df = df.drop(df[(~df.stop_name.str.contains(self._stop_name))].index)
            df = df[["stop_id", "stop_name"]]

            _LOGGER.debug("Count fo stops after filtering: %s", len(df))

            # add trips
            trips = await self.hass.async_add_executor_job(
                self._api.stop_times, df["stop_id"].to_list()
            )

            trips = trips[["stop_id", "trip_id", "departure_time"]]

            all_trips = await self.hass.async_add_executor_job(self._api.trips)

            df = trips.merge(all_trips, on="trip_id", how="left").drop(
                ["block_id"], axis=1
            )

            # add route information
            routes = await self.hass.async_add_executor_job(
                self._api.routes, None, None, self._transport_types
            )

            routes = routes[["route_id", "route_short_name", "route_type"]]

            df = df.merge(routes, on="route_id", how="left")
            df = df.drop(df[(~df.route_id.isin(routes["route_id"]))].index)

            _LOGGER.debug("Confguration frame len: %s", len(df))

            if df.empty:
                errors[CONFIG_STATION_NAME] = "error_no_stop_found"

            if not errors:
                self._cf = df
                self._stop_name = user_input[CONFIG_STATION_NAME]
                self._stop_id = self._cf.iloc[0]["stop_id"]
                return await self.async_step_connections()

        return self.async_show_form(
            step_id="station",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_STATION_NAME): selector(
                        {
                            "select": {
                                "options": list(set(self._cf["stop_name"])),
                                "mode": "dropdown",
                                "sort": True,
                            }
                        }
                    ),
                    vol.Required(CONFIG_TRANSPORT_TYPE): selector(
                        {
                            "select": {
                                "options": [
                                    {"label": "Bus", "value": "3"},
                                    {"label": "Zug", "value": "2"},
                                    {"label": "U-Bahn", "value": "1"},
                                    {"label": "Straßenbahn", "value": "0"},
                                ],
                                "mode": "list",
                                "multiple": True,
                            }
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_connections(self, user_input=None):
        """ToDo."""
        errors = {}

        _LOGGER.debug("Start step_connections")
        _LOGGER.debug("- user_input: %s", user_input)

        if user_input is not None:
            connections = [
                await convert_to_sensor_data(x) for x in user_input[CONFIG_CONNECTIONS]
            ]

            _LOGGER.debug("Result connections: %s", connections)

            entry_title = slugify(self._stop_name)

            await self.async_set_unique_id(entry_title)
            self._abort_if_unique_id_configured()

            self._entry_data[CONFIG_STATION_ID] = self._stop_id
            self._entry_data[CONFIG_SENSORS_DATA] = connections

            return self.async_create_entry(
                title=self._stop_name,
                data=self._entry_data,
            )

        groups = self._cf.groupby(["trip_headsign", "route_short_name"])

        names_options = []

        for x, frame in groups:
            (label, value) = await convert_connection_to_options(
                self._stop_name, x, frame
            )
            names_options.append({"label": label, "value": value})

        return self.async_show_form(
            step_id="connections",
            data_schema=vol.Schema(
                {
                    CONFIG_CONNECTIONS: selector(
                        {
                            "select": {
                                "mode": "dropdown",
                                "multiple": True,
                                "sort": True,
                                "options": names_options,
                            }
                        }
                    )
                }
            ),
            errors=errors,
        )
