"""Integração iGPSPORT iGS10S (BLE)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import IGPSCoordinator
from .services import async_setup_services

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.DEVICE_TRACKER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
]

type IGPSConfigEntry = ConfigEntry[IGPSCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: IGPSConfigEntry) -> bool:
    address = entry.data["address"]
    coordinator = IGPSCoordinator(hass, entry, address)
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # A primeira leitura pelo proxy BLE pode levar mais de um minuto: roda em
    # segundo plano para não travar o boot (as entidades restauram o último estado).
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), "igps_first_refresh"
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IGPSConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
