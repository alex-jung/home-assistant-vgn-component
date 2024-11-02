from dataclasses import dataclass
import datetime
from enum import StrEnum

from aenum import MultiValueEnum


class TransportType(MultiValueEnum):
    TRAM = "Tram", 0
    SUBWAY = "UBahn", 1
    RAIL = "Zug", 2
    BUS = "Bus", 3
    FERRY = "Fähre", 4
    CABLE_TRAM = "Kabelstraßenbahn", 5
    AERIAL_LIFT = "Luftseilbahn", 6
    FUNICULAR = "Standseilbahn", 7
    TROLLEYBUS = "Oberleitungsbus", 8
    MONORAIL = "Einschienenbahn", 9

    @property
    def index(self):
        return self.values[1]

    @classmethod
    def from_text(cls, value: str):
        match value:
            case "Tram":
                return TransportType.TRAM
            case "UBahn" | "U-Bahn":
                return TransportType.SUBWAY
            case "Zug":
                return TransportType.RAIL
            case "Bus":
                return TransportType.BUS
            case "Fähre":
                return TransportType.FERRY
            case "Kabelstraßenbahn":
                return TransportType.CABLE_TRAM
            case "Luftseilbahn":
                return TransportType.AERAL_LIFT
            case "Standseilbahn":
                return TransportType.FUNICULAR
            case "Oberleitungsbus":
                return TransportType.TROLLEYBUS
            case "Einschienenbahn":
                return TransportType.MONORAIL


class OccupancyLevel(StrEnum):
    UNKNOWN = "Unbekannt"
    WEAKLY = "Schwachbesetzt"
    HEAVILY = "Starkbesetzt"
    CROWDED = "Ueberfuellt"


class Route:
    def __init__(
        self, id: str, short_name: str, long_name: str, transport_type: int
    ) -> None:
        if not id:
            raise ValueError("Route id can not be empty")

        self._id = id.strip()
        self._short_name = short_name
        self._long_name = long_name.replace("  ", " ")
        self._transport_type = TransportType(transport_type)

    @property
    def id(self):
        return self._id

    @property
    def short_name(self):
        return self._short_name

    @property
    def long_name(self):
        return self._long_name

    @property
    def night_line(self):
        return self._id.startswith("16")

    @property
    def transport_type(self) -> TransportType:
        return self._transport_type

    def __hash__(self) -> int:
        return hash(self._id)

    def __str__(self) -> str:
        return f"{self.id}: {self.transport_type.name} [{self.short_name}] - {self.long_name}"


@dataclass
class Trip:
    id: str
    route: Route
    departure_time: str
    service_id: str
    head_sign: str
    direction: int
    block_id: int = -1


@dataclass()
class Coordinates:
    """Coordinates in WGS 84 Format in degrees."""

    latitude: float
    longitude: float


@dataclass()
class Station:
    """Station data object class."""

    name: str
    station_id: int
    coordinates: Coordinates
    transport_types: list[TransportType]


class Departure:
    """Departure data object class."""

    def __init__(
        self,
        station_id: str,
        line_name: str,
        direction: int,
        direction_text: str,
        transport_type: TransportType,
        planned_departure_time: datetime.datetime,
        actual_departure_time: datetime.datetime,
        coordinates: Coordinates | None = None,
        occupancy_level: OccupancyLevel = OccupancyLevel.UNKNOWN,
        ride_id: int = -1,
        ride_type_id: int = -1,
        vehicle_number: str | None = None,
        forecast: bool = False,
    ) -> None:
        self.station_id = station_id
        self.line_name = line_name
        self.direction = direction
        self.direction_text = direction_text
        self.transport_type = transport_type
        self.planned_departure_time = planned_departure_time
        self.actual_departure_time = actual_departure_time
        self.coordinates = coordinates
        self.occupancy_level = occupancy_level
        self.ride_id = ride_id
        self.ride_type_id = ride_type_id
        self.vehicle_number = vehicle_number
        self.forecast = forecast

    def __str__(self) -> str:
        return f'[{self.station_id}]-{self.transport_type.value} {self.line_name}[{self.direction}]-"{self.direction_text}"-{self.planned_departure_time}'


@dataclass()
class Ride:
    """Ride data object class."""

    ride_id: int
    line_name: str
    direction: str
    operating_day: datetime.date
    start_time: datetime.datetime
    end_time: datetime.datetime
    start_station_id: str
    end_station_id: str
    vehicle_number: str


@dataclass()
class RoutePoint:
    """Single stop of a route."""

    station_name: str
    station_id: int
    stop_point: str
    planned_arrival_time: datetime.datetime
    actual_arrival_time: datetime.datetime
    planned_departure_time: datetime.datetime
    actual_departure_time: datetime.datetime
    direction_text: str
    coordinates: Coordinates
    transit: bool
    no_boarding: bool
    no_get_off: bool
    additional_stop: bool


@dataclass
class SensorData:
    station_name: str
    stop_id: str
    transport: int
    line_name: str
    direction_text: str
    direction: int


class Stop:
    def __init__(self, id: str, name: str) -> None:
        self._id = id
        self._name = name

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def vgn_number(self) -> str | None:
        id_splited = self.id.split(":")

        if len(id_splited) == 1:
            return self._id
        elif len(id_splited) >= 3:
            return id_splited[2]

        return None

    def __str__(self) -> str:
        return f'Stop(id={self.id},name="{self.name}",coordinates={self.coordinates},loc_type={self.loc_type},parent={self.parent})'
