import asyncio
from typing import final

import aiohttp
import logging

from .converter import to_departures, to_stops
from .data_classes import Departure, Stop, TransportType
from .exceptions import VgnGetError

VGN_REST_API_URL: final = "https://start.vag.de/dm/api/v1/"

_LOGGER = logging.getLogger(__name__)


class VGNRestClient:
    """ToDo."""

    async def __aenter__(self):
        self._client_session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args, **kwargs):
        await self._client_session.__aexit__(*args, **kwargs)

    @staticmethod
    def _url(path):
        return "https://start.vag.de/dm/api/v1/" + path

    async def _get(self, query) -> dict:
        async with self._client_session.get(query) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                raise VgnGetError(
                    f"Could not resolve query {query}. Returned {resp.status}"
                )

    async def api_version(self) -> str:
        """Version info from the VGN REST-API."""
        query = self._url("haltestellen/VGN/location?lon=0&lat=0")
        return (await self._get(query)).get("Metadata").get("Version")

    @staticmethod
    def _url(path):
        return VGN_REST_API_URL + path

    async def api_version(self) -> str:
        """Version info from the VGN REST-API."""
        query = self._url("haltestellen/VGN/location?lon=0&lat=0")
        return (await self._get(query)).get("Metadata").get("Version")

    async def stops(self, station_name: str) -> list[Stop]:
        """List of stations for the specified station name.

        Args:
            station_name: Name of a station.

        Returns:
            list: List of station objects for the given stop_name.

        """
        query = (
            self._url(f"haltestellen/VGN?name={station_name}")
            if station_name
            else self._url("haltestellen/VGN")
        )
        return to_stops((await self._get(query)).get("Haltestellen"))

    async def departure_schedule(
        self,
        stop_id: int,
        transport_type: list[TransportType] = [
            TransportType.BUS,
            TransportType.SUBWAY,
            TransportType.RAIL,
        ],
        timespan: int = 10,
        timedelay: int = 5,
        limit_result: int = 100,
    ) -> list[Departure]:
        """Departures for a specific stop.

        Args:
            stop_id: The VGN stop identifier number.
            transport_type: Information shall only be given for the defined transport means of transportation.
            limit_result (optional): Limit amount of returned results. Default limit is 100.
            timedelay (optional): Time delay for the request in minutes.
            timespan (optional): Time window for the query in minutes.

        Returns:
            list: List of departures for the given station.

        """
        if limit_result <= 0:
            limit_result = 100
        transport_type_str = ",".join([x.value for x in transport_type])
        query = self._url(
            f"abfahrten/VGN/{stop_id}"
            f"?product={transport_type_str}"
            f"&timespan={timespan}"
            f"&timedelay={timedelay}"
            f"&limitcount={limit_result}"
        )
        return to_departures((await self._get(query)).get("Abfahrten"))
