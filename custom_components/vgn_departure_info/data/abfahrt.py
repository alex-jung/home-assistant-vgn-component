"""Module represents trip Classes."""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Abfahrt:
    """Represents a trip."""

    line_name: str = ""
    stop_point: str = ""
    stop_point_text: str = ""
    direction: str = ""
    direction_text: str = ""
    departure_must: datetime | None = None
    departure_is: datetime | None = None
    product: str = ""
    trip_number: str = ""
    operation_day: str = ""
    trip_art: str = ""
    car_number: str = ""
    occupancy_level: str = ""
    prognose: str = ""

    def __str__(self) -> str:  # noqa: D105
        return f"{self.line_name} - {self.direction}"

    def __hash__(self) -> int:
        return hash(f"{self.line_name}_{self.direction}_{self.product}")

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Abfahrt):
            return False

        return (
            self.line_name == __value.line_name
            and self.direction == __value.direction
            and self.product == __value.product
        )
