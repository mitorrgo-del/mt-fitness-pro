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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

app = Flask(__name__, static_folder=os.path.join(ROOT_DIR, 'app'), static_url_path='')
CORS(app)

# --- DB CONNECTION PG8000 ---
def get_db_conn():
    db_url = os.environ.get('DATABASE_URL')
    import pg8000
    import ssl
    url_clean = db_url.replace('postgresql://', '').replace('postgres://', '')
    user_pass, host_port_db = url_clean.split('@')
    user, password = user_pass.split(':')
    host_port, dbname = host_port_db.split('/')
    host, port = host_port.split(':') if ':' in host_port else (host_port, 5432)
    return pg8000.connect(user=user, password=password, host=host, port=int(port), database=dbname, ssl_context=ssl.create_default_context())

# --- LOGIN ROUTE (FIXED) ---
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Ensure tables exist
    cur.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT, role TEXT, status TEXT, token TEXT, phone TEXT, access_until TEXT)")
    
    # Ensure Admin exists
    cur.execute("SELECT id FROM users WHERE email = %s", (email,))
    if not cur.fetchone() and email == 'mitorrgo@gmail.com':
        uid = str(uuid.uuid4())
        token = "token-" + str(uuid.uuid4())
        cur.execute("INSERT INTO users (id, email, password, name, role, status, token) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (uid, 'mitorrgo@gmail.com', 'admin123', 'Coach Mitor', 'ADMIN', 'APPROVED', token))
        conn.commit()

    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    res = cur.fetchone()
    if res:
        cols = [d[0] for d in cur.description]
        user = dict(zip(cols, res))
        conn.close()
        if user['status'] != 'APPROVED': return jsonify({'error': 'Cuenta pendiente.'}), 403
        return jsonify({'token': user['token'], 'role': user['role'], 'name': user['name'], 'id': user['id'], 'email': user['email']})
    
    conn.close()
    return jsonify({'error': 'Email o contraseña incorrecta'}), 401

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
