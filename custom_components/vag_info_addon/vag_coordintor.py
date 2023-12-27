"""There is VAG coordinator module."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class VagCoordinator(DataUpdateCoordinator):
    """Coordinator class for VAG Addon."""

    def __init__(self, hass: HomeAssistant, my_api) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="My sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=60),
        )
        self._api = my_api

        _LOGGER.debug("VAG Coordinator created")

    async def _async_update_data(self):
        _LOGGER.info("Fetching data")

        return await self._api.get_data()
