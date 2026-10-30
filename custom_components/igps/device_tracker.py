"""Última posição GPS que o iGS10S registrou."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import IGPSConfigEntry
from .entity import IGPSEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([IGPSTracker(entry.runtime_data)])


class IGPSTracker(IGPSEntity, TrackerEntity):
    _attr_translation_key = "location"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "location")

    @property
    def latitude(self) -> float | None:
        return self.coordinator.data.latitude if self.coordinator.data else None

    @property
    def longitude(self) -> float | None:
        return self.coordinator.data.longitude if self.coordinator.data else None
