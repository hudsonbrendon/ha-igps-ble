"""DataUpdateCoordinator: lê o iGS10S via python-igps-ble + bleak-retry-connector."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import asdict, replace
from pathlib import Path
from typing import TypeVar

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from habluetooth import BluetoothServiceInfoBleak
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util
from igps_ble import (
    Activity,
    IGPSCommandError,
    IGPSDeviceState,
    IGPSSession,
    UserProfile,
    read_state,
    set_profile,
)
from igps_ble.client import download_activity

from .const import DOMAIN, RIDING_UPDATE_INTERVAL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)
T = TypeVar("T")


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
        self._backup_running = False

    @property
    def _service_info(self) -> BluetoothServiceInfoBleak | None:
        return bluetooth.async_last_service_info(
            self.hass, self.address, connectable=True
        )

    @property
    def profile(self) -> UserProfile:
        """Perfil gravado pelo HA (o aparelho não devolve o perfil no GET)."""
        return UserProfile(**self.config_entry.options.get("profile", {}))

    def fit_dir(self, serial: str | None = None) -> Path:
        """Onde os .fit baixados ficam (pasta de mídia → aparece no Media)."""
        media = self.hass.config.media_dirs.get("local") or self.hass.config.path(
            "media"
        )
        serial = serial or (self.data.serial if self.data else None) or self.address
        return Path(media) / "igps" / serial.replace(":", "")

    @staticmethod
    def fit_name(activity: Activity) -> str:
        return f"{activity.start:%Y-%m-%d-%H%M%S}.fit"

    async def _connect(self):
        service_info = self._service_info
        if service_info is None:
            raise HomeAssistantError("iGS10S fora de alcance")
        client = await establish_connection(
            BleakClientWithServiceCache, service_info.device, self.address
        )
        session = IGPSSession(client)
        try:
            await session.start()
        except Exception:
            await client.disconnect()
            raise
        return client, session

    async def async_run(self, fn: Callable[[IGPSSession], Awaitable[T]]) -> T:
        """Abre uma conexão, roda ``fn(session)`` e desconecta (1 retry)."""
        async with self._lock:
            # Sinal fraco derruba a conexão às vezes: uma segunda tentativa basta.
            for attempt in range(2):
                try:
                    client, session = await self._connect()
                    try:
                        return await fn(session)
                    finally:
                        await client.disconnect()
                except IGPSCommandError as err:
                    raise HomeAssistantError(
                        f"iGS10S recusou o comando (status {err.status})"
                    ) from err
                except Exception as err:
                    if attempt:
                        raise HomeAssistantError(f"Falha no iGS10S: {err}") from err
        raise AssertionError("unreachable")

    async def _async_update_data(self) -> IGPSDeviceState:
        service_info = self._service_info
        if service_info is None:
            if self.data is not None:
                return self.data
            raise UpdateFailed(f"iGS10S {self.address} fora de alcance")

        try:
            state = await self.async_run(
                lambda s: read_state(
                    s.client,
                    self.address,
                    service_info.name,
                    service_info.rssi,
                    session=s,
                )
            )
        except HomeAssistantError as err:
            raise UpdateFailed(str(err)) from err

        if self.data is not None:
            # Consulta que estourou o tempo neste poll: mantém o último valor.
            state = replace(
                state,
                **{
                    name: getattr(self.data, name)
                    for name in ("serial", "activities", "memory_total", "memory_free")
                    if getattr(state, name) is None
                },
            )

        if state.activities and not self._backup_running:
            # Fora do poll: baixar .fit leva dezenas de segundos e travaria o boot.
            self._backup_running = True
            self.config_entry.async_create_background_task(
                self.hass, self._async_backup(state), "igps_fit_backup"
            )

        # Pedalando (ex.: rolo em casa): poll rápido para os dados ao vivo.
        self.update_interval = (
            RIDING_UPDATE_INTERVAL
            if state.cycling_status in ("recording", "paused")
            else UPDATE_INTERVAL
        )
        return state

    async def _async_backup(self, state: IGPSDeviceState) -> None:
        """Baixa os .fit que ainda não estão na pasta (backup automático)."""
        try:
            folder = self.fit_dir(state.serial)
            have = await self.hass.async_add_executor_job(
                lambda: {f.name: f.stat().st_size for f in folder.glob("*.fit")}
                if folder.exists()
                else {}
            )
            for activity in state.activities or ():
                # Tamanho diferente = download anterior incompleto: baixa de novo.
                if have.get(self.fit_name(activity)) != activity.size:
                    await self.async_download(activity, state.serial)
        except HomeAssistantError as err:
            _LOGGER.warning("iGS10S: backup dos .fit falhou: %s", err)
        finally:
            self._backup_running = False

    async def async_download(
        self, activity: Activity, serial: str | None = None
    ) -> Path:
        """Baixa (de novo) um .fit e devolve o caminho salvo."""
        data = await self.async_run(
            lambda s: download_activity(s, activity.id, activity.size)
        )
        path = self.fit_dir(serial) / self.fit_name(activity)
        await self.hass.async_add_executor_job(_write, path, data)
        _LOGGER.info("iGS10S: atividade salva em %s", path)
        return path

    def activity(self, start: str | None) -> Activity:
        """Atividade pelo início (ISO, como no atributo) ou a mais recente."""
        activities = (self.data.activities if self.data else None) or ()
        for item in activities:
            if start is None or item.start.isoformat().startswith(start[:19]):
                return item
        raise HomeAssistantError(f"Atividade {start!r} não encontrada no aparelho")

    async def async_set_profile(self, **changes) -> None:
        """Grava o perfil inteiro no aparelho e guarda nas options da entrada."""
        offset = dt_util.now().utcoffset()
        profile = replace(
            self.profile,
            **changes,
            time_zone_s=int(offset.total_seconds()) if offset else 0,
        )
        await self.async_run(lambda s: set_profile(s, profile))
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, "profile": asdict(profile)},
        )
        self.async_update_listeners()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, suffix=".part", delete=False
    ) as f:
        f.write(data)
    Path(f.name).chmod(0o644)  # tempfile cria 600
    Path(f.name).replace(path)
