"""Setup completo com o protocolo mockado: entidades novas + escrita de perfil."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from homeassistant.core import HomeAssistant
from igps_ble import Activity, IGPSDeviceState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.igps.const import DOMAIN
from custom_components.igps.coordinator import IGPSCoordinator
from custom_components.igps.diagnostics import async_get_config_entry_diagnostics

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
    activities=(Activity(1130913480, datetime(2025, 11, 1, 6, 38), 22068),),
)


async def test_entities_and_profile_write(hass: HomeAssistant, tmp_path):
    hass.config.media_dirs = {"local": str(tmp_path)}
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
            "custom_components.igps.coordinator.download_activity",
            AsyncMock(return_value=b"\x0e\x10.FIT"),
        ) as download,
        patch(
            "custom_components.igps.coordinator.set_profile", AsyncMock()
        ) as set_profile,
    ):
        session.return_value.start = AsyncMock()
        session.return_value.simple = AsyncMock(return_value={})
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)

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

        diag = await async_get_config_entry_diagnostics(hass, entry)
        assert diag["entry"]["data"]["address"] == "**REDACTED**"
        assert diag["data"]["serial"] == "**REDACTED**"
        assert diag["data"]["battery_level"] == 51

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

        # Backup automático do .fit novo na pasta de mídia.
        fit = tmp_path / "igps" / "799940" / "2025-11-01-063800.fit"
        assert fit.read_bytes() == b"\x0e\x10.FIT"
        assert download.await_count == 1

        # Botão destrutivo chega no aparelho com o frame do app.
        await hass.services.async_call(
            "button",
            "press",
            {"entity_id": "button.igs10s_delete_all_activities"},
            blocking=True,
        )
        args, kwargs = session.return_value.simple.await_args
        assert args[:2] == (6, 6) and kwargs["channel"].endswith("dcca7e")

        reply = await hass.services.async_call(
            DOMAIN, "download_activity", {}, blocking=True, return_response=True
        )
        assert reply == {"files": [str(fit)]}

        # Intervalo de leitura ajustável (vale quando não está pedalando).
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.igs10s_read_interval", "value": 60},
            blocking=True,
        )
        assert entry.options["scan_interval_min"] == 60
        assert entry.runtime_data.idle_interval.total_seconds() == 3600
        assert hass.states.get("number.igs10s_read_interval").state == "60.0"
