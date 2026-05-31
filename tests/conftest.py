"""Fixtures de teste da integração."""

import pytest
from homeassistant.helpers.service_info.bluetooth import BluetoothServiceInfo

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
async def auto_enable_bluetooth(enable_bluetooth):
    """Habilita o stack de Bluetooth mockado para todos os testes."""
    yield


@pytest.fixture
def igs10s_service_info() -> BluetoothServiceInfo:
    return BluetoothServiceInfo(
        name="iGS10S",
        address="AA:BB:CC:DD:EE:FF",
        rssi=-44,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
    )
