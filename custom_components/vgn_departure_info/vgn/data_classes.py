from dataclasses import dataclass, asdict
import datetime as dt
from enum import IntEnum
import json
from .helpers import datestr_to_date
from homeassistant.util import dt as dt_util
import zoneinfo


class TransportType(IntEnum):
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
    name: str
    ids: list[str]

    @property
    def is_parent(self):
        return any(x.startswith("Parent") for x in self.ids)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Stop):
            return False

        return self.name == value.name

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self) -> int:
        return hash(self.name)


class Connection:
    def __init__(
        self,
        stop_id: str,
        name: str,
        line_name: str,
        transport: int,
        direction_id: int,
        route_id_s: list[str],
    ) -> None:
        self.stop_id = stop_id
        self.name = name
        self.line_name = line_name
        self.transport = TransportType(transport)
        self.direction_id = direction_id
        self.route_ids = route_id_s
        self.uid = f"{stop_id}#{name}#{line_name}#{transport}#{direction_id}"

    def to_dict(self):
        return json.dumps(self, default=lambda obj: obj.__dict__)

    @classmethod
    def from_dict(cls, connection: str):
        if not connection:
            return None

        conn_dict = json.loads(connection)

        return Connection(
            conn_dict["stop_id"],
            conn_dict["name"],
            conn_dict["line_name"],
            conn_dict["transport"],
            conn_dict["direction_id"],
            conn_dict["route_ids"],
        )


class Departures:
    def __init__(self, stop_id: str, date: str, times: list[str]) -> None:
        self.stop_id = stop_id
        self.times = self._convert_to_datetimes(date, times)

    def _convert_to_datetimes(self, date: str, times: list[str]):
        # r_date = dt_util.parse_date(date)
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

    def to_dict(self):
        return {"stop_id": self.stop_id, "times": self.times}
