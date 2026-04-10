# -*- coding: utf-8 -*-
import os
import sys
import uuid
import datetime
import json
import traceback
import smtplib
from email.mime.text import MIMEText
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS

# --- CONFIGURACIÓN DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# --- IMPORTACIÓN DE LÓGICA LOCAL ---
try:
    from ai_services import analyze_goal_with_ai, simulate_payment_and_unlock
    from exercises_data import exercises_data
except Exception as e:
    print(f"Error importando módulos locales: {e}")
    exercises_data = []

app = Flask(__name__, static_folder=os.path.join(ROOT_DIR, 'app'), static_url_path='')
CORS(app)

# --- BASE DE DATOS (CONEXIÓN SEGURA PG8000) ---
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
            # Adaptamos query de SQLite a Postgres
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
        url_clean = db_url.replace('postgresql://', '').replace('postgres://', '')
        user_pass, host_port_db = url_clean.split('@')
        user, password = user_pass.split(':')
        host_port, dbname = host_port_db.split('/')
        host, port = host_port.split(':') if ':' in host_port else (host_port, 5432)
        conn = pg8000.connect(user=user, password=password, host=host, port=int(port), database=dbname, ssl_context=ssl.create_default_context())
        return DbWrapper(conn, True)
    else:
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return DbWrapper(conn, False)

# --- MIDDLEWARE DE AUTENTICACIÓN ---
def require_auth(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            t = request.headers.get('Authorization')
            if not t: return jsonify({'error': 'Faltan credenciales.'}), 401
            t = t.replace('Bearer ', '')
            conn = get_db()
            user_res = conn.execute("SELECT * FROM users WHERE token = %s" if conn.is_pg else "SELECT * FROM users WHERE token = ?", (t,))
            user = conn.fetchone(user_res)
            conn.close()
            if not user: return jsonify({'error': 'Token inválido'}), 401
            if user['status'] != 'APPROVED': return jsonify({'error': 'Cuenta pendiente.'}), 403
            if roles and user['role'] not in roles: return jsonify({'error': 'Rango Denegado.'}), 403
            return f(dict(user), *args, **kwargs)
        return decorated
    return decorator

# --- RUTAS DE AUTENTICACIÓN ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    q = "SELECT * FROM users WHERE email = %s AND password = %s" if conn.is_pg else "SELECT * FROM users WHERE email = ? AND password = ?"
    user_res = conn.execute(q, (data.get('email'), data.get('password')))
    user_row = conn.fetchone(user_res)
    conn.close()
    
    if user_row:
        user = dict(user_row)
        if user['status'] != 'APPROVED': return jsonify({'error': 'Cuenta pendiente.'}), 403
        return jsonify({
            'token': user['token'], 'role': user['role'], 'name': user['name'], 'id': user['id'], 'email': user['email']
        })
    return jsonify({'error': 'Email o contraseña incorrecta'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db()
    q_check = "SELECT id FROM users WHERE email = %s" if conn.is_pg else "SELECT id FROM users WHERE email = ?"
    if conn.fetchone(conn.execute(q_check, (data.get('email'),))):
        conn.close(); return jsonify({'error': 'El email ya existe'}), 400
        
    uid = str(uuid.uuid4())
    token = "token-" + str(uuid.uuid4())
    role = 'ADMIN' if data.get('email') == 'mitorrgo@gmail.com' else 'CLIENT'
    status = 'APPROVED' if role == 'ADMIN' else 'PENDING'
    
    q_ins = """INSERT INTO users (id, email, password, name, role, status, token) VALUES (%s,%s,%s,%s,%s,%s,%s)""" if conn.is_pg else \
            """INSERT INTO users (id, email, password, name, role, status, token) VALUES (?,?,?,?,?,?,?)"""
    conn.execute(q_ins, (uid, data.get('email'), data.get('password'), data.get('name'), role, status, token))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Registrado.', 'status': status, 'token': token, 'role': role})

# --- RUTA DE CONTACTO ---
@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    goal = data.get('objective')
    
    try:
        msg = MIMEText(f"Nueva solicitud de asesoría:\nNombre: {name}\nEmail: {email}\nObjetivo: {goal}")
        msg['Subject'] = f"SOLICITUD WEB: {name}"
        msg['From'] = "info@mtfitness.es"
        msg['To'] = "info@mtfitness.es"
        
        with smtplib.SMTP('smtp.ionos.es', 587) as s:
            s.starttls()
            s.login("info@mtfitness.es", "mtfitness2026")
            s.send_message(msg)
        return jsonify({"status": "success", "message": "Solicitud enviada"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- RUTAS DE CLIENTE ---
@app.route('/api/client/my_workout')
@require_auth(roles=['CLIENT'])
def client_workout(user):
    conn = get_db()
    q = """SELECT ue.*, e.name, e.icon_path FROM user_exercises ue JOIN exercises e ON ue.exercise_id = e.id WHERE ue.user_id = %s""" if conn.is_pg else \
        """SELECT ue.*, e.name, e.icon_path FROM user_exercises ue JOIN exercises e ON ue.exercise_id = e.id WHERE ue.user_id = ?"""
    res = conn.fetchall(conn.execute(q, (user['id'],)))
    conn.close()
    return jsonify(res)

# --- RUTAS ESTÁTICAS (IMÁGENES Y WEB) ---
@app.route('/')
def index_root():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), path)

@app.route('/uploads/exercises/<path:path>')
def serve_exercise_images(path):
    return send_from_directory(os.path.join(ROOT_DIR, 'uploads', 'exercises'), path)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    app.run(debug=True)
