"""Bus notification integration."""

from dataclasses import dataclass
import logging

from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import VgnUpdateCoordinator
from .vgn.data_classes import Connection

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

type VgnConfigEntry = ConfigEntry[VgnConfigEntryData]


@dataclass
class VgnConfigEntryData:
    connections: list[Connection]
    coordinator: VgnUpdateCoordinator


async def async_setup_entry(hass: core.HomeAssistant, entry: VgnConfigEntry) -> bool:
    """ToDo."""
    _LOGGER.debug("Setting up entry: %s", entry.data)

    coordinator = VgnUpdateCoordinator(hass, entry.title, entry.data)

    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    entry.runtime_data = coordinator

    # await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
