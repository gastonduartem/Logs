# client_reports_auto.py — cliente simulador "reports" (automático)
# Envía logs al servidor central en forma periódica o en lotes.
# Requiere: pip install requests

import requests
import random
import time
import argparse  # CLI (Command Line Interface)
from datetime import datetime, timezone
from typing import List, Dict

# URL del servidor central (tiene que estar corriendo run.py)
SERVER_URL = "http://127.0.0.1:8000/logs"

# Token válido para este servicio (debe existir en el servidor -> auth.py)
TOKEN = "svc-reports-123"

# Nombre del servicio (debe coincidir con el esperado para este token)
SERVICE_NAME = "reports"

# Niveles de severidad (el servidor normaliza WARNING->WARN)
SEVERITIES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Mensajes simulados 
MESSAGES = [
    "Generando reporte mensual",
    "Reporte exportado a CSV",
    "Timeout consultando ventas",
    "Permisos insuficientes para usuario",
    "Fallo al renderizar PDF",
    "Reintento de envío de email",
    "Reporte vacío (sin datos)",
    "Cache caliente poblada",
    "Conexión a base restablecida"
]


# Construimos un log individual (dict) con timestamp UTC ISO
def build_log(message: str, severity: str) -> Dict[str, str]:
    """
    timestamp: ISO UTC, service igual al esperado por el token, severity y message
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": SERVICE_NAME,
        "severity": severity,
        "message": message,
    }


# Envío de 1 log por request (POST con un objeto)
def send_single_log(server_url: str, token: str) -> None:
    # Armamos un payload aleatorio (mensaje + severidad)
    payload = build_log(
        message=random.choice(MESSAGES),
        severity=random.choice(SEVERITIES),
    )

    # Headers HTTP: formato JSON y token de autorización
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
    }

    # Enviamos al servidor
    resp = requests.post(server_url, json=payload, headers=headers, timeout=5)
    print("[single] HTTP:", resp.status_code, "| resp:", resp.json())


# Envío por lotes (POST con una lista de objetos)
def send_batch_logs(batch_size: int, server_url: str, token: str) -> None:
    # Construimos N logs en memoria (lista de dicts)
    batch: List[Dict[str, str]] = [
        build_log(
            message=random.choice(MESSAGES),
            severity=random.choice(SEVERITIES),
        )
        for _ in range(batch_size)
    ]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
    }

    resp = requests.post(server_url, json=batch, headers=headers, timeout=10)
    print(f"[batch x{batch_size}] HTTP:", resp.status_code, "| resp:", resp.json())


def main():
    # Parámetros por CLI para controlar el envío
    parser = argparse.ArgumentParser(
        description="Cliente automático para enviar logs del servicio 'reports'"
    )
    # --mode: single (1 log por envío) o batch (lista de logs)
    parser.add_argument(
        "--mode",
        choices=["single", "batch"],
        default="single",
        help="Modo de envío: single (por defecto) o batch",
    )
    # --interval: segundos entre envíos (por las dudas)
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Segundos a esperar entre envíos (default 2.0)",
    )
    # --batch-size: tamaño del lote si mode=batch
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Tamaño del lote cuando mode=batch (default 5)",
    )
    # --count: cuántas veces enviar (0 = infinito hasta CTRL+C)
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Cantidad de envíos a realizar (0 = infinito hasta CTRL+C)",
    )
    # --url y --token por si querés probar otro servidor/credencial
    parser.add_argument(
        "--url", type=str, default=SERVER_URL, help="URL de POST /logs"
    )
    parser.add_argument(
        "--token", type=str, default=TOKEN, help="Token del servicio (Authorization)"
    )

    # Leemos/validamos lo que vino por CLI
    args = parser.parse_args()

    # NO reasignamos globales; usamos variables locales claras
    server_url = args.url
    token = args.token

    print(
        f"===> Iniciando cliente '{SERVICE_NAME}'"
        f" | mode={args.mode} | interval={args.interval}s"
        f" | count={'∞' if args.count == 0 else args.count}"
        + (f" | batch_size={args.batch_size}" if args.mode == 'batch' else "")
    )
    print(" Enviando a:", server_url)
    print(" Token:", token)
    print(" Presioná CTRL+C para detener.\n")

    try:
        sent = 0
        while True:
            if args.mode == "single":
                send_single_log(server_url, token)
            else:
                # mode=batch
                batch_size = max(1, args.batch_size)
                send_batch_logs(batch_size, server_url, token)

            sent += 1
            # Si se definió un límite de envíos (--count > 0), cortamos al llegar
            if args.count > 0 and sent >= args.count:
                print("\nListo. Se alcanzó el límite de envíos (--count).")
                break

            # Pausa entre envíos para no saturar
            time.sleep(max(0.1, args.interval))

    except KeyboardInterrupt:
        print("\nDetenido por el usuario (CTRL+C). ¡Hasta la próxima!")


if __name__ == "__main__":
    main()
