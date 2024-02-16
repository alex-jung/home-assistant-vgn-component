"""There is VAG coordinator module."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api.vag_rest_api import VagRestApi

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = 60  # seconds


class VagCoordinator(DataUpdateCoordinator):
    """Coordinator class for VAG Addon."""

    def __init__(
        self, hass: HomeAssistant, api, vgn_number: str, line: str, product: str
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="VagCoordinator",
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self._api: VagRestApi = api
        self._vgn_number = vgn_number
        self._line = line
        self._product = product

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

        return await self.hass.async_add_executor_job(
            self._api.get_abfahrten, self._vgn_number, self._line, self._product
        )
