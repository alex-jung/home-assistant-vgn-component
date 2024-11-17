"""Config flow for VGN Departures."""

from copy import deepcopy
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.selector import selector
from homeassistant.util import Any, slugify

from .const import (
    CFG_CONNECTIONS,
    CFG_ERROR_ALREADY_CONFIGURED,
    CFG_ERROR_GTFS_NOT_FOUND,
    CFG_ERROR_NO_CHANGES_OPTIONS,
    CFG_ERROR_STOP_NOT_FOUND,
    CFG_STOP,
    CFG_STOP_NAME,
    DOMAIN,
)
from .vgn.api_gtfs import ApiGtfs
from .vgn.data_classes import Connection, Stop
from .vgn.exceptions import GtfsFileNotFound

_LOGGER = logging.getLogger(__name__)


def get_select_connections_options(
    connections: list[dict] | list[Connection],
) -> dict[str, str]:
    """Prepare sorted dict of connections for multi_select. Key contains connection uid and value is connection attributes as dict."""
    result = {}

    for connection in connections:
        is_dict = isinstance(connection, dict)

        func = (
            get_select_connection_option_from_dict
            if is_dict
            else get_select_connection_option_from_obj
        )

        result.update(func(connection))

    return dict(sorted(result.items(), key=lambda item: item[1]))


def get_select_connection_option_from_dict(connection: dict) -> dict[str, str]:
    """Convert connection dict into option dict for multi_select."""
    uid = connection["uid"]
    transport = connection["transport"]
    line_name = connection["line_name"]
    name = connection["name"]

    return {uid: f"{transport} - {line_name} - {name}"}


def get_select_connection_option_from_obj(connection: Connection) -> dict[str, str]:
    """Convert connection object into option dict for multi_select."""
    uid = connection.uid
    transport = connection.transport
    line_name = connection.line_name
    name = connection.name

    return {uid: f"{transport} - {line_name} - {name}"}


class OptionsFlowHandler(OptionsFlow):
    """Options flow handler for VGN Departures config entry."""

    def __init__(self, stop: dict, connections: list[dict]) -> None:
        """Initialize options flow."""
        self._stop: dict = stop
        self._selected_connections: list[dict] = [
            Connection.from_dict(x) for x in connections
        ]
        self._api: ApiGtfs = ApiGtfs()
        # list of all available for _stop connections
        self._all_connections: list[Connection] = []
        # list of uid(s) selected for this configuration entry
        self._selected_uids: list[str] = [x.uid for x in self._selected_connections]

        _LOGGER.debug("Start options dialog")
        _LOGGER.debug("Stop: %s", self._stop)
        _LOGGER.debug("Connections: %s", self._selected_connections)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            removed_connections = list(
                filter(
                    lambda x: x.uid not in user_input[CFG_CONNECTIONS],
                    self._selected_connections,
                )
            )
            added_connections = list(
                filter(
                    lambda x: x.uid in user_input[CFG_CONNECTIONS]
                    and x.uid not in self._selected_uids,
                    self._all_connections,
                )
            )

            if not removed_connections and not added_connections:
                _LOGGER.debug("No changes on entry configuration detected")
                return self.async_abort(reason=CFG_ERROR_NO_CHANGES_OPTIONS)

            updated_config = deepcopy(self.config_entry.data[CFG_CONNECTIONS])

            entity_registry = er.async_get(self.hass)
            entries = er.async_entries_for_config_entry(
                entity_registry, self.config_entry.entry_id
            )

            connections_map = {e.unique_id: e.entity_id for e in entries}

            # delete connection(s) removed by user from registry
            for uid in [x.uid for x in removed_connections]:
                _LOGGER.debug("Remove connection with uid:%s", uid)

                entity_registry.async_remove(connections_map[uid])

                updated_config = [e for e in updated_config if e["uid"] != uid]

            # add new connection(s) added be user
            for connection in added_connections:
                _LOGGER.debug("Add connection with uid:%s", connection.uid)

                updated_config.append(connection.to_dict())

            data = {
                CFG_STOP: self._stop,
                CFG_CONNECTIONS: updated_config,
            }

            self.hass.config_entries.async_update_entry(self.config_entry, data=data)

            return self.async_create_entry(data=data)

        try:
            await self._api.load()
        except GtfsFileNotFound:
            return self.async_abort(reason=CFG_ERROR_GTFS_NOT_FOUND)

        self._all_connections: list[dict] = await self._api.connections(
            Stop.from_dict(self._stop)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CFG_CONNECTIONS,
                        default=self._selected_uids,
                    ): cv.multi_select(
                        get_select_connections_options(self._all_connections)
                    ),
                }
            ),
        )


class FlowHandler(ConfigFlow, domain=DOMAIN):
    """FlowHandler for VGN Departures component."""

    VERSION = 2
    MINOR_VERSION = 0

    def __init__(self) -> None:
        """Initialize flow handler."""
        super().__init__()

        self._api: ApiGtfs = ApiGtfs()
        # list of all "stops" available in GTFS
        # one bus stop can have multiple stop objects: for each drive direction and transport type
        self._all_stops: Stop[str] = []
        # stop object selected by user
        self._stop: Stop | None = None
        # list of all connections available for choosen stop
        self._connections: list[Connection] = []

        _LOGGER.debug("Start '%s' configuration flow", DOMAIN)

    async def async_step_user(self, user_input=None):
        """Step to choose stop name."""

        _LOGGER.debug("Start step_user: %s", user_input)

        errors = {}
        placeholders = {}

        if user_input is not None:
            choose = user_input[CFG_STOP_NAME]

            if choose not in [x.name for x in self._all_stops]:
                errors[CFG_STOP_NAME] = CFG_ERROR_STOP_NOT_FOUND
                placeholders[CFG_STOP_NAME] = choose
            else:
                self._stop = next(
                    filter(
                        lambda x: x.name == choose,
                        self._all_stops,
                    )
                )

                await self.async_set_unique_id(slugify(self._stop.name))

                self._abort_if_unique_id_configured(error=CFG_ERROR_ALREADY_CONFIGURED)

            if not errors:
                return await self.async_step_connections()

        try:
            await self._api.load()
        except GtfsFileNotFound:
            return self.async_abort(reason=CFG_ERROR_GTFS_NOT_FOUND)

        self._all_stops = await self._api.stops()

        _LOGGER.debug("Loaded %s stop(s)", len(self._all_stops))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CFG_STOP_NAME): selector(
                        {
                            "select": {
                                "options": [x.name for x in self._all_stops],
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
        """Step to choose connections the user is interested in."""

        _LOGGER.debug("Start 'step_connections': %s", user_input)

        errors = {}

        if user_input is not None:
            connections = list(
                filter(
                    lambda x: x.uid in user_input[CFG_CONNECTIONS], self._connections
                )
            )

            return self.async_create_entry(
                title=self._stop.name,
                data={
                    CFG_STOP: self._stop.to_dict(),
                    CFG_CONNECTIONS: [x.to_dict() for x in connections],
                },
            )

        self._connections: list[dict] = await self._api.connections(self._stop)

        return self.async_show_form(
            step_id="connections",
            data_schema=vol.Schema(
                {
                    vol.Required(CFG_CONNECTIONS, default=[]): cv.multi_select(
                        get_select_connections_options(self._connections)
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""

        return OptionsFlowHandler(
            config_entry.data[CFG_STOP], config_entry.data[CFG_CONNECTIONS]
        )
