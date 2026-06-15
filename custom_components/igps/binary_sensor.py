"""Binary sensor de presença: o iGS10S foi visto por BLE recentemente?"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import IGPSConfigEntry
from .entity import IGPSEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([IGPSPresenceSensor(entry.runtime_data)])


class IGPSPresenceSensor(IGPSEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "presence"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "presence")

    @property
    def available(self) -> bool:
        """Disponível mesmo offline: ele justamente reporta a presença."""
        return True

    @property
    def is_on(self) -> bool:
        """True se o HA tem um advertisement recente e conectável do aparelho."""
        return (
            bluetooth.async_last_service_info(
                self.hass, self.coordinator.address, connectable=True
            )
            is not None
        )
