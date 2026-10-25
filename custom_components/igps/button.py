"""Comandos de um clique: atividades, manutenção, GPS, pareamento, DFU.

Vários são destrutivos (formatar, reset de fábrica, apagar atividades) e o HA
não pede confirmação — ficam em Configuração no card do aparelho.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from igps_ble import IGPSSession
from igps_ble import client as igps

from . import IGPSConfigEntry
from .coordinator import IGPSCoordinator
from .entity import IGPSEntity


@dataclass(frozen=True, kw_only=True)
class IGPSButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[IGPSSession], Awaitable[None]] | None = None


def _control(cmd: str):
    return lambda s: igps.factory_control(s, cmd)


BUTTONS: tuple[IGPSButtonDescription, ...] = (
    IGPSButtonDescription(key="refresh", translation_key="refresh"),
    IGPSButtonDescription(
        key="download_activities", translation_key="download_activities"
    ),
    IGPSButtonDescription(
        key="delete_all_activities",
        translation_key="delete_all_activities",
        press_fn=igps.delete_all_activities,
    ),
    IGPSButtonDescription(
        key="gps_cold_start",
        translation_key="gps_cold_start",
        press_fn=lambda s: igps.gps_control(s, "cold_start"),
    ),
    IGPSButtonDescription(
        key="reset_settings",
        translation_key="reset_settings",
        press_fn=_control("reset_settings"),
    ),
    IGPSButtonDescription(
        key="format", translation_key="format", press_fn=_control("format")
    ),
    IGPSButtonDescription(
        key="low_level_format",
        translation_key="low_level_format",
        press_fn=_control("low_level_format"),
    ),
    IGPSButtonDescription(
        key="factory_reset",
        translation_key="factory_reset",
        press_fn=_control("factory_reset"),
    ),
    IGPSButtonDescription(
        key="enter_check",
        translation_key="enter_check",
        press_fn=_control("enter_check"),
    ),
    IGPSButtonDescription(
        key="lock", translation_key="lock", press_fn=_control("lock")
    ),
    IGPSButtonDescription(
        key="temperature_log",
        translation_key="temperature_log",
        press_fn=_control("temperature_log"),
    ),
    IGPSButtonDescription(
        key="voltage_log",
        translation_key="voltage_log",
        press_fn=_control("voltage_log"),
    ),
    IGPSButtonDescription(
        key="ant_log", translation_key="ant_log", press_fn=_control("ant_log")
    ),
    IGPSButtonDescription(key="unbond", translation_key="unbond", press_fn=igps.unbond),
    IGPSButtonDescription(
        key="enter_dfu", translation_key="enter_dfu", press_fn=igps.enter_dfu
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(IGPSButton(coordinator, desc) for desc in BUTTONS)


class IGPSButton(IGPSEntity, ButtonEntity):
    entity_description: IGPSButtonDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: IGPSCoordinator, description) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        coordinator = self.coordinator
        key = self.entity_description.key
        if key == "download_activities":
            for activity in (
                coordinator.data.activities if coordinator.data else ()
            ) or ():
                await coordinator.async_download(activity)
        elif self.entity_description.press_fn is not None:
            await coordinator.async_run(self.entity_description.press_fn)
        await coordinator.async_request_refresh()
