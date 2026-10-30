# Changelog

## Unreleased (0.3.3)

- Home Assistant 2026.10 / Python 3.14: tests run on
  `pytest-homeassistant-custom-component==0.13.375` (adds `serialx`, now a
  runtime dependency of HA's `usb` component).
- `AddConfigEntryEntitiesCallback` on every platform and `PARALLEL_UPDATES`
  declared per platform.
- Diagnostics download (address, serial and GPS position redacted).
- `quality_scale.yaml` next to the manifest.
- Manifest: library requirements pinned (`python-igps-ble==0.3.4`,
  `bleak-retry-connector==4.7.1`), `loggers` declared.
- Tooling: ruff config aligned with the other integrations
  (`target-version = "py314"`), CI on Python 3.14, HACS floor `2025.6.0`.

## 0.3.2

- Read interval stays available while the device is off.

## 0.3.1

- Adjustable read interval (number entity) to save battery.
