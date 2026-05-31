# iGPSPORT iGS10S — Recon BLE + Lib `python-igps-ble` + Integração `ha-igps-ble`

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer recon do iGPSPORT iGS10S por Bluetooth LE, confirmar empiricamente o que o dispositivo expõe, e entregar (1) uma lib Python pura e independente `python-igps-ble` que lê presença + bateria + device-info do iGS10S, e (2) uma integração Home Assistant `ha-igps-ble` que consome essa lib e expõe esses dados como entidades — com marca/ícones gerados do logo oficial iGPSPORT embutidos no próprio custom component.

**Architecture:** O iGS10S é um ciclocomputador *passivo*. O Bluetooth dele existe pra sincronizar arquivos `.fit` com o app iGPSPORT via um serviço GATT **proprietário** (não documentado publicamente). Sem quebrar esse protocolo, o que é obtível de forma confiável por BLE de terceiros é: **presença** (advertisement), **bateria** (se expuser o Battery Service padrão `0x180F`) e **device-info** (se expuser `0x180A`). Este plano é **recon-first**: as Tasks 1–4 escaneiam o aparelho real e gravam os fatos em `docs/RECON_FINDINGS.md` + `docs/PROTOCOL.md` *antes* de a lib/integração assumirem qualquer UUID. As partes puras (parsers) são TDD com fixtures autoritativos do Bluetooth SIG; a camada de I/O (bleak) usa as descobertas do recon. A sincronização proprietária de `.fit` (dados de pedalada) fica documentada como **stretch/follow-up**, fora do escopo entregável.

**Tech Stack:** Python 3.11+, [`bleak`](https://github.com/hbldh/bleak) (BLE multiplataforma), `pytest`, `pytest-asyncio`. Integração: Home Assistant (`bluetooth_adapters`, `bleak-retry-connector`). Marca: Pillow (geração das variantes de ícone). Recon: scanner do `bleak` no Mac que roda o HA; captura de tráfego app↔aparelho via Android (Developer Options → Bluetooth HCI snoop log) + Wireshark quando necessário.

**Confidence legend:** ✅ confirmado de fonte pública/padrão SIG · ⚠️ hipótese a confirmar no iGS10S real · ❓ pergunta em aberto.

### Fatos de partida (a confirmar no recon)

- ✅ O iGS10S é Bluetooth 4.0 BLE + ANT+; o BLE serve pra sync de `.fit` com o app iGPSPORT e firmware update.
- ✅ Battery Service `0x180F` / characteristic Battery Level `0x2A19` retorna **1 byte** com a porcentagem `0–100` (padrão Bluetooth SIG). Device Information Service `0x180A`: Model Number `0x2A24` e Firmware Revision `0x2A26` são strings UTF-8 (padrão SIG).
- ⚠️ Que o iGS10S realmente exponha `0x180F`/`0x180A` é hipótese — **MUST** ser confirmado na Task 2.
- ⚠️ Nome de advertisement do aparelho (`local_name`). Hipótese: começa com `iGS10S` ou `iGPSPORT`. Confirmar na Task 1, é o que casa o discovery do HA.
- ❓ Dados de pedalada (velocidade/distância/tempo) por BLE de terceiros — tratados como **fora de escopo** (precisariam quebrar o sync proprietário). Não são deliverable.

---

## File Structure

Dois repositórios git novos, espelhando o padrão dos seus pares existentes (`yn360-ble`+`yn360-homeassistant`, `mvave-tankg-ble`+`ha-mvave-tankg`, `jbl-charge5`).

### Repo 1 — `python-igps-ble` (em `/Users/hudsonbrendon/Github/python-igps-ble`)

| Arquivo | Responsabilidade |
|---------|------------------|
| `pyproject.toml` | Metadata + deps (`bleak`); extras dev (`pytest`, `pytest-asyncio`). |
| `src/igps_ble/__init__.py` | Exports públicos + `__version__`. |
| `src/igps_ble/const.py` | UUIDs SIG, prefixos de `local_name`, defaults. **Sem I/O.** |
| `src/igps_ble/models.py` | `IGPSDeviceState` (dataclass). **Sem I/O.** |
| `src/igps_ble/parser.py` | Parsers **puros**: `parse_battery_level`, `decode_device_string`. **Sem I/O.** |
| `src/igps_ble/scanner.py` | `discover_devices` via `BleakScanner` (casa por nome/serviço). Toca BLE. |
| `src/igps_ble/client.py` | `IGPSClient` async (`bleak`): conecta, lê bateria/device-info, devolve `IGPSDeviceState`. Único arquivo que conecta. |
| `src/igps_ble/__main__.py` | CLI: `scan`, `info`. |
| `tests/test_parser.py` | TDD dos parsers com fixtures SIG. |
| `tests/test_scanner.py` | TDD do scanner com `BleakScanner` mockado. |
| `tests/test_client.py` | TDD do client com `BleakClient` mockado. |
| `assets/igpsport-logo.png` | Logo oficial iGPSPORT (fonte da marca). |
| `README.md` | Doc no padrão das suas libs. |
| `.github/workflows/ci.yml` | Lint + testes. |
| `.github/workflows/publish.yml` | Publish PyPI on tag. |

### Repo 2 — `ha-igps-ble` (em `/Users/hudsonbrendon/Github/ha-igps-ble`)

| Arquivo | Responsabilidade |
|---------|------------------|
| `custom_components/igps/manifest.json` | Domínio `igps`, discovery BLE, `requirements: python-igps-ble`. |
| `custom_components/igps/const.py` | `DOMAIN`, defaults, chaves. |
| `custom_components/igps/coordinator.py` | `DataUpdateCoordinator` que usa `IGPSClient` + `bleak-retry-connector`. |
| `custom_components/igps/config_flow.py` | Bluetooth config flow (`async_step_bluetooth` + `user`). |
| `custom_components/igps/entity.py` | Base entity (device_info comum). |
| `custom_components/igps/sensor.py` | Bateria, RSSI, modelo, firmware. |
| `custom_components/igps/binary_sensor.py` | Presença/conectado. |
| `custom_components/igps/__init__.py` | Setup/unload do config entry. |
| `custom_components/igps/strings.json` | Strings UI base (inglês). |
| `custom_components/igps/translations/en.json` | EN. |
| `custom_components/igps/translations/pt-BR.json` | PT-BR. |
| `custom_components/igps/brand/icon.png` … | Ícones gerados do logo oficial (vão direto no component). |
| `hacs.json` | Metadata HACS. |
| `docs/RECON_FINDINGS.md` | **Deliverable de recon:** fatos confirmados no aparelho real. |
| `docs/PROTOCOL.md` | **Deliverable de recon:** GATT mapeado + nota do sync proprietário (stretch). |
| `docs/captures/` | Artefatos crus: `gatt_dump.txt`, notas. |
| `scripts/scan.py`, `scripts/gatt_dump.py` | Ferramentas de recon. |
| `scripts/make_brand.py` | Gera variantes de ícone do logo oficial (Pillow). |
| `assets/igpsport-logo.png` | Logo oficial (fonte). |
| `README.md` | Doc no padrão das suas integrações. |
| `.github/workflows/{hassfest,validate,tests}.yml` | CI. |
| `requirements_test.txt` | Deps de teste. |
| `pyproject.toml` | Config de teste/lint do repo da integração. |
| `tests/conftest.py`, `tests/test_config_flow.py` | TDD da integração. |

---

## FASE A — Recon no aparelho real

> Estas tasks tocam o iGS10S físico. Ligue o aparelho e deixe-o perto do Mac que roda o HA. Os UUIDs/nome confirmados aqui alimentam todas as tasks de código seguintes.

## Task 0: Skeleton do repo da lib

**Files:**
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/pyproject.toml`
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/__init__.py`
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/.gitignore`

- [ ] **Step 1: Inicializar o repo git**

Run:
```bash
mkdir -p /Users/hudsonbrendon/Github/python-igps-ble && cd /Users/hudsonbrendon/Github/python-igps-ble && git init
```
Expected: `Initialized empty Git repository in /Users/hudsonbrendon/Github/python-igps-ble/.git/`

- [ ] **Step 2: Escrever `.gitignore`**

Create `/Users/hudsonbrendon/Github/python-igps-ble/.gitignore`:
```gitignore
__pycache__/
*.pyc
.venv/
.pytest_cache/
*.egg-info/
dist/
build/
```

- [ ] **Step 3: Escrever `pyproject.toml`**

Create `/Users/hudsonbrendon/Github/python-igps-ble/pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "python-igps-ble"
version = "0.1.0"
description = "Pure-Python BLE library for the iGPSPORT iGS10S cycling computer (presence, battery, device info)"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.11"
authors = [{ name = "Hudson Brendon", email = "contato.hudsonbrendon@gmail.com" }]
dependencies = ["bleak>=0.22"]

[project.urls]
Homepage = "https://github.com/hudsonbrendon/python-igps-ble"
Issues = "https://github.com/hudsonbrendon/python-igps-ble/issues"

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "ruff>=0.5"]

