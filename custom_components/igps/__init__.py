"""Integração iGPSPORT iGS10S (BLE)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IGPSCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

type IGPSConfigEntry = ConfigEntry[IGPSCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: IGPSConfigEntry) -> bool:
    address = entry.data["address"]
    coordinator = IGPSCoordinator(hass, entry, address)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IGPSConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
