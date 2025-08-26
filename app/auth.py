# auth.py — autenticación para el servidor de logs

# En este paso usamos tokens "estáticos" (duros en el código) solo para aprender el flujo.

# typing: módulo estándar de Python que nos deja anotar tipos de variables y funciones. Optional: “este valor puede ser del tipo X o None”
from typing import Optional

# Mapa de tokens válidos → servicio asociado que se espera que use ese token. Si llega un log con token "svc-reports-123", esperamos que el campo "service" sea "reports".
TOKENS = {
    "svc-reports-123":  "reports",
    "svc-payments-456": "payments",
    "svc-chat-789":     "chat",
}

# esta función recibe un string o nada, y devuelve un string o nada
def parse_auth_header(auth_header: Optional[str]) -> Optional[str]:
    
    if not auth_header:
        return None
    parts = auth_header.split()
    # Debe tener EXACTAMENTE 2 partes: ["Token", "<valor>"]
    if len(parts) == 2 and parts[0].lower() == "token":
        return parts[1]
    return None

def validate_token(auth_header: Optional[str]) -> Optional[str]:
    """
    Valida si el token del header está en nuestra lista de válidos.
    Retorna el token (str) si es válido, o None si es inválido/ausente.
    """
    token = parse_auth_header(auth_header)
    if token is None:
        return None
    if token in TOKENS:
        return token
    return None
