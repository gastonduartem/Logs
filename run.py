# run.py — punto de entrada de la aplicación
# Este archivo arranca el servidor Flask. 


from app import create_app   # Importamos la función fábrica de la app

# Creamos la instancia de la aplicación Flask usando la factory function
# from app.__init__ import create_app,  funciona pero no es la forma estándar
# En Python, cuando una carpeta tiene un archivo llamado __init__.py, automáticamente se convierte en un paquete importable.
app = create_app()

# Este bloque se ejecuta solo si corremos este archivo directamente:
#   python run.py
if __name__ == "__main__":
    # Arrancamos el servidor
    # host="127.0.0.1" → accesible solo desde tu máquina
    # port=8000 → puerto donde se levanta la app
    # debug=True → recarga automática y mensajes de error detallados (solo en desarrollo)
    app.run(host="127.0.0.1", port=8000, debug=True)
