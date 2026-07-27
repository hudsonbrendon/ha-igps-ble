"""Sensores do iGS10S: bateria, RSSI, modelo, firmware."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from igps_ble.models import IGPSDeviceState

from . import IGPSConfigEntry
from .entity import IGPSEntity


@dataclass(frozen=True, kw_only=True)
class IGPSSensorDescription(SensorEntityDescription):
    value_fn: Callable[[IGPSDeviceState], int | str | None]


SENSORS: tuple[IGPSSensorDescription, ...] = (
    IGPSSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.battery_level,
    ),
    IGPSSensorDescription(
        key="rssi",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.rssi,
    ),
    IGPSSensorDescription(
        key="model",
        translation_key="model",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.model,
    ),
    IGPSSensorDescription(
        key="firmware",
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.firmware,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(IGPSSensor(coordinator, desc) for desc in SENSORS)


class IGPSSensor(IGPSEntity, RestoreSensor):
    entity_description: IGPSSensorDescription

    def __init__(self, coordinator, description: IGPSSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._restored_value: int | str | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_data := await self.async_get_last_sensor_data()) is not None:
            self._restored_value = last_data.native_value

    @property
    def native_value(self) -> int | str | None:
        if self.coordinator.data is not None:
            return self.entity_description.value_fn(self.coordinator.data)
        return self._restored_value
