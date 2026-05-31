# iGPSPORT iGS10S — Protocolo BLE (escopo de terceiros)

> Verificado empiricamente em 2026-05-31 (macOS/bleak). Ver `RECON_FINDINGS.md` e
> `docs/captures/` para os valores crus.

## Em escopo (lido por terceiros sem app oficial)

### Device Information Service — `0000180a-0000-1000-8000-00805f9b34fb`  [confirmado: ✅]
- Manufacturer Name — `00002a29-…` — string UTF-8. Valor real: `iGPSPORT`.
- Hardware Revision — `00002a27-…` — string UTF-8. Valor real: `V1.00`.
- **Software Revision — `00002a28-…`** — string UTF-8. Valor real: `V1.15`. **(= firmware)**
- ❌ Model Number `00002a24`, Serial `00002a25` e Firmware Revision `00002a26` **não existem** neste aparelho.

### Presença
- Derivada do advertisement BLE (`local_name` = `iGS10S`). O HA trata "visto recentemente"
  como presente. O advert também expõe o serviço `0x180A`.

### Bateria — ❌ NÃO disponível por SIG
- O iGS10S **não** expõe Battery Service `0x180F` nem Battery Level `0x2A19`.
- A % de bateria, se obtível, está no canal proprietário Nordic UART (ver abaixo) — em RE.

## Canal proprietário (Nordic UART) — RE em andamento

Quatro instâncias de Nordic UART Service, UUID base `6e40000x-b5a3-f393-e0a9-e50e24dccaYe`:

| Instância | Service | RX (write) | TX (notify) |
|-----------|---------|------------|-------------|
| 1 | `6e400001-…cca9e` | `6e400002-…cca9e` | `6e400003-…cca9e` |
| 2 | `6e400001-…cca8e` | `6e400002-…cca8e` | `6e400003-…cca8e` |
| 3 | `6e400001-…cca7e` | `6e400002-…cca7e` | `6e400003-…cca7e` |
| 4 | `6e400001-…cca6e` | `6e400002-…cca6e` | `6e400003-…cca6e` |

- App escreve comandos em RX (`…0002`), aparelho responde em TX (`…0003`).
- Múltiplas instâncias provavelmente multiplexam funções (sync de atividade, config, live data).
- Sem handshake, o aparelho não emite nada (escuta passiva = 0 bytes).
- Framing/handshake desconhecidos; sem docs públicas nem RE conhecido (busca em 2026-05).

### Plano de RE
1. Capturar tráfego app(iPhone)↔aparelho via **PacketLogger** + perfil de log Bluetooth da Apple.
2. Salvar `.pklg` em `docs/captures/igps_sync.pklg`.
3. Analisar com Wireshark/tshark: isolar writes em `…0002` e notifies em `…0003`, casar com os
   valores que o app mostrou (bateria %, etc.) pra deduzir o framing.
4. Só então estender `python-igps-ble` com o decoder do NUS.
