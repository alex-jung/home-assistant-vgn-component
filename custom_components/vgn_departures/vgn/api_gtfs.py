"""API class to manage GTFS data."""

import asyncio
import logging
from pathlib import Path
import re
from typing import Final

import aiofiles
import aiofiles.os
import aiofiles.ospath
from aiopath import AsyncPath
import aioshutil
from async_lru import alru_cache
import polars as pl

from .data_classes import Connection, Departures, Stop
from .exceptions import GtfsFileNotFound
from .helpers import datestr_to_date, weekday_to_str

_LOGGER = logging.getLogger(__name__)

GTFS_LOCATION: Final = f"{Path(__file__).resolve().parent}/data/GTFS.zip"


class ApiGtfs:
    """API for GTFS data."""

    def __init__(self) -> None:
        """Initialize API."""
        self._agency: pl.DataFrame | None
        self._calendar: pl.DataFrame | None
        self._calendar_dates: pl.DataFrame | None
        self._routes: pl.DataFrame | None
        self._stops: pl.DataFrame | None
        self._stop_times: pl.DataFrame | None
        self._transfers: pl.DataFrame | None
        self._trips: pl.DataFrame | None

    async def load(self) -> None:
        """Extract GTFS zip file and load data contains in txt files."""
        _LOGGER.debug("Loading GTFS data files")

        path = AsyncPath(GTFS_LOCATION)

        if not await path.exists():
            raise GtfsFileNotFound(f'GTFS zip file path "{path}" does not exist')

        async with aiofiles.tempfile.TemporaryDirectory() as tmp_dir:
            await aioshutil.unpack_archive(str(path), tmp_dir, format="zip")

            for file in await aiofiles.os.listdir(tmp_dir):
                file_path = f"{tmp_dir}/{file}"

                _LOGGER.debug("Reading file %s", file_path)

                match file:
                    case "stops.txt":
                        self._stops = await self._read_df(file_path)
                    case "agency.txt":
                        self._agency = await self._read_df(file_path)
                    case "transfers.txt":
                        self._transfers = await self._read_df(file_path)
                    case "calendar.txt":
                        self._calendar = await self._read_df(file_path)
                    case "calendar_dates.txt":
                        self._calendar_dates = await self._read_df(file_path)
                    case "stop_times.txt":
                        self._stop_times = await self._read_df(file_path)
                    case "trips.txt":
                        self._trips = await self._read_df(file_path)
                    case "routes.txt":
                        self._routes = await self._read_df(file_path)
                    case _:
                        _LOGGER.warning("Ignore unknown file %s", file_path)

        _LOGGER.debug("GTFS data files loaded")

    @alru_cache
    async def stops(
        self, name: str | None = None, incl_parents: bool = False
    ) -> list[Stop]:
        """Return stops found in GTFS contain provided name(case insensitive)."""
        stops = self._stops.clone()

        _LOGGER.debug("Get stops for name: %s", name)

        df = None

        df_filters = []

        if not incl_parents:
            expr_parents = ~pl.col("location_type").str.contains("1")
            df_filters.append(expr_parents)

        if name:
            expr_name = pl.col("stop_name").str.contains(f"(?i){name}")
            df_filters.append(expr_name)

        df = stops.filter(*df_filters)

        groups = df.group_by(pl.col("stop_name"))

        stops = []

        for n, data in groups:
            stop = Stop(n[0], data["stop_id"].to_list())

            stops.append(stop)

        return sorted(stops, key=lambda x: x.name)

    @alru_cache
    async def connections(self, stop: Stop) -> list[Connection]:
        """Return connections for privided stop object."""
        connections = []

        for stop_id in stop.ids:
            connections += await self._connections(stop_id)

        return connections

    @alru_cache
    async def departures(self, connection: Connection, date: str) -> Departures:
        """Return all departiures for provided connection and date."""
        if not connection:
            raise ValueError("No connection instance provided")
        if not date or not re.fullmatch(r"\d{8}", date):
            raise ValueError("No date provided or invalid formate used")

        _LOGGER.debug(
            'Searching departures for connection "%s" on "%s"', connection.name, date
        )

        routes = self._routes.clone()
        stop_times: pl.DataFrame = self._stop_times.clone()
        trips: pl.DataFrame = self._trips.clone()

        s_active_trips = await self._active_trips(date)

        s_routes = routes.filter(
            pl.col("route_id").is_in(connection.route_ids)
        ).get_column("route_id")

        # get unique trips for requested connection
        s_trips = (
            trips.filter(
                (pl.col("route_id").is_in(s_routes))
                & (pl.col("trip_id").is_in(s_active_trips))
                & (pl.col("direction_id") == connection.direction_id)
                & (pl.col("trip_headsign") == connection.name)
            )
            .unique("trip_id")
            .get_column("trip_id")
        )

        times = (
            stop_times.filter(
                (pl.col("trip_id").is_in(s_trips))
                & (pl.col("stop_id") == connection.stop_id)
            )
            .get_column("departure_time")
            .sort()
        )

        return Departures(connection.stop_id, date, times.to_list())

    async def _active_trips(self, date: str) -> pl.Series:
        """Return all active trips for provided date."""
        trips: pl.DataFrame = self._trips.clone()
        calendar: pl.DataFrame = self._calendar.clone()
        calendar_dates: pl.DataFrame = self._calendar_dates.clone()

        df_exceptions = calendar_dates.filter(pl.col("date") == int(date))

        df_added = df_exceptions.filter(pl.col("exception_type") == 1).get_column(
            "service_id"
        )
        df_removed = df_exceptions.filter(pl.col("exception_type") == 2).get_column(
            "service_id"
        )

        weekday_str = weekday_to_str(datestr_to_date(date).weekday())

        exp_match = (
            (~pl.col("service_id").is_in(df_removed))
            & (pl.col("start_date") < int(date))
            & (pl.col("end_date") > int(date))
            & ((pl.col(weekday_str) == 1) | (pl.col("service_id").is_in(df_added)))
        )

        s_active_services = calendar.filter(exp_match).get_column("service_id")

        return trips.filter(pl.col("service_id").is_in(s_active_services)).get_column(
            "trip_id"
        )

    async def _connections(self, stop_id: str) -> list[Connection]:
        """Return all connections for provided stop_id."""
        routes = self._routes.clone()
        trips = self._trips.clone()
        stop_times = self._stop_times.clone()

        # find trip_ids
        trip_ids = (
            stop_times.filter(pl.col("stop_id") == stop_id).select("trip_id").unique()
        )

        df_trips = trips.filter(pl.col("trip_id").is_in(trip_ids))

        g_routes = routes.join(df_trips, on="route_id").group_by(
            ["trip_headsign", "direction_id"]
        )

        connections: list[Connection] = []

        for name, data in g_routes:
            c_name = name[0]
            c_direction = name[1]
            c_line_name = data.row(0, named=True)["route_short_name"]
            c_transport = data.row(0, named=True)["route_type"]
            c_routes = data.unique("route_id").get_column("route_id").to_list()

            connections.append(
                Connection(
                    stop_id, c_name, c_line_name, c_transport, c_direction, c_routes
                )
            )

        return connections

    async def _read_df(self, path) -> pl.DataFrame:
        """Load csv file asyncron."""
        return await asyncio.get_running_loop().run_in_executor(None, pl.read_csv, path)
