import os
import sys
# Deployment Timestamp: 2026-04-10 17:07

# Añadimos el directorio raíz al path para que encuentre flask_app.py
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    # Importamos la aplicación principal de MT Fitness
    from flask_app import app
    print("SUCCESS: Full MT Fitness application loaded.")
except Exception as e:
    # Fallback de emergencia si algo falla al importar el archivo grande
    from flask import Flask, jsonify
    import traceback
    
    app = Flask(__name__)
    
    @app.route('/')
    @app.route('/<path:path>')
    def startup_error(path=None):
        return jsonify({
            "error": "CRITICAL_BOOT_ERROR",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "tip": "Revisa los logs de Vercel y verifica que todas las librerías en requirements.txt estén instaladas."
        }), 500
    print(f"ERROR: Failed to load main flask_app: {e}")

# Vercel necesita encontrar la variable 'app' para ejecutar la función
