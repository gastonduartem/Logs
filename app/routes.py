# routes.py — define los endpoints (rutas) de la aplicación

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

# Importamos helpers de autenticación
from .auth import validate_token, TOKENS

bp = Blueprint("routes", __name__)


# LOG_BUFFER guardará dicts con los logs aceptados por POST /logs
LOG_BUFFER: List[Dict[str, Any]] = []

# Conjunto de severidades válidas. WARNING la llamamos como WARN.
VALID_SEVERITIES = {"DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"}

# La función normaliza y limpia el campo de severidad, para que siempre quede en un conjunto conocido de valores.
# Siempre espera un string y devuelve un string
def normalize_severity(s: str) -> str:
    
    s = (s or "INFO").upper()
    if s == "WARNING":
        s = "WARN"
    return s if s in VALID_SEVERITIES else "INFO"

# Chequeo rápido para que no nos manden None o vacío
def looks_like_iso8601(s: Any) -> bool:
    return isinstance(s, str) and bool(s.strip())

# Chequea que el JSON envio todos los parametros
def validate_log_item(item: Dict[str, Any]) -> Tuple[bool, str]:
    
    required = ["timestamp", "service", "severity", "message"]
    for k in required:
        if k not in item:
            return False, f"missing field: {k}"

    if not looks_like_iso8601(item["timestamp"]):
        return False, "invalid timestamp (expected ISO8601 string)"

    if not isinstance(item["service"], str) or not item["service"].strip():
        return False, "invalid service"

    if not isinstance(item["message"], str) or not item["message"].strip():
        return False, "invalid message"

    return True, "ok"


# Rutas simples ya conocidas
@bp.get("/")
def root():
    return jsonify({
        "ok": True,
        "hint": "Usá /health para chequear el servicio, y POST /logs para enviar logs",
        "time": datetime.now(timezone.utc).isoformat()
    })

@bp.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "log-central (step-2, POST /logs sin DB)",
        "time": datetime.now(timezone.utc).isoformat()
    })

# -------------------------------------------------------------------
# NUEVO: POST /logs — recibe 1 log o lista de logs
# -------------------------------------------------------------------
@bp.post("/logs")
def ingest_logs():
    
    # 1) Autenticación por token. Evita que cualquiera mande logs sin permiso
    auth_header = request.headers.get("Authorization")
    token = validate_token(auth_header)
    if token is None:
        return jsonify({"error": "Quién sos"}), 401

    # 2) Leer JSON, con silent=True: en vez de lanzar un error/romper la app, simplemente devuelve None
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "JSON inválido o ausente"}), 400

    # Si nos mandan 1 objeto,  lo convertimos a lista de una para procesar uniforme
    items = payload if isinstance(payload, list) else [payload]

    total_logs = 0
    errors = []

    # 3/4/5) Validación por ítem + normalización + guardado en memoria

    # Obtenemos los tokens de cada servicio (es unico para cada servicio)
    expected_service = TOKENS.get(token)  

    # Recorremos cada log recibido, lo validamos, si falla lo agg a errors junto con su posicion en la lista y pasa al sgte
    for index, item in enumerate(items):
        # Llama a la funcion que valida el log, devuelve una tupla de (True o False y un mensaje)
        ok, msg = validate_log_item(item)
        if not ok:
            # Si es False, lo agg a la lista de errores
            errors.append({"index": index, "error": msg})
            continue

        # Chequeamos que el token sea el service esperado
        if expected_service and item.get("service") != expected_service:
            errors.append({"index": index, "error": f"service mismatch for token (expected '{expected_service}')" })
            continue

        # Armamos el registro "limpio" para guardar en memoria
        record = {
            "timestamp": item["timestamp"],               
            "service":   item["service"].strip(),
            "severity":  normalize_severity(item.get("severity", "INFO")),
            "message":   item["message"].strip(),
            "token_used": token,                          # trazabilidad
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
        LOG_BUFFER.append(record)
        total_logs += 1

    # 6) Responder
    # - Si todo falló, devolvemos 400 para que el cliente sepa que no sirvió nada del lote.
    if total_logs == 0 and errors:
        return jsonify({"total_logs": 0, "errors": errors}), 400

    # Si al menos 1 entró, devolvemos 201 (creado)
    return jsonify({"total_logs": total_logs, "errors": errors}), 201


