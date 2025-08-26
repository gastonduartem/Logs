# routes.py — define los endpoints (rutas) de la aplicación

# Aquí centralizamos todas las rutas (URLs) que va a responder nuestro servidor. Las agrupamos en un "Blueprint" llamado 'bp', que luego se conecta en __init__.py.

from flask import Blueprint, jsonify          # Blueprint = agrupar rutas, jsonify = dict → JSON
from datetime import datetime, timezone       # Para devolver fecha y hora

# Creamos un Blueprint. 
# Primer parámetro: nombre interno del blueprint ("routes").
# Segundo parámetro: __name__ indica el módulo actual.
bp = Blueprint("routes", __name__)

# Ruta raíz (GET /)
@bp.get("/")
def root():
    return jsonify({
        "ok": True,                                         # indicador de que el server responde
        "hint": "Usá /health para chequear el servicio",    # pista para el usuario
        "time": datetime.now(timezone.utc).isoformat()      # hora actual en formato estándar
    })

# Ruta de salud (GET /health)
# Confirma que la app está arriba y respondiendo correctamente.
@bp.get("/health")
def health():
    return jsonify({
        "status": "ok",                                     # Estado fijo
        "service": "log-central (step-1, estructura bp)",   # Identificador de nuestro servicio
        "time": datetime.now(timezone.utc).isoformat()      # Hora actual
    })
