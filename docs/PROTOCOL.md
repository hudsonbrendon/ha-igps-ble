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
