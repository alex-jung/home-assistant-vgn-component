"""Module represents trip Classes."""
from dataclasses import dataclass


@dataclass
class Abfahrt:
    """Represents a trip."""

    line_name: str = ""
    stop_point: str = ""
    stop_point_text: str = ""
    direction: str = ""
    direction_text: str = ""
    departure_must: str = ""
    departure_is: str = ""
    product: str = ""
    trip_number: str = ""
    operation_day: str = ""
    trip_art: str = ""
    car_number: str = ""
    occupancy_level: str = ""
    prognose: str = ""

    def __str__(self) -> str:  # noqa: D105
        return f"{self.line_name} - {self.direction}"
