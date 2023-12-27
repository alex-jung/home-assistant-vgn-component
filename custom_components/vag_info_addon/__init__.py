"""Bus notification integration."""
import logging

from homeassistant import config_entries, core

from .api.vag_rest_api import VagRestApi
from .const import CONF_STOP_VAG_NUMBER, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    _LOGGER.debug(f"Setup component for entry: {entry.entry_id}")

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "api": VagRestApi(hass, stop_number=entry.data[CONF_STOP_VAG_NUMBER]),
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True
