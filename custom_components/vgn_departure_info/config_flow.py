"""ToDo."""

import logging
from typing import Any

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
from .vgn.data_classes import Connection, Stop, TransportType
from .vgn.gtfs_client import ApiGtfs

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ToDo."""

    VERSION = 2
    MINOR_VERSION = 0

    def __init__(self) -> None:
        """ToDo."""
        super().__init__()
        self._api: ApiGtfs = ApiGtfs()
        self._stop_list: Stop[str] = []
        self._stop: Stop | None = None
        self._connections: list[Connection] = []

        _LOGGER.info("Start '%s' configuration flow", DOMAIN)

    async def async_step_user(self, user_input=None):
        """Step to provide stop name."""
        _LOGGER.debug("Start step_user: %s", user_input)

        errors = {}
        placeholders = {}

        if user_input is not None:
            _LOGGER.debug("Fetching VGN stops")

            if user_input[CONFIG_STATION_NAME] not in [x.name for x in self._stop_list]:
                errors[CONFIG_STATION_NAME] = "error_no_stop_found"
                placeholders[CONFIG_STATION_NAME] = user_input[CONFIG_STATION_NAME]
            else:
                self._stop = next(
                    filter(
                        lambda x: x.name == user_input[CONFIG_STATION_NAME],
                        self._stop_list,
                    )
                )

            if not errors:
                return await self.async_step_connections()

        await self._api.load()

        self._stop_list = await self._api.stops()

        _LOGGER.debug("Loaded %s stop(s)", len(self._stop_list))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_STATION_NAME): selector(
                        {
                            "select": {
                                "options": [x.name for x in self._stop_list],
                                "mode": "dropdown",
                                "custom_value": True,
                                "sort": True,
                            }
                        }
                    )
                }
            ),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def async_step_connections(self, user_input=None):
        """ToDo."""
        _LOGGER.debug("Start 'step_connections': %s", user_input)

        errors = {}

        if user_input is not None:
            connections = [
                self._connections[int(idx)] for idx in user_input[CONFIG_CONNECTIONS]
            ]

            entry_title = slugify(self._stop.name)

            await self.async_set_unique_id(entry_title)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=self._stop.name,
                data={
                    CONFIG_CONNECTIONS: [x.to_dict() for x in connections],
                },
            )

        self._connections = await self._api.connections(self._stop)

        def convert(connections):
            result = []
            for idx, value in enumerate(connections):
                result.append(
                    {
                        "value": str(idx),
                        "label": f"{value.transport} - {value.line_name} - {value.name}",
                    }
                )

            return result

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
                                "options": convert(self._connections),
                            }
                        }
                    )
                }
            ),
            errors=errors,
        )
