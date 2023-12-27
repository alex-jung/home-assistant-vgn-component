import json
import logging

import requests

from config.custom_components.vag_info_addon.const import VGN_SERVICE_URL
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class VagRestApi:
    def __init__(self, hass: HomeAssistant, stop_number: str) -> None:
        self._hass = hass
        self._url = f"{VGN_SERVICE_URL}/{stop_number}/"

        _LOGGER.debug("VagRestApi initialized")

    async def get_data(self):
        _LOGGER.debug(f"Api get_data() called")

        return await self._hass.async_add_executor_job(self._load)

    def _load(self):
        _LOGGER.info(f"Url = {self._url}")

        r = requests.get(self._url, timeout=60)
        r.encoding = "utf-8"

        data = json.loads(r.text)["Abfahrten"]

        return list(data)
