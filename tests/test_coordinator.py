"""Testes de comportamento offline do coordinator e da entidade base."""

from unittest.mock import MagicMock, PropertyMock, patch

from homeassistant.core import HomeAssistant
from igps_ble.models import IGPSDeviceState

from custom_components.igps.coordinator import IGPSCoordinator
from custom_components.igps.entity import IGPSEntity

ADDRESS = "AA:BB:CC:DD:EE:FF"


def _make_state() -> IGPSDeviceState:
    return IGPSDeviceState(
        address=ADDRESS,
        name="iGS10S",
        rssi=-44,
        battery_level=80,
        model="iGS10S",
        firmware="1.0.0",
        hardware="rev-a",
        manufacturer="iGPSPORT",
    )


async def test_update_returns_cached_data_when_out_of_range(hass: HomeAssistant):
    """Com dados em cache e o aparelho fora de alcance, mantém o último estado."""
    entry = MagicMock()
    coordinator = IGPSCoordinator(hass, entry, ADDRESS)
    cached = _make_state()
    coordinator.data = cached

    with patch.object(
        IGPSCoordinator, "_service_info", new_callable=PropertyMock, return_value=None
    ):
        result = await coordinator._async_update_data()

    assert result is cached


def test_entity_available_tracks_coordinator_data(hass: HomeAssistant):
    """available é True quando o coordinator tem dados e False quando não tem."""
    entry = MagicMock()
    coordinator = IGPSCoordinator(hass, entry, ADDRESS)
    entity = IGPSEntity(coordinator, "test")

    coordinator.data = _make_state()
    assert entity.available is True

    coordinator.data = None
    assert entity.available is False
