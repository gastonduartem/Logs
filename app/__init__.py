# __init__.py — inicializa la aplicación Flask

# Crea y configura la app Flask. 

from flask import Flask

def create_app():
    """
    Fábrica de aplicaciones Flask.
    - Crea la instancia principal de Flask.
    - Registra los blueprints (grupos de rutas).
    - Devuelve la app lista para correr.
    """
    # Creamos la instancia de Flask, __name__ inicializador
    app = Flask(__name__)

    # Importamos y registramos las rutas definidas en routes.py
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    # Retornamos la app creada
    return app
