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
