"""Github custom component."""
from datetime import UTC, datetime
import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONFIG_DIRECTION, CONFIG_LINE_NAME, CONFIG_PRODUCT_NAME, DOMAIN
from .data.abfahrt import Abfahrt
from .vgn_coordinator import VgnCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up config entries."""
    coordinator: VgnCoordinator = hass.data[DOMAIN][entry.entry_id]

    new_entities = []

    for entry_data in coordinator.entries:
        new_entities.append(VgnNextStopEntity(hass, coordinator, entry_data))

    async_add_entities(new_entities)


class VgnNextStopEntity(CoordinatorEntity, SensorEntity):
    """Custom entity for VGN information."""

    def __init__(
        self, hass: HomeAssistant, coordinator: VgnCoordinator, data: dict
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._coordinator = coordinator
        self._direction = data[CONFIG_DIRECTION]
        self._product = data[CONFIG_PRODUCT_NAME]
        self._line = data[CONFIG_LINE_NAME]

        title = self._coordinator.title

        self._attr_name = f"vgn_{title}_{self._product}_{self._line}_{self._direction}"
        self._attr_unique_id = (
            f"vgn_{title}_{self._product}_{self._line}_{self._direction}"
        )
        self._attr_should_poll = False
        self._value = "..."

        _LOGGER.info("VGN Sensor entity created")

    @property
    def native_value(self):
        """Returns value of this sensor."""
        return self._value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        # _LOGGER.info(f"Updating VGN sensor: {self._product}-{self._direction}")
        # _LOGGER.info(f"From coordinator got {len(self._coordinator.data)} Abfahrten")

        abfahrten: list[Abfahrt] = list(
            filter(
                lambda x: x.direction == self._direction
                and x.line_name == self._line
                and x.product == self._product,
                self._coordinator.data,
            )
        )

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

        # _LOGGER.info(f"After filtering got {len(abfahrten)} Abfahrten")
        # _LOGGER.info(abfahrten)

        abfahrten = sorted(abfahrten, key=lambda x: x.departure_must)
        next_abfahrt: Abfahrt = abfahrten[0]

        # _LOGGER.info(f"Next Abfahrt: {next_abfahrt}")
        # _LOGGER.info("-" * 30)

        # calculate value
        soll_time = next_abfahrt.departure_must
        ist_time = next_abfahrt.departure_is

        delay = ist_time - soll_time
        delta = ist_time - datetime.now(UTC)

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
