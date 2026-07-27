"""Base de entidade com device_info compartilhado."""

from __future__ import annotations

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import IGPSCoordinator


class IGPSEntity(RestoreEntity, CoordinatorEntity[IGPSCoordinator]):
    """Entidade base ligada ao coordinator do iGS10S.

    ``coordinator.data`` já mantém o último valor enquanto o aparelho está
    apenas fora de alcance (ver coordinator.py) — mas isso vive só na
    memória do processo. Esta base fecha a lacuna do *restart*: via
    ``RestoreEntity``, lembra se havia um estado válido (nem
    ``unavailable`` nem ``unknown``) antes do restart, e usa isso em
    ``available``.

    O sensor de presença (`IGPSPresenceSensor`) é a exceção deliberada:
    nunca usa esse restore para seu próprio ``is_on``, porque presença é um
    fato ao vivo, não um valor a lembrar.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: IGPSCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_{key}"
        self._restored_available = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        self._restored_available = (
            last_state is not None
            and last_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
        )

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None or self._restored_available

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
