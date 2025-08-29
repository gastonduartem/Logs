# routes.py — define los endpoints (rutas) de la aplicación

from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

# Importamos helpers de autenticación
from .auth import validate_token, TOKENS

# imports para DB y parseo de fecha real
from dateutil import parser as dtparser   # parsea ISO8601 “en serio”
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from .db import SessionLocal              # sesión de DB (SQLite via SQLAlchemy)
from .models import Log                   # modelo ORM (tabla logs)

# forma de organizar y agrupar rutas en módulos separados (nombre interno del blueprint, referencia al módulo actual)
bp = Blueprint("routes", __name__)

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

# >>> NUEVO: parseamos ISO8601 a datetime (si viene sin timezone, lo pasamos a UTC)
def parse_timestamp_iso8601(s: str) -> datetime:
    # Convierte string ISO8601 (o similar) a datetime con timezone.
    # Si no trae timezone, normalizamos a UTC.
    dt = dtparser.parse(s)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

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


# Rutas simples
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
        "service": "log-central",
        "time": datetime.now(timezone.utc).isoformat()
    })



# POST /logs — ahora guardamos en DB (SQLite via SQLAlchemy)

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

    # 3/4/5) Validación por ítem + normalización + guardado (ahora en DB)

    # Obtenemos los tokens de cada servicio (es unico para cada servicio)
    expected_service = TOKENS.get(token)

    # Abrimos sesión de DB (se cierra automáticamente al salir del with)
    try:
        with SessionLocal() as s:
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

                # Convertir timestamp string a datetime (ISO8601 real)
                try:
                    ts_dt = parse_timestamp_iso8601(item["timestamp"])
                except Exception:
                    errors.append({"index": index, "error": "invalid timestamp (cannot parse ISO8601)"})
                    continue

                # Armamos el registro "limpio" para guardar en DB
                log_row = Log(
                    timestamp=ts_dt,                                  # ahora es datetime
                    received_at=datetime.now(timezone.utc),           # datetime
                    service=item["service"].strip(),
                    severity=normalize_severity(item.get("severity", "INFO")),
                    message=item["message"].strip(),
                    token_used=token                                  # trazabilidad
                )

                # Guardamos en DB (agrego a la sesión, commit al final del lote)
                s.add(log_row)
                total_logs += 1

            # Commit una sola vez por lote (mejor performance)
            s.commit()

    except SQLAlchemyError as e:
        # error de DB controlado
        return jsonify({"error": "db_error", "detail": str(e)}), 500

    # 6) Responder
    # - Si todo falló, devolvemos 400 para que el cliente sepa que no sirvió nada del lote.
    if total_logs == 0 and errors:
        return jsonify({"total_logs": 0, "errors": errors}), 400

    # Si al menos 1 entró, devolvemos 201 (creado)
    return jsonify({"total_logs": total_logs, "errors": errors}), 201



# GET /logs — consulta en DB con filtros básicos

@bp.get("/logs")
def list_logs():
   
    # helper para parsear fechas del query string
    def parse_query_param(param_name: str):
        raw_value = request.args.get(param_name)
        if not raw_value:
            return None
        try:
            return parse_timestamp_iso8601(raw_value)
        except Exception:
            return None

    # filtros por fecha
    timestamp_start = parse_query_param("timestamp_start")
    timestamp_end = parse_query_param("timestamp_end")
    received_start = parse_query_param("received_at_start")
    received_end = parse_query_param("received_at_end")

    # filtros exactos
    service_filter = request.args.get("service")
    severity_filter = request.args.get("severity")

    # paginado
    try:
        # limit ¿cuántos quiero traer?
        limit_results = max(1, min(1000, int(request.args.get("limit", 100))))
        # offset ¿desde cuál empezar?
        offset_results = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        return jsonify({"error": "limit/offset inválidos"}), 400

    # armamos la consulta
    query = select(Log)
    if timestamp_start:
        query = query.filter(Log.timestamp >= timestamp_start)
    if timestamp_end:
        query = query.filter(Log.timestamp <= timestamp_end)
    if received_start:
        query = query.filter(Log.received_at >= received_start)
    if received_end:
        query = query.filter(Log.received_at <= received_end)
    if service_filter:
        query = query.filter(Log.service == service_filter)
    if severity_filter:
        query = query.filter(Log.severity == severity_filter.upper())

    query = query.order_by(Log.received_at.desc()).limit(limit_results).offset(offset_results)

    # ejecutar y serializar
    with SessionLocal() as session:
        # Ejecuta la peticion, convierte cada fila devuelta en un objeto real (clase Log), convierte el iterador en una lista completa
        result_rows = session.execute(query).scalars().all()
        serialized_logs = []
        for row in result_rows:
            serialized_logs.append({
                "id": row.id,
                "timestamp": row.timestamp.isoformat(),
                "received_at": row.received_at.isoformat(),
                "service": row.service,
                "severity": row.severity,
                "message": row.message,
                "token_used": row.token_used,
            })
        return jsonify(serialized_logs)

