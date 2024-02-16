"""Bus notification integration."""
import logging

from homeassistant import config_entries, core

from .api.vag_rest_api import VagRestApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    _LOGGER.info(f"Setup component for entry: {entry.entry_id}")  # noqa: G004

    api = VagRestApi()

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = {
        "data": entry.data,
        "api": api,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True
