# 🐧 Logging Distribuido - Penguin Academy Challenge

_"Los sistemas caen. Los logs sobreviven."_ — proverbio DevOps

Este proyecto implementa un **sistema de logging distribuido** usando **Flask** y **SQLite**.  
La idea: múltiples servicios simulados (**clientes**) envían sus logs a un **servidor central**,  
que valida, guarda y expone los logs para consulta.

---

## 🚀 Tecnologías usadas

- **Python 3.12+**
- **Flask** → framework web para exponer endpoints REST.
- **SQLAlchemy** → ORM para mapear clases Python ↔ tablas SQLite.
- **SQLite** → base de datos embebida (archivo `logs.db`).
- **Requests** → usado por los clientes para enviar logs vía HTTP.

---

## 📂 Estructura del proyecto

```bash
proyectos/Logs/
│
├── app/
│ ├── init.py # Inicializa la app Flask (factory pattern)
│ ├── routes.py # Endpoints (/health, /logs)
│ ├── auth.py # Autenticación por tokens estáticos
│ ├── db.py # Configuración de la base de datos
│ └── models.py # Definición de la tabla Log
│
├── run.py # Punto de entrada para arrancar el servidor
├── client_report.py # Cliente básico: envía un log a mano
├── client_reports_auto.py # Cliente automático: envía logs aleatorios
├── logs.db # Base de datos SQLite (se crea al correr la app)
└── README.md # Este archivo
```

---

## 🛠️ Instalación y configuración

1. Clonar el repo:
   ```bash
   git clone git@github.com:TU_USUARIO/Logs.git
   cd Logs
   ```
2. Crear y activar entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate # Linux/Mac
.venv\Scripts\activate # Windows
```

3. Instalar dependencias

```bash
pip install flask sqlalchemy requests python-dateutil
```

---

## ▶️ USO

Correr el servidor central

```bash
python run.py
```

El servidor arranca en
http://127.0.0.1:8000

---

## 📌 Endpoints disponibles

- `GET /` → mensaje de bienvenida y hint de uso.
- `GET /health` → chequeo de salud del servicio.
- `POST /logs` → recibe uno o varios logs (JSON).
- `GET /logs` → devuelve logs guardados, con filtros opcionales:
  - `timestamp_start`, `timestamp_end`
  - `received_at_start`, `received_at_end`
  - `service`, `severity`
  - `limit`, `offset`

---

## Ejemplos de POST

```bash
curl -X POST http://127.0.0.1:8000/logs \
  -H "Content-Type: application/json" \
  -H "Authorization: Token svc-reports-123" \
  -d '{"timestamp":"2025-08-27T10:00:00Z","service":"reports","severity":"INFO","message":"Hola logs"}'
```

---

## 🔐 Autenticación

Los servicios deben enviar un token válido en el header:
-Authorization: Token <valor>

Tokens validos estan en app/auth.py

```bash
TOKENS = {
    "svc-reports-123":  "reports",
    "svc-payments-456": "payments",
    "svc-chat-789":     "chat",
}
```

---

## 🤖 Clientes simulados

Cliente manual (client_report.py)
Envía un solo log:

```bash
python client_report.py
```

Cliente automático (client_reports_auto.py)
Envía logs cada X segundos o en lotes:

```bash
# Enviar un log cada 2s (infinito hasta CTRL+C)
python client_reports_auto.py --mode=single --interval=2

# Enviar 3 logs en lote cada 1s, 5 veces
python client_reports_auto.py --mode=batch --batch-size=3 --interval=1 --count=5
```
