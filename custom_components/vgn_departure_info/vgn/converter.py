from datetime import datetime

from dateutil.parser import parse

from .data_classes import Coordinates, Departure, Route, Station, Stop, TransportType


def _to_datetime(date_str: str):
    if date_str:
        return parse(date_str)

    return None


def _to_date(iso_8601_str: str):
    if iso_8601_str:
        return datetime.datetime.strptime(iso_8601_str, "%Y-%m-%d").date()

    return None


def _to_direction(direction: str) -> int:
    return 0 if direction == "Richtung1" else 1


def _to_transport_type(type_string: str) -> TransportType:
    if type_string == "Bus":
        return TransportType.BUS
    elif type_string == "Tram":
        return TransportType.TRAM
    elif type_string == "UBahn":
        return TransportType.SUBWAY
    else:
        raise TypeError(f"Unknown transport type {type_string}.")


def to_stops(returned_dict: dict) -> list[Station]:
    """ToDo."""

    return [
        Stop(
            x.get("VGNKennung"),
            x.get("Haltestellenname"),
            Coordinates(x.get("Latitude"), x.get("Longitude")),
        )
        for x in returned_dict
    ]


def to_stations(returned_dict: dict) -> list[Station]:
    """ToDo."""
    return [
        Station(
            x.get("Haltestellenname"),
            x.get("VGNKennung"),
            Coordinates(x.get("Latitude"), x.get("Longitude")),
        )
        for x in returned_dict
    ]


def to_departures(returned_dict: dict) -> list[Departure]:
    """ToDo."""

    return [
        Departure(
            x.get("Haltepunkt"),
            x.get("Linienname"),
            _to_direction(x.get("Richtung")),
            x.get("Richtungstext"),
            _to_transport_type(x.get("Produkt")),
            _to_datetime(x.get("AbfahrtszeitSoll")),
            _to_datetime(x.get("AbfahrtszeitIst")),
            Coordinates(x.get("Latitude"), x.get("Longitude")),
            x.get("Besetzgrad"),
            x.get("Fahrtnummer"),
            x.get("Fahrtartnummer"),
            x.get("Fahrzeugnummer"),
            x.get("Prognose"),
        )
        for x in returned_dict
    ]
