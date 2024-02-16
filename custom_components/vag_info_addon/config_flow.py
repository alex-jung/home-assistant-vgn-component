"""Dummy comment."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import selector

from .api.vag_rest_api import VagRestApi
from .const import (
    CONFIG_DIRECTION,
    CONFIG_DIRECTION_TEXT,
    CONFIG_LINE_NAME,
    CONFIG_PRODUCT_NAME,
    CONFIG_STOP_NAME,
    CONFIG_STOP_VGN_NUMBER,
    DOMAIN,
)
from .data.haltestelle import Haltestelle

_LOGGER = logging.getLogger(__name__)

VGN_PRODUCTS = ["Bus", "UBahn", "Train"]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 1

    haltestellen: list[Haltestelle] = []

    entry_data: dict[str, Any] = {
        CONFIG_STOP_NAME: None,
        CONFIG_STOP_VGN_NUMBER: None,
        CONFIG_LINE_NAME: None,
        CONFIG_PRODUCT_NAME: None,
        CONFIG_DIRECTION: None,
        CONFIG_DIRECTION_TEXT: None,
    }

    def __init__(self) -> None:
        super().__init__()

        self._api = VagRestApi()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                self.haltestellen = await self.hass.async_add_executor_job(
                    self._api.get_haltestellen, user_input[CONFIG_STOP_NAME]
                )
            except ValueError:
                errors[CONFIG_STOP_NAME] = "invalid_stop_name"
                raise PlatformNotReady("Failed to fetch VAG data") from None

            if not errors:
                return await self.async_step_product()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_STOP_NAME): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_product(self, user_input=None):
        """Second step to define VGN number and product."""
        errors = {}
        hs_names = [x.name for x in self.haltestellen]
        haltestelle = None

        if user_input is not None:
            try:
                haltestelle = self._find_haltestelle_by_name(
                    user_input[CONFIG_STOP_NAME]
                )
            except ValueError:
                errors[
                    CONFIG_STOP_NAME
                ] = f'Keine Haltestelle mit Namen "{user_input[CONFIG_STOP_NAME]}" gefunden'

            if not errors:
                self.entry_data[CONFIG_STOP_NAME] = user_input[CONFIG_STOP_NAME]
                self.entry_data[CONFIG_STOP_VGN_NUMBER] = haltestelle.vgn_number
                self.entry_data[CONFIG_LINE_NAME] = user_input[CONFIG_LINE_NAME]
                self.entry_data[CONFIG_PRODUCT_NAME] = user_input[CONFIG_PRODUCT_NAME]

                return await self.async_step_direction()

        return self.async_show_form(
            step_id="product",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_STOP_NAME): selector(
                        {"select": {"options": hs_names, "mode": "dropdown"}}
                    ),
                    vol.Required(CONFIG_PRODUCT_NAME): selector(
                        {
                            "select": {
                                "options": VGN_PRODUCTS,
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Required(CONFIG_LINE_NAME): cv.string,
                }
            ),
            errors=errors,
        )

    async def async_step_direction(self, user_input=None):
        """Third step to define direction."""
        errors = {}

        abfahrten = None
        directions = {}

        try:
            abfahrten = await self.hass.async_add_executor_job(
                self._api.get_abfahrten,
                self.entry_data[CONFIG_STOP_VGN_NUMBER],
                self.entry_data[CONFIG_LINE_NAME],
            )

            for ab in abfahrten:
                directions[ab.direction_text] = ab.direction
        except ValueError:
            raise ValueError

        if user_input is not None:
            self.entry_data[CONFIG_DIRECTION_TEXT] = user_input[CONFIG_DIRECTION_TEXT]
            self.entry_data[CONFIG_DIRECTION] = directions[
                user_input[CONFIG_DIRECTION_TEXT]
            ]

            entry_title = f"{self.entry_data[CONFIG_STOP_NAME]} - {self.entry_data[CONFIG_PRODUCT_NAME]} - {self.entry_data[CONFIG_LINE_NAME]} - {self.entry_data[CONFIG_DIRECTION_TEXT]}"

            if not errors:
                return self.async_create_entry(
                    title=entry_title,
                    data=self.entry_data,
                )

        return self.async_show_form(
            step_id="direction",
            data_schema=vol.Schema(
                {
                    vol.Required(CONFIG_DIRECTION_TEXT): selector(
                        {
                            "select": {
                                "options": list(directions.keys()),
                                "mode": "dropdown",
                            }
                        }
                    ),
                }
            ),
            errors=errors,
        )

    def _find_haltestelle_by_name(self, name: str):
        for hs in self.haltestellen:
            if hs.name == name:
                return hs
        raise ValueError


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
                        CONFIG_STOP_VGN_NUMBER,
                        default=entry_data[CONFIG_STOP_VGN_NUMBER],
                    ): cv.string,
                    vol.Required(
                        CONFIG_PRODUCT_NAME,
                        default=entry_data[CONFIG_PRODUCT_NAME],
                    ): selector(
                        {
                            "select": {
                                "options": ["Bus", "UBahn", "Tram"],
                                "mode": "dropdown",
                            }
                        }
                    ),
                    vol.Required(
                        CONFIG_DIRECTION,
                        default=entry_data[CONFIG_DIRECTION],
                    ): cv.string,
                    vol.Required(
                        CONFIG_LINE_NAME,
                        default=entry_data[CONFIG_LINE_NAME],
                    ): cv.string,
                }
            ),
        )
