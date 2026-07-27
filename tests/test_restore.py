"""Restore-on-restart: entities keep their last value across a HA restart.

``test_coordinator.py`` covers staying available while the iGS10S is merely
out of range *within one running HA process* (``coordinator.data`` lives in
memory). This file covers the harder case: a HA restart reborns
``coordinator.data`` as ``None``, so the previous run's last value has to
come back from Home Assistant's restore-state storage instead.

Unlike ``jbl_charge5``, ``async_setup_entry`` here calls
``coordinator.async_config_entry_first_refresh()`` unconditionally, which
raises ``ConfigEntryNotReady`` when the BLE device can't be reached — so a
full config-entry setup can't be exercised with the device offline. These
tests instead exercise the entities directly, the same unit-level style
already used in ``test_coordinator.py``.
"""

from unittest.mock import MagicMock

from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import (
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
)

from custom_components.igps.binary_sensor import IGPSPresenceSensor
from custom_components.igps.coordinator import IGPSCoordinator
from custom_components.igps.sensor import SENSORS, IGPSSensor

ADDRESS = "AA:BB:CC:DD:EE:FF"


def _coordinator(hass: HomeAssistant) -> IGPSCoordinator:
    return IGPSCoordinator(hass, MagicMock(), ADDRESS)


async def test_battery_sensor_restores_last_value_after_restart(
    hass: HomeAssistant,
):
    """Battery must show its pre-restart value, not go unavailable forever."""
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State("sensor.igs10s_battery", "80"),
                {"native_value": 80, "native_unit_of_measurement": "%"},
            ),
        ),
    )
    battery_desc = next(d for d in SENSORS if d.key == "battery")
    sensor = IGPSSensor(_coordinator(hass), battery_desc)
    sensor.hass = hass
    sensor.entity_id = "sensor.igs10s_battery"

    await sensor.async_added_to_hass()

    assert sensor.available is True
    assert sensor.native_value == 80


async def test_model_sensor_restores_last_value_after_restart(hass: HomeAssistant):
    """Diagnostic string sensor restores its already-formatted last value."""
    mock_restore_cache_with_extra_data(
        hass,
        (
            (
                State("sensor.igs10s_model", "iGS10S"),
                {"native_value": "iGS10S", "native_unit_of_measurement": None},
            ),
        ),
    )
    model_desc = next(d for d in SENSORS if d.key == "model")
    sensor = IGPSSensor(_coordinator(hass), model_desc)
    sensor.hass = hass
    sensor.entity_id = "sensor.igs10s_model"

    await sensor.async_added_to_hass()

    assert sensor.available is True
    assert sensor.native_value == "iGS10S"


async def test_sensor_unavailable_when_nothing_was_ever_restored(
    hass: HomeAssistant,
):
    """No prior state, no live data: stays unavailable, no fake value."""
    battery_desc = next(d for d in SENSORS if d.key == "battery")
    sensor = IGPSSensor(_coordinator(hass), battery_desc)
    sensor.hass = hass
    sensor.entity_id = "sensor.igs10s_battery"

    await sensor.async_added_to_hass()

    assert sensor.available is False
    assert sensor.native_value is None


async def test_presence_sensor_never_restores_a_stale_on(hass: HomeAssistant):
    """Connectivity is a live fact: a saved 'on' must never leak back in."""
    mock_restore_cache(hass, [State("binary_sensor.igs10s_presence", "on")])
    sensor = IGPSPresenceSensor(_coordinator(hass))
    sensor.hass = hass
    sensor.entity_id = "binary_sensor.igs10s_presence"

    await sensor.async_added_to_hass()

    assert sensor.available is True
    assert sensor.is_on is False
