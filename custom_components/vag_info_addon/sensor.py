"""Github custom component."""
from datetime import datetime, timezone
import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DIRECTION, CONF_LINE_NAME, CONF_PRODUCT, DOMAIN
from .vag_coordintor import VagCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up config entry."""
    _LOGGER.debug(f"Start configuration sensor for entry {entry}")

    api = hass.data[DOMAIN][entry.entry_id]["api"]
    config = hass.data[DOMAIN][entry.entry_id]["config"]
    coordinator = VagCoordinator(hass, api)

    vag_product = config[CONF_PRODUCT]
    vag_line = config[CONF_LINE_NAME]
    vag_direction = config[CONF_DIRECTION]

    if not api:
        _LOGGER.error("No api object found")

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            VagNextStopEntity(
                hass=hass,
                coordinator=coordinator,
                vag_product=vag_product,
                vag_line=vag_line,
                vag_direction=vag_direction,
            )
        ],
        update_before_add=True,
    )


class VagNextStopEntity(CoordinatorEntity, SensorEntity):
    """Custom entity for VAG information."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: VagCoordinator,
        vag_product: str,
        vag_line: str,
        vag_direction: str,
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._coordinator = coordinator
        self._product = vag_product
        self._line = vag_line
        self._direction = vag_direction

        self._attr_name = f"vag_{vag_product}_{vag_line}_{vag_direction}"
        self._attr_unique_id = f"vag_{vag_product}_{vag_line}_{vag_direction}"
        self._attr_should_poll = False
        self._value = "Loading"

        _LOGGER.info("VAG Sensor entity created")

    @property
    def native_value(self):
        """Returns value of this sensor."""
        return self._value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Sensor update called")

        # select correct data

        # _LOGGER.info(f"Filter line: {self._line}")
        # _LOGGER.info(f"Filter richtung: {self._direction}")
        # _LOGGER.info(f"Filter product: {self._product}")

        data = list(
            filter(
                lambda x: (
                    x["Linienname"] == self._line
                    and x["Richtung"] == self._direction
                    and x["Produkt"] == self._product
                ),
                self._coordinator.data,
            )
        )

        # _LOGGER.debug(data)

        if not data:
            self._value = "-"

            self._attr_extra_state_attributes = {
                "Linename": "-",
                "Direction": "-",
                "Richtungstext": "-",
                "AbfahrtszeitSoll": "-",
                "AbfahrtszeitIst": "-",
                "Prognose": "-",
                "Besetzgrad": "-",
                "last_update": datetime.now(),
                "Verzoegerung": "-",
            }
            self.async_write_ha_state()
            return

        data_value = None

        if isinstance(data, list | tuple):
            data_value = data[0]
        else:
            data_value = data

        # calculate value
        soll_time = datetime.fromisoformat(data_value["AbfahrtszeitSoll"])
        ist_time = datetime.fromisoformat(data_value["AbfahrtszeitIst"])

        delay = ist_time - soll_time
        delta = ist_time - datetime.now(timezone.utc)

        (delta_days, delta_hours, delta_minutes) = self._days_hours_minutes(delta)

        # set extra attributes
        self._attr_extra_state_attributes = {
            "Linename": data_value["Linienname"],
            "Direction": data_value["Richtung"],
            "Richtungstext": data_value["Richtungstext"],
            "AbfahrtszeitSoll": data_value["AbfahrtszeitSoll"],
            "AbfahrtszeitIst": data_value["AbfahrtszeitIst"],
            "Prognose": data_value["Prognose"],
            "Besetzgrad": data_value["Besetzgrad"],
            "last_update": datetime.now(),
            "Verzoegerung": delay.total_seconds(),
        }

        # _LOGGER.debug(f"{delta_days=}")
        # _LOGGER.debug(f"{delta_hours=}")
        # _LOGGER.debug(f"{delta_minutes=}")

        if delta_days > 0:
            self._value = f"in {delta_days} Tagen"

        if delta_hours > 0:
            self._value = f"in {delta_hours} Std"
        elif delta_minutes > 0:
            self._value = f"in {delta_minutes} Min"
        else:
            self._value = "Jetzt"

        self._value = "{:<20}".format(self._value)

        self.async_write_ha_state()

    def _days_hours_minutes(self, td):
        return td.days, td.seconds // 3600, (td.seconds // 60) % 60
