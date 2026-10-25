"""Setup completo com o protocolo mockado: entidades novas + escrita de perfil."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from homeassistant.core import HomeAssistant
from igps_ble import Activity, IGPSDeviceState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.igps.const import DOMAIN
from custom_components.igps.coordinator import IGPSCoordinator

ADDRESS = "AA:BB:CC:DD:EE:FF"

STATE = IGPSDeviceState(
    address=ADDRESS,
    name="iGS10S",
    rssi=-50,
    battery_level=51,
    firmware="V1.15",
    hardware="V1.00",
    manufacturer="iGPSPORT",
    battery_voltage=3.718,
    serial="799940",
    protocol_version="1.01",
    memory_total=8112,
    memory_free=8064,
    temperature=26.7,
    device_time=datetime(2026, 10, 25, 10, 9),
    cycling_status="recording",
    latitude=-5.8,
    longitude=-35.2,
    ride={"cadence": 85},
    activities=(Activity(datetime(2025, 11, 1, 6, 38), 22068),),
)


async def test_entities_and_profile_write(hass: HomeAssistant):
    entry = MockConfigEntry(domain=DOMAIN, data={"address": ADDRESS}, unique_id=ADDRESS)
    entry.add_to_hass(hass)
    client = MagicMock(disconnect=AsyncMock())
    info = MagicMock(name="iGS10S", rssi=-50)
    info.name = "iGS10S"
    with (
        patch.object(
            IGPSCoordinator,
            "_service_info",
            new_callable=PropertyMock,
            return_value=info,
        ),
        patch(
            "custom_components.igps.coordinator.establish_connection",
            AsyncMock(return_value=client),
        ),
        patch(
            "custom_components.igps.coordinator.read_state",
            AsyncMock(return_value=STATE),
        ),
        patch("custom_components.igps.coordinator.IGPSSession") as session,
        patch(
            "custom_components.igps.coordinator.set_profile", AsyncMock()
        ) as set_profile,
    ):
        session.return_value.start = AsyncMock()
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        states = {s.entity_id: s for s in hass.states.async_all()}
        by_suffix = {
            e.split(".", 1)[1].removeprefix("igs10s_"): s for e, s in states.items()
        }
        assert states["sensor.igs10s_battery"].state == "51"
        assert by_suffix["temperature"].state == "26.7"
        assert by_suffix["free_memory"].state == "99.4"
        ride = by_suffix["ride_status"]
        assert ride.state == "recording" and ride.attributes["cadence"] == 85
        assert by_suffix["stored_activities"].state == "1"
        assert (
            states["device_tracker.igs10s_last_gps_position"].attributes["latitude"]
            == -5.8
        )
        # Pedalando => poll rápido.
        assert entry.runtime_data.update_interval.total_seconds() == 30

        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.igs10s_wheel_circumference", "value": 2096},
            blocking=True,
        )
        profile = set_profile.await_args.args[1]
        assert profile.wheel_mm == 2096
        assert entry.options["profile"]["wheel_mm"] == 2096
        assert hass.states.get("number.igs10s_wheel_circumference").state == "2096"
