<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/igps/brand/dark_logo.png">
    <img src="custom_components/igps/brand/logo.png" alt="iGPSPORT" width="360">
  </picture>
</p>

# iGPSPORT iGS10S for Home Assistant

[![Tests](https://github.com/hudsonbrendon/ha-igps-ble/actions/workflows/tests.yml/badge.svg)](https://github.com/hudsonbrendon/ha-igps-ble/actions/workflows/tests.yml)
[![Hassfest](https://github.com/hudsonbrendon/ha-igps-ble/actions/workflows/hassfest.yml/badge.svg)](https://github.com/hudsonbrendon/ha-igps-ble/actions/workflows/hassfest.yml)
[![Validate](https://github.com/hudsonbrendon/ha-igps-ble/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/ha-igps-ble/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Release](https://img.shields.io/github/v/release/hudsonbrendon/ha-igps-ble)](https://github.com/hudsonbrendon/ha-igps-ble/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Auto-discovers an **iGPSPORT iGS10S** cycling computer over Bluetooth LE and
exposes its presence, signal strength, and device information in Home Assistant.

The Bluetooth protocol and device control live in a separate Python library,
[**`python-igps-ble`**](https://github.com/hudsonbrendon/python-igps-ble)
([PyPI](https://pypi.org/project/python-igps-ble/)), which this integration pulls
in automatically via `manifest.json` `requirements`.

## Features

- 🔍 **Automatic discovery** — power on the iGS10S near Home Assistant and it
  shows up as a discovered device (no MAC address or YAML required).
- 📡 **Presence** — a connectivity `binary_sensor` that turns on while the device
  is advertising nearby.
- 📶 **Signal strength** — an RSSI `sensor` (diagnostic).
- 🏷️ **Device info** — model, hardware revision, and firmware `sensor`s, also
  shown on the device page in the device registry.
- 🔋 **Battery** — a battery `sensor` that populates when the device exposes the
  standard Battery Service (the iGS10S does not — see **Scope**).
- 🛰️ **Works through ESPHome Bluetooth proxies** — it uses Home Assistant's shared
  Bluetooth stack, so the device doesn't need to be near the HA host, only near a
  proxy.
- 🌐 **Localized** — UI and entities translated to English and Português (Brasil).

## Requirements

- Home Assistant **2024.6** or newer.
- A Bluetooth adapter on the Home Assistant host **or** an
  [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html)
  within range of the device.
- An iGPSPORT iGS10S.

## Installation

### HACS (recommended)

1. In Home Assistant, open **HACS → ⋮ (top right) → Custom repositories**.
2. Add the repository URL `https://github.com/hudsonbrendon/ha-igps-ble`
   and choose the **Integration** category.
3. Search for **iGPSPORT iGS10S** in HACS, install it, and **restart Home Assistant**.

### Manual

1. Copy `custom_components/igps/` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Power on the iGS10S within range of Home Assistant (or a Bluetooth proxy).
2. Home Assistant discovers it automatically — go to
   **Settings → Devices & Services** and you'll see an **iGPSPORT iGS10S**
   *Discovered* card. Click **Configure → Submit**.
3. If it isn't auto-discovered, add it manually: **Settings → Devices & Services
   → Add Integration → iGPSPORT iGS10S**.

> Bluetooth LE allows one connection at a time. Close the official iGPSPORT app
> while Home Assistant is using the device, otherwise it may not be reachable.

## Entities

### Binary sensor

| Entity | Description |
|--------|-------------|
| `binary_sensor.<name>_presence` | On while the iGS10S has been seen over BLE recently; off when out of range or powered off. |

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.<name>_battery` | Battery level (%), when the device exposes a Battery Service. |
| `sensor.<name>_rssi` | Bluetooth signal strength (dBm). Diagnostic, disabled by default. |
| `sensor.<name>_model` | Model number. Diagnostic, disabled by default. |
| `sensor.<name>_firmware` | Firmware (software revision). Diagnostic, disabled by default. |

Manufacturer, hardware revision, and firmware are also shown on the device page in
the device registry.

## Scope

The iGS10S does **not** expose battery level, speed, distance, or ride data to
third parties over Bluetooth — that telemetry lives behind an authenticated,
proprietary Nordic UART protocol used by the official iGPSPORT app, which is out
of scope for this integration (see [`docs/PROTOCOL.md`](docs/PROTOCOL.md) for the
reverse-engineering notes). This integration covers what is read reliably over
standard BLE: presence, signal strength, and device information.

## Credits

Bluetooth library: [python-igps-ble](https://github.com/hudsonbrendon/python-igps-ble).
Author [@hudsonbrendon](https://github.com/hudsonbrendon).

## License

MIT — see [LICENSE](LICENSE).
