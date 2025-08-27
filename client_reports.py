# client_reports.py — cliente simulador del servicio "reports"
# Envía un log a mano al servidor central (POST /logs)

import requests
from datetime import datetime, timezone

# URL del servidor central (tiene que estar corriendo run.py)
SERVER_URL = "http://127.0.0.1:8000/logs"

# Token válido para este servicio (debe existir en el servidor -> auth.py)
TOKEN = "svc-reports-123"

# Nombre del servicio (debe coincidir con el esperado para este token)
SERVICE_NAME = "reports"

# Armamos un log manual
payload = {
    "timestamp": datetime.now(timezone.utc).isoformat(),  # fecha/hora en UTC
    "service": SERVICE_NAME,                              # nombre del servicio
    "severity": "INFO",                                   # nivel de log
    "message": "Primer log enviado desde el cliente"       # descripción
}

# Headers HTTP: formato JSON y token de autorización
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {TOKEN}"
}

# Enviamos el log al servidor central
response = requests.post(SERVER_URL, json=payload, headers=headers)

# Mostramos el resultado en consola
print("Código HTTP:", response.status_code)
print("Respuesta JSON:", response.json())
