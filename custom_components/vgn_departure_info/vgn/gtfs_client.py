from datetime import datetime, timedelta
import logging
from pathlib import Path

import gtfs_kit as gk

from homeassistant.util import dt as dt_util

# from homeassistant.util import dt
from .data_classes import Departure, TransportType

_LOGGER = logging.getLogger(__name__)

import tzlocal


class VGNGtfsClient:
    """ToDo."""

    _instance = None
    _initialized = False
    _feed = None
    _df_stops = None
    _df_routes = None
    _df_stop_times = None
    _df_trips = None

    @classmethod
    def instance(cls):
        """ToDo."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._load_gtfs()

        return cls._instance

    @classmethod
    def _load_gtfs(cls):
        data_path = Path(f"{Path(__file__).resolve().parent}/data/GTFS.zip")

        if not data_path.exists():
            raise RuntimeError(f'GTFS zip file "{data_path}" not found')

        cls._feed = gk.read_feed(data_path, dist_units="km")

        _LOGGER.debug("Start loading GTFS data")

        cls._df_stops = cls._feed.get_stops()
        cls._df_routes = cls._feed.get_routes()
        cls._df_stop_times = cls._feed.get_stop_times()
        cls._df_trips = cls._feed.get_trips()

        _LOGGER.debug("GTFS data loaded")

        VGNGtfsClient._initialized = True

    def stops(
        self, name: str, incl_parents: bool = False, case_sensitive: bool = False
    ):
        if not VGNGtfsClient._initialized:
            raise RuntimeError("VgnGtfsClient is not initialized")

        if not name:
            raise ValueError("No stop name provided")

        df = VGNGtfsClient._feed.get_stops().copy()

        if not incl_parents:
            df = df[df["location_type"].isna()]

        return df[df["stop_name"].str.contains(name, case=case_sensitive)]

    def trips(self, date: str | None = None, time: str | None = None):
        if not VGNGtfsClient._initialized:
            raise RuntimeError("VgnGtfsClient is not initialized")

        return VGNGtfsClient._feed.get_trips(date=date, time=time).copy()

    def stop_times(self, stop_id: list[str] | None = None):
        if not VGNGtfsClient._initialized:
            raise RuntimeError("VgnGtfsClient is not initialized")

        df = VGNGtfsClient._feed.get_stop_times().copy()

        if not stop_id:
            return df

        return df[df["stop_id"].isin(stop_id)]

    def routes(
        self,
        date: str | None = None,
        time: str | None = None,
        transport_type: list[TransportType] | None = None,
    ):
        if not VGNGtfsClient._initialized:
            raise RuntimeError("VgnGtfsClient is not initialized")

        df = VGNGtfsClient._feed.get_routes(date=date, time=time).copy()

        if transport_type:
            values = [x.index for x in transport_type]
            df = df[df["route_type"].isin(values)]

        return df

    def departures(self, date: str, time_box: int, stop_id: list[str]):
        if not VGNGtfsClient._initialized:
            raise RuntimeError("VgnGtfsClient is not initialized")

        df_times = VGNGtfsClient._feed.get_stop_times(date)[
            ["trip_id", "departure_time", "stop_id"]
        ]
        df_trips = self._feed.get_trips(date).copy()

        time_min = dt_util.now().replace(tzinfo=None)
        time_max = time_min + timedelta(minutes=time_box)

        def convert_to_datetime(time):
            today = datetime.now()
            year = today.year
            month = today.month
            day = today.day

            result = None
            timedelta = None

            try:
                hours, mins, secs = (int(x) for x in time.split(":"))
                if hours >= 24:
                    hours %= 24
                    timedelta = timedelta(days=1)

                result = datetime(
                    year=year,
                    month=month,
                    day=day,
                    hour=hours,
                    minute=mins,
                    second=secs,
                )

                if timedelta:
                    result += timedelta
            except Exception:
                result = None
            return result

        trips_with_time = df_trips.merge(df_times, on="trip_id", how="left")

        if stop_id:
            trips_with_time = trips_with_time[trips_with_time["stop_id"].isin(stop_id)]

        trips_with_time["departure_time"] = trips_with_time["departure_time"].apply(
            convert_to_datetime
        )
        trips_with_time["departure_time"] = trips_with_time["departure_time"].astype(
            "datetime64[ns]"
        )

        if time_box:
            _LOGGER.debug("Time now: %s", dt_util.now())
            _LOGGER.debug("Time box: %s - %s", time_min, time_max)

            trips_with_time = trips_with_time[
                (trips_with_time["departure_time"] >= time_min)
                & (trips_with_time["departure_time"] <= time_max)
            ]

        # add route information
        routes = VGNGtfsClient._df_routes.copy()
        routes = routes[["route_id", "route_short_name", "route_type"]]

        trips_with_time = trips_with_time.merge(routes, on="route_id", how="left")

        return [
            Departure(
                x.stop_id,
                x.route_short_name,
                x.direction_id,
                x.trip_headsign,
                TransportType(x.route_type),
                x.departure_time,
                x.departure_time,
            )
            for x in trips_with_time.itertuples()
        ]
