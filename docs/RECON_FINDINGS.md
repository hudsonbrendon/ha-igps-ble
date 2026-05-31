# Recon — iGPSPORT iGS10S (BLE)

Aparelho: iGPSPORT iGS10S · Manufacturer: iGPSPORT · Hardware: V1.00 · Software/Firmware: V1.15
Data do recon: 2026-05-31
Host de recon: macOS (bleak). No macOS o "address" é um UUID por-host, não o MAC real.

## Advertisement (Task 1)

| Campo | Valor observado |
|-------|-----------------|
| `local_name` | `iGS10S` |
| address (macOS UUID) | `72855D4F-E051-E8E7-BFDE-DA2AE5530A6A` |
| RSSI típico (~30 cm) | `-46 dBm` |
| service_uuids no advert | `['0000180a-0000-1000-8000-00805f9b34fb']` (Device Information) |
| Anuncia ligado/ativo? | sim (encontrado de imediato com o aparelho ligado) |

Conclusão p/ discovery do HA: casar `local_name` por prefixo `iGS10S` (o manifest também
aceita `iGPSPORT*` por segurança). O advert anuncia o Device Information Service `0x180A`.

## GATT services (Task 2)

Dump completo em `docs/captures/gatt_dump.txt`. Leitura confirmada char a char:

| UUID | Serviço/Char | Tipo | Props | Valor lido | Nota |
|------|--------------|------|-------|------------|------|
| `6e400001-…cca9e` | Nordic UART Service | custom | — | — | canal proprietário (sync .fit) |
| `6e400002-…cca9e` | NUS RX | custom | write, write-no-resp | — | comando p/ aparelho |
| `6e400003-…cca9e` | NUS TX | custom | notify | — | resposta do aparelho |
| `6e400001-…cca8e` | NUS (2ª instância) | custom | — | — | idem (RX 0002 / TX 0003) |
| `6e400001-…cca7e` | NUS (3ª instância) | custom | — | — | idem |
| `6e400001-…cca6e` | NUS (4ª instância) | custom | — | — | idem |
| `0000180a-…` | Device Information | SIG | — | — | ✅ presente |
| `00002a29-…` | Manufacturer Name | SIG | read | `69475053504f5254` = `iGPSPORT` | ✅ |
| `00002a27-…` | Hardware Revision | SIG | read | `56312e3030` = `V1.00` | ✅ |
| `00002a28-…` | Software Revision | SIG | read | `56312e3135` = `V1.15` | ✅ **este é o firmware** |
| `0000180f-…` | Battery Service | SIG | — | — | ❌ **AUSENTE** |
| `00002a19-…` | Battery Level | SIG | — | — | ❌ **AUSENTE** |
| `00002a24-…` | Model Number | SIG | — | — | ❌ ausente |
| `00002a25-…` | Serial Number | SIG | — | — | ❌ ausente |
| `00002a26-…` | Firmware Revision | SIG | — | — | ❌ ausente (firmware está em `0x2A28`) |

### Implicações para o código (corrigir suposições do plano)

- **Bateria:** não existe `0x180F`/`0x2A19`. Não há % de bateria por SIG. (Investigação do
  NUS proprietário em andamento — ver abaixo.)
- **Firmware:** ler **`0x2A28` (Software Revision)**, não `0x2A26` (ausente).
- **Hardware:** `0x2A27` disponível (`V1.00`) — bônus, pode virar sensor.
- **Model:** `0x2A24` ausente → usar fallback `DEFAULT_MODEL = "iGS10S"`.
- **Manufacturer:** `0x2A29` = `iGPSPORT` ✅.

## NUS — engenharia reversa (em andamento)

- Escuta passiva nas 4 chars TX (`6e400003-…`) por 25 s: **zero notificações espontâneas**
  (`docs/captures/nus_passive.txt`). O aparelho só responde após handshake do app.
- Próximo passo: capturar o tráfego app(iPhone)↔aparelho com **PacketLogger** (perfil de log
  Bluetooth da Apple) → `docs/captures/igps_sync.pklg`, e analisar com Wireshark/tshark
  filtrando os handles do NUS. Objetivo: achar handshake + onde estão bateria/telemetria.

## Conclusões para o discovery do HA

- `local_name` prefix para casar no manifest: `iGS10S` (+ `iGPSPORT*`).
- Entidades garantidas hoje: presença (advert), RSSI, manufacturer, hardware rev, firmware (sw rev).
- Bateria/pedalada: dependem do resultado da RE do NUS.
