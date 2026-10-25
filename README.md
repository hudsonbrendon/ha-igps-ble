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
exposes its battery, internal sensors, ride status, stored activities and last GPS
position in Home Assistant — and lets you set the rider/bike profile on the device.

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
- 🔋 **Battery** — level (%) and voltage, read over iGPSPORT's proprietary
  protocol (the iGS10S has no standard Battery Service).
- 🌡️ **Internal sensors** — temperature, free memory and the device clock.
- 🚴 **Ride status** — idle / recording / paused; while recording (e.g. on an
  indoor trainer) it polls every 30 s and exposes the live ride data as attributes.
- 🗂️ **Stored activities** — how many rides are on the device and when the last one
  started.
- 📍 **Last GPS position** — a `device_tracker` with the last fix the device got.
- ⚙️ **Rider & bike profile** — weight, height, age, sex, wheel circumference and
  bike weight, written to the device (the time zone is taken from Home Assistant).
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
| `sensor.<name>_battery` | Battery level (%). |
| `sensor.<name>_battery_voltage` | Battery voltage (V). Diagnostic. |
| `sensor.<name>_temperature` | Internal temperature sensor (°C). |
| `sensor.<name>_free_memory` | Free storage (%). Diagnostic. |
| `sensor.<name>_ride_status` | `idle` / `recording` / `paused`. Attributes: raw live ride fields (`speed`, `distance`, `cadence`, `heart_rate`, `power`, `altitude`, …) and `start`. |
| `sensor.<name>_stored_activities` | Number of rides stored on the device; attribute `activities` lists start time and `.fit` size. |
| `sensor.<name>_last_activity` | Start time of the most recent stored ride. |
| `sensor.<name>_device_clock` | The device's clock. Diagnostic, disabled by default. |
| `sensor.<name>_protocol_version` | Protocol version. Diagnostic, disabled by default. |
| `sensor.<name>_rssi` | Bluetooth signal strength (dBm). Diagnostic, disabled by default. |
| `sensor.<name>_model` / `_firmware` | Model and firmware. Diagnostic, disabled by default. |

Serial number, hardware revision and firmware are also on the device page.

### Device tracker

| Entity | Description |
|--------|-------------|
| `device_tracker.<name>_last_gps_position` | Last GPS fix stored by the device. |

### Configuration (number / select)

| Entity | Description |
|--------|-------------|
| `number.<name>_rider_weight` / `_rider_height` / `_rider_age` | Rider profile (calories). |
| `number.<name>_wheel_circumference` | Wheel circumference in mm (speed from a wheel sensor). |
| `number.<name>_bike_weight` | Bike weight (kg). |
| `select.<name>_rider_sex` | Male / female. |

The device accepts the profile but never reports it back, so these entities show
the last values Home Assistant wrote (`assumed_state`). Every write sends the whole
profile plus Home Assistant's UTC offset, which sets the device clock's time zone.

## Scope

Everything above was reverse engineered from the official iGPSPORT Ride Android
app and validated on a real iGS10S — see [`docs/PROTOCOL.md`](docs/PROTOCOL.md).
Not exposed: downloading `.fit` files, deleting activities, factory commands
(format/reset) and display settings (`CONFIG` is answered with *unsupported* by the
iGS10S firmware). Time sync is not available either — the clock comes from GPS.
The live ride attributes are raw protocol values; their units are not confirmed.

## Credits

Bluetooth library: [python-igps-ble](https://github.com/hudsonbrendon/python-igps-ble).
Author [@hudsonbrendon](https://github.com/hudsonbrendon).

## License

MIT — see [LICENSE](LICENSE).
