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
