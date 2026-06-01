"""Fixtures de teste da integração."""

import pytest
from homeassistant.helpers.service_info.bluetooth import BluetoothServiceInfo

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Permite timers pendentes no teardown.

    No Linux, o scanner do componente `bluetooth` (puxado pela dependência
    `bluetooth_adapters`) agenda um timer de expiração de dispositivos
    (`BaseHaScanner._async_expire_devices_schedule_next`) que o harness de teste
    de custom component não cancela, fazendo o teste falhar no teardown.
    """
    return True


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """Permite tasks pendentes deixadas pelo stack de Bluetooth no teardown."""
    return True


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
