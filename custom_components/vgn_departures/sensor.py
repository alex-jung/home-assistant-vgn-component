"""VGN Departures sensor integration."""

import logging

from homeassistant import config_entries, core
from homeassistant.components.sensor import SensorEntity, datetime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ATTRIBUTION,
    ATTR_DIRECTION,
    ATTR_DIRECTION_TEXT,
    ATTR_LINE_NAME,
    ATTR_OCCUPANCY_LEVEL,
    ATTR_PLANNED_DEPARTURE_TIME,
    ATTR_STOP_ID,
    ATTR_TRANSPORT_TYPE,
)
from .coordinator import VgnUpdateCoordinator
from .vgn.data_classes import Connection, TransportType

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, async_add_entities
):
    """Set up VGN Departures sensors."""

    coordinator: VgnUpdateCoordinator = entry.runtime_data

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            VgnSensorEntity(hass, coordinator, entry_data)
            for entry_data in coordinator.connections
        ],
        update_before_add=True,
    )


class VgnSensorEntity(CoordinatorEntity, SensorEntity):
    """VGN Sensor provides information about next departure(s)."""

    _attr_attribution = ATTR_ATTRIBUTION

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: VgnUpdateCoordinator,
        connection: Connection,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._hass: HomeAssistant = hass
        self._coordinator: VgnUpdateCoordinator = coordinator
        self._uid: str = connection.uid
        self._line: str = connection.line_name
        self._direction: int = connection.direction_id
        self._stop_id: str = connection.stop_id
        self._transport: TransportType = connection.transport
        self._direction_text: str = connection.name
        self._occupancy_level: str | None = None
        self._coordinates: str = None
        self._planned_departure_time: datetime | None = None
        self._value = None

        self._attr_name = f"{coordinator.title} - {self._transport} {self._line} - {self._direction_text}"
        self._attr_unique_id = connection.uid
        self._attr_should_poll = False

        self._attr_extra_state_attributes = {
            ATTR_STOP_ID: self._stop_id,
            ATTR_LINE_NAME: self._line,
            ATTR_TRANSPORT_TYPE: str(self._transport),
            ATTR_DIRECTION: self._direction,
            ATTR_DIRECTION_TEXT: self._direction_text,
            ATTR_OCCUPANCY_LEVEL: self._occupancy_level,
            ATTR_PLANNED_DEPARTURE_TIME: self._planned_departure_time,
        }

        _LOGGER.debug("VGN sensor entity created - Unique id: %s", self._attr_unique_id)
        _LOGGER.debug("hass: %s", self._hass)
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
    def icon(self) -> str:
        """Icon of the entity, based on transport type."""
        match self._transport:
            case TransportType.BUS:
                return "mdi:bus"
            case TransportType.TRAM | TransportType.CABLE_TRAM:
                return "mdi:tram"
            case TransportType.SUBWAY:
                return "mdi:subway"
            case TransportType.RAIL:
                return "mdi:train"
            case TransportType.FERRY:
                return "mdi:ferry"
            case _:
                return "mdi:train-bus"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        _LOGGER.debug("Updating VGN sensor: %s", self._attr_name)
        _LOGGER.debug("direction: %s", self._direction)
        _LOGGER.debug("direction_text: %s", self._direction_text)
        _LOGGER.debug("line: %s", self._line)
        _LOGGER.debug("transport: %s", self._transport)

        # _LOGGER.debug("Received data: %s", self._coordinator.data[self._uid])

        data = self._coordinator.data[self._uid]

        if data and data["times"]:
            self._value = data["times"][0]

        self.async_write_ha_state()