[project.scripts]
igps-ble = "igps_ble.__main__:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["src"]

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

- [ ] **Step 4: Escrever o package init**

Create `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/__init__.py`:
```python
"""Pure-Python BLE library for the iGPSPORT iGS10S cycling computer."""

from .models import IGPSDeviceState

__version__ = "0.1.0"

__all__ = ["IGPSDeviceState", "__version__"]
```

- [ ] **Step 5: Criar venv e instalar**

Run:
```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
```
Expected: termina com `Successfully installed ... bleak ... pytest ...` sem erro. (O import de `models` no `__init__` ainda vai falhar até a Task 6 — tudo bem, o install não importa o pacote.)

- [ ] **Step 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && git add -A && git commit -m "chore: project skeleton with bleak + pytest"
```

---

## Task 1: Scan — descobrir nome e endereço do iGS10S

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/scripts/scan.py`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/docs/RECON_FINDINGS.md`

- [ ] **Step 1: Inicializar o repo da integração**

Run:
```bash
mkdir -p /Users/hudsonbrendon/Github/ha-igps-ble/scripts /Users/hudsonbrendon/Github/ha-igps-ble/docs/captures && cd /Users/hudsonbrendon/Github/ha-igps-ble && git init
```
Expected: `Initialized empty Git repository in /Users/hudsonbrendon/Github/ha-igps-ble/.git/`

- [ ] **Step 2: Escrever o scanner de recon**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/scripts/scan.py`:
```python
"""Recon: scan BLE e imprime tudo que parece iGPSPORT.

Uso: python scripts/scan.py [segundos]
Ligue o iGS10S e deixe perto do computador antes de rodar.
"""

import asyncio
import sys

from bleak import BleakScanner

NAME_HINTS = ("igs", "igps", "igpsport")


async def main(seconds: float) -> None:
    print(f"Escaneando por {seconds}s... (ligue o iGS10S)")
    devices = await BleakScanner.discover(timeout=seconds, return_adv=True)
    found = False
    for address, (device, adv) in devices.items():
        name = (adv.local_name or device.name or "").strip()
        low = name.lower()
        is_hint = any(h in low for h in NAME_HINTS)
        mark = "<<< POSSÍVEL iGPSPORT" if is_hint else ""
        if is_hint or name:
            found = True
            print(f"{address}  rssi={adv.rssi:>4}  name={name!r}  "
                  f"services={list(adv.service_uuids)} {mark}")
    if not found:
        print("Nada nomeado encontrado. O iGS10S pode só anunciar quando ligado/ativo.")


if __name__ == "__main__":
    secs = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    asyncio.run(main(secs))
```

- [ ] **Step 3: Rodar o scan com o aparelho ligado**

Run:
```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/python /Users/hudsonbrendon/Github/ha-igps-ble/scripts/scan.py 20
```
Expected: pelo menos uma linha marcada `<<< POSSÍVEL iGPSPORT` com um `address`, um `name` e um `rssi`. **Anote o `name` e o `address` exatos.**
Se nada aparecer: confirme que o aparelho está ligado e na tela inicial (não em standby), aproxime do Mac e rode de novo com `40`. Se mesmo assim nada, o BLE só sobe durante o pareamento — abra o app iGPSPORT no celular pra forçar o advertisement e rode o scan em paralelo.

- [ ] **Step 4: Registrar os achados**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/docs/RECON_FINDINGS.md` (preencha `<...>` com os valores reais do Step 3):
```markdown
# Recon — iGPSPORT iGS10S (BLE)

Aparelho: iGPSPORT iGS10S · Firmware exibido no menu: <ver no aparelho>
Data do recon: 2026-05-31

## Advertisement (Task 1)

| Campo | Valor observado |
|-------|-----------------|
| `local_name` | `<ex.: iGS10S>` |
| MAC / address | `<ex.: A1:B2:C3:...>` |
| RSSI típico (~30 cm) | `<ex.: -52 dBm>` |
| service_uuids no advert | `<lista ou vazio>` |
| Anuncia em standby? | `<sim/não>` |

## GATT services (Task 2) — preencher depois

## Conclusões para o discovery do HA

- `local_name` prefix para casar no manifest: `<...>`
```

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "recon: BLE scan script + advertisement findings"
```

---

## Task 2: GATT dump — confirmar Battery Service e Device Information

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/scripts/gatt_dump.py`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/docs/captures/gatt_dump.txt`
- Modify: `/Users/hudsonbrendon/Github/ha-igps-ble/docs/RECON_FINDINGS.md`

- [ ] **Step 1: Escrever o dumper de GATT**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/scripts/gatt_dump.py`:
```python
"""Recon: conecta no iGS10S e lista todos os services/characteristics.

Uso: python scripts/gatt_dump.py <ADDRESS>
"""

import asyncio
import sys

from bleak import BleakClient

# Characteristics padrão Bluetooth SIG que queremos confirmar.
READABLE_SIG = {
    "00002a19-0000-1000-8000-00805f9b34fb": "Battery Level",
    "00002a24-0000-1000-8000-00805f9b34fb": "Model Number",
    "00002a26-0000-1000-8000-00805f9b34fb": "Firmware Revision",
    "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer Name",
    "00002a27-0000-1000-8000-00805f9b34fb": "Hardware Revision",
}


async def main(address: str) -> None:
    async with BleakClient(address) as client:
        print(f"Conectado: {address}\n")
        for service in client.services:
            print(f"[service] {service.uuid}  {service.description}")
            for char in service.characteristics:
                props = ",".join(char.properties)
                line = f"  [char] {char.uuid}  ({props})  {char.description}"
                if "read" in char.properties and char.uuid in READABLE_SIG:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        line += f"  ==> {value.hex()}  ({READABLE_SIG[char.uuid]})"
                    except Exception as exc:  # noqa: BLE001 - recon, queremos ver tudo
                        line += f"  ==> erro lendo: {exc}"
                print(line)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python scripts/gatt_dump.py <ADDRESS>")
    asyncio.run(main(sys.argv[1]))
