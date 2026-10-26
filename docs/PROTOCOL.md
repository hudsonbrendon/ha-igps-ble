# iGPSPORT iGS10S — Protocolo BLE

> RE de 2026-10-25: APK **iGPSPORT Ride** `com.qiwu.worldwide.ride` 8.06.46
> (pacote Java `com.igpsport.blelib`, decompilado com jadx) + validação ao vivo num
> iGS10S (firmware V1.15, protocolo 1.01). Implementação de referência:
> [`python-igps-ble`](https://github.com/hudsonbrendon/python-igps-ble)
> (`igps_ble/protocol.py`, `igps_ble/client.py`).
>
> **Correção do recon de 2026-05-31:** o canal *não* é autenticado. O "token base64"
> visto na captura é o `member_id` (id do usuário na nuvem) dentro do perfil que o
> app grava — não um login. Qualquer cliente BLE fala o protocolo.

## Device Information Service (SIG) — `0x180A`

Manufacturer `0x2A29` = `iGPSPORT`, Hardware `0x2A27` = `V1.00`,
**Software `0x2A28` = firmware** (`V1.15`). Não há `0x180F` (bateria), `0x2A24`,
`0x2A25` nem `0x2A26`.

## Canais (4× Nordic UART)

UUID base `6e40000X-b5a3-f393-e0a9-e50e24dccaYe`; RX = `…0002` (write), TX = `…0003`
(notify).

| Canal | `Ye` | Uso |
|-------|------|-----|
| ch1 | `9e` | payload protobuf da maioria dos serviços |
| ch2 | `8e` | **controle**: headers de 20 B e ACKs |
| ch3 | `7e` | payload de CYCLING_DATA (lista/arquivos de atividade) |
| ch4 | `6e` | gen 4 (não usado pelo iGS10S) |

O app classifica o iGS10S como **geração 3** (`DeviceInfoHelper`): payload no canal de
dados, header no ch2. (Gen 4 concatena header+payload num canal só.)

## Enquadramento

Requisição: escreve o protobuf no RX de dados **em pacotes de 20 B** (o firmware
descarta o que passar de 20 B por write — o app fatia com `DataSplitter`; no macOS o
MTU maior faz o bleak mandar tudo junto e o aparelho responde `DataError`), depois o
header no ch2 RX:

```
[0]  01            header (02 = ACK)
[1]  service       Common.service_type_index
[2]  sub-service   ff = nenhum (CONFIG/BACK usam o subtipo)
[3]  ff
[4]  operação      enum OPERATE_TYPE do serviço
[5]  ff   [6] ff
[7:9] len(payload) big-endian
[9]  crc8(payload)
[10] 01            end type = protobuf
[11:19] ff × 8
[19] crc8(header[0:19])
```

CRC = **CRC-8/MAXIM** (poly refletido 0x31 → 0x8C, init 0). Confere com a captura do
app: `08111002` → `0111ffff02ffff0004ad01ffffffffffffffffae`.

Resposta: notificações de payload no TX do mesmo canal e, por último, um header no
ch2 TX (op = `SEND`/`GET`). Comandos de escrita respondem com **ACK**
`02 svc sub ff op ff ff STATUS ff… crc`. `STATUS` (`DeviceReturnStatus`): 0 ok,
1 DataError, 2 MemoryError, 3 LowBattery, 5 IsBeingUsed, **6 UnsupportedCommand**,
33 DeviceIsSportRecording…

Todo payload começa com `1: service_type, 2: operação` (exceto CONFIG e BACK, que usam
`2: subtipo, 3: operação`).

## Serviços que o iGS10S responde

| Svc | Nome | Op | Ch | Resposta / efeito |
|-----|------|----|----|-------------------|
| 11 | FACTORY | 6 BATTARY_GET | 1 | `6: {1: tensão mV, 2: %}` → ex. 3718 mV, 51 % |
| 11 | FACTORY | 1 SN_GET | 1 | `3: {1: "799…"}` serial |
| 11 | FACTORY | 5 MEMORY_GET | 1 | `5: {1: total, 2: livre}` (8112 / 8064) |
| 11 | FACTORY | 4 SENSOR_GET | 1 | `4: [{1: tipo, 2: valor, 3: status}]`: 1 GPS, 2 RTC (segundos FIT, hora **local**), 3 AIR (bruto, unidade desconhecida), 4 TEM (décimos de °C), 5 ACC |
| 11 | FACTORY | 254 ALL_GET | 1 | dump de teste de fábrica (SNR GNSS, ANT…) |
| 17 | DEV_VER_INFO | 2 GET | 1 | `3: {3: ble_boot, 4: ble_app, 5: hw, 6: protocolo}` (×100) |
| 13 | DEV_STATUS | 1 GET | 1 | `3: {1: 0 livre/1 gravando/2 pausa, 2: início}`, `4: {1,2: lat/lon double}`, `5: rt_data_message` (só gravando) |
| 6 | CYCLING_DATA | 1 LIST_GET | **3** | `3: [{1: início (FIT local), 2: bytes}]` |
| 9 | USER_CONFIG | 1 SET | 1 | `3: {1 sexo (1 masc/0 fem), 2 peso×10, 3 idade, 4 altura cm, 5 roda mm, 6 peso bike×10, 7 fuso s}` → ACK 0 |
| 9 | USER_CONFIG | 2 GET | 1 | sempre zeros (não reflete o SET) |
| 10 | BLE | 1 BOND_INFO | 1 | `3: {1: status}` |

Verificado: o SET de USER_CONFIG aplica — omitir o campo 7 deixou o relógio em UTC;
mandar `7: -10800` voltou para a hora local. Campo ausente = 0, então grave sempre o
perfil inteiro.

`rt_data_message` (DEV_STATUS campo 5): 1 velocidade, 2 vel. média, 3 tempo, 4
distância, 5 cadência, 6 FC, 7 FC média, 8 potência, 9 subida total, 10 subida média,
11 altitude, 12 inclinação, 13 vel. máx, 14 FC máx, 15 cad. média, 16 cad. máx,
17 pot. média, 18 pot. máx, 19 rumo. Escalas não confirmadas (o app não usa esse
campo; precisa de uma pedalada para validar).

Epoch FIT = 1989-12-31 00:00; o aparelho guarda horário local nessa base.

## Respondidos com UnsupportedCommand (6) ou sem efeito

- CONFIG (12) — páginas, bike, unidades, idioma, backlight, som, alarmes, auto-pause:
  status 6 para todo subtipo (inclusive o SET que o app manda).
- SENSOR (14), LANGUAGE (18).
- BACK/TIME (3/6, `timeCalibration`): status 6. FACTORY RTC_SET (12) dá ACK 0 mas o
  relógio não muda — a hora vem do GPS + fuso do perfil.

## Download de `.fit` (CYCLING_DATA/FILE_GET, ch3)

Pedido `{1: 6, 2: 3, 3: {1: id}}` (id = timestamp FIT cru da lista). O aparelho manda
pedaços `cycling_data_msg {3: {1: id}, 4: file_content}` (4 KB pelo Mac, 1 KB pelo
rádio do HA), cada um seguido de header op 4 (FILE_SEND). O cliente confere
`len`/`crc8` do pedaço e responde ACK `02 06 ff ff 04 ff ff STATUS` — 0 = manda o
próximo, 1 = reenvia. `header[10] == 3` marca o último pedaço. O app confere o tamanho
total com o da lista: o aparelho às vezes encerra cedo (pedaço vazio com fim = 3) e aí
tem que baixar de novo. Validado: os 3 `.fit` do aparelho saem idênticos (CRC FIT ok).

Escritas como *write with response*: pelo proxy BLE do HA, ACK sem resposta se perde
e o aparelho aborta a transferência.

## Comandos de manutenção (implementados, seguindo o app)

| Comando | Frame | Testado ao vivo |
|---------|-------|-----------------|
| Apagar atividade | CYCLING_DATA op 5 `{3: {1: id}}` ch3 | ✅ 26/10: apagou só a atividade alvo (as outras ficaram); id inexistente → ACK 0 sem efeito |
| Apagar todas | CYCLING_DATA op 6 ch3 | não |
| Formatar / baixo nível / restaurar ajustes / reset de fábrica | FACTORY op 23 `{8: {1: 16/17/18/19, 2: 1}}` | não |
| Modo teste, travar, logs temp/tensão/ANT | FACTORY op 23 `{8: {1: 1/2/32/33/34, 2: 1}}` | não |
| GPS liga/desliga, cold start, economia, GNSS | FACTORY op 16 `{14: {1: tipo, 2: status}}` | não |
| Constelações (bitmask) | FACTORY op 18 `{15: {1: mask}}` | não |
| Modelo dinâmico | FACTORY op 20 `{16: {1: modo}}` | GET → ACK 0 |
| Posição de referência | FACTORY op 8 `{9: {1: lat, 2: lon}}` (double) | não |
| Economia de energia, nascer/pôr do sol, filtros | FACTORY op 11 / 9 / 14 | não |
| Simular atividades | FACTORY op 7 `{7: {1: n, 2: bytes}}` | ACK 0, não criou nada fora do modo teste |
| Regravar serial | FACTORY op 3 `{3: {1: sn}}` | não |
| Desvincular do app | BLE op 4 | não |
| Modo DFU | FIRMWARE op 5 (BLE_UPDATE) → bootloader Nordic | não |

Os comandos de fábrica não têm tela no app (bancada), então nomes e valores vêm dos
enums do protobuf. Os GETs de filtro/GNSS/sol/RTC não devolvem dados neste firmware.
Firmware: o iGS10S atualiza por Nordic DFU (`.zip` da nuvem iGPSPORT, gravado com
nRF Connect/nrfutil depois do modo DFU); o reboot (MCU_UPDATE) só existe na gen 4.

