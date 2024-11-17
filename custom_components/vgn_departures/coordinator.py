"""The VGN Departures update coordinator."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import CFG_CONNECTIONS, FETCH_UPDATE_INTERVAL
from .vgn.api_gtfs import ApiGtfs
from .vgn.data_classes import Connection, Departures
from .vgn.exceptions import GtfsFileNotFound

_LOGGER = logging.getLogger(__name__)


class VgnUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator class for VGN Departures component updates."""

    def __init__(self, hass: HomeAssistant, title: str, data) -> None:
        """Bla bla."""
        super().__init__(
            hass,
            _LOGGER,
            name=__name__,
            update_interval=timedelta(seconds=FETCH_UPDATE_INTERVAL),
        )

        _LOGGER.debug("Setup coordinator with connections: %s", data[CFG_CONNECTIONS])

        self._title: str = title
        self._connections: list[Connection] = [
            Connection.from_dict(x) for x in data[CFG_CONNECTIONS]
        ]
        self._api: ApiGtfs = ApiGtfs()
        self.data: dict[str, dict] = {conn.uid: {} for conn in self._connections}

    @property
    def title(self) -> str:
        """Return entry title."""
        return self._title

    @property
    def connections(self) -> list[Connection]:
        """Return connections udpated by this coordinator."""
        return self._connections

    async def _async_setup(self) -> dict[str, dict]:
        _LOGGER.debug("Setup coordinator '%s'", self.title)
        try:
            await self._api.load()
        except GtfsFileNotFound:
            _LOGGER.error("Failed loading GTFS files")
            raise

    async def _async_update_data(self):
        _LOGGER.debug("Start update data for '%s'", self.title)

        current_time = dt_util.now().replace(second=0, microsecond=0)

        for connection in self._connections:
            departures: Departures = await self._api.departures(
                connection, current_time.strftime("%Y%m%d")
            )

            self.data[connection.uid].update(
                {
                    "stop_id": departures.stop_id,
                    "times": list(
                        filter(lambda x: x >= current_time, departures.times)
                    ),
                }
            )

        _LOGGER.debug("Update data finished")

        return self.data
