"""Base de entidade com device_info compartilhado."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import IGPSCoordinator


class IGPSEntity(CoordinatorEntity[IGPSCoordinator]):
    """Entidade base ligada ao coordinator do iGS10S."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IGPSCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_{key}"

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None

    @property
    def device_info(self) -> DeviceInfo:
        state = self.coordinator.data
        return DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, self.coordinator.address)},
            identifiers={(DOMAIN, self.coordinator.address)},
            manufacturer=MANUFACTURER,
            model=(state.model if state else None) or DEFAULT_MODEL,
            name=(state.name if state else None) or DEFAULT_MODEL,
            sw_version=state.firmware if state else None,
            hw_version=state.hardware if state else None,
        )
