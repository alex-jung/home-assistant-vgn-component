"""There is VAG coordinator module."""

from datetime import timedelta
import logging

from requests.exceptions import HTTPError, Timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import update_coordinator
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api.vag_rest_api import VagRestApi
from .const import CONFIG_LINE_NAME, CONFIG_PRODUCT_NAME, CONFIG_STOP_VGN_NUMBER, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = 60  # seconds


class VagCoordinator(DataUpdateCoordinator):
    """Coordinator class for VAG custom component."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize VAG coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="VagLog",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.logger.debug("Create Coordinator")
        self.logger.debug(entry.data[DOMAIN])

        self._api = VagRestApi()
        self._vgn_number = entry.data[DOMAIN][CONFIG_STOP_VGN_NUMBER]
        self._line = entry.data[DOMAIN][CONFIG_LINE_NAME]
        self._product = entry.data[DOMAIN][CONFIG_PRODUCT_NAME]
        self.unique_id = entry.entry_id

        _LOGGER.debug("VAG Coordinator created")

    @property
    def vgn_number(self):
        return self._vgn_number

    @property
    def line_name(self):
        return self._line

    @property
    def vgn_product(self):
        return self._product

    async def _async_update_data(self):
        _LOGGER.info("Fetching data")

        try:
            data = await self.hass.async_add_executor_job(
                self._api.get_abfahrten, self._vgn_number, self._line, self._product
            )
        except (Timeout, HTTPError) as err:
            raise update_coordinator.UpdateFailed(err) from err

        self.logger.debug("Successfully fetched data from VAG")

        return data
