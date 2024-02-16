"""Service for VAG Rest API."""
import json
import logging

import requests

from ..const import (
    REST_API_ABFAHRTEN_TAG,
    REST_API_BUS_STOP_NAME_TAG,
    REST_API_BUS_STOPS_TAG,
    REST_API_CAR_NUMBER_TAG,
    REST_API_DEPARTURE_IS_TAG,
    REST_API_DEPARTURE_MUST_TAG,
    REST_API_DIRECTION_TAG,
    REST_API_DIRECTION_TEXT_TAG,
    REST_API_LINE_NAME_TAG,
    REST_API_OCCUPANCY_LEVEL_TAG,
    REST_API_OPERATION_DAY_TAG,
    REST_API_PRODUCT_TAG,
    REST_API_PROGNOSE_TAG,
    REST_API_STOP_POINT_TAG,
    REST_API_STOP_POINT_TEXT_TAG,
    REST_API_TRIP_ART_TAG,
    REST_API_TRIP_NUMBER_TAG,
    REST_API_VAG_NUMBER_TAG,
    REST_API_VGN_NUMBER_TAG,
    REST_API_VGN_PRODUCTS_TAG,
)
from ..data.abfahrt import Abfahrt
from ..data.haltestelle import Haltestelle

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20  # seconds

REST_API_URL_HALTESTELLEN = "https://start.vag.de/dm/api/haltestellen.json/vag"
REST_API_URL_ABFAHRTEN = "https://start.vag.de/dm/api/abfahrten.json/vgn"


class VagRestApi:
    """Rest API service."""

    def get_haltestellen(self, stop_name: str) -> list[Haltestelle]:
        """Return Haltestellen found for `stop_name`."""
        if not stop_name:
            raise ValueError("No stop_name provided")

        url = f"{REST_API_URL_HALTESTELLEN}?name={stop_name}"

        answer = self._run_request(url=url)

        if not answer or REST_API_BUS_STOPS_TAG not in answer:
            return []

        haltestellen = []

        for hs in answer[REST_API_BUS_STOPS_TAG]:
            vag_kennung = self._get_value_or_none(hs, REST_API_VAG_NUMBER_TAG)
            vgn_kennung = self._get_value_or_none(hs, REST_API_VGN_NUMBER_TAG)
            hs_name = self._get_value_or_none(hs, REST_API_BUS_STOP_NAME_TAG)
            hs_products = self._get_value_or_none(hs, REST_API_VGN_PRODUCTS_TAG)

            if vgn_kennung not in [x.vgn_number for x in haltestellen]:
                obj = Haltestelle(
                    name=hs_name,
                    vag_number=vag_kennung,
                    vgn_number=vgn_kennung,
                    products=hs_products,
                )

                haltestellen.append(obj)

        return haltestellen

    def get_abfahrten(
        self, vgn_number: str, line: str | None = None, product: str | None = None
    ):
        """Return Abfahrten found for defined bus stop with number `vgn_number`.

        Optionaly results can be reduced by providing additional arguments `line` and `product`
        """
        # _LOGGER.debug(f"Get Abfahrten: {line=}, {product=}")

        url = f"{REST_API_URL_ABFAHRTEN}/{vgn_number}/"

        if line:
            url += f"{line}/"

        if product:
            url += f"?product={product}"

        answer = self._run_request(url=url)

        if not answer or REST_API_ABFAHRTEN_TAG not in answer:
            return []

        abfahrten = []

        for abfahrt in answer[REST_API_ABFAHRTEN_TAG]:
            ab_line_name = self._get_value_or_none(abfahrt, REST_API_LINE_NAME_TAG)
            ab_stop_point = self._get_value_or_none(abfahrt, REST_API_STOP_POINT_TAG)
            ab_direction = self._get_value_or_none(abfahrt, REST_API_DIRECTION_TAG)
            ab_direction_text = self._get_value_or_none(
                abfahrt, REST_API_DIRECTION_TEXT_TAG
            )
            ab_departure_must = self._get_value_or_none(
                abfahrt, REST_API_DEPARTURE_MUST_TAG
            )
            ab_departure_is = self._get_value_or_none(
                abfahrt, REST_API_DEPARTURE_IS_TAG
            )
            ab_product = self._get_value_or_none(abfahrt, REST_API_PRODUCT_TAG)
            ab_trip_number = self._get_value_or_none(abfahrt, REST_API_TRIP_NUMBER_TAG)
            ab_operation_day = self._get_value_or_none(
                abfahrt, REST_API_OPERATION_DAY_TAG
            )
            ab_trip_art = self._get_value_or_none(abfahrt, REST_API_TRIP_ART_TAG)
            ab_car_number = self._get_value_or_none(abfahrt, REST_API_CAR_NUMBER_TAG)
            ab_occupancy_level = self._get_value_or_none(
                abfahrt, REST_API_OCCUPANCY_LEVEL_TAG
            )
            ab_prognose = self._get_value_or_none(abfahrt, REST_API_PROGNOSE_TAG)
            ab_stop_point_text = self._get_value_or_none(
                abfahrt, REST_API_STOP_POINT_TEXT_TAG
            )

            obj = Abfahrt(
                line_name=ab_line_name,
                stop_point=ab_stop_point,
                direction=ab_direction,
                direction_text=ab_direction_text,
                departure_must=ab_departure_must,
                departure_is=ab_departure_is,
                product=ab_product,
                trip_number=ab_trip_number,
                operation_day=ab_operation_day,
                trip_art=ab_trip_art,
                car_number=ab_car_number,
                occupancy_level=ab_occupancy_level,
                prognose=ab_prognose,
                stop_point_text=ab_stop_point_text,
            )

            abfahrten.append(obj)

        return abfahrten

    def _get_value_or_none(self, json_data, key):
        if not json_data:
            return None

        return json_data[key] if key in json_data else None

    def _run_request(self, url: str):
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.encoding = "utf-8"

        if not r.ok:
            raise BadRequestError(url)

        return json.loads(r.text)


class BadRequestError(Exception):
    """Exception by invalid response from VAG server."""
