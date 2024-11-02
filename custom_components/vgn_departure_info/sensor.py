"""Github custom component."""

import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    DOMAIN,
    MAX_DEPARTURES,
    ATTR_DIRECTION,
    ATTR_STOP_ID,
    ATTR_DEPARTURES,
    ATTR_DIRECTION_TEXT,
    ATTR_LINE_NAME,
    ATTR_TRANSPORT_TYPE,
)
from .vgn.data_classes import Departure, SensorData, TransportType
from .vgn_update_coordinator import VgnUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up config entries."""
    coordinator: VgnUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            VgnSensorEntity(hass, coordinator, entry_data)
            for entry_data in coordinator.sensors
        ],
        update_before_add=True,
    )


class VgnSensorEntity(CoordinatorEntity, SensorEntity):
    """Custom entity for VGN information."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: VgnUpdateCoordinator,
        data: SensorData,
    ) -> None:
        """ToDo."""
        super().__init__(coordinator)

        _LOGGER.debug("Create VGN sensor with data: %s", data)

        self._hass = hass
        self._coordinator = coordinator
        self._line = data["line_name"]
        self._direction = data["direction"]
        self._stop_id = data["stop_id"]
        self._transport = TransportType(data["transport"])
        self._direction_text = data["direction_text"]
        self._value = "unknown"

        self._attr_name = f"{coordinator.title} - {self._transport.value} {self._line} - {self._direction_text}"
        self._attr_unique_id = slugify(
            f"{self._coordinator.title}_{self._transport.value}_{self._line}_{self._direction_text}_{self._direction}"
        )
        self._attr_should_poll = False

        self._attr_extra_state_attributes = {
            ATTR_LINE_NAME: self._line,
            ATTR_STOP_ID: self._stop_id,
            ATTR_TRANSPORT_TYPE: self._transport.value,
            ATTR_DIRECTION: self._direction,
            ATTR_DIRECTION_TEXT: self._direction_text,
        }

        _LOGGER.info("VGN sensor entity created - Unique id: %s", self._attr_unique_id)
        _LOGGER.debug("line: %s", self._line)
        _LOGGER.debug("direction: %s", self._direction)
        _LOGGER.debug("station_id: %s", self._stop_id)
        _LOGGER.debug("transport: %s", self._transport)
        _LOGGER.debug("direction_text: %s", self._direction_text)
        _LOGGER.debug("value: %s", self._value)

    @property
    def native_value(self):
        """Returns value of this sensor."""
        return self._value

    @property
    def icon(self) -> str | None:
        """Icon of the entity, based on transport type."""
        match self._transport:
            case TransportType.BUS:
                return "mdi:bus"
            case TransportType.TRAM:
                return "mdi:tram"
            case TransportType.SUBWAY:
                return "mdi:subway"
            case _:
                return "mdi:eye"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        _LOGGER.info("Updating VGN sensor: %s", self._attr_name)
        _LOGGER.debug("self._direction: %s", self._direction)
        _LOGGER.debug("self._direction_text: %s", self._direction_text)
        _LOGGER.debug("self._line: %s", self._line)
        _LOGGER.debug("self._transport: %s", self._transport)

        _LOGGER.info(
            "From coordinator got %s departures",
            len(self._coordinator.data) if self._coordinator.data else 0,
        )

        departures: list[Departure] = self._coordinator.data

        if not departures:
            _LOGGER.debug("No data available from coordinator")
            return

        my_departures = list(
            filter(
                lambda x: x.direction == self._direction and x.line_name == self._line,
                departures,
            )
        )

        _LOGGER.debug("My departures:")
        for departure in my_departures:
            _LOGGER.debug(departure)

        if not my_departures:
            _LOGGER.warning("No departures received")

            self._value = None
            self.async_write_ha_state()

            return

        next_departure = my_departures[0]

        _LOGGER.debug("Next departure:")
        _LOGGER.debug(next_departure)

        self._value = next_departure.actual_departure_time.replace(second=0)

        self._attr_extra_state_attributes["departures"] = [
            x.actual_departure_time.replace(second=0)
            for x in departures[:MAX_DEPARTURES]
        ]

        self.async_write_ha_state()
