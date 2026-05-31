"""Recon (RE): escuta passiva dos Nordic UART Services do iGS10S.

O iGS10S expõe 4 instâncias de Nordic UART Service (UUID base
6e40000x-b5a3-f393-e0a9-e50e24dccaYe, Y = 9,8,7,6). Esse é o canal
proprietário que o app iGPSPORT usa pra sync de .fit, config e telemetria.

Este script NÃO escreve nada no aparelho. Apenas:
  1. conecta;
  2. subscreve em todas as characteristics com `notify`;
  3. registra qualquer notificação espontânea por N segundos.

Muitos aparelhos só falam após um handshake do app — se nada chegar,
o próximo passo é capturar o tráfego app↔aparelho (Android HCI snoop log).

Uso: python scripts/nus_probe.py <ADDRESS> [segundos]
"""

import asyncio
import sys

from bleak import BleakClient

NUS_BASES = (
    "6e400001-b5a3-f393-e0a9-e50e24dcca9e",
    "6e400001-b5a3-f393-e0a9-e50e24dcca8e",
    "6e400001-b5a3-f393-e0a9-e50e24dcca7e",
    "6e400001-b5a3-f393-e0a9-e50e24dcca6e",
)


def _make_handler(uuid: str):
    def handler(_char, data: bytearray) -> None:
        print(f"[notify] {uuid}  {bytes(data).hex()}  ({len(data)}B)  {bytes(data)!r}")

    return handler


async def main(address: str, seconds: float) -> None:
    async with BleakClient(address) as client:
        print(f"Conectado: {address}")
        notifiers: list[str] = []
        for service in client.services:
            for char in service.characteristics:
                if "notify" in char.properties:
                    await client.start_notify(char.uuid, _make_handler(char.uuid))
                    notifiers.append(char.uuid)
                    print(f"  subscrito notify -> {char.uuid}")
        if not notifiers:
            print("Nenhuma char notify. Nada a escutar.")
            return
        print(f"\nEscutando {seconds}s (sem escrever nada)...")
        await asyncio.sleep(seconds)
        print("Fim da escuta.")
        for uuid in notifiers:
            try:
                await client.stop_notify(uuid)
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: python scripts/nus_probe.py <ADDRESS> [segundos]")
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    asyncio.run(main(sys.argv[1], secs))
