import sys
import os
import traceback

# Forzar el path para encontrar archivos en la raíz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask import Flask, jsonify

app = Flask(__name__)

# Intentar cargar la lógica real dentro de una función para que no rompa el arranque global
_real_app = None

def get_real_app():
    global _real_app
    if _real_app is None:
        try:
            # Importamos aquí para retrasar la carga de librerías pesadas
            from flask_app import app as main_app
            _real_app = main_app
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"BOOT ERROR: {e}")
            
            # App de emergencia que reporta el error
            error_app = Flask(__name__)
            @error_app.route('/<path:path>')
            @error_app.route('/')
            def boot_error(path=None):
                return jsonify({
                    "error": "FUNCTION_BOOT_FAILED",
                    "details": str(e),
                    "traceback": error_details
                }), 500
            _real_app = error_app
    return _real_app

# Proxy de rutas para atrapar el error
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    real_app = get_real_app()
    # Usamos el dispatch de Flask para delegar la petición
    with real_app.test_request_context(
        path=request.path,
        base_url=request.base_url,
        query_string=request.query_string,
        method=request.method,
        headers=request.headers,
        data=request.get_data()
    ):
        try:
            return real_app.full_dispatch_request()
        except Exception as e:
            return jsonify({"error": "RUNTIME_DISPATCH_ERROR", "msg": str(e)}), 500

from flask import request