```

- [ ] **Step 2: Rodar o dump e salvar a saída**

Run (troque `<ADDRESS>` pelo da Task 1):
```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/python /Users/hudsonbrendon/Github/ha-igps-ble/scripts/gatt_dump.py <ADDRESS> | tee /Users/hudsonbrendon/Github/ha-igps-ble/docs/captures/gatt_dump.txt
```
Expected: lista de `[service]`/`[char]`. **Procure especificamente:**
- `0000180f-...` (Battery Service) com char `00002a19-...` → linha com `==> XX (Battery Level)`, onde `XX` em hex convertido pra decimal = a % de bateria mostrada no aparelho.
- `0000180a-...` (Device Information) com `00002a24` (Model) e `00002a26` (Firmware).
- Um ou mais serviços com UUID **não-SIG** (ex.: base `0000xxxx-...` proprietária ou UUID 128-bit custom) → esse é o canal de sync proprietário (anote, mas **não** é escopo deste plano).

- [ ] **Step 3: Confirmar a leitura de bateria contra o aparelho**

Olhe a % de bateria no menu do iGS10S e compare com o byte lido (`int(hex, 16)`). Devem bater (±1).
Expected: ex. aparelho mostra `87%`, char `2a19` retornou `57` hex = `87` decimal. ✅
Se o iGS10S **não** expõe `0x180f`/`0x2a19`: registre isso — a lib vai reportar `battery_level=None` e o sensor de bateria fica indisponível; o resto (presença, RSSI) continua valendo.

- [ ] **Step 4: Preencher o RECON_FINDINGS**

Edite `/Users/hudsonbrendon/Github/ha-igps-ble/docs/RECON_FINDINGS.md`, seção "GATT services (Task 2)", com uma tabela: UUID | tipo (SIG/custom) | properties | valor lido | nota. Marque explicitamente se `0x180F` e `0x180A` existem (✅/❌) e qual UUID é o serviço proprietário de sync.

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "recon: GATT dump + confirm standard battery/device-info services"
```

---

## Task 3: Documentar o protocolo (deliverable de recon)

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/docs/PROTOCOL.md`

- [ ] **Step 1: Escrever o PROTOCOL.md**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/docs/PROTOCOL.md` (preencha conforme o recon real; o template abaixo já traz o que é padrão SIG):
```markdown
# iGPSPORT iGS10S — Protocolo BLE (escopo de terceiros)

> Verificado empiricamente em 2026-05-31. Ver `RECON_FINDINGS.md` para os valores crus.

## Em escopo (lido por terceiros sem app oficial)

### Battery Service — `0000180f-0000-1000-8000-00805f9b34fb`  [confirmado: ✅/❌]
- Battery Level — `00002a19-0000-1000-8000-00805f9b34fb`
- Leitura: **1 byte**, uint8, `0–100` = porcentagem. `read` (e às vezes `notify`).

### Device Information Service — `0000180a-0000-1000-8000-00805f9b34fb`  [confirmado: ✅/❌]
- Model Number — `00002a24-...` — string UTF-8.
- Firmware Revision — `00002a26-...` — string UTF-8.
- Manufacturer Name — `00002a29-...` — string UTF-8 (provável `iGPSPORT`).

### Presença
- Derivada do advertisement BLE (`local_name` = `<...>`). O HA trata "visto recentemente" como presente.

## Fora de escopo (sync proprietário — STRETCH / follow-up)

- Serviço custom `<UUID do recon>` carrega o sync de `.fit` e config do app iGPSPORT.
- Framing/handshake desconhecidos; sem docs públicas nem RE conhecido (busca em 2026-05).
- Para um dia obter dados de pedalada: capturar tráfego app↔aparelho (Android HCI snoop log + Wireshark), reverter o framing, e só então estender a lib. **Não faz parte deste plano.**
```

- [ ] **Step 2: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "docs: BLE protocol spec (in-scope vs proprietary sync)"
```

---

## FASE B — Lib `python-igps-ble` (TDD)

## Task 4: Constantes e modelo de estado

**Files:**
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/const.py`
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/models.py`

- [ ] **Step 1: Escrever as constantes**

Create `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/const.py`:
```python
"""UUIDs Bluetooth SIG e defaults do iGPSPORT iGS10S.

UUIDs confirmados no recon (docs/RECON_FINDINGS.md). Ajuste NAME_PREFIXES
para o local_name exato observado na Task 1.
"""

# Battery Service / characteristic (Bluetooth SIG).
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

# Device Information Service / characteristics (Bluetooth SIG).
DEVICE_INFO_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
FIRMWARE_REVISION_UUID = "00002a26-0000-1000-8000-00805f9b34fb"
MANUFACTURER_NAME_UUID = "00002a29-0000-1000-8000-00805f9b34fb"

# Prefixos de local_name usados pra reconhecer o aparelho no advertisement.
# Confirme/ajuste com o que a Task 1 observou.
NAME_PREFIXES = ("iGS10S", "iGPSPORT", "iGS")

