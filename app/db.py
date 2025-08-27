# db.py — Conexión y sesión de base de datos

from sqlalchemy import create_engine # Es la función que crea el motor de conexión a la base de datos
from sqlalchemy.orm import sessionmaker # 
from .models import Base

# Motor SQLite (archivo local logs.db), crea el motor de conexión a la DB.
# "sqlite:///logs.db": ruta de la DB (archivo SQLite en el proyecto) | echo=False: si lo pones True, imprime en consola cada query SQL que ejecuta | future=True: usa el estilo más nuevo de SQLAlchemy
ENGINE = create_engine("sqlite:///logs.db", echo=False, future=True)

# Sesión para consultar/insertar (abrir/cerrar por request), crea la fábrica de sesiones, que son las que realmente usamos para insertar/consultar datos.
# bind=ENGINE: esta sesión va a usar el motor de conexión que definimos arriba | autoflush=False: no manda cambios automáticamente hasta que llamemos a commit() | autocommit=False: no confirma automáticamente, también requiere commit()
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False, future=True)

# Crear tablas si no existen
def init_db():
    Base.metadata.create_all(bind=ENGINE)
