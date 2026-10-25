"""Serviços com parâmetros (o que não cabe num botão)."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from igps_ble import client as igps
from igps_ble import protocol as p

from .const import DOMAIN
from .coordinator import IGPSCoordinator

ENTRY = vol.Optional("config_entry_id")
CHANNELS = {"data": p.DATA_RX, "third": p.THIRD_RX}


def _coordinator(hass: HomeAssistant, call: ServiceCall) -> IGPSCoordinator:
    entries = [
        e
        for e in hass.config_entries.async_loaded_entries(DOMAIN)
        if call.data.get("config_entry_id") in (None, e.entry_id)
    ]
    if not entries:
        raise HomeAssistantError("Nenhum iGS10S configurado/carregado")
    return entries[0].runtime_data


def _jsonable(msg):
    """Resposta protobuf crua → JSON (bytes viram hex ou submensagem)."""
    out = {}
    for key, values in msg.items():
        items = []
        for value in values:
            if isinstance(value, bytes):
                try:
                    items.append(_jsonable(p.decode(value)) if value else "")
                except ValueError:
                    items.append(value.hex())
            else:
                items.append(value)
        out[str(key)] = items
    return out


def async_setup_services(hass: HomeAssistant) -> None:
    def register(name, schema, handler, response=SupportsResponse.NONE):
        hass.services.async_register(
            DOMAIN, name, handler, vol.Schema({ENTRY: cv.string, **schema}), response
        )

    async def run(call: ServiceCall, fn) -> None:
        coordinator = _coordinator(hass, call)
        await coordinator.async_run(fn)
        await coordinator.async_request_refresh()

    async def download(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator(hass, call)
        start = call.data.get("start")
        activities = (
            [coordinator.activity(start)]
            if start
            else list((coordinator.data.activities if coordinator.data else ()) or ())
        )
        paths = [str(await coordinator.async_download(a)) for a in activities]
        return {"files": paths}

    async def delete(call: ServiceCall) -> None:
        activity = _coordinator(hass, call).activity(call.data["start"])
        await run(call, lambda s: igps.delete_activity(s, activity.id))

    async def send_command(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator(hass, call)
        fields = [tuple(item) for item in call.data.get("fields", [])]
        reply = await coordinator.async_run(
            lambda s: igps.command(
                s,
                call.data["service"],
                call.data["operation"],
                fields,
                sub=call.data.get("sub", 0xFF),
                channel=CHANNELS[call.data.get("channel", "data")],
            )
        )
        return {"reply": _jsonable(reply)}

    register(
        "download_activity",
        {vol.Optional("start"): cv.string},
        download,
        SupportsResponse.OPTIONAL,
    )
    register("delete_activity", {vol.Required("start"): cv.string}, delete)
    register(
        "factory_command",
        {
            vol.Required("command"): vol.In(list(igps.CONTROL)),
            vol.Optional("status", default=1): vol.Coerce(int),
        },
        lambda c: run(
            c, lambda s: igps.factory_control(s, c.data["command"], c.data["status"])
        ),
    )
    register(
        "gps_control",
        {
            vol.Required("command"): vol.In(list(igps.GPS_COMMAND)),
            vol.Optional("status", default=1): vol.Coerce(int),
        },
        lambda c: run(
            c, lambda s: igps.gps_control(s, c.data["command"], c.data["status"])
        ),
    )
    register(
        "set_gnss",
        {vol.Required("systems"): vol.All(cv.ensure_list, [vol.In(list(igps.GNSS))])},
        lambda c: run(c, lambda s: igps.set_gnss(s, c.data["systems"])),
    )
    register(
        "set_gps_dynamic",
        {vol.Required("mode"): vol.In(list(igps.GPS_DYNAMIC))},
        lambda c: run(c, lambda s: igps.set_gps_dynamic(s, c.data["mode"])),
    )

    async def gps_position(call: ServiceCall) -> None:
        lat = call.data.get("latitude", hass.config.latitude)
        lon = call.data.get("longitude", hass.config.longitude)
        await run(call, lambda s: igps.set_gps_position(s, lat, lon))

    register(
        "set_gps_position",
        {
            vol.Optional("latitude"): cv.latitude,
            vol.Optional("longitude"): cv.longitude,
        },
        gps_position,
    )
    register(
        "set_power_save_time",
        {vol.Required("value"): vol.Coerce(int)},
        lambda c: run(c, lambda s: igps.set_power_save_time(s, c.data["value"])),
    )
    register(
        "set_sun_time",
        {
            vol.Required("sunrise"): vol.Coerce(int),
            vol.Required("sunset"): vol.Coerce(int),
        },
        lambda c: run(
            c, lambda s: igps.set_sun_time(s, c.data["sunrise"], c.data["sunset"])
        ),
    )
    register(
        "set_filter",
        {
            vol.Required("filter"): vol.In(list(igps.FILTERS)),
            vol.Required("enabled"): cv.boolean,
        },
        lambda c: run(
            c, lambda s: igps.set_filter(s, c.data["filter"], c.data["enabled"])
        ),
    )
    register(
        "set_serial",
        {vol.Required("serial"): cv.string},
        lambda c: run(c, lambda s: igps.set_serial(s, c.data["serial"])),
    )
    register(
        "simulate_activities",
        {vol.Required("count"): vol.Coerce(int), vol.Required("size"): vol.Coerce(int)},
        lambda c: run(
            c, lambda s: igps.simulate_activities(s, c.data["count"], c.data["size"])
        ),
    )
    register(
        "send_command",
        {
            vol.Required("service"): vol.Coerce(int),
            vol.Required("operation"): vol.Coerce(int),
            vol.Optional("fields", default=[]): list,
            vol.Optional("sub", default=0xFF): vol.Coerce(int),
            vol.Optional("channel", default="data"): vol.In(list(CHANNELS)),
        },
        send_command,
        SupportsResponse.OPTIONAL,
    )