MANUFACTURER = "iGPSPORT"
DEFAULT_MODEL = "iGS10S"
```

- [ ] **Step 2: Escrever o modelo de estado**

Create `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/models.py`:
```python
"""Modelo imutável do estado lido do iGS10S."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IGPSDeviceState:
    """Snapshot do que a lib conseguiu ler do aparelho.

    Campos opcionais ficam None quando o aparelho não expõe a characteristic
    correspondente (ex.: sem Battery Service => battery_level None).
    """

    address: str
    name: str
    rssi: int | None = None
    battery_level: int | None = None
    model: str | None = None
    firmware: str | None = None
    manufacturer: str | None = None
```

- [ ] **Step 3: Commit**

```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && git add -A && git commit -m "feat: SIG UUID constants and IGPSDeviceState model"
```

---

## Task 5: Parsers puros (TDD)

**Files:**
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/parser.py`
- Test: `/Users/hudsonbrendon/Github/python-igps-ble/tests/test_parser.py`

- [ ] **Step 1: Escrever o teste que falha**

Create `/Users/hudsonbrendon/Github/python-igps-ble/tests/test_parser.py`:
```python
import pytest

from igps_ble.parser import decode_device_string, parse_battery_level


def test_battery_level_reads_single_byte_percent():
    # Padrão SIG 0x2A19: 1 byte uint8 = porcentagem. 0x57 = 87%.
    assert parse_battery_level(bytes([0x57])) == 87


def test_battery_level_zero_and_full():
    assert parse_battery_level(bytes([0x00])) == 0
    assert parse_battery_level(bytes([0x64])) == 100


def test_battery_level_empty_returns_none():
    assert parse_battery_level(b"") is None


def test_battery_level_out_of_range_clamped():
    # Alguns aparelhos devolvem 0xFF ("desconhecido"); tratamos como None.
    assert parse_battery_level(bytes([0xFF])) is None


def test_decode_device_string_strips_nul_and_whitespace():
    # Strings do Device Info vêm UTF-8, às vezes com NUL de padding.
    assert decode_device_string(b"iGS10S\x00") == "iGS10S"
    assert decode_device_string(b"  V1.20 \x00") == "V1.20"


def test_decode_device_string_empty_returns_none():
    assert decode_device_string(b"") is None
    assert decode_device_string(b"\x00\x00") is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/pytest tests/test_parser.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'igps_ble.parser'`

- [ ] **Step 3: Implementar o mínimo**

Create `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/parser.py`:
```python
"""Parsers puros (sem I/O) para os bytes das characteristics SIG."""

from __future__ import annotations


def parse_battery_level(data: bytes) -> int | None:
    """Battery Level (0x2A19): 1 byte uint8, 0..100. None se ausente/inválido."""
    if not data:
        return None
    value = data[0]
    if value > 100:
        return None
    return value


def decode_device_string(data: bytes) -> str | None:
    """Device Information string UTF-8; remove NUL de padding e espaços."""
    if not data:
        return None
    text = data.decode("utf-8", errors="replace").replace("\x00", "").strip()
    return text or None
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/pytest tests/test_parser.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && git add -A && git commit -m "feat: pure parsers for battery level and device-info strings"
```

---

## Task 6: Scanner (TDD com BleakScanner mockado)

**Files:**
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/scanner.py`
- Test: `/Users/hudsonbrendon/Github/python-igps-ble/tests/test_scanner.py`

- [ ] **Step 1: Escrever o teste que falha**

Create `/Users/hudsonbrendon/Github/python-igps-ble/tests/test_scanner.py`:
```python
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from igps_ble.scanner import discover_devices, is_igps_device


def _adv(local_name, rssi=-50, service_uuids=None):
    return SimpleNamespace(
        local_name=local_name, rssi=rssi, service_uuids=service_uuids or []
    )


def test_is_igps_device_matches_known_prefixes():
    assert is_igps_device("iGS10S") is True
    assert is_igps_device("iGPSPORT iGS10S") is True
    assert is_igps_device("iGS520") is True


def test_is_igps_device_rejects_others():
    assert is_igps_device("JBL Charge 5") is False
    assert is_igps_device("") is False
    assert is_igps_device(None) is False


@pytest.mark.asyncio
async def test_discover_devices_filters_and_maps():
    bledev = SimpleNamespace(address="AA:BB:CC:DD:EE:FF", name="iGS10S")
    other = SimpleNamespace(address="11:22:33:44:55:66", name="TV")
    discovered = {
        "AA:BB:CC:DD:EE:FF": (bledev, _adv("iGS10S", rssi=-44)),
        "11:22:33:44:55:66": (other, _adv("TV", rssi=-70)),
    }
    with patch(
        "igps_ble.scanner.BleakScanner.discover",
        new=AsyncMock(return_value=discovered),
    ):
        results = await discover_devices(timeout=1.0)

    assert len(results) == 1
    state = results[0]
    assert state.address == "AA:BB:CC:DD:EE:FF"
    assert state.name == "iGS10S"
    assert state.rssi == -44
    assert state.battery_level is None  # scan não conecta
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/pytest tests/test_scanner.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'igps_ble.scanner'`

- [ ] **Step 3: Implementar o mínimo**

Create `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/scanner.py`:
```python
"""Descoberta BLE do iGS10S (toca o adaptador Bluetooth)."""

from __future__ import annotations

from bleak import BleakScanner

from .const import NAME_PREFIXES
from .models import IGPSDeviceState


def is_igps_device(local_name: str | None) -> bool:
    """True se o nome de advertisement bate com um prefixo conhecido do iGPSPORT."""
    if not local_name:
        return False
    return any(local_name.startswith(prefix) for prefix in NAME_PREFIXES)


async def discover_devices(timeout: float = 10.0) -> list[IGPSDeviceState]:
    """Escaneia e devolve um IGPSDeviceState por aparelho iGPSPORT visto.

    Não conecta — campos de bateria/device-info ficam None aqui.
    """
    discovered = await BleakScanner.discover(timeout=timeout, return_adv=True)
    results: list[IGPSDeviceState] = []
    for address, (device, adv) in discovered.items():
        name = adv.local_name or device.name
        if not is_igps_device(name):
            continue
        results.append(
            IGPSDeviceState(address=address, name=name, rssi=adv.rssi)
        )
    return results
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/pytest tests/test_scanner.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && git add -A && git commit -m "feat: BLE scanner with iGPSPORT name matching"
```

---

## Task 7: Client async (TDD com BleakClient mockado)

**Files:**
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/client.py`
- Test: `/Users/hudsonbrendon/Github/python-igps-ble/tests/test_client.py`

- [ ] **Step 1: Escrever o teste que falha**

Create `/Users/hudsonbrendon/Github/python-igps-ble/tests/test_client.py`:
```python
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from igps_ble.client import IGPSClient
from igps_ble.const import (
    BATTERY_LEVEL_UUID,
    FIRMWARE_REVISION_UUID,
    MANUFACTURER_NAME_UUID,
    MODEL_NUMBER_UUID,
)


def _fake_bleak_client():
    """BleakClient mock: services presentes, reads roteados por UUID."""
    reads = {
        BATTERY_LEVEL_UUID: bytes([0x57]),  # 87%
        MODEL_NUMBER_UUID: b"iGS10S\x00",
        FIRMWARE_REVISION_UUID: b"V1.20",
        MANUFACTURER_NAME_UUID: b"iGPSPORT",
    }

    async def read_gatt_char(uuid):
        if uuid not in reads:
            raise KeyError(uuid)
        return reads[uuid]

    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.read_gatt_char = AsyncMock(side_effect=read_gatt_char)
    # services com os UUIDs disponíveis (para has_char).
    services = MagicMock()
    services.get_characteristic = lambda uuid: object() if uuid in reads else None
    client.services = services
    return client


@pytest.mark.asyncio
async def test_read_state_populates_all_fields():
    fake = _fake_bleak_client()
    with patch("igps_ble.client.BleakClient", return_value=fake):
        client = IGPSClient("AA:BB:CC:DD:EE:FF", name="iGS10S", rssi=-44)
        state = await client.async_read_state()

    assert state.battery_level == 87
    assert state.model == "iGS10S"
    assert state.firmware == "V1.20"
    assert state.manufacturer == "iGPSPORT"
    assert state.rssi == -44


@pytest.mark.asyncio
async def test_read_state_missing_battery_is_none():
    fake = _fake_bleak_client()
    fake.services.get_characteristic = lambda uuid: (
        None if uuid == BATTERY_LEVEL_UUID else object()
    )
    with patch("igps_ble.client.BleakClient", return_value=fake):
        client = IGPSClient("AA:BB:CC:DD:EE:FF", name="iGS10S")
        state = await client.async_read_state()

    assert state.battery_level is None
    assert state.model == "iGS10S"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/pytest tests/test_client.py -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'igps_ble.client'`

- [ ] **Step 3: Implementar o mínimo**

Create `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/client.py`:
```python
"""Client async que conecta no iGS10S e lê as characteristics em escopo.

