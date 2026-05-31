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

### Resultado da RE (captura PacketLogger iPhone, 2026-05-31)

Captura: `docs/captures/igps_sync.pklg` (15.705 pacotes, 425 ATT). Extrações em
`att_handles.txt`, `att_ops.txt`, `att_nus.txt`.

**Mapa de handles (iGS10S, 4 instâncias NUS):**

| Canal | Service UUID | RX (write) | TX (notify) | CCCD |
|-------|--------------|-----------|-------------|------|
| ch1 | `6e400001-…-…dcca9e` | `0x000d` | `0x000f` | `0x0010` |
| ch2 | `6e400001-…-…dcca8e` | `0x0013` | `0x0015` | `0x0016` |
| ch3 | `6e400001-…-…dcca7e` | `0x0019` | `0x001b` | `0x001c` |
| ch4 | `6e400001-…-…dcca6e` | `0x001f` | `0x0021` | `0x0022` |

**Dois formatos proprietários coexistem:**

1. **TLV custom** (ch1/ch2): `01 <tipo> ffff <seq> ffff <len:be16> <payload> ffffffffffffffff <chk>`.
   - app→ `0111ffff02ffff0004ad01…ae`  · device→ `0111ffff03ffff000e4101…b5`
   - app→ `0106ffff01ffff00047f01…c4`  · device→ `0106ffff02ffff0027d201…d9`
2. **Protobuf** (ch3): ex. device→ `08 06 10 02 1a0a 08 <varint> 10 <varint> 1a09 08 <varint> 10 <varint> …`
   (mensagens com pares repetidos, aparência de séries temporais de atividade).

**Handshake / autenticação (bloqueador):** no connect o app habilita notify nas 4 CCCDs e
escreve no ch1 (`0x000d`) um bloco de config contendo um **token base64**
`<token de pareamento — redigido>` (24 chars base64). O canal é **autenticado** — sem
reproduzir esse login o aparelho não entrega dados.

**Conclusão:** Em toda a captura o app **nunca fez um Read de characteristic** (`0x0a`) — não
há byte de bateria exposto. Bateria/pedalada vivem dentro dos frames protobuf/TLV autenticados.
Uma lib de terceiros precisaria replicar o token de login + reimplementar TLV e protobuf —
RE pesado, frágil e provavelmente quebra a cada firmware. **Fora de escopo viável.**
O `0x180F` (Battery Service) visto na captura é de **outro** aparelho BLE do iPhone, não do iGS10S.

**Escopo final entregável por BLE:** presença, RSSI, manufacturer, hardware rev, firmware (sw rev).
