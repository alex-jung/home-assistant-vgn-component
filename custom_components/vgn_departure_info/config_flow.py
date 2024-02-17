import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector
from homeassistant.util import slugify

from .api.vgn_rest_api import VgnRestApi
from .const import (
    CONFIG_DIRECTION,
    CONFIG_DIRECTION_TEXT,
    CONFIG_LINE_NAME,
    CONFIG_PRODUCT_NAME,
    CONFIG_STOP_LIST,
    CONFIG_STOP_NAME,
    CONFIG_STOP_VGN_NUMBER,
    DOMAIN,
)
from .data.haltestelle import Haltestelle

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        super().__init__()

        self._api = VgnRestApi()
        self._entry_data: dict[str, Any] = {
            CONFIG_STOP_NAME: None,
            CONFIG_STOP_VGN_NUMBER: None,
            CONFIG_STOP_LIST: [],
        }
        self._haltestellen: list[Haltestelle] = []

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                self._haltestellen = await self.hass.async_add_executor_job(
                    self._api.get_haltestellen, user_input[CONFIG_STOP_NAME]
                )
            except ValueError:
                errors[CONFIG_STOP_NAME] = "failed_to_connect"

            if not self._haltestellen:
                errors[CONFIG_STOP_NAME] = "no_bus_stop_found"

            if not errors:
                return await self.async_step_street()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_STOP_NAME): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_street(self, user_input=None):
        errors = {}
        hs_names = [x.name for x in self._haltestellen]

        if user_input is not None:
            haltestelle = next(
                filter(
                    lambda x: x.name == user_input[CONFIG_STOP_NAME],
                    self._haltestellen,
                ),
                None,
            )

            if not haltestelle:
                errors[CONFIG_STOP_NAME] = "no_bus_stop_found"

            if not errors:
                self._entry_data[CONFIG_STOP_NAME] = user_input[CONFIG_STOP_NAME]
                self._entry_data[CONFIG_STOP_VGN_NUMBER] = haltestelle.vgn_number

                entry_title = slugify(f"{self._entry_data[CONFIG_STOP_NAME]}")

                await self.async_set_unique_id(entry_title)
                self._abort_if_unique_id_configured()

                abfahrten = await self.hass.async_add_executor_job(
                    self._api.get_abfahrten, haltestelle.vgn_number
                )
                # remove "duplicate" Abfahrten:
                # same product, line name and direction but different time
                abfahrten = list(set(abfahrten))

                for abfahrt in abfahrten:
                    self._entry_data[CONFIG_STOP_LIST].append(
                        {
                            CONFIG_STOP_VGN_NUMBER: abfahrt.stop_point,
                            CONFIG_LINE_NAME: abfahrt.line_name,
                            CONFIG_PRODUCT_NAME: abfahrt.product,
                            CONFIG_DIRECTION: abfahrt.direction,
                            CONFIG_DIRECTION_TEXT: abfahrt.direction_text,
                        }
                    )

                return self.async_create_entry(
                    title=entry_title,
                    data=self._entry_data,
                )

        return self.async_show_form(
            step_id="street",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_STOP_NAME): selector(
                        {"select": {"options": hs_names, "mode": "dropdown"}}
                    ),
                }
            ),
            errors=errors,
        )
