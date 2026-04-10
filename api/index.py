# -*- coding: utf-8 -*-
import os
import sys
import uuid
import datetime
import json
import traceback
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS

# Añadimos el directorio raíz al path para que encuentre los módulos locales si se separan
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Importamos lógica local (Intentando ser lo más autocontenido posible)
try:
    from ai_services import analyze_goal_with_ai, simulate_payment_and_unlock
    from exercises_data import exercises_data
except Exception as e:
    print(f"Error importando módulos locales: {e}")
    exercises_data = []

app = Flask(__name__, static_folder=os.path.join(ROOT_DIR, 'app'), static_url_path='')
CORS(app)

# Configuración de base de datos segura para Serverless
DB_FILE = os.path.join(ROOT_DIR, 'mtfitness.db')

class DbWrapper:
    def __init__(self, conn, is_pg):
        self.conn = conn
        self.is_pg = is_pg
    def cursor(self): return self.conn.cursor()
    def commit(self): self.conn.commit()
    def close(self): self.conn.close()
    
    def execute(self, query, params=()):
        if self.is_pg:
            query = query.replace('?', '%s').replace('DATETIME', 'TIMESTAMP').replace('AUTOINCREMENT', '')
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur
        else:
            return self.conn.execute(query, params)

    def fetchone(self, cur):
        if not cur: return None
        res = cur.fetchone()
        if res and self.is_pg:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, res))
        return dict(res) if res and not isinstance(res, tuple) else res

    def fetchall(self, cur):
        if not cur: return []
        res = cur.fetchall()
        if self.is_pg:
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in res]
        return [dict(r) if not isinstance(r, tuple) else r for r in res]

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        import pg8000
        import ssl
        try:
            url_clean = db_url.replace('postgresql://', '').replace('postgres://', '')
            user_pass, host_port_db = url_clean.split('@')
            user, password = user_pass.split(':')
            host_port, dbname = host_port_db.split('/')
            if ':' in host_port:
                host, port = host_port.split(':')
            else:
                host, port = host_port, 5432
            
            conn = pg8000.connect(user=user, password=password, host=host, port=int(port), database=dbname, ssl_context=ssl.create_default_context())
            return DbWrapper(conn, True)
        except Exception as e:
            print(f"ERROR CONNECTING TO NEON: {e}")
            raise e
    else:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return DbWrapper(conn, False)

# --- RUTAS PRINCIPALES ---

@app.route('/')
def index_root():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/uploads/exercises/<path:path>')
def serve_exercise_images(path):
    return send_from_directory(os.path.join(ROOT_DIR, 'uploads', 'exercises'), path)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "db": "connected" if os.environ.get('DATABASE_URL') else "local"})

# --- Mantenemos el resto del código simplificado para evitar errores de arranque ---
# Una vez que esto funcione, restauraremos las rutas de Auth y Admin.

if __name__ == "__main__":
    app.run(debug=True)