Único módulo que abre conexão BLE. Aceita um BleakClient já criado (ou um
BLEDevice) — útil pra reaproveitar a conexão do bleak-retry-connector no HA.
"""

from __future__ import annotations

from bleak import BleakClient

from .const import (
    BATTERY_LEVEL_UUID,
    FIRMWARE_REVISION_UUID,
    MANUFACTURER_NAME_UUID,
    MODEL_NUMBER_UUID,
)
from .models import IGPSDeviceState
from .parser import decode_device_string, parse_battery_level


class IGPSClient:
    """Lê presença/bateria/device-info de um iGS10S via BLE."""

    def __init__(
        self, address: str, name: str = "iGS10S", rssi: int | None = None
    ) -> None:
        self._address = address
        self._name = name
        self._rssi = rssi

    async def async_read_state(self) -> IGPSDeviceState:
        """Conecta, lê o que o aparelho expõe, e devolve o snapshot."""
        async with BleakClient(self._address) as client:
            battery = await self._read(client, BATTERY_LEVEL_UUID)
            model = await self._read(client, MODEL_NUMBER_UUID)
            firmware = await self._read(client, FIRMWARE_REVISION_UUID)
            manufacturer = await self._read(client, MANUFACTURER_NAME_UUID)

        return IGPSDeviceState(
            address=self._address,
            name=self._name,
            rssi=self._rssi,
            battery_level=parse_battery_level(battery) if battery is not None else None,
            model=decode_device_string(model) if model is not None else None,
            firmware=decode_device_string(firmware) if firmware is not None else None,
            manufacturer=(
                decode_device_string(manufacturer)
                if manufacturer is not None
                else None
            ),
        )

    @staticmethod
    async def _read(client: BleakClient, uuid: str) -> bytes | None:
        """Lê a char se ela existir; None se o aparelho não a expõe."""
        if client.services.get_characteristic(uuid) is None:
            return None
        try:
            return await client.read_gatt_char(uuid)
        except Exception:  # noqa: BLE001 - char some/erra => trata como ausente
            return None
```

- [ ] **Step 4: Rodar e ver passar**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/pytest tests/test_client.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && git add -A && git commit -m "feat: async IGPSClient reading battery + device-info over BLE"
```

---

## Task 8: CLI da lib

**Files:**
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/__main__.py`

- [ ] **Step 1: Escrever a CLI**

Create `/Users/hudsonbrendon/Github/python-igps-ble/src/igps_ble/__main__.py`:
```python
"""CLI: `igps-ble scan` e `igps-ble info <ADDRESS>`."""

from __future__ import annotations

import argparse
import asyncio

from .client import IGPSClient
from .scanner import discover_devices


async def _scan(timeout: float) -> None:
    devices = await discover_devices(timeout=timeout)
    if not devices:
        print("Nenhum iGPSPORT encontrado. Ligue o aparelho e aproxime.")
        return
    for d in devices:
        print(f"{d.address}  rssi={d.rssi}  name={d.name}")


async def _info(address: str) -> None:
    state = await IGPSClient(address).async_read_state()
    print(f"Endereço:     {state.address}")
    print(f"Modelo:       {state.model}")
    print(f"Firmware:     {state.firmware}")
    print(f"Fabricante:   {state.manufacturer}")
    print(f"Bateria:      {state.battery_level}%")


def main() -> None:
    parser = argparse.ArgumentParser(prog="igps-ble")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_scan = sub.add_parser("scan", help="Procura aparelhos iGPSPORT por perto")
    p_scan.add_argument("--timeout", type=float, default=10.0)
    p_info = sub.add_parser("info", help="Conecta e lê bateria/device-info")
    p_info.add_argument("address")

    args = parser.parse_args()
    if args.cmd == "scan":
        asyncio.run(_scan(args.timeout))
    elif args.cmd == "info":
        asyncio.run(_info(args.address))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test da CLI (sem aparelho)**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/igps-ble scan --timeout 3`
Expected: roda sem stacktrace; imprime aparelhos ou "Nenhum iGPSPORT encontrado." (Com o iGS10S ligado, deve listar o endereço real; valide `igps-ble info <ADDRESS>` contra a % no aparelho.)

- [ ] **Step 3: Commit**

```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && git add -A && git commit -m "feat: igps-ble CLI (scan, info)"
```

---

## Task 9: README + CI da lib

**Files:**
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/README.md`
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/.github/workflows/ci.yml`
- Create: `/Users/hudsonbrendon/Github/python-igps-ble/.github/workflows/publish.yml`

- [ ] **Step 1: Escrever o README**

Create `/Users/hudsonbrendon/Github/python-igps-ble/README.md`:
```markdown
# python-igps-ble

Pure-Python BLE library for the **iGPSPORT iGS10S** cycling computer.

Reads, over standard Bluetooth Low Energy, what the device exposes to
third parties: **presence**, **battery level**, and **device info**
(model / firmware / manufacturer). The proprietary `.fit` sync used by the
official iGPSPORT app is **out of scope** (see `ha-igps-ble/docs/PROTOCOL.md`).

> Built to back the [`ha-igps-ble`](https://github.com/hudsonbrendon/ha-igps-ble)
> Home Assistant integration, but usable standalone.

## Install

```bash
pip install python-igps-ble
```

## CLI

```bash
igps-ble scan                 # procura aparelhos iGPSPORT por perto
igps-ble info AA:BB:CC:DD:EE:FF   # bateria + device-info
```

## Uso programático

```python
import asyncio
from igps_ble import IGPSDeviceState
from igps_ble.scanner import discover_devices
from igps_ble.client import IGPSClient

async def main():
    for dev in await discover_devices(timeout=10):
        state: IGPSDeviceState = await IGPSClient(dev.address, dev.name).async_read_state()
        print(state)

asyncio.run(main())
```

## Escopo

| Dado | Suportado | Fonte |
|------|-----------|-------|
| Presença | ✅ | advertisement BLE |
| Bateria % | ✅* | Battery Service `0x180F` |
| Modelo / firmware | ✅* | Device Information `0x180A` |
| Velocidade / distância / pedalada | ❌ | sync proprietário (não exposto por BLE) |

\* depende de o iGS10S expor o serviço SIG correspondente — confirmado por recon.

## Desenvolvimento

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

## Licença

MIT
```

- [ ] **Step 2: Escrever o CI**

Create `/Users/hudsonbrendon/Github/python-igps-ble/.github/workflows/ci.yml`:
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest -v
```

- [ ] **Step 3: Escrever o publish**

Create `/Users/hudsonbrendon/Github/python-igps-ble/.github/workflows/publish.yml`:
```yaml
name: Publish
on:
  release:
    types: [published]
jobs:
  pypi:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 4: Rodar a suíte completa + lint**

Run: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/ruff check . && .venv/bin/pytest -v`
Expected: `ruff` sem erros; pytest `12 passed`.

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && git add -A && git commit -m "docs: README; ci: test matrix + PyPI publish workflow"
```

---

## FASE C — Marca / ícones (do logo oficial iGPSPORT)

> O HA brands repo não está aceitando PRs, então os ícones vão **direto no custom component**, em `custom_components/igps/brand/`, no mesmo conjunto de arquivos que `jbl-charge5` usa.

## Task 10: Obter o logo oficial e gerar as variantes

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/assets/igpsport-logo.png`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/scripts/make_brand.py`
- Create: `custom_components/igps/brand/{icon,icon@2x,logo,logo@2x,dark_icon,dark_icon@2x,dark_logo,dark_logo@2x}.png`

- [ ] **Step 1: Baixar o logo oficial iGPSPORT**

Pegue o logo oficial do site iGPSPORT (`https://www.igpsport.com/` — header/branding) ou da página do produto. Salve a maior versão PNG com fundo transparente em:
`/Users/hudsonbrendon/Github/ha-igps-ble/assets/igpsport-logo.png`

Verifique:
```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/python -c "from PIL import Image; im=Image.open('/Users/hudsonbrendon/Github/ha-igps-ble/assets/igpsport-logo.png'); print(im.size, im.mode)"
```
Expected: imprime as dimensões e modo (idealmente `RGBA`). Se não for `RGBA`, escolha outra fonte com transparência.
(Se não houver Pillow no venv: `cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/pip install pillow`.)

- [ ] **Step 2: Escrever o gerador de marca**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/scripts/make_brand.py`:
```python
"""Gera os ícones/logos do brand do HA a partir do logo oficial iGPSPORT.

Especificação HA brands:
- icon: quadrado, 256x256 (icon.png) e 512x512 (icon@2x.png).
- logo: largura até 512 (logo.png) / 1024 (logo@2x.png), altura proporcional.
- variantes dark_*: mesmas dimensões, para temas escuros.

