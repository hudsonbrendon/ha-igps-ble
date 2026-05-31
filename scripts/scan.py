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
