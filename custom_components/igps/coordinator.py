"""DataUpdateCoordinator: lê o iGS10S via python-igps-ble + bleak-retry-connector."""

from __future__ import annotations

import logging

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
from habluetooth import BluetoothServiceInfoBleak
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from igps_ble.const import (
    BATTERY_LEVEL_UUID,
    FIRMWARE_REVISION_UUID,
    HARDWARE_REVISION_UUID,
    MANUFACTURER_NAME_UUID,
    MODEL_NUMBER_UUID,
    SOFTWARE_REVISION_UUID,
)
from igps_ble.models import IGPSDeviceState
from igps_ble.parser import decode_device_string, parse_battery_level

from .const import DOMAIN, UPDATE_INTERVAL

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

    @property
    def _service_info(self) -> BluetoothServiceInfoBleak | None:
        return bluetooth.async_last_service_info(
            self.hass, self.address, connectable=True
        )

    async def _async_update_data(self) -> IGPSDeviceState:
        service_info = self._service_info
        if service_info is None:
            raise UpdateFailed(f"iGS10S {self.address} fora de alcance")

        ble_device = service_info.device

        async def _read(client, uuid):
            if client.services.get_characteristic(uuid) is None:
                return None
            try:
                return await client.read_gatt_char(uuid)
            except Exception:  # noqa: BLE001
                return None

        client = await establish_connection(
            BleakClientWithServiceCache, ble_device, self.address
        )
        try:
            battery = await _read(client, BATTERY_LEVEL_UUID)
            model = await _read(client, MODEL_NUMBER_UUID)
            # iGS10S reporta firmware na Software Revision (0x2A28); fallback
            # pra Firmware Revision (0x2A26) em aparelhos que usem a clássica.
            firmware = await _read(client, SOFTWARE_REVISION_UUID)
            if firmware is None:
                firmware = await _read(client, FIRMWARE_REVISION_UUID)
            hardware = await _read(client, HARDWARE_REVISION_UUID)
            manufacturer = await _read(client, MANUFACTURER_NAME_UUID)
        finally:
            await client.disconnect()

        return IGPSDeviceState(
            address=self.address,
            name=service_info.name,
            rssi=service_info.rssi,
            battery_level=parse_battery_level(battery) if battery else None,
            model=decode_device_string(model) if model else None,
            firmware=decode_device_string(firmware) if firmware else None,
            hardware=decode_device_string(hardware) if hardware else None,
            manufacturer=decode_device_string(manufacturer) if manufacturer else None,
        )
