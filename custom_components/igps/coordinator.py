"""DataUpdateCoordinator: lê o iGS10S via python-igps-ble + bleak-retry-connector."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, replace

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from habluetooth import BluetoothServiceInfoBleak
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from igps_ble import IGPSDeviceState, IGPSSession, UserProfile, read_state, set_profile

from .const import DOMAIN, RIDING_UPDATE_INTERVAL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class IGPSCoordinator(DataUpdateCoordinator[IGPSDeviceState]):
    """Conecta no aparelho periodicamente e publica o snapshot."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, address: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}-{address}",
            update_interval=UPDATE_INTERVAL,
        )
        self.address = address
        # Uma conexão por vez: poll e escrita de perfil disputam o mesmo rádio.
        self._lock = asyncio.Lock()

    @property
    def _service_info(self) -> BluetoothServiceInfoBleak | None:
        return bluetooth.async_last_service_info(
            self.hass, self.address, connectable=True
        )

    @property
    def profile(self) -> UserProfile:
        """Perfil gravado pelo HA (o aparelho não devolve o perfil no GET)."""
        return UserProfile(**self.config_entry.options.get("profile", {}))

    async def _async_update_data(self) -> IGPSDeviceState:
        service_info = self._service_info
        if service_info is None:
            if self.data is not None:
                return self.data
            raise UpdateFailed(f"iGS10S {self.address} fora de alcance")

        async with self._lock:
            client = await establish_connection(
                BleakClientWithServiceCache, service_info.device, self.address
            )
            try:
                state = await read_state(
                    client, self.address, service_info.name, service_info.rssi
                )
            finally:
                await client.disconnect()

        # Pedalando (ex.: rolo em casa): poll rápido para os dados ao vivo.
        self.update_interval = (
            RIDING_UPDATE_INTERVAL
            if state.cycling_status in ("recording", "paused")
            else UPDATE_INTERVAL
        )
        return state

    async def async_set_profile(self, **changes) -> None:
        """Grava o perfil inteiro no aparelho e guarda nas options da entrada."""
        service_info = self._service_info
        if service_info is None:
            raise HomeAssistantError("iGS10S fora de alcance")
        offset = dt_util.now().utcoffset()
        profile = replace(
            self.profile,
            **changes,
            time_zone_s=int(offset.total_seconds()) if offset else 0,
        )
        async with self._lock:
            # Sinal fraco derruba a conexão às vezes: uma segunda tentativa basta.
            for attempt in range(2):
                try:
                    client = await establish_connection(
                        BleakClientWithServiceCache, service_info.device, self.address
                    )
                    try:
                        session = IGPSSession(client)
                        await session.start()
                        await set_profile(session, profile)
                    finally:
                        await client.disconnect()
                    break
                except Exception as err:
                    if attempt:
                        raise HomeAssistantError(
                            f"Falha ao gravar perfil: {err}"
                        ) from err
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, "profile": asdict(profile)},
        )
        self.async_update_listeners()
