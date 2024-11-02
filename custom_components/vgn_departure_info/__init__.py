"""Bus notification integration."""

from homeassistant import core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .vgn_update_coordinator import VgnUpdateCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: core.HomeAssistant, entry: ConfigEntry) -> bool:
    """ToDo."""
    coordinator = VgnUpdateCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
