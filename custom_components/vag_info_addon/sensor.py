"""Github custom component."""
from datetime import datetime, timezone
import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONFIG_DIRECTION,
    CONFIG_LINE_NAME,
    CONFIG_PRODUCT_NAME,
    CONFIG_STOP_VGN_NUMBER,
    DOMAIN,
)
from .data.abfahrt import Abfahrt
from .vag_coordinator import VagCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up config entry."""
    _LOGGER.info(f"Start configuration sensor for entry ID:{entry.entry_id}")

    _LOGGER.debug("Old data:")
    _LOGGER.debug(hass.data[DOMAIN][entry.entry_id])

    api = hass.data[DOMAIN][entry.entry_id]["api"]
    data = hass.data[DOMAIN][entry.entry_id]["data"]

    if api:
        _LOGGER.debug("API is not None")

    if data:
        _LOGGER.debug(f"data is not None: {data}")

    coordinator = hass.data.setdefault(DOMAIN, {})[entry.entry_id] = VagCoordinator(
        hass,
        api,
        vgn_number=data[CONFIG_STOP_VGN_NUMBER],
        line=data[CONFIG_LINE_NAME],
        product=data[CONFIG_PRODUCT_NAME],
    )

    if not api:
        _LOGGER.error("No api object found")

    # await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            VagNextStopEntity(
                hass=hass, coordinator=coordinator, direction=data[CONFIG_DIRECTION]
            )
        ],
        # update_before_add=True,
    )


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading entry {entry}")


async def async_remove_entry(hass, entry) -> None:
    """Handle removal of an entry."""
    _LOGGER.info(f"Removing entry {entry}")


class VagNextStopEntity(CoordinatorEntity, SensorEntity):
    """Custom entity for VAG information."""

    def __init__(
        self, hass: HomeAssistant, coordinator: VagCoordinator, direction: str
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._coordinator = coordinator
        self._product = coordinator.vgn_product
        self._line = coordinator.line_name
        self._direction = direction

        self._attr_name = f"vag_{self._product}_{self._line}_{self._direction}"
        self._attr_unique_id = f"vag_{self._product}_{self._line}_{self._direction}"
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
        # _LOGGER.info(f"Filter direction: {self._direction}")

        abfahrten = list(
            filter(lambda x: x.direction == self._direction, self._coordinator.data)
        )

        # _LOGGER.debug(data)

        if not abfahrten:
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

        next_abfahrt: Abfahrt = abfahrten[0]

        # calculate value
        soll_time = datetime.fromisoformat(next_abfahrt.departure_must)
        ist_time = datetime.fromisoformat(next_abfahrt.departure_is)

        delay = ist_time - soll_time
        delta = ist_time - datetime.now(timezone.utc)

        (delta_days, delta_hours, delta_minutes) = self._days_hours_minutes(delta)

        # set extra attributes
        self._attr_extra_state_attributes = {
            "Linename": next_abfahrt.line_name,
            "Direction": next_abfahrt.direction,
            "Richtungstext": next_abfahrt.direction_text,
            "AbfahrtszeitSoll": next_abfahrt.departure_must,
            "AbfahrtszeitIst": next_abfahrt.departure_is,
            "Prognose": next_abfahrt.prognose,
            "Besetzgrad": next_abfahrt.occupancy_level,
            "last_update": datetime.now(),
            "Verzoegerung": delay.total_seconds(),
        }

        if delta_days > 0:
            self._value = f"in {delta_days} Tagen"

        if delta_hours > 0:
            self._value = f"in {delta_hours} Std"
        elif delta_minutes > 0:
            self._value = f"in {delta_minutes} Min"
        else:
            self._value = "Jetzt"

        self.async_write_ha_state()

    def _days_hours_minutes(self, td):
        return td.days, td.seconds // 3600, (td.seconds // 60) % 60
