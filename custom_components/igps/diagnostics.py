"""Diagnóstico da entrada: options e último snapshot do aparelho, redigidos."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import IGPSConfigEntry

TO_REDACT = {"address", "serial", "latitude", "longitude", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: IGPSConfigEntry
) -> dict[str, Any]:
    """Devolve dados da entrada e o último estado lido, sem endereço/série/posição."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "entry": async_redact_data(
            {"data": dict(entry.data), "options": dict(entry.options)}, TO_REDACT
        ),
        "data": async_redact_data(asdict(data), TO_REDACT) if data else None,
        "update_interval": coordinator.update_interval.total_seconds()
        if coordinator.update_interval
        else None,
    }
