"""Dummy comment."""
import logging
from typing import Any, Optional

import voluptuous as vol

import requests

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from homeassistant.helpers.selector import selector

from .const import (
    CONF_DIRECTION,
    CONF_LINE_NAME,
    CONF_PRODUCT,
    CONF_STOP_VAG_NUMBER,
    DOMAIN,
    VGN_SERVICE_URL,
)

_LOGGER = logging.getLogger(__name__)


async def validate_number(number):
    int(number)


async def validate_vag_stop_number(number):
    url = f"{VGN_SERVICE_URL}/{number}"

    if not requests.get(url, timeout=10).ok:
        raise ValueError

    return True


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    data: Optional[dict[str, Any]]

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                await validate_vag_stop_number(user_input[CONF_STOP_VAG_NUMBER])
            except ValueError:
                errors[CONF_STOP_VAG_NUMBER] = "wrong_stop_number"

            try:
                await validate_number(user_input[CONF_LINE_NAME])
            except ValueError:
                errors[CONF_LINE_NAME] = "wrong_line_name"

            if not errors:
                self.data = user_input

                return self.async_create_entry(
                    title=f"{user_input[CONF_LINE_NAME]} - {user_input[CONF_DIRECTION]}",
                    data=self.data,
                )

        user_input = user_input or {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOP_VAG_NUMBER): cv.string,
                    vol.Required(CONF_PRODUCT): selector(
                        {
                            "select": {
                                "options": ["Bus", "UBahn", "Tram"],
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Required(CONF_DIRECTION): cv.string,
                    vol.Required(CONF_LINE_NAME): cv.string,
                }
            ),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

        _LOGGER.debug(f"OptionsFlowHandler created - {self.config_entry.options}")

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        _LOGGER.debug(f"step_init. {user_input=}")
        _LOGGER.debug(f"step_init. {self.config_entry.data=}")

        entry_data = self.config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_STOP_VAG_NUMBER,
                        default=entry_data[CONF_STOP_VAG_NUMBER],
                    ): cv.string,
                    vol.Required(
                        CONF_PRODUCT,
                        default=entry_data[CONF_PRODUCT],
                    ): selector(
                        {
                            "select": {
                                "options": ["Bus", "UBahn", "Tram"],
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Required(
                        CONF_DIRECTION,
                        default=entry_data[CONF_DIRECTION],
                    ): cv.string,
                    vol.Required(
                        CONF_LINE_NAME,
                        default=entry_data[CONF_LINE_NAME],
                    ): cv.string,
                }
            ),
        )
