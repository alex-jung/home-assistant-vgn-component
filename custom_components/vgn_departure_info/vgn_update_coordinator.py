"""There is VGN coordinator module."""

import asyncio
from datetime import datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONFIG_SENSORS_DATA,
    CONFIG_STATION_ID,
    FETCH_UPDATE_INTERVAL,
    REQUEST_TIME_SPAN,
)
from .vgn.exceptions import VgnGetError
from .vgn.gtfs_client import VGNGtfsClient
from .vgn.rest_client import VGNRestClient

_LOGGER = logging.getLogger(__name__)


class VgnUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator class for VGN custom component updates."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Bla bla."""
        super().__init__(
            hass,
            _LOGGER,
            name=__name__,
            update_interval=timedelta(seconds=FETCH_UPDATE_INTERVAL),
        )

        self._title: str = entry.title
        self._stop_id = entry.data[CONFIG_STATION_ID]
        self._vgn_number = self._extract_vgn_number(self._stop_id)
        self._sensors: list[dict] = entry.data[CONFIG_SENSORS_DATA]
        self._rest_api: bool = False
        self._gtfs_api: VGNGtfsClient = None

        _LOGGER.info("VGN update coordinator has been created:")
        _LOGGER.info('Title:"%s"', self._title)
        _LOGGER.info('VGN Number:"%s"', self._vgn_number)
        _LOGGER.info('Sensors:"%s"', self._sensors)

    @property
    def title(self):
        """Return entry title."""
        return self._title

    @property
    def vgn_number(self):
        """Return VGN stop station internal number(needed for Rest-Api)."""
        return self._vgn_number

    @property
    def sensors(self):
        """Return sensor data configurations belong to this coordinator."""
        return self._sensors

    async def _async_setup(self) -> None:
        self._gtfs_api = await self.hass.async_add_executor_job(VGNGtfsClient.instance)

    async def _async_update_data(self):
        if self._rest_api:
            _LOGGER.debug("Request departures via Rest-API for '%s'", self.title)

            async with VGNRestClient() as vgn_client:
                try:
                    res = await asyncio.create_task(
                        vgn_client.departure_schedule(
                            self.vgn_number, timespan=REQUEST_TIME_SPAN, timedelay=0
                        )
                    )
                except VgnGetError:
                    _LOGGER.warning(
                        "Rest-API query failed -> set flag rest_api to False"
                    )
                    self._rest_api = False
                else:
                    return res
        else:
            _LOGGER.debug(
                "REST-API is not supported for VGN Number %s", self.vgn_number
            )

        _LOGGER.debug("Request departures via Gtfs for '%s'", self.title)

        timepoint = datetime.today().strftime("%Y%m%d")
        time_box = 60
        stop_id = [x["stop_id"] for x in self.sensors]

        _LOGGER.debug("Request data:")
        _LOGGER.debug("timepoint: %s", timepoint)
        _LOGGER.debug("time_box: %s", time_box)
        _LOGGER.debug("stop_id: %s", stop_id)

        return await self.hass.async_add_executor_job(
            self._gtfs_api.departures, timepoint, time_box, stop_id
        )
        return await self._gtfs_api.departures(timepoint, time_box, stop_id)

        return await asyncio.create_task(
            self._gtfs_api.departures(
                datetime.today().strftime("%Y%m%d"),
                time_box=60,
                stop_id=[x["stop_id"] for x in self.sensors],
            )
        )

    def _extract_vgn_number(self, id: str) -> str:
        id_splited = id.split(":")

        return id_splited[2] if len(id_splited) >= 3 else id
