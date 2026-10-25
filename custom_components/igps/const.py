"""Constantes da integração iGPSPORT iGS10S."""

from datetime import timedelta

DOMAIN = "igps"
MANUFACTURER = "iGPSPORT"
DEFAULT_MODEL = "iGS10S"

# Polling ativo (conecta pra ler bateria/device-info). O aparelho é passivo
# e pode estar fora de alcance/desligado boa parte do tempo, então o intervalo
# é folgado pra não brigar pelo rádio.
UPDATE_INTERVAL = timedelta(minutes=10)
# Enquanto o aparelho grava uma atividade (ex.: rolo em casa), lê os dados ao
# vivo (velocidade, cadência, FC, potência) com mais frequência.
RIDING_UPDATE_INTERVAL = timedelta(seconds=30)

# Quanto tempo sem advertisement antes de considerar "ausente".
PRESENCE_TIMEOUT = timedelta(minutes=5)