Uso: python scripts/make_brand.py assets/igpsport-logo.png custom_components/igps/brand
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def _square(img: Image.Image, size: int) -> Image.Image:
    """Encaixa o logo num canvas quadrado transparente, centralizado."""
    src = img.copy()
    src.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(src, ((size - src.width) // 2, (size - src.height) // 2), src)
    return canvas


def _wide(img: Image.Image, width: int) -> Image.Image:
    """Redimensiona mantendo proporção para a largura alvo."""
    ratio = width / img.width
    return img.resize((width, max(1, round(img.height * ratio))), Image.LANCZOS)


def _dark_variant(img: Image.Image) -> Image.Image:
    """Versão para fundo escuro: inverte luminância preservando alpha.

    Para logos coloridos, troque esta função por uma arte clara dedicada.
    """
    r, g, b, a = img.split()
    rgb = Image.merge("RGB", (r, g, b))
    from PIL import ImageOps

    inverted = ImageOps.invert(rgb)
    ir, ig, ib = inverted.split()
    return Image.merge("RGBA", (ir, ig, ib, a))


def main(src_path: str, out_dir: str) -> None:
    src = Image.open(src_path).convert("RGBA")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    _square(src, 256).save(out / "icon.png")
    _square(src, 512).save(out / "icon@2x.png")
    _wide(src, 512).save(out / "logo.png")
    _wide(src, 1024).save(out / "logo@2x.png")

    dark = _dark_variant(src)
    _square(dark, 256).save(out / "dark_icon.png")
    _square(dark, 512).save(out / "dark_icon@2x.png")
    _wide(dark, 512).save(out / "dark_logo.png")
    _wide(dark, 1024).save(out / "dark_logo@2x.png")

    print(f"Gerado em {out}:")
    for f in sorted(out.glob("*.png")):
        print(" -", f.name, Image.open(f).size)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python scripts/make_brand.py <logo.png> <out_dir>")
    main(sys.argv[1], sys.argv[2])
```

- [ ] **Step 3: Gerar os ícones**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && /Users/hudsonbrendon/Github/python-igps-ble/.venv/bin/python scripts/make_brand.py assets/igpsport-logo.png custom_components/igps/brand
```
Expected: lista os 8 PNGs com tamanhos `icon.png (256, 256)`, `icon@2x.png (512, 512)`, `logo.png (512, H)`, `logo@2x.png (1024, H)` e as 4 variantes `dark_*`.

- [ ] **Step 4: Conferir visualmente**

Abra `custom_components/igps/brand/icon.png` e `dark_icon.png`. O ícone deve ficar legível em fundo claro e escuro. Se a inversão automática ficar ruim (logo colorido), substitua `dark_*` por uma arte clara feita à mão com as mesmas dimensões.

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "brand: generate HA icons/logos from official iGPSPORT logo"
```

---

## FASE D — Integração `ha-igps-ble`

## Task 11: Manifest, const e hacs.json

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/manifest.json`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/const.py`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/hacs.json`

- [ ] **Step 1: Escrever o manifest**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/manifest.json` (troque o `local_name` pelo confirmado na Task 1; ordem de chaves alfabética exigida pelo hassfest):
```json
{
  "domain": "igps",
  "name": "iGPSPORT iGS10S",
  "bluetooth": [
    { "local_name": "iGS10S*" },
    { "local_name": "iGPSPORT*" }
  ],
  "codeowners": ["@hudsonbrendon"],
  "config_flow": true,
  "dependencies": ["bluetooth_adapters"],
  "documentation": "https://github.com/hudsonbrendon/ha-igps-ble",
  "integration_type": "device",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/hudsonbrendon/ha-igps-ble/issues",
  "requirements": ["python-igps-ble>=0.1.0", "bleak-retry-connector>=3.5.0"],
  "version": "0.1.0"
}
```

- [ ] **Step 2: Escrever o const**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/const.py`:
```python
"""Constantes da integração iGPSPORT iGS10S."""

from datetime import timedelta

DOMAIN = "igps"
MANUFACTURER = "iGPSPORT"
DEFAULT_MODEL = "iGS10S"

# Polling ativo (conecta pra ler bateria/device-info). O aparelho é passivo
# e pode estar fora de alcance/desligado boa parte do tempo, então o intervalo
# é folgado pra não brigar pelo rádio.
UPDATE_INTERVAL = timedelta(minutes=10)

# Quanto tempo sem advertisement antes de considerar "ausente".
PRESENCE_TIMEOUT = timedelta(minutes=5)
```

- [ ] **Step 3: Escrever o hacs.json**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/hacs.json`:
```json
{
  "name": "iGPSPORT iGS10S",
  "render_readme": true,
  "homeassistant": "2024.6.0"
}
```

- [ ] **Step 4: Validar JSON**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && python3 -c "import json; json.load(open('custom_components/igps/manifest.json')); json.load(open('hacs.json')); print('JSON ok')"
```
Expected: `JSON ok`

- [ ] **Step 5: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "feat: integration manifest, const, hacs metadata"
```

---

## Task 12: Coordinator

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/coordinator.py`

- [ ] **Step 1: Escrever o coordinator**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/coordinator.py`:
```python
"""DataUpdateCoordinator: lê o iGS10S via python-igps-ble + bleak-retry-connector."""

from __future__ import annotations

import logging

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
from habluetooth import BluetoothServiceInfoBleak
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from igps_ble.const import (
    BATTERY_LEVEL_UUID,
    FIRMWARE_REVISION_UUID,
    MANUFACTURER_NAME_UUID,
    MODEL_NUMBER_UUID,
)
from igps_ble.models import IGPSDeviceState
from igps_ble.parser import decode_device_string, parse_battery_level

from .const import DEFAULT_MODEL, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class IGPSCoordinator(DataUpdateCoordinator[IGPSDeviceState]):
    """Conecta no aparelho periodicamente e publica o snapshot."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, address: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{address}",
            update_interval=UPDATE_INTERVAL,
        )
        self._entry = entry
        self.address = address

    @property
    def _service_info(self) -> BluetoothServiceInfoBleak | None:
        return bluetooth.async_last_service_info(
            self.hass, self.address, connectable=True
        )

    async def _async_update_data(self) -> IGPSDeviceState:
        service_info = self._service_info
        if service_info is None:
            raise UpdateFailed(f"iGS10S {self.address} fora de alcance")

        ble_device = service_info.device

        async def _read(client, uuid):
            if client.services.get_characteristic(uuid) is None:
                return None
            try:
                return await client.read_gatt_char(uuid)
            except Exception:  # noqa: BLE001
                return None

        client = await establish_connection(
            BleakClientWithServiceCache, ble_device, self.address
        )
        try:
            battery = await _read(client, BATTERY_LEVEL_UUID)
            model = await _read(client, MODEL_NUMBER_UUID)
            firmware = await _read(client, FIRMWARE_REVISION_UUID)
            manufacturer = await _read(client, MANUFACTURER_NAME_UUID)
        finally:
            await client.disconnect()

        return IGPSDeviceState(
            address=self.address,
            name=service_info.name,
            rssi=service_info.rssi,
            battery_level=parse_battery_level(battery) if battery else None,
            model=decode_device_string(model) if model else DEFAULT_MODEL,
            firmware=decode_device_string(firmware) if firmware else None,
            manufacturer=decode_device_string(manufacturer) if manufacturer else None,
        )
```

- [ ] **Step 2: Checagem de sintaxe**

Run: `cd /Users/hudsonbrendon/Github/ha-igps-ble && python3 -m py_compile custom_components/igps/coordinator.py && echo OK`
Expected: `OK` (imports de HA não resolvem fora do runtime — `py_compile` só valida sintaxe).

- [ ] **Step 3: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "feat: coordinator using bleak-retry-connector + python-igps-ble"
```

---

## Task 13: Config flow (TDD)

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/config_flow.py`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/requirements_test.txt`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/pyproject.toml`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/tests/conftest.py`
- Test: `/Users/hudsonbrendon/Github/ha-igps-ble/tests/test_config_flow.py`

- [ ] **Step 1: Escrever as deps de teste e config de pytest**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/requirements_test.txt`:
```text
homeassistant>=2024.6.0
pytest-homeassistant-custom-component
python-igps-ble>=0.1.0
bleak-retry-connector>=3.5.0
```

Create `/Users/hudsonbrendon/Github/ha-igps-ble/pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

Create `/Users/hudsonbrendon/Github/ha-igps-ble/tests/conftest.py`:
```python
"""Fixtures de teste da integração."""

import pytest
from homeassistant.helpers.service_info.bluetooth import BluetoothServiceInfo

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
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
```

- [ ] **Step 2: Escrever o teste que falha**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/tests/test_config_flow.py`:
```python
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.igps.const import DOMAIN


async def test_bluetooth_discovery_creates_entry(
    hass: HomeAssistant, igs10s_service_info
):
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=igs10s_service_info,
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "iGS10S"
    assert result2["result"].unique_id == "AA:BB:CC:DD:EE:FF"


async def test_user_flow_aborts_when_no_devices(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"
```

- [ ] **Step 3: Rodar e ver falhar**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && python3 -m venv .venv-ha && .venv-ha/bin/pip install -r requirements_test.txt && .venv-ha/bin/pytest tests/test_config_flow.py -v
```
Expected: FAIL com `ModuleNotFoundError: No module named 'custom_components.igps.config_flow'` (ou erro de import do DOMAIN).

- [ ] **Step 4: Implementar o config flow**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/config_flow.py`:
```python
"""Config flow: descoberta Bluetooth + passo manual."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from igps_ble.scanner import is_igps_device

from .const import DOMAIN


class IGPSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Fluxo de configuração do iGS10S."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None
        self._discovered_name: str | None = None
        self._discovered: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Disparado quando o HA vê um advertisement que casa o manifest."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovered_address = discovery_info.address
        self._discovered_name = discovery_info.name
        self.context["title_placeholders"] = {"name": discovery_info.name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name or "iGPSPORT iGS10S",
                data={"address": self._discovered_address},
            )
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._discovered_name or "iGS10S"},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Seleção manual a partir dos aparelhos vistos pelo HA."""
        if user_input is not None:
            address = user_input["address"]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered.get(address, "iGPSPORT iGS10S"),
                data={"address": address},
            )

        current = self._async_current_ids()
        for info in async_discovered_service_info(self.hass):
            if (
                info.address not in current
                and info.address not in self._discovered
                and is_igps_device(info.name)
            ):
                self._discovered[info.address] = info.name

        if not self._discovered:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("address"): vol.In(self._discovered)}
            ),
        )
```

- [ ] **Step 5: Rodar e ver passar**

Run: `cd /Users/hudsonbrendon/Github/ha-igps-ble && .venv-ha/bin/pytest tests/test_config_flow.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "feat: bluetooth config flow (TDD)"
```

---

## Task 14: Entity base + `__init__` (setup/unload)

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/entity.py`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/__init__.py`

- [ ] **Step 1: Escrever a entity base**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/entity.py`:
```python
"""Base de entidade com device_info compartilhado."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import IGPSCoordinator


class IGPSEntity(CoordinatorEntity[IGPSCoordinator]):
    """Entidade base ligada ao coordinator do iGS10S."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IGPSCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        state = self.coordinator.data
        return DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, self.coordinator.address)},
            identifiers={(DOMAIN, self.coordinator.address)},
            manufacturer=MANUFACTURER,
            model=(state.model if state else None) or DEFAULT_MODEL,
            name=(state.name if state else None) or DEFAULT_MODEL,
            sw_version=state.firmware if state else None,
        )
```

- [ ] **Step 2: Escrever o `__init__`**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/__init__.py`:
```python
"""Integração iGPSPORT iGS10S (BLE)."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import IGPSCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

type IGPSConfigEntry = ConfigEntry[IGPSCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: IGPSConfigEntry) -> bool:
    address = entry.data["address"]
    coordinator = IGPSCoordinator(hass, entry, address)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IGPSConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
```

- [ ] **Step 3: Checagem de sintaxe**

Run: `cd /Users/hudsonbrendon/Github/ha-igps-ble && python3 -m py_compile custom_components/igps/entity.py custom_components/igps/__init__.py && echo OK`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "feat: base entity + config entry setup/unload"
```

---

## Task 15: Sensores (bateria, RSSI, modelo, firmware)

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/sensor.py`

- [ ] **Step 1: Escrever os sensores**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/sensor.py`:
```python
"""Sensores do iGS10S: bateria, RSSI, modelo, firmware."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from igps_ble.models import IGPSDeviceState

from . import IGPSConfigEntry
from .entity import IGPSEntity


@dataclass(frozen=True, kw_only=True)
class IGPSSensorDescription(SensorEntityDescription):
    value_fn: Callable[[IGPSDeviceState], int | str | None]


SENSORS: tuple[IGPSSensorDescription, ...] = (
    IGPSSensorDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.battery_level,
    ),
    IGPSSensorDescription(
        key="rssi",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.rssi,
    ),
    IGPSSensorDescription(
        key="model",
        translation_key="model",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.model,
    ),
    IGPSSensorDescription(
        key="firmware",
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.firmware,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(IGPSSensor(coordinator, desc) for desc in SENSORS)


class IGPSSensor(IGPSEntity, SensorEntity):
    entity_description: IGPSSensorDescription

    def __init__(self, coordinator, description: IGPSSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> int | str | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
```

- [ ] **Step 2: Checagem de sintaxe**

Run: `cd /Users/hudsonbrendon/Github/ha-igps-ble && python3 -m py_compile custom_components/igps/sensor.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "feat: battery, rssi, model, firmware sensors"
```

---

## Task 16: Binary sensor de presença

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/binary_sensor.py`

- [ ] **Step 1: Escrever o binary sensor**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/binary_sensor.py`:
```python
"""Binary sensor de presença: o iGS10S foi visto por BLE recentemente?"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import IGPSConfigEntry
from .entity import IGPSEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IGPSConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([IGPSPresenceSensor(entry.runtime_data)])


class IGPSPresenceSensor(IGPSEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "presence"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "presence")

    @property
    def is_on(self) -> bool:
        """True se o HA tem um advertisement recente e conectável do aparelho."""
        return (
            bluetooth.async_last_service_info(
                self.hass, self.coordinator.address, connectable=True
            )
            is not None
        )
```

- [ ] **Step 2: Checagem de sintaxe**

Run: `cd /Users/hudsonbrendon/Github/ha-igps-ble && python3 -m py_compile custom_components/igps/binary_sensor.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "feat: presence binary sensor"
```

---

## Task 17: Strings e traduções (EN + PT-BR)

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/strings.json`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/translations/en.json`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/translations/pt-BR.json`

- [ ] **Step 1: Escrever strings.json**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/strings.json`:
```json
{
  "config": {
    "flow_title": "{name}",
    "step": {
      "bluetooth_confirm": {
        "description": "Configurar o {name}?"
      },
      "user": {
        "data": { "address": "Dispositivo" }
      }
    },
    "abort": {
      "no_devices_found": "Nenhum iGPSPORT encontrado por perto",
      "already_configured": "Este dispositivo já está configurado"
    }
  },
  "entity": {
    "binary_sensor": {
      "presence": { "name": "Presença" }
    },
    "sensor": {
      "rssi": { "name": "Sinal" },
      "model": { "name": "Modelo" },
      "firmware": { "name": "Firmware" }
    }
  }
}
```

- [ ] **Step 2: Escrever en.json (cópia inglês)**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/translations/en.json`:
```json
{
  "config": {
    "flow_title": "{name}",
    "step": {
      "bluetooth_confirm": {
        "description": "Set up {name}?"
      },
      "user": {
        "data": { "address": "Device" }
      }
    },
    "abort": {
      "no_devices_found": "No iGPSPORT devices found nearby",
      "already_configured": "This device is already configured"
    }
  },
  "entity": {
    "binary_sensor": {
      "presence": { "name": "Presence" }
    },
    "sensor": {
      "rssi": { "name": "Signal" },
      "model": { "name": "Model" },
      "firmware": { "name": "Firmware" }
    }
  }
}
```

- [ ] **Step 3: Escrever pt-BR.json**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/custom_components/igps/translations/pt-BR.json`:
```json
{
  "config": {
    "flow_title": "{name}",
    "step": {
      "bluetooth_confirm": {
        "description": "Configurar o {name}?"
      },
      "user": {
        "data": { "address": "Dispositivo" }
      }
    },
    "abort": {
      "no_devices_found": "Nenhum iGPSPORT encontrado por perto",
      "already_configured": "Este dispositivo já está configurado"
    }
  },
  "entity": {
    "binary_sensor": {
      "presence": { "name": "Presença" }
    },
    "sensor": {
      "rssi": { "name": "Sinal" },
      "model": { "name": "Modelo" },
      "firmware": { "name": "Firmware" }
    }
  }
}
```

- [ ] **Step 4: Validar JSON**

Run:
```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && python3 -c "import json,glob; [json.load(open(f)) for f in glob.glob('custom_components/igps/**/*.json', recursive=True)]; print('JSON ok')"
```
Expected: `JSON ok`

- [ ] **Step 5: Rodar a suíte da integração**

Run: `cd /Users/hudsonbrendon/Github/ha-igps-ble && .venv-ha/bin/pytest -v`
Expected: PASS (config flow segue passando; nada quebrou).

- [ ] **Step 6: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "feat: strings + EN/PT-BR translations"
```

---

## Task 18: CI da integração (hassfest, HACS validate, tests)

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/.github/workflows/hassfest.yml`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/.github/workflows/validate.yml`
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/.github/workflows/tests.yml`

- [ ] **Step 1: hassfest**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/.github/workflows/hassfest.yml`:
```yaml
name: Hassfest
on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master
```

- [ ] **Step 2: HACS validate**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/.github/workflows/validate.yml`:
```yaml
name: HACS
on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
```

- [ ] **Step 3: Testes**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/.github/workflows/tests.yml`:
```yaml
name: Tests
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements_test.txt
      - run: pytest -v
```

- [ ] **Step 4: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "ci: hassfest, HACS validate, tests workflows"
```

---

## Task 19: README da integração

**Files:**
- Create: `/Users/hudsonbrendon/Github/ha-igps-ble/README.md`

- [ ] **Step 1: Escrever o README**

Create `/Users/hudsonbrendon/Github/ha-igps-ble/README.md`:
```markdown
# iGPSPORT iGS10S — Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Integração Home Assistant (HACS) para o ciclocomputador **iGPSPORT iGS10S** via
Bluetooth LE. Usa a lib independente
[`python-igps-ble`](https://github.com/hudsonbrendon/python-igps-ble).

<p align="center">
  <img src="custom_components/igps/brand/logo.png" alt="iGPSPORT" width="280">
</p>

## O que ela traz pro HA

| Entidade | Tipo | Observação |
|----------|------|------------|
| Presença | `binary_sensor` | Aparelho visto por BLE recentemente |
| Bateria | `sensor` (%) | Se o aparelho expõe o Battery Service padrão |
| Sinal (RSSI) | `sensor` (dBm) | Diagnóstico, desabilitado por padrão |
| Modelo | `sensor` | Diagnóstico |
| Firmware | `sensor` | Diagnóstico |

> **Escopo:** o iGS10S não expõe velocidade/distância/dados de pedalada por
> Bluetooth a terceiros — isso fica no sync proprietário do app iGPSPORT
> (ver [`docs/PROTOCOL.md`](docs/PROTOCOL.md)). Esta integração cobre o que é
> lido de forma confiável por BLE padrão.

## Instalação (HACS)

1. HACS → Integrations → menu (⋮) → **Custom repositories**.
2. Adicione `https://github.com/hudsonbrendon/ha-igps-ble` como **Integration**.
3. Instale "iGPSPORT iGS10S" e reinicie o Home Assistant.
4. Ligue o iGS10S perto do host do HA — ele deve ser **descoberto automaticamente**
   (Configurações → Dispositivos e Serviços → Descobertos). Ou adicione manual
   por **+ Adicionar Integração → iGPSPORT iGS10S**.

## Requisitos

- Home Assistant com Bluetooth configurado (adaptador local ou proxy ESPHome).
- O iGS10S precisa estar ligado e ao alcance pra leituras de bateria/device-info.

## Desenvolvimento

```bash
python -m venv .venv-ha && .venv-ha/bin/pip install -r requirements_test.txt
.venv-ha/bin/pytest
```

## Licença

MIT
```

- [ ] **Step 2: Commit**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "docs: integration README"
```

---

## Task 20: Verificação ponta-a-ponta no aparelho real

**Files:** (nenhum novo — validação)

- [ ] **Step 1: Lib contra o aparelho**

Run (iGS10S ligado e perto):
```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/igps-ble scan && .venv/bin/igps-ble info <ADDRESS>
```
Expected: `scan` lista o iGS10S; `info` mostra modelo/firmware e a bateria batendo (±1) com a tela do aparelho. Se bateria vier `None`, confirme no `RECON_FINDINGS.md` que `0x180F` não existe — comportamento esperado, não bug.

- [ ] **Step 2: Suítes completas**

Run:
```bash
cd /Users/hudsonbrendon/Github/python-igps-ble && .venv/bin/ruff check . && .venv/bin/pytest -q
cd /Users/hudsonbrendon/Github/ha-igps-ble && .venv-ha/bin/pytest -q
```
Expected: ambos verdes.

- [ ] **Step 3: Carregar no HA real (opcional mas recomendado)**

Copie/симлink `custom_components/igps` para o `config/custom_components/` do HA 99lab (via SSH `homeassistant`), reinicie, e confirme: o aparelho aparece em **Descobertos**, configura, e as entidades (presença on, bateria, modelo, firmware) populam.
Expected: device "iGS10S" criado com a marca correta e entidades com valores reais.

- [ ] **Step 4: Atualizar RECON_FINDINGS com o resultado final**

Edite a seção "Conclusões" do `docs/RECON_FINDINGS.md` registrando o que funcionou de fato (bateria sim/não, device-info sim/não) — vira a fonte de verdade do que a integração entrega.

- [ ] **Step 5: Commit final**

```bash
cd /Users/hudsonbrendon/Github/ha-igps-ble && git add -A && git commit -m "docs: record end-to-end verification results"
```

---

## Pós-implementação: histórico de commits limpo

> Sua preferência: **sem co-autoria do Claude** nos commits, e **squash do histórico antes do primeiro push público**.

- [ ] Garanta que nenhum commit tem trailer `Co-Authored-By: Claude`.
- [ ] Antes do primeiro push de cada repo, faça squash dos commits por-task em um histórico limpo (ou um único commit inicial coeso), conforme seu padrão de publicação.
- [ ] Crie os repos no GitHub (`gh repo create hudsonbrendon/python-igps-ble --public` e `hudsonbrendon/ha-igps-ble --public`) e dê push.
- [ ] Adicione os topics do HACS no repo da integração (ex.: `home-assistant`, `hacs`, `bluetooth`, `igpsport`) — sem topics o HACS validate falha.

---

## Self-Review (do autor do plano)

**Cobertura do spec do usuário:**
- ✅ Analisar o aparelho + buscar docs/fóruns → Fase A (recon real) + pesquisa web feita (sem RE público; registrado em PROTOCOL.md).
- ✅ Lib Python BLE independente → `python-igps-ble` (Tasks 0,4–9), usável standalone (CLI + API), publicável no PyPI.
- ✅ Reutilizável fora do HA → a lib não importa nada de HA; a integração depende dela via `requirements`.
- ✅ Integração HA no padrão dos seus repos → `ha-igps-ble` (Tasks 11–19), espelha `jbl-charge5`/`ha-mvave-tankg`.
- ✅ Máximo de info pro HA → bateria, RSSI, modelo, firmware, presença (o obtível de forma honesta por BLE).
- ✅ Sem histórico do Claude nos commits → seção pós-implementação + sem co-autoria.
- ✅ Docs no padrão das suas libs/integrações → READMEs espelhando os existentes; PROTOCOL.md/RECON_FINDINGS.md como no jbl-charge5.
- ✅ Brand/ícones do logo oficial, direto no custom component → Task 10 (`brand/` com 8 PNGs, como jbl-charge5), confirmado que HA brands não aceita PR.

**Scan de placeholders:** nenhum "TBD"/"adicione tratamento adequado"; todo código está completo. Os `<ADDRESS>`/`<local_name>` são valores que **só existem após o recon no aparelho real** — marcados explicitamente como saída da Fase A, não placeholders de implementação.

**Consistência de tipos:** `IGPSDeviceState` (campos `address,name,rssi,battery_level,model,firmware,manufacturer`) usado igual na lib, coordinator e entidades. `parse_battery_level`/`decode_device_string` mesma assinatura em parser, client e coordinator. UUIDs centralizados em `igps_ble.const` e reusados no coordinator. Domínio `igps` consistente em manifest, const, config_flow e testes. Lib package `igps_ble` ≠ domínio HA `igps` (evita import clash; a integração importa a lib instalada via `requirements`).

**Risco aberto registrado:** se o iGS10S não expõe `0x180F`/`0x180A` (descoberto na Task 2), bateria/device-info ficam `None` e as entidades correspondentes ficam indisponíveis — presença + RSSI continuam valendo. Isso é tratado em código (leitura defensiva) e documentado, não é falha do plano.
```