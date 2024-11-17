"""Helper classes for the VGN Departures component."""

from dataclasses import dataclass
import datetime as dt
from enum import IntEnum
import zoneinfo

from homeassistant.util import slugify

from .helpers import datestr_to_date


class TransportType(IntEnum):
    """Transport types."""

    TRAM = 0
    SUBWAY = 1
    RAIL = 2
    BUS = 3
    FERRY = 4
    CABLE_TRAM = 5
    AERIAL_LIFT = 6
    FUNICULAR = 7
    TROLLEYBUS = 8
    MONORAIL = 9

    def __str__(self) -> str:
        """Convert enum value to string."""
        match self.value:
            case TransportType.TRAM:
                return "Straßenbahn"
            case TransportType.SUBWAY:
                return "U-Bahn"
            case TransportType.RAIL:
                return "Zug"
            case TransportType.BUS:
                return "Bus"
            case TransportType.FERRY:
                return "Fähre"
            case TransportType.CABLE_TRAM:
                return "Seilbahn"
            case TransportType.AERIAL_LIFT:
                return "Luftseilbahn"
            case TransportType.FUNICULAR:
                return "Funikulär"
            case TransportType.TROLLEYBUS:
                return "Oberleitungsbus"
            case TransportType.MONORAIL:
                return "Einschienenbahn"
            case _:
                return "Unknown"


@dataclass
class Stop:
    """Object represents a bus stop(Haltestelle)."""

    name: str
    ids: list[str]

    @property
    def is_parent(self):
        """Return whether the stop is a parent stop or not."""
        return any(x.startswith("Parent") for x in self.ids)

    def to_dict(self):
        """Convert stop object to a dictionary."""
        return {"name": self.name, "ids": self.ids, "is_parent": self.is_parent}

    @classmethod
    def from_dict(cls, stop: dict):
        """Create a stop object from a dictionary."""
        if not stop:
            return None

        return Stop(stop["name"], stop["ids"])

    def __eq__(self, value: object) -> bool:
        """Overwritten to compare two objects."""
        if not isinstance(value, Stop):
            return False

        return self.name == value.name

    def __lt__(self, other):
        """Overwritten to compare two objects(needed for sorting)."""
        return self.name < other.name

    def __hash__(self) -> int:
        """Return hash value for this object."""
        return hash(self.name)


class Connection:
    """Class connection contains information about a specific drive trip."""

    def __init__(
        self,
        stop_id: str,
        name: str,
        line_name: str,
        transport: TransportType,
        direction_id: int,
        route_id_s: list[str],
    ) -> None:
        """Create a Connection object."""
        self.stop_id = stop_id
        self.name = name
        self.line_name = line_name
        self.transport = TransportType(transport)
        self.direction_id = direction_id
        self.route_ids = route_id_s
        self.uid = slugify(f"{stop_id}#{name}#{line_name}#{transport}#{direction_id}")

    def to_dict(self):
        """Convert connection object to a dictionary."""
        return {
            "stop_id": self.stop_id,
            "name": self.name,
            "line_name": self.line_name,
            "transport": self.transport.value,
            "direction_id": self.direction_id,
            "route_ids": self.route_ids,
            "uid": self.uid,
        }

    @classmethod
    def from_dict(cls, connection: dict):
        """Create a connection object from a dictionary."""
        if not connection:
            return None

        return Connection(
            connection["stop_id"],
            connection["name"],
            connection["line_name"],
            connection["transport"],
            connection["direction_id"],
            connection["route_ids"],
        )

    def __eq__(self, value: object) -> bool:
        """Overwritten to compare two objects."""
        if not isinstance(value, Connection):
            return False

        return self.uid == value.uid

    def __hash__(self) -> int:
        """Return hash value for this object."""
        return hash(self.uid)

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.stop_id}:{self.name}-{self.line_name}-{self.transport}-{self.direction_id}"


class Departures:
    """Contains departure times for a specific connection."""

    def __init__(self, stop_id: str, date: str, times: list[str]) -> None:
        """Create a Departure object."""
        self.stop_id = stop_id
        self.times = self._convert_to_datetimes(date, times)

    def _convert_to_datetimes(self, date: str, times: list[str]) -> list[dt.datetime]:
        r_date = datestr_to_date(date)

        r_times = []

        for time in times:
            (hour, minute, _) = (int(x) for x in time.split(":"))

            if hour >= 24:
                r_date = r_date + dt.timedelta(days=1)

            r_times.append(
                dt.datetime(
                    year=r_date.year,
                    month=r_date.month,
                    day=r_date.day,
                    hour=hour % 24,
                    minute=minute,
                    tzinfo=zoneinfo.ZoneInfo("Europe/Berlin"),
                )
            )

        return r_times

    def to_dict(self) -> dict[str, str | list[str]]:
        """Convert departures object to a dictionary."""
        return {"stop_id": self.stop_id, "times": self.times}
