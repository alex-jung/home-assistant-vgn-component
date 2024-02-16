"""Github custom component."""
from datetime import UTC, datetime
import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONFIG_DIRECTION, DOMAIN
from .data.abfahrt import Abfahrt
from .vag_coordinator import VagCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            VagNextStopEntity(
                hass=hass,
                coordinator=coordinator,
                direction=entry.data[DOMAIN][CONFIG_DIRECTION],
            )
        ],
    )


class VagNextStopEntity(CoordinatorEntity, SensorEntity):
    """Custom entity for VAG information."""

    def __init__(
        self, hass: HomeAssistant, coordinator: VagCoordinator, direction: str
    ) -> None:
        super().__init__(coordinator)
        self._hass = hass
        self._coordinator = coordinator
        self._direction = direction

        product = coordinator.vgn_product
        line = coordinator.line_name
        vgn_number = self._coordinator.vgn_number

        self._attr_name = f"vag_{vgn_number}_{product}_{line}_{self._direction}"
        self._attr_unique_id = f"vag_{vgn_number}_{product}_{line}_{self._direction}"
        self._attr_should_poll = False
        self._value = "Laden..."

        _LOGGER.info("VAG Sensor entity created")

    @property
    def native_value(self):
        """Returns value of this sensor."""
        return self._value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        abfahrten = list(
            filter(lambda x: x.direction == self._direction, self._coordinator.data)
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

        next_abfahrt: Abfahrt = abfahrten[0]

        # calculate value
        soll_time = datetime.fromisoformat(next_abfahrt.departure_must)
        ist_time = datetime.fromisoformat(next_abfahrt.departure_is)

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
