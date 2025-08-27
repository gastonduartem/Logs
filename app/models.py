# models.py — Modelos ORM (tablas de la base de datos)
# Usamos SQLAlchemy para mapear clases Python a tablas SQL.

from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column #Es una clase base que usamos para declarar nuestros modelos ORM, Cada modelo (ej: Log) hereda de esta base,| Es un tipo genérico (tipo anotación) para indicar que un atributo de la clase es una columna de la DB | Es la función que define la columna real dentro del modelo. Ahí se ponen las configuraciones: tipo SQL, si es primary_key, nullable, default, etc.
from sqlalchemy import String, DateTime, Integer, Text, Index

# Base para los modelos (requerido por SQLAlchemy)
class Base(DeclarativeBase):
    pass

# Tabla de logs (cada fila = 1 log)
class Log(Base):
    __tablename__ = "logs"

    # id autoincremental (clave primaria)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # cuándo ocurrió el evento (viene del cliente)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # cuándo recibimos y guardamos (lado servidor)
    # default=datetime.utcnow: si no me mandan un valor para received_at, por defecto coloca la hora actual en UTC
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # metadatos del log
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)   # INFO/WARN/ERROR/...
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # para trazabilidad (qué token usó)
    token_used: Mapped[str] = mapped_column(String(64), nullable=False)

