"""There is VGN coordinator module."""

from datetime import timedelta
import logging

from requests.exceptions import HTTPError, Timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import update_coordinator
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api.vgn_rest_api import VgnRestApi
from .const import CONFIG_STOP_LIST, CONFIG_STOP_VGN_NUMBER, FETCH_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class VgnCoordinator(DataUpdateCoordinator):
    """Coordinator class for VGN custom component updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="VagLog",
            update_interval=timedelta(seconds=FETCH_UPDATE_INTERVAL),
        )
        _LOGGER.info(f"Create VGN-Coordinator for {entry.title}")

        self._api = VgnRestApi()
        self._vgn_number = entry.data[CONFIG_STOP_VGN_NUMBER]
        self._title = entry.title
        self._entries = entry.data[CONFIG_STOP_LIST]

    @property
    def entries(self):
        return self._entries

    @property
    def vgn_number(self):
        return self._vgn_number

    @property
    def title(self):
        return self._title

    async def _async_update_data(self):
        self.logger.info(f"Fetching data for '{self.title}'")

        try:
            data = await self.hass.async_add_executor_job(
                self._api.get_abfahrten, self.vgn_number
            )
        except (Timeout, HTTPError) as err:
            raise update_coordinator.UpdateFailed(err) from err

        self.logger.info(
            f"Data successfully fetched with {len(data) if data else 0} data entries"
        )

        return data
