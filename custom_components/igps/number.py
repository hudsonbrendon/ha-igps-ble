"""Perfil do ciclista/bike gravado no iGS10S (calorias, velocidade por sensor).

O aparelho aceita o perfil mas não o devolve, então o valor exibido é o último
que o HA gravou (guardado nas options da entrada).
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory, UnitOfLength, UnitOfMass, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import IGPSConfigEntry
from .entity import IGPSEntity


@dataclass(frozen=True, kw_only=True)
class IGPSNumberDescription(NumberEntityDescription):
    field: str


NUMBERS: tuple[IGPSNumberDescription, ...] = (
    IGPSNumberDescription(
        key="weight",
        translation_key="weight",
        field="weight_kg",
        device_class=NumberDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        native_min_value=20,
        native_max_value=200,
        native_step=1,
    ),
    IGPSNumberDescription(
        key="height",
        translation_key="height",
        field="height_cm",
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
        native_min_value=100,
        native_max_value=230,
        native_step=1,
    ),
    IGPSNumberDescription(
        key="age",
        translation_key="age",
        field="age",
        native_unit_of_measurement=UnitOfTime.YEARS,
        native_min_value=5,
        native_max_value=99,
        native_step=1,
    ),
    IGPSNumberDescription(
        key="wheel",
        translation_key="wheel",
        field="wheel_mm",
        device_class=NumberDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        native_min_value=0,
        native_max_value=3000,
        native_step=1,
    ),
    IGPSNumberDescription(
        key="bike_weight",
        translation_key="bike_weight",
        field="bike_weight_kg",
        device_class=NumberDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        native_min_value=0,
        native_max_value=50,
        native_step=1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(IGPSNumber(coordinator, desc) for desc in NUMBERS)


class IGPSNumber(IGPSEntity, NumberEntity):
    entity_description: IGPSNumberDescription
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_assumed_state = True

    def __init__(self, coordinator, description: IGPSNumberDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        value = getattr(self.coordinator.profile, self.entity_description.field)
        return value or None  # 0 = nunca gravado pelo HA

    async def async_set_native_value(self, value: float) -> None:
        field = self.entity_description.field
        await self.coordinator.async_set_profile(
            **{field: value if field.endswith("_kg") else int(value)}
        )
