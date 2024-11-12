"""There is VGN coordinator module."""

import asyncio
from datetime import datetime, timedelta
from functools import partial
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONFIG_SENSORS_DATA,
    CONFIG_STATION_ID,
    FETCH_UPDATE_INTERVAL,
    REQUEST_TIME_SPAN,
)
from .vgn.data_classes import Connection, Departures
from .vgn.exceptions import VgnGetError
from .vgn.gtfs_client import ApiGtfs

_LOGGER = logging.getLogger(__name__)


class VgnUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator class for VGN custom component updates."""

    def __init__(self, hass: HomeAssistant, title: str, data) -> None:
        """Bla bla."""
        super().__init__(
            hass,
            _LOGGER,
            name=__name__,
            update_interval=timedelta(seconds=FETCH_UPDATE_INTERVAL),
        )

        self._title: str = title
        self._connections: list[Connection] = [
            Connection.from_dict(x) for x in data["connections"]
        ]
        self._api: ApiGtfs = None
        self.data: dict = {conn.uid: {} for conn in self._connections}

        # _LOGGER.debug("Coordinator connections: %s", data)

        # self._stop_id = entry.data[CONFIG_STATION_ID]
        # self._vgn_number = self._extract_vgn_number(self._stop_id)

        # _LOGGER.info("VGN update coordinator has been created:")
        # _LOGGER.info('Title:"%s"', self._title)
        # _LOGGER.info('VGN Number:"%s"', self._vgn_number)
        # _LOGGER.info('Sensors:"%s"', self._sensors)

    @property
    def title(self):
        """Return entry title."""
        return self._title

    @property
    def vgn_number(self):
        """Return VGN stop station internal number(needed for Rest-Api)."""
        return self._vgn_number

    @property
    def connections(self):
        """Return sensor data configurations belong to this coordinator."""
        return self._connections

    async def _async_setup(self) -> None:
        self._api = ApiGtfs()
        await self._api.load()

    async def _async_update_data(self):
        _LOGGER.debug("Start update data for entry '%s'", self.title)
        _LOGGER.debug(self.data)

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

    def _extract_vgn_number(self, id: str) -> str:
        id_splited = id.split(":")

        return id_splited[2] if len(id_splited) >= 3 else id
