"""Sensores do iGS10S: bateria, temperatura, memória, status de pedal, atividades."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util
from igps_ble.models import IGPSDeviceState

from . import IGPSConfigEntry
from .entity import IGPSEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class IGPSSensorDescription(SensorEntityDescription):
    value_fn: Callable[[IGPSDeviceState], Any]
    attrs_fn: Callable[[IGPSDeviceState], dict[str, Any]] | None = None


def _local(value: datetime | None) -> datetime | None:
    """O aparelho guarda horário local sem fuso; ancora no fuso do HA."""
    if value is None:
        return None
    return value.replace(tzinfo=dt_util.get_default_time_zone())


def _memory_free(s: IGPSDeviceState) -> float | None:
    if not s.memory_total or s.memory_free is None:
        return None
    return round(s.memory_free / s.memory_total * 100, 1)


def _activities_attrs(s: IGPSDeviceState) -> dict[str, Any]:
    return {
        "activities": [
            {"start": _local(a.start).isoformat(), "size": a.size}
            for a in s.activities or ()
        ]
    }


def _ride_attrs(s: IGPSDeviceState) -> dict[str, Any]:
    # rt_data_message cru: escalas não confirmadas (o app não usa esse campo).
    start = _local(s.cycling_start)
    return {**s.ride, "start": start.isoformat() if start else None}


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
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=2,
        value_fn=lambda s: s.battery_voltage,
    ),
    IGPSSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: s.temperature,
    ),
    IGPSSensorDescription(
        key="memory_free",
        translation_key="memory_free",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_memory_free,
    ),
    IGPSSensorDescription(
        key="cycling_status",
        translation_key="cycling_status",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "recording", "paused"],
        value_fn=lambda s: s.cycling_status,
        attrs_fn=_ride_attrs,
    ),
    IGPSSensorDescription(
        key="activities",
        translation_key="activities",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda s: None if s.activities is None else len(s.activities),
        attrs_fn=_activities_attrs,
    ),
    IGPSSensorDescription(
        key="last_activity",
        translation_key="last_activity",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda s: _local(s.activities[0].start) if s.activities else None,
    ),
    IGPSSensorDescription(
        key="device_time",
        translation_key="device_time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: _local(s.device_time),
    ),
    IGPSSensorDescription(
        key="protocol_version",
        translation_key="protocol_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.protocol_version,
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
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(IGPSSensor(coordinator, desc) for desc in SENSORS)


class IGPSSensor(IGPSEntity, RestoreSensor):
    entity_description: IGPSSensorDescription

    def __init__(self, coordinator, description: IGPSSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._restored_value: Any = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last_data := await self.async_get_last_sensor_data()) is not None:
            self._restored_value = last_data.native_value

    @property
    def native_value(self) -> Any:
        if self.coordinator.data is not None:
            return self.entity_description.value_fn(self.coordinator.data)
        return self._restored_value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attrs_fn = self.entity_description.attrs_fn
        if attrs_fn is None or self.coordinator.data is None:
            return None
        return attrs_fn(self.coordinator.data)
