"""Sexo do perfil (cálculo de calorias no iGS10S)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import IGPSConfigEntry
from .entity import IGPSEntity

SEX = {"male": 1, "female": 0}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([IGPSSexSelect(entry.runtime_data)])


class IGPSSexSelect(IGPSEntity, SelectEntity):
    _attr_translation_key = "sex"
    _attr_options = list(SEX)
    _attr_entity_category = EntityCategory.CONFIG
    _attr_assumed_state = True

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "sex")

    @property
    def current_option(self) -> str | None:
        if "profile" not in self.coordinator.config_entry.options:
            return None
        sex = self.coordinator.profile.sex
        return next(k for k, v in SEX.items() if v == sex)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_profile(sex=SEX[option])
