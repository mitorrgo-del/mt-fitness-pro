from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import sqlite3
import os
import uuid
import datetime
import werkzeug.utils
from functools import wraps
from ai_services import analyze_goal_with_ai, simulate_payment_and_unlock
import openai
import requests
import json
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Buscar .env en raíz o en secrets de Render
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(dotenv_path):
    dotenv_path = '/etc/secrets/.env'

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"DEBUG: Cargando variables desde {dotenv_path}")
else:
    load_dotenv() # Fallback a env vars del S.O.
    print("DEBUG: Intentando cargar variables de entorno del sistema")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "sk-proj-YOUR_API_KEY_HERE")

app = Flask(__name__, static_folder='app')
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'mtfitness.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class DbWrapper:
    def __init__(self, conn, is_pg):
        self.conn = conn
        self.is_pg = is_pg
    def cursor(self):
        return self.conn.cursor()
    def execute(self, query, params=()):
        if self.is_pg:
            query = query.replace('?', '%s')
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur
        else:
            return self.conn.execute(query, params)
    def executemany(self, query, params=()):
        if self.is_pg:
            query = query.replace('?', '%s')
            cur = self.conn.cursor()
            cur.executemany(query, params)
            return cur
        else:
            return self.conn.executemany(query, params)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()
    def fetchone(self, cur=None):
        if cur is None: return None
        if hasattr(cur, 'fetchone'):
            res = cur.fetchone()
        else:
            res = cur
        return dict(res) if res and not isinstance(res, tuple) else res
    def fetchall(self, cur=None):
        if cur is None: return []
        if hasattr(cur, 'fetchall'):
            res = cur.fetchall()
        else:
            res = cur
        return [dict(r) if not isinstance(r, tuple) else r for r in res]

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(db_url, sslmode='require', cursor_factory=RealDictCursor)
        return DbWrapper(conn, True)
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        return DbWrapper(conn, False)

def init_db():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print("Production DB (Postgres) detected. Assuming migrations are handled or running init...")
    
    conn_wrap = get_db()
    c = conn_wrap # Fix NameError c in entire script scope
    
    # We will skip DROP tables in production normally, but for the first run:
    if os.environ.get('RESEED_DB'):
        conn_wrap.execute("DROP TABLE IF EXISTS exercises")
        conn_wrap.execute("DROP TABLE IF EXISTS foods")
    
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT, 
        role TEXT, status TEXT, token TEXT, phone TEXT, 
        objective_weight REAL, routine_weeks INTEGER DEFAULT 4, access_until TEXT,
        bot_active INTEGER DEFAULT 1
    )''')
    
    # PRO Exercises Catalog
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, muscle_group TEXT
    )''')
    
    # PRO Foods Catalog (per 100g)
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT,
        kcal REAL, protein REAL, carbs REAL, fat REAL
    )''')
    
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, date TEXT DEFAULT CURRENT_TIMESTAMP,
        weight REAL, waist REAL, chest REAL, hip REAL, thigh REAL, biceps REAL
    )''')

    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, date TEXT DEFAULT CURRENT_TIMESTAMP,
        weight REAL, photo_front TEXT, photo_side TEXT, photo_back TEXT
    )''')

    # PRO Assigned Food Plans (Admin -> Client)
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS user_foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, food_id INTEGER,
        meal_name TEXT, grams REAL, day_name TEXT DEFAULT 'Día 1',
        added_date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # PRO Assigned Workout Plans (Admin -> Client)
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS user_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, exercise_id INTEGER,
        day_of_week TEXT, sets TEXT, reps TEXT, rest TEXT,
        target_muscles TEXT, set_type TEXT DEFAULT 'NORMAL', 
        combined_with INTEGER,
        added_date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn_wrap.commit()

    
    # MIGRACIÓN SEGURA: Añadir columnas si no existen
    def column_exists(table, column):
        try:
            if conn_wrap.is_pg:
                c_check = conn_wrap.cursor()
                c_check.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
                res = c_check.fetchone()
                return res is not None
            else:
                c_check = conn_wrap.cursor()
                c_check.execute(f"PRAGMA table_info({table})")
                cols = c_check.fetchall()
                return any(col['name'] == column for col in cols)
        except Exception as e:
            print(f"Error checking column {column} in {table}: {e}")
            return False

    columns_to_add = [
        ("user_exercises", "set_type", "TEXT DEFAULT 'NORMAL'"),
        ("user_exercises", "combined_with", "INTEGER"),
        ("user_exercises", "target_muscles", "TEXT"),
        ("user_foods", "day_name", "TEXT DEFAULT 'Día 1'"),
        ("users", "surname", "TEXT"),
        ("users", "age", "INTEGER"),
        ("users", "height", "REAL"),
        ("users", "current_weight", "REAL"),
        ("users", "objective", "TEXT"),
        ("users", "profile_image", "TEXT"),
        ("users", "biceps", "REAL"),
        ("users", "thigh", "REAL"),
        ("users", "hip", "REAL"),
        ("users", "waist", "REAL"),
        ("reports", "biceps", "REAL"),
        ("reports", "thigh", "REAL"),
        ("reports", "hip", "REAL"),
        ("reports", "waist", "REAL"),
    ]
    for table, col, defn in columns_to_add:
        if not column_exists(table, col):
            try:
                print(f"MIGRATION: Adding column {col} to {table}...")
                conn_wrap.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
                conn_wrap.commit()
            except Exception as e:
                print(f"Failed to add {col} to {table}: {e}")
                if conn_wrap.is_pg: conn_wrap.conn.rollback()
        else:
            print(f"DEBUG: Column {col} already exists in {table}")

    # PRO Meal Tracking
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS meal_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, date TEXT, meal_name TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # PRIVACY & COACHING CHAT
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, sender_role TEXT, message TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # PRO Workout Weight Logging
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS workout_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, assignment_id INTEGER,
        set_number INTEGER, weight_kg REAL, date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(assignment_id) REFERENCES user_exercises(id)
    )''')

    # MARKETING LEADS
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS marketing_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        last_goal TEXT,
        status TEXT DEFAULT 'COLD',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_followup DATETIME
    )''')

    def sync_pro_exercises():
        """Sincroniza el catálogo de 873 ejercicios reales."""
        # Se define aquí dentro para no ensuciar el scope global o se puede mover fuera
        conn = get_db()
        current = conn.execute("SELECT count(*) as count FROM exercises").fetchone()
        count = current['count'] if isinstance(current, dict) else (current[0] if current else 0)
        
        # Si faltan muchos, o si queremos forzar una actualización de nombres
        # Para v1.1.0 forzamos si no detectamos el formato con paréntesis en alguno representativo
        sample = conn.execute("SELECT name FROM exercises LIMIT 5").fetchall()
        needs_migration = not any('(' in (row['name'] if isinstance(row, dict) else row[0]) for row in sample)
        
        if count < 800 or needs_migration:
            print(f"MIGRATION: Syncing {len(exercises_data)} PRO exercises...")
            # Si es migración crítica de nombres, podemos limpiar o solo insertar los que faltan
            # Por seguridad en init_db, solo insertamos los que no existen por Display Name
            # Pero para que el IconMapper funcione, necesitamos el sufijo.
            import re
            def translate_name(name):
                replacements = {
                    'Barbell': 'con Barra', 'Dumbbell': 'con Mancuernas', 'Bench Press': 'Press de Banca',
                    'Incline': 'Inclinado', 'Decline': 'Declinado', 'Squat': 'Sentadilla', 'Lunge': 'Zancada',
                    'Deadlift': 'Peso Muerto', 'Row': 'Remo', 'Curl': 'Curl', 'Extension': 'Extensión',
                    'Extensions': 'Extensión', 'Pull-Up': 'Dominada', 'Pulldown': 'Jalón', 'Front Raise': 'Elevación Frontal',
                    'Shoulder Press': 'Press de Hombro', 'Lateral Raise': 'Elevación Lateral', 'Raise': 'Elevación',
                    'Crunch': 'Crunch Abdominal', 'Plank': 'Plancha', 'Machine': 'en Máquina', 'Cable': 'en Polea'
                }
                disp = name.replace('_', ' ').replace('-', ' ')
                for eng, esp in replacements.items():
                    disp = re.sub(r'(?i)\b' + re.escape(eng) + r'\b', esp, disp)
                return f"{disp} ({name})"

            # Insertar en bloques para eficiencia
            to_insert = []
            for name_only, mg in exercises_data:
                display_name = translate_name(name_only)
                # Si no existe este nombre exacto, lo añadimos
                # En v1.1.0 esto poblará la DB con los nombres nuevos
                to_insert.append((display_name, mg))
            
            # Borramos antiguos si detectamos que son los "cortos" (sin paréntesis)
            if needs_migration:
                conn.execute("DELETE FROM exercises")
                conn.commit()

            conn.executemany("INSERT INTO exercises (name, muscle_group) VALUES (?, ?)", to_insert)
            conn.commit()
    
    sync_pro_exercises()

    # Check if we have foods
    res_f = conn_wrap.execute("SELECT count(*) as count FROM foods")
    row_f = conn_wrap.fetchone(res_f)
    count_foods = row_f['count'] if isinstance(row_f, dict) else (row_f[0] if row_f else 0)
    if count_foods == 0:
        foods = [
            # PROTEINAS (Valores aprox. por 100g en crudo)
            ('Pechuga de Pollo', 'Proteínas', 113, 23.5, 0, 1.2),
            ('Contramuslo de Pollo (sin piel)', 'Proteínas', 120, 20, 0, 4),
            ('Solomillo de Ternera', 'Proteínas', 130, 21, 0, 5),
            ('Ternera picada magra', 'Proteínas', 140, 20, 0, 6),
            ('Lomo de Cerdo', 'Proteínas', 145, 21, 0, 6.4),
            ('Pavo (Pechuga)', 'Proteínas', 105, 24, 0, 1),
            ('Salmón fresco', 'Proteínas', 208, 20, 0, 13),
            ('Atún al natural (lata)', 'Proteínas', 110, 25, 0, 1),
            ('Merluza', 'Proteínas', 80, 16, 0, 1.5),
            ('Bacalao fresco', 'Proteínas', 82, 18, 0, 0.7),
            ('Lubina', 'Proteínas', 97, 18.5, 0, 2.5),
            ('Dorada', 'Proteínas', 115, 19.8, 0, 3.9),
            ('Gambas / Langostinos', 'Proteínas', 95, 20, 0, 1.5),
            ('Calamares', 'Proteínas', 90, 16, 3, 1.3),
            ('Pulpo cocido', 'Proteínas', 85, 17, 2, 1),
            ('Tofu firme', 'Proteínas', 144, 15, 4, 8),
            ('Heura (Bocados)', 'Proteínas', 126, 18, 0.7, 3),
            ('Lomo embuchado', 'Proteínas', 210, 31, 1, 8),
            ('Jamón Serrano (magro)', 'Proteínas', 240, 30, 0, 13),
            ('Huevo entero (L)', 'Proteínas', 155, 13, 1, 11),
            ('Clara de huevo', 'Proteínas', 48, 11, 0.7, 0.2),

            # HIDRATOS (Valores por 100g cocinado / seco segun proceda)
            ('Arroz Blanco (cocido)', 'Hidratos', 130, 2.7, 28, 0.3),
            ('Arroz Integral (cocido)', 'Hidratos', 111, 2.6, 23, 0.9),
            ('Arroz Basmati (cocido)', 'Hidratos', 121, 3.5, 25, 0.4),
            ('Pasta de trigo (cocida)', 'Hidratos', 155, 5.5, 30, 1),
            ('Pasta Integral (cocida)', 'Hidratos', 125, 5, 25, 0.8),
            ('Couscous (cocido)', 'Hidratos', 112, 3.8, 23, 0.2),
            ('Quinoa (cocida)', 'Hidratos', 120, 4.4, 21, 2),
            ('Avena en copos (seco)', 'Hidratos', 380, 13, 60, 7),
            ('Patata cocida', 'Hidratos', 85, 2, 19, 0.1),
            ('Boniato / Batata cocida', 'Hidratos', 90, 1.5, 20, 0.1),
            ('Pan Integral', 'Hidratos', 250, 9, 45, 3),
            ('Pan de Centeno', 'Hidratos', 260, 8, 48, 3),
            ('Garbanzos (cocidos)', 'Hidratos', 160, 9, 27, 2.5),
            ('Lentejas (cocidas)', 'Hidratos', 115, 9, 20, 0.5),
            ('Judías Blancas (cocidas)', 'Hidratos', 140, 9, 25, 0.5),
            ('Guisantes (cocidos)', 'Hidratos', 80, 5, 14, 0.5),
            ('Maíz dulce', 'Hidratos', 85, 3, 18, 1),
            ('Tortita de Arroz', 'Hidratos', 385, 8, 80, 3),
            ('Tortilla de Maíz', 'Hidratos', 215, 5, 45, 3),
            ('Yuca cocida', 'Hidratos', 160, 1.4, 38, 0.3),

            # GRASAS
            ('Aceite de Oliva (AOVE)', 'Grasas', 884, 0, 0, 100),
            ('Aguacate', 'Grasas', 160, 2, 8, 14),
            ('Nueces', 'Grasas', 650, 15, 14, 65),
            ('Almendras', 'Grasas', 580, 21, 21, 50),
            ('Avellanas', 'Grasas', 630, 15, 16, 60),
            ('Cacahuetes', 'Grasas', 570, 25, 16, 49),
            ('Pistachos', 'Grasas', 560, 20, 27, 45),
            ('Anacardos', 'Grasas', 555, 18, 30, 44),
            ('Semillas de Chía', 'Grasas', 490, 16, 42, 30),
            ('Semillas de Calabaza', 'Grasas', 560, 30, 10, 49),
            ('Mantequilla de Cacahuete', 'Grasas', 590, 25, 20, 50),
            ('Olivas Negras', 'Grasas', 115, 1, 6, 11),
            ('Olivas Verdes', 'Grasas', 145, 1, 4, 15),

            # VERDURAS
            ('Brócoli', 'Verduras', 34, 2.8, 7, 0.4),
            ('Espinacas', 'Verduras', 23, 2.9, 3.6, 0.4),
            ('Espárragos', 'Verduras', 20, 2.2, 4, 0.1),
            ('Judías Verdes', 'Verduras', 31, 1.8, 7, 0.1),
            ('Calabacín', 'Verduras', 17, 1.2, 3, 0.3),
            ('Berenjena', 'Verduras', 25, 1, 6, 0.2),
            ('Pimiento Rojo', 'Verduras', 30, 1, 6, 0.3),
            ('Pimiento Verde', 'Verduras', 20, 1, 4.6, 0.2),
            ('Cebolla', 'Verduras', 40, 1, 9, 0.1),
            ('Tomate', 'Verduras', 18, 0.9, 4, 0.2),
            ('Pepino', 'Verduras', 15, 0.7, 3.6, 0.1),
            ('Lechuga', 'Verduras', 15, 1.4, 3, 0.2),
            ('Canónigos', 'Verduras', 20, 2, 3.6, 0.4),
            ('Champiñones', 'Verduras', 22, 3, 3, 0.3),
            ('Zanahoria', 'Verduras', 40, 1, 9, 0.2),
            ('Coliflor', 'Verduras', 25, 2, 5, 0.3),
            ('Alcachofa', 'Verduras', 50, 3, 11, 0.2),

            # FRUTAS
            ('Manzana', 'Frutas', 52, 0.3, 14, 0.2),
            ('Plátano', 'Frutas', 90, 1, 23, 0.3),
            ('Pera', 'Frutas', 57, 0.4, 15, 0.1),
            ('Naranja', 'Frutas', 47, 1, 12, 0.1),
            ('Fresas', 'Frutas', 32, 0.7, 8, 0.3),
            ('Arándanos', 'Frutas', 57, 0.7, 14, 0.3),
            ('Frambuesas', 'Frutas', 52, 1.2, 12, 0.6),
            ('Piña', 'Frutas', 50, 0.5, 13, 0.1),
            ('Kiwi', 'Frutas', 61, 1, 15, 0.5),
            ('Mango', 'Frutas', 60, 0.8, 15, 0.4),
            ('Sandía', 'Frutas', 30, 0.6, 8, 0.2),
            ('Melón', 'Frutas', 35, 0.8, 8, 0.2),
            ('Uvas', 'Frutas', 70, 0.7, 17, 0.4),
            ('Ciruela', 'Frutas', 45, 0.7, 11, 0.3),
            ('Melocotón', 'Frutas', 40, 1, 10, 0.3),

            # LACTEOS Y OTROS
            ('Leche Desnatada', 'Lácteos', 34, 3.4, 5, 0.1),
            ('Leche Entera', 'Lácteos', 60, 3.2, 4.8, 3.2),
            ('Yogur Natural 0%', 'Lácteos', 50, 5, 5, 0.1),
            ('Queso Fresco Batido 0%', 'Lácteos', 45, 8, 3.5, 0.1),
            ('Queso Cottage', 'Lácteos', 100, 12, 3, 4),
            ('Queso Mozzarella Light', 'Lácteos', 160, 24, 1, 7),
            ('Whey Protein (80%)', 'Suplementos', 370, 80, 5, 5),
            ('Creatina Monohidrato', 'Suplementos', 0, 0, 0, 0),
            ('Miel', 'Hidratos', 300, 0.3, 80, 0),
            ('Chocolate Negro +85%', 'Grasas', 580, 8, 20, 48)
        ]
        conn_wrap.executemany("INSERT INTO foods (name, category, kcal, protein, carbs, fat) VALUES (?, ?, ?, ?, ?, ?)", foods)

    # Ensure Admin exists
    exists_admin = conn_wrap.fetchone(conn_wrap.execute("SELECT id FROM users WHERE email = 'mitorrgo@gmail.com'"))
    if not exists_admin:
        conn_wrap.execute("INSERT INTO users (id, email, password, name, role, status, token) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (str(uuid.uuid4()), 'mitorrgo@gmail.com', 'admin123', 'Coach Mitor', 'ADMIN', 'APPROVED', 'token-admin-123'))

    conn_wrap.commit()
    conn_wrap.close()

init_db()

def require_auth(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            t = request.headers.get('Authorization')
            if not t: return jsonify({'error': 'Faltan credenciales.'}), 401
            t = t.replace('Bearer ', '')
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE token = ?", (t,)).fetchone()
            conn.close()
            if not user: return jsonify({'error': 'Token inválido'}), 401
            if user['status'] != 'APPROVED': return jsonify({'error': 'Cuenta pendiente.'}), 403
            if roles and user['role'] not in roles: return jsonify({'error': 'Rango Denegado.'}), 403
            return f(dict(user), *args, **kwargs)
        return decorated
    return decorator


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    conn = get_db()
    if conn.execute("SELECT id FROM users WHERE email = ?", (data.get('email'),)).fetchone():
        conn.close(); return jsonify({'error': 'El email ya existe'}), 400
        
    uid = str(uuid.uuid4())
    token = "token-" + str(uuid.uuid4())
    role = 'ADMIN' if data.get('email') == 'mitorrgo@gmail.com' else 'CLIENT'
    status = 'APPROVED' if role == 'ADMIN' else 'PENDING'
    
    conn.execute("""
        INSERT INTO users (
            id, email, password, name, surname, role, status, token, 
            phone, age, height, current_weight, routine_weeks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, data.get('email'), data.get('password'), data.get('name'), data.get('surname', ''), 
        role, status, token, data.get('phone', ''), data.get('age', 0), 
        data.get('height', 0.0), data.get('current_weight', 0.0), 4
    ))
    conn.commit()
    conn.close()
    
    # Notificar al Coach por Email
    if role == 'CLIENT':
        try:
            send_registration_email(data.get('name', 'Nuevo Cliente'), data.get('email', ''))
        except:
            pass

    return jsonify({'message': 'Registrado.', 'status': status, 'token': token, 'role': role, 'name': data.get('name')})

def send_admin_notification(subject, body):
    import smtplib
    from email.mime.text import MIMEText
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "info@mtfitness.es"
        msg['To'] = "info@mtfitness.es"
        
        # Real Ionos SMTP
        s = smtplib.SMTP('smtp.ionos.es', 587)
        s.set_debuglevel(1) # Para ver qué pasa en logs
        s.starttls()
        s.login("info@mtfitness.es", "mtfitness2026")
        s.send_message(msg)
        s.quit()
        print(f"DEBUG: Email sent successfully: {subject}")
    except Exception as e:
        print(f"SMTP NOTIFICATION ERROR: {e}")

def send_registration_email(client_name, client_email):
    subject = f"NUEVO CLIENTE APP: {client_name}"
    body = f"Nuevo registro en la App MT Fitness PRO:\n\nNombre: {client_name}\nEmail: {client_email}\n\nRevisa el Panel de Administración para aprobar el acceso tras confirmar el pago."
    send_admin_notification(subject, body)



@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    user_row = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (data.get('email'), data.get('password'))).fetchone()
    conn.close()
    if user_row:
        user = dict(user_row)
        
        # AUTO-UPGRADE TO ADMIN IF COACH EMAIL
        coach_emails = ['mitorrgo@gmail.com', 'mtfitness2026@gmail.com']
        if user['email'] in coach_emails and user['role'] != 'ADMIN':
            conn = get_db()
            conn.execute("UPDATE users SET role = 'ADMIN' WHERE id = ?", (user['id'],))
            conn.commit()
            user['role'] = 'ADMIN'

        if user['status'] != 'APPROVED': return jsonify({'error': 'Cuenta pendiente.'}), 403
        
        # Check Expiration (only for clients)
        if user['role'] == 'CLIENT' and user['access_until']:
            expiration = datetime.datetime.strptime(user['access_until'], '%Y-%m-%d')
            if datetime.datetime.now() > expiration:
                return jsonify({'error': 'Suscripción caducada. Contacta con tu Coach.'}), 403

        def calc_days_left(access_until):
            if not access_until: return 0
            try:
                exp = datetime.datetime.strptime(access_until, '%Y-%m-%d')
                delta = exp - datetime.datetime.now()
                return max(0, delta.days)
            except: return 0

        return jsonify({
            'token': user['token'], 
            'role': user['role'], 
            'name': user['name'],
            'surname': user.get('surname', ''),
            'email': user['email'],
            'id': user['id'],
            'age': user.get('age'),
            'height': user.get('height'),
            'current_weight': user.get('current_weight'),
            'objective': user.get('objective', ''),
            'days_left': calc_days_left(user.get('access_until')),
            'biceps': user.get('biceps'),
            'thigh': user.get('thigh'),
            'hip': user.get('hip'),
            'waist': user.get('waist'),
        })
    return jsonify({'error': 'Credenciales incorrectas'}), 401

@app.route('/api/profile/update', methods=['POST'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def update_profile(user):
    # Support both JSON and Multipart (for images)
    if request.is_json:
        data = request.json
    else:
        data = request.form
        
    image = request.files.get('profile_image')
    image_filename = None
    
    if image:
        image_filename = f"profile_{user['id']}_{uuid.uuid4().hex}.jpg"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
    try:
        conn = get_db()
        # Si se subió imagen, la actualizamos. Si no, dejamos la que estaba.
        if image_filename:
            conn.execute('''UPDATE users SET 
                name = ?, surname = ?, age = ?, height = ?, current_weight = ?, objective = ?, profile_image = ?,
                biceps = ?, thigh = ?, hip = ?, waist = ?
                WHERE id = ?''', 
                (data.get('name'), data.get('surname'), data.get('age'), data.get('height'), 
                 data.get('current_weight'), data.get('objective'), image_filename,
                 data.get('biceps'), data.get('thigh'), data.get('hip'), data.get('waist'),
                 user['id']))
        else:
            conn.execute('''UPDATE users SET 
                name = ?, surname = ?, age = ?, height = ?, current_weight = ?, objective = ?,
                biceps = ?, thigh = ?, hip = ?, waist = ?
                WHERE id = ?''', 
                (data.get('name'), data.get('surname'), data.get('age'), data.get('height'), 
                 data.get('current_weight'), data.get('objective'),
                 data.get('biceps'), data.get('thigh'), data.get('hip'), data.get('waist'),
                 user['id']))
            
        conn.commit()
        conn.close()
        return jsonify({'message': 'Perfil actualizado', 'profile_image': image_filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
@require_auth(roles=['ADMIN'])
def admin_get_users(admin):
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    
    def calc_days_left(access_until):
        if not access_until: return 0
        try:
            exp = datetime.datetime.strptime(access_until, '%Y-%m-%d')
            delta = exp - datetime.datetime.now()
            return max(0, delta.days)
        except: return 0

    res = []
    for u in users:
        d = dict(u)
        d['days_left'] = calc_days_left(u['access_until'])
        res.append(d)
    return jsonify(res)

@app.route('/api/admin/approve/<target_id>', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_approve_user(admin, target_id):
    conn = get_db()
    conn.execute("UPDATE users SET status = 'APPROVED' WHERE id = ?", (target_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Aprobado'})

@app.route('/api/reports/submit', methods=['POST'])
@require_auth(roles=['CLIENT', 'ADMIN'])
def submit_report(user):
    # --- REGLA DE VIERNES ---
    now = datetime.datetime.now()
    if now.weekday() != 4: # 4 es Viernes
        return jsonify({'error': 'Los reportes solo pueden enviarse los Viernes (00:00 - 23:59).'}), 403
    
    # --- REGLA DE 1 VEZ POR SEMANA ---
    conn = get_db()
    today_str = now.strftime('%Y-%m-%d')
    existing = conn.execute("SELECT id FROM reports WHERE user_id = ? AND date(date) = ?", (user['id'], today_str)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Ya has enviado tu recorte de esta semana.'}), 403

    weight = request.form.get('weight')
    biceps = request.form.get('biceps')
    thigh = request.form.get('thigh')
    hip = request.form.get('hip')
    waist = request.form.get('waist')
    
    front = request.files.get('photo_front')
    side = request.files.get('photo_side')
    back = request.files.get('photo_back')
    
    front_filename = None
    if front:
        front_filename = f"front_{user['id']}_{uuid.uuid4().hex}.jpg"
        front.save(os.path.join(app.config['UPLOAD_FOLDER'], front_filename))
        
    side_filename = None
    if side:
        side_filename = f"side_{user['id']}_{uuid.uuid4().hex}.jpg"
        side.save(os.path.join(app.config['UPLOAD_FOLDER'], side_filename))
        
    back_filename = None
    if back:
        back_filename = f"back_{user['id']}_{uuid.uuid4().hex}.jpg"
        back.save(os.path.join(app.config['UPLOAD_FOLDER'], back_filename))
        
    conn.execute("""
        INSERT INTO reports (user_id, weight, biceps, thigh, hip, waist, photo_front, photo_side, photo_back) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user['id'], weight, biceps, thigh, hip, waist, front_filename, side_filename, back_filename))
    
    # Log detailed measurements
    conn.execute("""
        INSERT INTO measurements (user_id, weight, biceps, thigh, hip, waist) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user['id'], weight, biceps, thigh, hip, waist))
    
    conn.commit()
    conn.close()
    return jsonify({'message': 'Reporte semanal enviado correctamente. ¡Buen trabajo, sigues en el camino PRO!'})

@app.route('/api/measurements', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def get_measurements(user):
    target_id = request.args.get('user_id', user['id'])
    # Security: Client can only see their own measurements. Admin can see any.
    if user['role'] == 'CLIENT' and user['id'] != target_id:
        return jsonify({'error': 'No autorizado'}), 403
        
    conn = get_db()
    measurements = conn.execute("SELECT * FROM measurements WHERE user_id = ? ORDER BY date ASC", (target_id,)).fetchall()
    conn.close()
    return jsonify([dict(m) for m in measurements])

@app.route('/api/reports/history/<user_id>', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def get_reports(user, user_id):
    # Security: Client can only see their own reports. Admin can see any.
    if user['role'] == 'CLIENT' and user['id'] != user_id:
        return jsonify({'error': 'No autorizado'}), 403
        
    conn = get_db()
    reports = conn.execute("SELECT * FROM reports WHERE user_id = ? ORDER BY date DESC", (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in reports])

@app.route('/api/admin/add_food', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_add_food(admin):
    data = request.json
    try:
        conn = get_db()
        conn.execute("INSERT INTO foods (name, category, kcal, protein, carbs, fat) VALUES (?, ?, ?, ?, ?, ?)",
                     (data['name'], data['category'], data['kcal'], data['protein'], data['carbs'], data['fat']))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok', 'message': 'Alimento añadido al catálogo'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/add_exercise', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_add_exercise(admin):
    data = request.json
    try:
        conn = get_db()
        # Forzamos MAYÚSCULAS en el muscle_group para evitar líos de acentos
        muscle = data['muscle_group'].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U')
        conn.execute("INSERT INTO exercises (name, muscle_group) VALUES (?, ?)",
                     (data['name'], muscle))
        conn.commit()
        conn.close()
        return jsonify({'status': 'ok', 'message': 'Ejercicio añadido al catálogo'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/master/exec', methods=['POST'])
@require_auth(roles=['ADMIN'])
def master_exec(admin):
    data = request.json
    cmd = data.get('cmd')
    # SECRET MASTER TOKEN (HARDCODED FOR PRO)
    if data.get('master_token') != 'MT_MASTER_PRO_2026':
        return jsonify({'error': 'Token maestro inválido'}), 403
        
    try:
        import subprocess
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
        return jsonify({'status': 'ok', 'output': result})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'output': e.output if hasattr(e, 'output') else str(e)})
    except Exception as e:
        return jsonify({'status': 'error', 'output': str(e)})

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/admin/set_weeks/<target_id>', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_set_weeks(admin, target_id):
    conn = get_db()
    data = request.json
    conn.execute("UPDATE users SET routine_weeks = ? WHERE id = ?", (data.get('weeks', 4), target_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Semanas actualizadas'})

@app.route('/api/admin/add_subscription/<target_id>', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_add_subscription(admin, target_id):
    conn = get_db()
    data = request.json
    days = data.get('days', 30)
    
    # Check current access
    u = conn.execute("SELECT access_until FROM users WHERE id = ?", (target_id,)).fetchone()
    base_date = datetime.datetime.now()
    if u and u['access_until']:
        curr_exp = datetime.datetime.strptime(u['access_until'], '%Y-%m-%d')
        if curr_exp > base_date: base_date = curr_exp
        
    new_exp = (base_date + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    conn.execute("UPDATE users SET access_until = ? WHERE id = ?", (new_exp, target_id))
    conn.commit(); conn.close()
    return jsonify({'message': f'Suscripción ampliada hasta {new_exp}'})

@app.route('/api/admin/toggle_bot/<target_id>', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_toggle_bot(admin, target_id):
    conn = get_db()
    u = conn.execute("SELECT bot_active FROM users WHERE id = ?", (target_id,)).fetchone()
    if u:
        new_val = 0 if u['bot_active'] else 1
        conn.execute("UPDATE users SET bot_active = ? WHERE id = ?", (new_val, target_id))
        conn.commit()
    conn.close()
    return jsonify({'message': 'Bot toggled', 'new_state': new_val})

# ---- PRO FOOD ASSIGNMENT ENDPOINTS ----

@app.route('/api/client/log_meal', methods=['POST'])
@require_auth(roles=['CLIENT', 'ADMIN'])
def log_meal(user):
    data = request.json
    meal_name = data.get('meal_name')
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db()
    c = conn.cursor()
    
    # Check if already logged to avoid dupes
    exists = c.execute("SELECT 1 FROM meal_logs WHERE user_id = ? AND date = ? AND meal_name = ?", (user['id'], date_str, meal_name)).fetchone()
    if not exists:
        c.execute("INSERT INTO meal_logs (user_id, date, meal_name) VALUES (?, ?, ?)", (user['id'], date_str, meal_name))
        conn.commit()
    conn.close()
    
    return jsonify({'message': 'Comida registrada con éxito'})

# ---- PRO WORKOUT ASSIGNMENT ENDPOINTS ----
@app.route('/api/admin/exercises', methods=['GET'])
@require_auth(roles=['ADMIN'])
def catalog_exercises(admin):
    conn = get_db(); recs = conn.execute("SELECT * FROM exercises ORDER BY muscle_group, name").fetchall(); conn.close()
    return jsonify([dict(r) for r in recs])

@app.route('/api/admin/foods', methods=['GET'])
@require_auth(roles=['ADMIN'])
def catalog_foods(admin):
    conn = get_db(); recs = conn.execute("SELECT * FROM foods ORDER BY category, name").fetchall(); conn.close()
    return jsonify([dict(r) for r in recs])

@app.route('/api/admin/assign_exercise', methods=['POST'])
@require_auth(roles=['ADMIN'])
def assign_exercise(admin):
    data = request.json
    try:
        conn = get_db()
        conn.execute('''
            INSERT INTO user_exercises (user_id, exercise_id, day_of_week, sets, reps, rest, target_muscles, set_type, combined_with) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', 
        (data['user_id'], data['exercise_id'], data['day_of_week'], data['sets'], data['reps'], 
         data.get('rest', ''), data.get('target_muscles', ''), data.get('set_type', 'NORMAL'), data.get('combined_with')))
        conn.commit(); conn.close()
        return jsonify({'message': 'Ejercicio configurado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/remove_exercise/<id>', methods=['DELETE'])
@require_auth(roles=['ADMIN'])
def admin_remove_exercise_assignment(admin, id):
    conn = get_db(); conn.execute("DELETE FROM user_exercises WHERE id = ?", (id,)); conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/admin/catalog/exercise/<id>', methods=['DELETE'])
@require_auth(roles=['ADMIN'])
def admin_delete_catalog_exercise(admin, id):
    conn = get_db()
    # Check if used? For now just delete as user asked.
    conn.execute("DELETE FROM exercises WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Ejercicio eliminado del catálogo'})

@app.route('/api/admin/update_exercise/<int:assignment_id>', methods=['PUT', 'POST'])
@require_auth(roles=['ADMIN'])
def admin_update_exercise(admin, assignment_id):
    data = request.json
    conn = get_db()
    conn.execute('''
        UPDATE user_exercises SET sets = ?, reps = ?, rest = ?, target_muscles = ?, set_type = ?, combined_with = ?
        WHERE id = ?
    ''', (data['sets'], data['reps'], data.get('rest', ''), data.get('target_muscles', ''), 
          data.get('set_type', 'NORMAL'), data.get('combined_with'), assignment_id))
    conn.commit(); conn.close()
    return jsonify({'message': 'Asignación de ejercicio actualizada'})

@app.route('/api/admin/update_food/<int:assignment_id>', methods=['PUT', 'POST'])
@require_auth(roles=['ADMIN'])
def admin_update_food(admin, assignment_id):
    data = request.json
    conn = get_db()
    conn.execute('''
        UPDATE user_foods SET grams = ?, meal_name = ?, day_name = ?
        WHERE id = ?
    ''', (data['grams'], data['meal_name'], data.get('day_name', 'Día 1'), assignment_id))
    conn.commit(); conn.close()
    return jsonify({'message': 'Asignación de comida actualizada'})

@app.route('/api/admin/assign_food', methods=['POST'])
@require_auth(roles=['ADMIN'])
def assign_food(admin):
    data = request.json
    try:
        conn = get_db()
        conn.execute("INSERT INTO user_foods (user_id, food_id, meal_name, grams, day_name) VALUES (?, ?, ?, ?, ?)",
                     (data['user_id'], data['food_id'], data['meal_name'], data['grams'], data.get('day_name', 'Día 1')))
        conn.commit(); conn.close()
        return jsonify({'message': 'Alimento configurado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/remove_food/<id>', methods=['DELETE'])
@require_auth(roles=['ADMIN'])
def admin_remove_food(admin, id):
    conn = get_db(); conn.execute("DELETE FROM user_foods WHERE id = ?", (id,)); conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/client/my_workout', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def client_workout(user):
    target_id = request.args.get('user_id', user['id'])
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT ue.id as assignment_id, e.name, e.muscle_group, ue.day_of_week, ue.sets, ue.reps, ue.rest, 
               ue.target_muscles, ue.set_type, ue.combined_with
        FROM user_exercises ue
        JOIN exercises e ON ue.exercise_id = e.id
        WHERE ue.user_id = ?
        ORDER BY ue.day_of_week, ue.id
    ''', (target_id,))
    data = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(data)

def _get_diet_data_logic(user):
    target_id = request.args.get('user_id', user['id'])
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT uf.id as assignment_id, f.name, f.category, f.kcal, f.protein, f.carbs, f.fat, 
               uf.meal_name, uf.grams, uf.day_name,
               (f.kcal * uf.grams / 100) as calc_kcal,
               (f.protein * uf.grams / 100) as calc_protein,
               (f.carbs * uf.grams / 100) as calc_carbs,
               (f.fat * uf.grams / 100) as calc_fat
        FROM user_foods uf
        JOIN foods f ON uf.food_id = f.id
        WHERE uf.user_id = ?
        ORDER BY uf.day_name, uf.meal_name
    ''', (target_id,))
    data = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/api/client/my_plan', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def client_plan_legacy(user):
    return _get_diet_data_logic(user)

@app.route('/api/client/my_diet', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def client_diet(user):
    return _get_diet_data_logic(user)

@app.route('/api/client/my_workout_logs', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def get_workout_logs(user):
    target_id = request.args.get('user_id', user['id'])
    date_str = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    conn = get_db()
    logs = conn.execute("SELECT * FROM workout_logs WHERE user_id = ? AND date = ?", (target_id, date_str)).fetchall()
    conn.close()
    return jsonify([dict(l) for l in logs])

@app.route('/api/client/log_workout', methods=['POST'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def log_workout(user):
    data = request.json
    assignment_id = data.get('assignment_id')
    logs = data.get('logs')
    
    if not assignment_id or not logs:
        return jsonify({'error': 'Missing log data'}), 400
        
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db()
    c = conn.cursor()
    for log in logs:
        c.execute('''
            INSERT INTO workout_logs (user_id, assignment_id, set_number, weight_kg, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['id'], assignment_id, log['set'], float(log['weight']), date_str))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ---- MEASUREMENTS TRACKING ----
@app.route('/api/measurements', methods=['GET', 'POST'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def handle_measurements(user):
    conn = get_db()
    if request.method == 'POST':
        data = request.json
        q = "INSERT INTO measurements (user_id, date, weight, waist, chest, hip, thigh, biceps) VALUES (?, date('now'), ?, ?, ?, ?, ?, ?)"
        conn.execute(q, (user['id'], data.get('weight'), data.get('waist'), data.get('chest'), data.get('hip'), data.get('thigh'), data.get('biceps')))
        conn.commit(); conn.close()
        return jsonify({'message': 'Check-in guardado'}), 201
    else:
        target_id = request.args.get('user_id', user['id'])
        if user['role'] != 'ADMIN' and target_id != user['id']: target_id = user['id']
        records = conn.execute("SELECT * FROM measurements WHERE user_id = ? ORDER BY date DESC", (target_id,)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in records])

# ---- PROFILE ROUTES ----
@app.route('/api/client/profile', methods=['GET', 'PUT'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def manage_profile(user):
    conn = get_db()
    
    if request.method == 'PUT':
        data = request.json
        c = conn.cursor()
        c.execute("UPDATE users SET phone = ?, objective_weight = ? WHERE id = ?", 
                 (data.get('phone'), data.get('objective_weight'), user['id']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Perfil actualizado'})
        
    else: # GET
        u = conn.execute("SELECT name, email, phone, objective_weight, routine_weeks, access_until FROM users WHERE id = ?", (user['id'],)).fetchone()
        conn.close()
        return jsonify(dict(u) if u else {})


# ---- CHAT SYSTEM WITH AI BOT ----
@app.route('/api/ai/analyze', methods=['POST'])
def ai_analyze_lead():
    data = request.json
    user_input = data.get('goal', '')
    history = data.get('history', [])
    analysis = analyze_goal_with_ai(user_input, history)
    return jsonify({'analysis': analysis})

@app.route('/api/payment/simulate', methods=['POST'])
@require_auth(roles=['CLIENT', 'ADMIN'])
def payment_simulate(user):
    # This simulates a successful payment for the current user
    success = simulate_payment_and_unlock(user['id'], 'FULL_PLAN')
    if success:
        return jsonify({'message': 'Pago recibido. ¡Tu plan PRO ha sido desbloqueado!', 'status': 'APPROVED'})
    return jsonify({'error': 'Error procesando pago'}), 500

@app.route('/api/articles', methods=['GET'])
def get_blog_articles():
    conn = get_db()
    # Dummy articles for now or from DB if exists
    articles = conn.execute("SELECT * FROM articles ORDER BY date DESC").fetchall()
    conn.close()
    return jsonify([dict(a) for a in articles])

@app.route('/api/admin/generate_articles', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_generate_blog(admin):
    # Dummy generation logic
    return jsonify({'message': 'Articles generated (mock)'})

@app.route('/api/admin/social_posts', methods=['GET'])
@require_auth(roles=['ADMIN'])
def get_social_posts(admin):
    return jsonify([])

@app.route('/api/marketing/save_lead', methods=['POST'])
def save_marketing_lead():
    data = request.json
    email = data.get('email')
    goal = data.get('goal', '')
    if not email: return jsonify({'error': 'Email required'}), 400
    
    conn = get_db()
    try:
        conn.execute("INSERT OR REPLACE INTO marketing_leads (email, last_goal, status) VALUES (?, ?, 'COLD')", (email, goal))
        conn.commit()
    finally:
        conn.close()
    return jsonify({'message': 'Lead saved'})

def send_coach_email_alert(client_name):
    subject = f"ALERTA MT FITNESS: {client_name} necesita un Coach Humano"
    body = f"El cliente {client_name} ha realizado una consulta que el Bot no puede resolver de forma automatizada. Entra a la App MT Fitness para tomar el control del chat."
    send_admin_notification(subject, body)

def generate_bot_response(message, client_name):
    # --- MOTOR DE INTELIGENCIA MT FITNESS coach 4.2 ---
    import unicodedata
    def normalize(t):
        return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn').lower()
    
    msg = normalize(message)
    print(f"BOT THINKING: Processing '{msg}' for {client_name}")

    # Prioridad: SALUD Y SEGURIDAD
    if any(k in msg for k in ['dolor', 'lesion', 'hernia', 'punzada', 'hinchado', 'inflamado', 'asistencia', 'ayuda']):
        return f"ALERTA DE SEGURIDAD: {client_name}, si sientes un dolor agudo o punzante, detén el ejercicio de inmediato. He avisado al Coach para que revise tu situación técnica."

    # SALUDOS
    if any(k in msg for k in ['hola', 'buenos dias', 'buenas tardes', 'que tal', 'hey', 'saludos']):
        return f"¡Hola {client_name}! Soy tu Asistente de IA. ¿En qué área de tu plan 'Elevation' nos enfocamos hoy: técnica, nutrición o motivación?"

    # CREATINA (ESPECÍFICO)
    if 'creatina' in msg:
        return "Sobre la Creatina: Toma 5g diarios. No necesitas fase de carga ni descansar de ella. Es segura y ayuda a la fuerza y recuperación. ¿Alguna otra duda sobre esto?"

    # PROTEINA (ESPECÍFICO)
    if any(k in msg for k in ['proteina', 'batido', 'suplemento', 'isopro', 'whey']):
        return "Sobre la Proteína: Es una herramienta para llegar a tus macros de forma cómoda. Prioriza la comida sólida (pollo, pescado, huevos), pero usa el batido si te falta proteína al final del día. No es mágica, es comida."

    # NUTRICIÓN Y HAMBRE
    if any(k in msg for k in ['hambre', 'ansiedad', 'dieta', 'macros', 'calorias', 'comida', 'sustituir']):
        return f"Consejo nutricional {client_name}: Si tienes hambre, prioriza vegetales y agua. El plan está diseñado para tu objetivo; la disciplina en los gramos es lo que trae el resultado."

    # ENTRENAMIENTO
    if any(k in msg for k in ['tecnica', 'forma', 'sentadilla', 'press', 'entrenar', 'ejercicio']):
        return "Sobre entrenamiento: La ejecución es sagrada. Controla la bajada y no sacrifiques técnica por peso. Puedes subir un vídeo para que el Coach te corrija."

    # FALLBACK
    return f"He captado tu duda sobre '{message[:20]}'. He avisado al Coach para que te dé una respuesta técnica detallada. Mientras tanto, ¡seguimos con el plan!"

@app.route('/api/chat', methods=['GET', 'POST'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def manage_chat(user):
    conn = get_db()
    target_id = request.args.get('user_id', user['id'])
    if user['role'] != 'ADMIN' and target_id != user['id']: target_id = user['id']

    if request.method == 'POST':
        data = request.json
        user_msg = data.get('message')
        if not user_msg: return jsonify({'error': 'No message'}), 400
        
        try:
            conn.execute("INSERT INTO chat_messages (user_id, sender_role, message) VALUES (?, ?, ?)",
                         (target_id, user['role'], user_msg))
            conn.commit()
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            return jsonify({'error': 'Error guardando mensaje'}), 500

        conn.close()
        return jsonify({'status': 'ok', 'message': 'Mensaje enviado'})
    else:
        msgs = conn.execute("SELECT * FROM chat_messages WHERE user_id = ? ORDER BY timestamp ASC", (target_id,)).fetchall()
        # compatibility with Flutter/Web
        is_flutter = 'flutter' in request.headers.get('User-Agent', '').lower() or request.args.get('format') == 'list'
        if is_flutter:
            conn.close()
            return jsonify([dict(m) for m in msgs])

        conn.close()
        return jsonify({'messages': [dict(m) for m in msgs], 'bot_active': 0})

@app.route('/api/chat/clear', methods=['POST'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def clear_chat(user):
    conn = get_db()
    target_id = request.args.get('user_id', user['id'])
    if user['role'] != 'ADMIN' and target_id != user['id']: target_id = user['id']
    
    conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'message': 'Chat cleared'})

@app.route('/api/client/toggle_bot', methods=['POST'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def toggle_bot(user):
    print(f"TOGGLE LOG: Request from {user['name']} ({user['role']})")
    try:
        conn = get_db()
        target_id = request.args.get('user_id', user['id'])
        if user['role'] != 'ADMIN' and target_id != user['id']: target_id = user['id']
        
        print(f"TOGGLE LOG: Targeting user_id {target_id}")
        current = conn.execute("SELECT bot_active, name FROM users WHERE id = ?", (target_id,)).fetchone()
        if not current:
            print(f"TOGGLE ERROR: User {target_id} not found")
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # Toggle: 1 -> 0, 0 -> 1
        try:
            curr_val = int(current['bot_active']) if current['bot_active'] is not None else 0
        except:
            curr_val = 0
            
        new_status = 0 if curr_val == 1 else 1
        print(f"TOGGLE LOG: Changing {current['name']} bot from {curr_val} to {new_status}")
        
        conn.execute("UPDATE users SET bot_active = ? WHERE id = ?", (new_status, target_id))
        conn.commit(); conn.close()
        return jsonify({'bot_active': int(new_status)})
    except Exception as e:
        print(f"TOGGLE CRITICAL ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# --- AGENT COMMAND CENTER ENDPOINTS ---

@app.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.json
    user_prompt = data.get('message', '').lower()
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # --- LOCAL SIMULATED BRAIN (GRATUITO) ---
        import random
        
        # Inteligencia de palabras clave para elegir el mejor copy
        if 'pierna' in user_prompt or 'gluteo' in user_prompt:
            caption = "💥 El 90% de la gente se salta su día de tren inferior porque duele.\n\nEsa es exactamente la razón por la que tú deberías hacerlo el doble de fuerte. Las piernas son la base de tu templo. No construyas una mansión sobre gelatina. 🏛️🔥\n\n¿Estás listo para mutar? Únete al equipo PRO en el link."
            hashtags = "#DiaDePierna #LegDay #CreceONada #MTFitnessPRO #HipertrofiaReal"
        elif 'comida' in user_prompt or 'nutricion' in user_prompt or 'desayuno' in user_prompt:
            caption = "🍳 Abs are made in the kitchen! Puedes entrenar 3 horas al día, pero si tu nutrición es un desastre, solo estás perdiendo gasolina.\n\nEl secreto no es comer menos, es comer con ESTRATEGIA. Te enseño cómo mis atletas están recomponiendo su cuerpo sin pasar hambre. 🥑🥩\n\n👉🏻 Toca el link de mi bio para ver el plan."
            hashtags = "#NutricionFitness #ComidaReal #DietaFlexible #MTFitnessPRO #RecomposicionCorporal"
        elif 'motivacion' in user_prompt or 'empezar' in user_prompt:
            caption = "🚀 'Empiezo el lunes'. ¿Cuántas veces te has dicho eso?\n\nEl tiempo va a pasar de todas formas. Dentro de 6 meses desearás haber empezado HOY. No necesitas estar motivado todos los días, necesitas ser DISCIPLINADO. 💪🏻🔥\n\nNo esperes a estar listo. Empieza y te harás listo por el camino. Únete a mi equipo hoy."
            hashtags = "#MotivacionGym #DisciplinaFitness #CambioFisico #MTFitnessPRO #NoExcuses"
        else:
            caption = "🔥 Hay dos tipos de personas en el gimnasio: las que levantan peso para cansarse y las que entrenan para TRANSFORMARSE.\n\nSi llevas meses estancado, tu cuerpo se ha adaptado. La clave del crecimiento es entrenar INTELIGENTE. Yo te digo exactamente qué hacer repetición a repetición. 🧬⚡\n\n👉🏻 Link en bio para empezar tu transformación."
            hashtags = "#EntrenamientoInteligente #FitnessEspaña #CrecimientoMuscular #MTFitnessPRO"
        
        c.execute('''INSERT INTO social_media_posts (title, caption, image_url, status) 
                     VALUES (?, ?, ?, 'DRAFT')''',
                  (user_prompt[:50], caption, "https://mtfitness.es/ai_demo.png"))
        conn.commit()
    except Exception as e:
        print("Local AI Error:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()
        
    return jsonify({"status": "ok"})

@app.route('/api/agent/pending_posts', methods=['GET'])
def agent_pending():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM social_media_posts WHERE status = 'DRAFT' ORDER BY id DESC")
    posts = [dict(r) for r in c.fetchall()]
    conn.close()
    
    formatted = []
    for p in posts:
        formatted.append({
            "id": p['id'],
            "target": "Instagram",
            "imageUrl": p['image_url'] or "https://mtfitness.es/ai_demo.png",
            "caption": p['caption'],
            "hashtags": "",
            "status": "A la espera de tu aprobación",
            "created_at": p['created_at']
        })
    return jsonify(formatted)

@app.route('/api/agent/approve_post/<int:post_id>', methods=['POST'])
def agent_approve(post_id):
    conn = get_db()
    conn.execute("UPDATE social_media_posts SET status = 'PENDING' WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "approved"})

@app.route('/api/agent/reject_post/<int:post_id>', methods=['POST'])
def agent_reject(post_id):
    conn = get_db()
    conn.execute("UPDATE social_media_posts SET status = 'REJECTED' WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "rejected"})


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(app.static_folder, 'manifest.json')


@app.route('/api/increment_visits', methods=['GET', 'POST'])
def increment_visits():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    # Get country info from a free API (optional, can be slow)
    country = "Desconocido"
    try:
        # We handle this quickly to not slow down the page load
        res = requests.get(f'http://ip-api.com/json/{ip}?fields=country', timeout=1)
        if res.status_code == 200:
            country = res.json().get('country', 'Desconocido')
    except:
        pass

    conn = get_db()
    cursor = conn.cursor()
    
    # Tables for stats
    cursor.execute('''CREATE TABLE IF NOT EXISTS metrics (key TEXT UNIQUE, value INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS visitor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
        ip TEXT, 
        country TEXT
    )''')
    
    # Increment total
    cursor.execute('''INSERT OR IGNORE INTO metrics (key, value) VALUES ('total_visits', 0)''')
    cursor.execute('''UPDATE metrics SET value = value + 1 WHERE key = 'total_visits' ''')
    
    # Log visit
    cursor.execute('''INSERT INTO visitor_logs (ip, country) VALUES (?, ?)''', (ip, country))
    
    conn.commit()
    
    # Get total for display
    cursor.execute('''SELECT value FROM metrics WHERE key = 'total_visits' ''')
    visits = cursor.fetchone()[0]
    conn.close()
    return jsonify({"visits": visits, "country": country})

@app.route('/api/get_stats', methods=['GET'])
def get_stats():
    # Only for the coach (no token yet, but we'll protect it later)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''SELECT country, COUNT(*) as count FROM visitor_logs GROUP BY country ORDER BY count DESC''')
    countries = [{"country": row[0], "count": row[1]} for row in cursor.fetchall()]
    
    cursor.execute('''SELECT value FROM metrics WHERE key = 'total_visits' ''')
    total = cursor.fetchone()[0] if cursor.fetchone() else 0
    conn.close()
    return jsonify({"total_visits": total, "countries": countries})

@app.route('/api/master/upload_db', methods=['POST'])
def upload_db():
    master_token = request.form.get('master_token')
    if master_token != "MT_MASTER_PRO_2026":
        return jsonify({"error": "Unauthorized"}), 401
        
    db_file = request.files.get('db')
    if db_file:
        db_file.save(DB_FILE)
        return jsonify({"status": "Database Synced Successfully"})
    return jsonify({"error": "No file"}), 400

@app.route('/api/master/download_db', methods=['POST'])
def download_db():
    master_token = request.form.get('master_token')
    if master_token != "MT_MASTER_PRO_2026":
        return jsonify({"error": "Unauthorized"}), 401
    
    return send_from_directory(BASE_DIR, 'mtfitness.db', as_attachment=True)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/descargar-app')
def download_app_shorthand():
    return send_from_directory(app.static_folder, 'MTFitness_PRO_FINAL.apk', as_attachment=True)

@app.route('/uploads/<filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/generate_marketing', methods=['GET', 'POST'], strict_slashes=False)
def generate_marketing():
    data = request.json
    topic = data.get('topic')
    type = data.get('type') # 'blog' or 'instagram'
    
    if not topic:
        return jsonify({"error": "Topic required"}), 400
    
    # Custom prompt based on type
    if type == 'blog':
        prompt = f"Escribe un artículo de blog SEO de unas 300 palabras sobre '{topic}' para el entrenador Miguel Torres. Usa un tono motivador, profesional y directo. No uses la palabra 'ciencia'. Enfócate en resultados y alto rendimiento."
    else:
        prompt = f"Genera un post de Instagram rompedor sobre '{topic}' para Miguel Torres. Incluye un gancho inicial, 3 puntos clave, llamada a la acción y 5 hashtags virales del sector fitness (vete directamente al grano)."

    try:
        if "sk-proj" in OPENAI_API_KEY:
            # Simple AI response if no key, but we strive for real logic if user has it
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
              model="gpt-3.5-turbo",
              messages=[{"role": "user", "content": prompt}],
              max_tokens=500
            )
            content = response.choices[0].message.content
        else:
            content = f"Simulación de IA para: {topic}. (Configura la clave en el servidor para resultados reales)."
            
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    objective = data.get('objective')
    
    try:
        smtp_server = "smtp.ionos.es"
        smtp_port = 587
        sender_email = "info@mtfitness.es"
        password = "mtfitness2026"
        receiver_email = "info@mtfitness.es"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = f"NUEVO LEAD WEB: {name}"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        text_body = f"Nombre: {name}\nEmail: {email}\nObjetivo: {objective}"
        message.attach(MIMEText(text_body, "plain"))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        
        return jsonify({"status": "success", "message": "Email enviado"}), 200
    except Exception as e:
        print(f"Error enviando email: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/seed_exercises', methods=['GET'])
def seed_exercises():
    """
    Inserts all 873 exercises using Spanish names and original filenames.
    This guarantees the slug-matching in icon_mapper.dart finds the real image.
    Returns JSON with how many were added.
    """
    import re
    def translate_name(name):
        replacements = {
            'Barbell': 'con Barra', 'Dumbbell': 'con Mancuernas', 'Bench Press': 'Press de Banca',
            'Incline': 'Inclinado', 'Decline': 'Declinado', 'Squat': 'Sentadilla', 'Lunge': 'Zancada',
            'Deadlift': 'Peso Muerto', 'Row': 'Remo', 'Curl': 'Curl', 'Extension': 'Extensión',
            'Extensions': 'Extensión', 'Pull-Up': 'Dominada', 'Pulldown': 'Jalón', 'Front Raise': 'Elevación Frontal',
            'Shoulder Press': 'Press de Hombro', 'Lateral Raise': 'Elevación Lateral', 'Raise': 'Elevación',
            'Crunch': 'Crunch Abdominal', 'Plank': 'Plancha', 'Machine': 'en Máquina', 'Cable': 'en Polea'
        }
        disp = name.replace('_', ' ').replace('-', ' ')
        for eng, esp in replacements.items():
            disp = re.sub(r'(?i)\b' + re.escape(eng) + r'\b', esp, disp)
        return f"{disp} ({name})"

    exercises_data = [
        ("3_4_Sit-Up","Core"),("90_90_Hamstring","Pierna"),("Ab_Crunch_Machine","Core"),
        ("Ab_Roller","Core"),("Adductor","Compuesto"),("Adductor_Groin","Compuesto"),
        ("Advanced_Kettlebell_Windmill","Compuesto"),("Air_Bike","Cardio"),
        ("All_Fours_Quad_Stretch","Flexibilidad"),("Alternate_Hammer_Curl","Bíceps"),
        ("Alternate_Heel_Touchers","Core"),("Alternate_Incline_Dumbbell_Curl","Bíceps"),
        ("Alternate_Leg_Diagonal_Bound","Pierna"),("Alternating_Cable_Shoulder_Press","Hombro"),
        ("Alternating_Deltoid_Raise","Hombro"),("Alternating_Floor_Press","Pecho"),
        ("Alternating_Hang_Clean","Compuesto"),("Alternating_Kettlebell_Press","Hombro"),
        ("Alternating_Kettlebell_Row","Espalda"),("Alternating_Renegade_Row","Espalda"),
        ("Ankle_Circles","Flexibilidad"),("Ankle_On_The_Knee","Flexibilidad"),
        ("Anterior_Tibialis-SMR","Flexibilidad"),("Anti-Gravity_Press","Hombro"),
        ("Arm_Circles","Flexibilidad"),("Arnold_Dumbbell_Press","Hombro"),
        ("Around_The_Worlds","Pecho"),("Atlas_Stones","Compuesto"),
        ("Atlas_Stone_Trainer","Compuesto"),("Axle_Deadlift","Espalda"),
        ("Backward_Drag","Compuesto"),("Backward_Medicine_Ball_Throw","Compuesto"),
        ("Back_Flyes_-_With_Bands","Espalda"),("Balance_Board","Core"),
        ("Ball_Leg_Curl","Pierna"),("Band_Assisted_Pull-Up","Espalda"),
        ("Band_Good_Morning","Espalda"),("Band_Good_Morning_Pull_Through","Espalda"),
        ("Band_Hip_Adductions","Pierna"),("Band_Pull_Apart","Hombro"),
        ("Band_Skull_Crusher","Tríceps"),("Barbell_Ab_Rollout","Core"),
        ("Barbell_Ab_Rollout_-_On_Knees","Core"),("Barbell_Bench_Press_-_Medium_Grip","Pecho"),
        ("Barbell_Curl","Bíceps"),("Barbell_Curls_Lying_Against_An_Incline","Bíceps"),
        ("Barbell_Deadlift","Espalda"),("Barbell_Full_Squat","Pierna"),
        ("Barbell_Glute_Bridge","Pierna"),("Barbell_Guillotine_Bench_Press","Pecho"),
        ("Barbell_Hack_Squat","Pierna"),("Barbell_Hip_Thrust","Pierna"),
        ("Barbell_Incline_Bench_Press_-_Medium_Grip","Pecho"),("Barbell_Incline_Shoulder_Raise","Hombro"),
        ("Barbell_Lunge","Pierna"),("Barbell_Rear_Delt_Row","Hombro"),
        ("Barbell_Rollout_from_Bench","Core"),("Barbell_Seated_Calf_Raise","Pierna"),
        ("Barbell_Shoulder_Press","Hombro"),("Barbell_Shrug","Hombro"),
        ("Barbell_Shrug_Behind_The_Back","Hombro"),("Barbell_Side_Bend","Core"),
        ("Barbell_Side_Split_Squat","Pierna"),("Barbell_Squat","Pierna"),
        ("Barbell_Squat_To_A_Bench","Pierna"),("Barbell_Step_Ups","Pierna"),
        ("Barbell_Walking_Lunge","Pierna"),("Battling_Ropes","Cardio"),
        ("Bear_Crawl_Sled_Drags","Compuesto"),("Behind_Head_Chest_Stretch","Flexibilidad"),
        ("Bench_Dips","Tríceps"),("Bench_Jump","Pierna"),
        ("Bench_Press_-_Powerlifting","Pecho"),("Bench_Press_-_With_Bands","Pecho"),
        ("Bench_Press_with_Chains","Pecho"),("Bench_Sprint","Cardio"),
        ("Bent-Arm_Barbell_Pullover","Espalda"),("Bent-Arm_Dumbbell_Pullover","Espalda"),
        ("Bent-Knee_Hip_Raise","Core"),("Bent_Over_Barbell_Row","Espalda"),
        ("Bent_Over_Dumbbell_Rear_Delt_Raise_With_Head_On_Bench","Hombro"),
        ("Bent_Over_Low-Pulley_Side_Lateral","Hombro"),("Bent_Over_One-Arm_Long_Bar_Row","Espalda"),
        ("Bent_Over_Two-Arm_Long_Bar_Row","Espalda"),("Bent_Over_Two-Dumbbell_Row","Espalda"),
        ("Bent_Over_Two-Dumbbell_Row_With_Palms_In","Espalda"),("Bent_Press","Compuesto"),
        ("Bicycling","Cardio"),("Bicycling_Stationary","Cardio"),
        ("Board_Press","Pecho"),("Body-Up","Core"),
        ("Bodyweight_Flyes","Pecho"),("Bodyweight_Mid_Row","Espalda"),
        ("Bodyweight_Squat","Pierna"),("Bodyweight_Walking_Lunge","Pierna"),
        ("Body_Tricep_Press","Tríceps"),("Bosu_Ball_Cable_Crunch_With_Side_Bends","Core"),
        ("Bottoms-Up_Clean_From_The_Hang_Position","Compuesto"),("Bottoms_Up","Compuesto"),
        ("Box_Jump_Multiple_Response","Pierna"),("Box_Skip","Cardio"),
        ("Box_Squat","Pierna"),("Box_Squat_with_Bands","Pierna"),
        ("Box_Squat_with_Chains","Pierna"),("Brachialis-SMR","Flexibilidad"),
        ("Bradford_Rocky_Presses","Hombro"),("Butt-Ups","Core"),
        ("Butterfly","Flexibilidad"),("Butt_Lift_Bridge","Pierna"),
        ("Cable_Chest_Press","Pecho"),("Cable_Crossover","Pecho"),
        ("Cable_Crunch","Core"),("Cable_Deadlifts","Espalda"),
        ("Cable_Hammer_Curls_-_Rope_Attachment","Bíceps"),("Cable_Hip_Adduction","Pierna"),
        ("Cable_Incline_Pushdown","Tríceps"),("Cable_Incline_Triceps_Extension","Tríceps"),
        ("Cable_Internal_Rotation","Hombro"),("Cable_Iron_Cross","Pecho"),
        ("Cable_Judo_Flip","Compuesto"),("Cable_Lying_Triceps_Extension","Tríceps"),
        ("Cable_One_Arm_Tricep_Extension","Tríceps"),("Cable_Preacher_Curl","Bíceps"),
        ("Cable_Rear_Delt_Fly","Hombro"),("Cable_Reverse_Crunch","Core"),
        ("Cable_Rope_Overhead_Triceps_Extension","Tríceps"),("Cable_Rope_Rear-Delt_Rows","Hombro"),
        ("Cable_Russian_Twists","Core"),("Cable_Seated_Crunch","Core"),
        ("Cable_Seated_Lateral_Raise","Hombro"),("Cable_Shoulder_Press","Hombro"),
        ("Cable_Shrugs","Hombro"),("Cable_Wrist_Curl","Compuesto"),
        ("Calf-Machine_Shoulder_Shrug","Hombro"),("Calf_Press","Pierna"),
        ("Calf_Press_On_The_Leg_Press_Machine","Pierna"),("Calf_Raises_-_With_Bands","Pierna"),
        ("Calf_Raise_On_A_Dumbbell","Pierna"),("Calf_Stretch_Elbows_Against_Wall","Flexibilidad"),
        ("Calf_Stretch_Hands_Against_Wall","Flexibilidad"),("Calves-SMR","Flexibilidad"),
        ("Carioca_Quick_Step","Cardio"),("Car_Deadlift","Espalda"),
        ("Car_Drivers","Hombro"),("Cat_Stretch","Flexibilidad"),
        ("Chain_Handle_Extension","Tríceps"),("Chain_Press","Pecho"),
        ("Chair_Squat","Pierna"),("Chest_And_Front_Of_Shoulder_Stretch","Flexibilidad"),
        ("Chin-Up","Espalda"),("Clean","Compuesto"),
        ("Clean_and_Jerk","Compuesto"),("Clean_and_Press","Compuesto"),
        ("Clean_Deadlift","Espalda"),("Clean_Pull","Compuesto"),
        ("Close-Grip_Barbell_Bench_Press","Tríceps"),("Close-Grip_Dumbbell_Press","Tríceps"),
        ("Close-Grip_EZ_Bar_Curl","Bíceps"),("Close-Grip_Front_Lat_Pulldown","Espalda"),
        ("Close-Grip_Standing_Barbell_Curl","Bíceps"),("Cocoons","Core"),
        ("Concentration_Curls","Bíceps"),("Cross-Body_Crunch","Core"),
        ("Crossover_Reverse_Lunge","Pierna"),("Cross_Body_Hammer_Curl","Bíceps"),
        ("Crunches","Core"),("Crunch_-_Hands_Overhead","Core"),
        ("Crunch_-_Legs_On_Exercise_Ball","Core"),("Cuban_Press","Hombro"),
        ("Deadlift_with_Bands","Espalda"),("Deadlift_with_Chains","Espalda"),
        ("Dead_Bug","Core"),("Decline_Barbell_Bench_Press","Pecho"),
        ("Decline_Close-Grip_Bench_To_Skull_Crusher","Tríceps"),("Decline_Crunch","Core"),
        ("Decline_Dumbbell_Bench_Press","Pecho"),("Decline_Dumbbell_Flyes","Pecho"),
        ("Decline_Dumbbell_Triceps_Extension","Tríceps"),("Decline_EZ_Bar_Triceps_Extension","Tríceps"),
        ("Decline_Oblique_Crunch","Core"),("Decline_Push-Up","Pecho"),
        ("Decline_Reverse_Crunch","Core"),("Decline_Smith_Press","Pecho"),
        ("Deficit_Deadlift","Espalda"),("Dips_-_Chest_Version","Pecho"),
        ("Dips_-_Triceps_Version","Tríceps"),("Dip_Machine","Tríceps"),
        ("Donkey_Calf_Raises","Pierna"),("Double_Kettlebell_Jerk","Compuesto"),
        ("Double_Kettlebell_Push_Press","Compuesto"),("Double_Kettlebell_Snatch","Compuesto"),
        ("Double_Leg_Butt_Kick","Cardio"),("Drag_Curl","Bíceps"),
        ("Dumbbell_Alternate_Bicep_Curl","Bíceps"),("Dumbbell_Bench_Press","Pecho"),
        ("Dumbbell_Bench_Press_with_Neutral_Grip","Pecho"),("Dumbbell_Bicep_Curl","Bíceps"),
        ("Dumbbell_Clean","Compuesto"),("Dumbbell_Floor_Press","Pecho"),
        ("Dumbbell_Flyes","Pecho"),("Dumbbell_Incline_Row","Espalda"),
        ("Dumbbell_Incline_Shoulder_Raise","Hombro"),("Dumbbell_Lunges","Pierna"),
        ("Dumbbell_Lying_One-Arm_Rear_Lateral_Raise","Hombro"),("Dumbbell_Lying_Rear_Lateral_Raise","Hombro"),
        ("Dumbbell_One-Arm_Shoulder_Press","Hombro"),("Dumbbell_One-Arm_Triceps_Extension","Tríceps"),
        ("Dumbbell_One-Arm_Upright_Row","Hombro"),("Dumbbell_Prone_Incline_Curl","Bíceps"),
        ("Dumbbell_Raise","Hombro"),("Dumbbell_Rear_Lunge","Pierna"),
        ("Dumbbell_Scaption","Hombro"),("Dumbbell_Shoulder_Press","Hombro"),
        ("Dumbbell_Shrug","Hombro"),("Dumbbell_Side_Bend","Core"),
        ("Dumbbell_Squat","Pierna"),("Dumbbell_Step_Ups","Pierna"),
        ("EZ-Bar_Curl","Bíceps"),("EZ-Bar_Skullcrusher","Tríceps"),
        ("Face_Pull","Hombro"),("Farmers_Walk","Compuesto"),
        ("Finger_Curls","Compuesto"),("Flat_Bench_Cable_Flyes","Pecho"),
        ("Flat_Bench_Lying_Leg_Raise","Core"),("Floor_Glute-Ham_Raise","Pierna"),
        ("Floor_Press","Pecho"),("Flutter_Kicks","Core"),
        ("Freehand_Jump_Squat","Pierna"),("Frog_Hops","Pierna"),
        ("Front_Barbell_Squat","Pierna"),("Front_Box_Jump","Pierna"),
        ("Front_Cable_Raise","Hombro"),("Front_Dumbbell_Raise","Hombro"),
        ("Front_Incline_Dumbbell_Raise","Hombro"),("Front_Leg_Raises","Core"),
        ("Front_Plate_Raise","Hombro"),("Full_Range-Of-Motion_Lat_Pulldown","Espalda"),
        ("Glute_Ham_Raise","Pierna"),("Glute_Kickback","Pierna"),
        ("Goblet_Squat","Pierna"),("Good_Morning","Espalda"),
        ("Gorilla_Chin_Crunch","Core"),("Hack_Squat","Pierna"),
        ("Hammer_Curls","Bíceps"),("Hammer_Grip_Incline_DB_Bench_Press","Pecho"),
        ("Hamstring_Stretch","Flexibilidad"),("Handstand_Push-Ups","Hombro"),
        ("Hanging_Leg_Raise","Core"),("Hang_Clean","Compuesto"),
        ("Hang_Snatch","Compuesto"),("High_Cable_Curls","Bíceps"),
        ("Hip_Extension_with_Bands","Pierna"),("Hyperextensions_Back_Extensions","Espalda"),
        ("Incline_Barbell_Triceps_Extension","Tríceps"),("Incline_Cable_Chest_Press","Pecho"),
        ("Incline_Cable_Flye","Pecho"),("Incline_Dumbbell_Curl","Bíceps"),
        ("Incline_Dumbbell_Flyes","Pecho"),("Incline_Dumbbell_Press","Pecho"),
        ("Incline_Hammer_Curls","Bíceps"),("Incline_Push-Up","Pecho"),
        ("Inverted_Row","Espalda"),("Iron_Cross","Compuesto"),
        ("Jackknife_Sit-Up","Core"),("Jefferson_Squats","Pierna"),
        ("Jogging_Treadmill","Cardio"),("Kettlebell_Arnold_Press","Hombro"),
        ("Kettlebell_Figure_8","Compuesto"),("Kettlebell_Pistol_Squat","Pierna"),
        ("Kettlebell_Thruster","Compuesto"),("Kettlebell_Windmill","Compuesto"),
        ("Kneeling_Cable_Triceps_Extension","Tríceps"),("Kneeling_High_Pulley_Row","Espalda"),
        ("Kneeling_Jump_Squat","Pierna"),("Knee_Tuck_Jump","Pierna"),
        ("Landmine_180s","Compuesto"),("Lateral_Box_Jump","Pierna"),
        ("Lateral_Raise_-_With_Bands","Hombro"),("Leg_Extensions","Pierna"),
        ("Leg_Press","Pierna"),("Leverage_Chest_Press","Pecho"),
        ("Leverage_Deadlift","Espalda"),("Leverage_High_Row","Espalda"),
        ("Leverage_Incline_Chest_Press","Pecho"),("Leverage_Shoulder_Press","Hombro"),
        ("Lying_Cable_Curl","Bíceps"),("Lying_Close-Grip_Barbell_Triceps_Extension_Behind_The_Head","Tríceps"),
        ("Lying_Dumbbell_Tricep_Extension","Tríceps"),("Lying_Glute","Flexibilidad"),
        ("Lying_Hamstring","Flexibilidad"),("Lying_Leg_Curls","Pierna"),
        ("Lying_Rear_Delt_Raise","Hombro"),("Lying_Triceps_Press","Tríceps"),
        ("Machine_Bench_Press","Pecho"),("Machine_Bicep_Curl","Bíceps"),
        ("Machine_Preacher_Curls","Bíceps"),("Machine_Shoulder_Military_Press","Hombro"),
        ("Machine_Triceps_Extension","Tríceps"),("Medicine_Ball_Chest_Pass","Pecho"),
        ("Middle_Back_Shrug","Espalda"),("Mountain_Climbers","Core"),
        ("Muscle_Up","Compuesto"),("Narrow_Stance_Hack_Squats","Pierna"),
        ("Narrow_Stance_Leg_Press","Pierna"),("Neck_Press","Pecho"),
        ("Oblique_Crunches","Core"),("Olympic_Squat","Pierna"),
        ("One-Arm_Dumbbell_Row","Espalda"),("One-Arm_Kettlebell_Clean","Compuesto"),
        ("One-Arm_Kettlebell_Jerk","Compuesto"),("One-Arm_Kettlebell_Snatch","Compuesto"),
        ("One_Arm_Dumbbell_Bench_Press","Pecho"),("One_Arm_Lat_Pulldown","Espalda"),
        ("One_Leg_Barbell_Squat","Pierna"),("Open_Palm_Kettlebell_Clean","Compuesto"),
        ("Overhead_Cable_Curl","Bíceps"),("Overhead_Squat","Pierna"),
        ("Pallof_Press","Core"),("Parallel_Bar_Dip","Tríceps"),
        ("Physioball_Hip_Bridge","Pierna"),("Plank","Core"),
        ("Plate_Twist","Core"),("Plie_Dumbbell_Squat","Pierna"),
        ("Plyo_Push-up","Pecho"),("Power_Clean","Compuesto"),
        ("Power_Jerk","Compuesto"),("Power_Snatch","Compuesto"),
        ("Preacher_Curl","Bíceps"),("Preacher_Hammer_Dumbbell_Curl","Bíceps"),
        ("Pull_Through","Espalda"),("Push-Ups_-_Close_Triceps_Position","Tríceps"),
        ("Push-Ups_With_Feet_Elevated","Pecho"),("Pushups","Pecho"),
        ("Push_Press","Hombro"),("Pyramid","Compuesto"),
        ("Rack_Pulls","Espalda"),("Rear_Leg_Raises","Pierna"),
        ("Recumbent_Bike","Cardio"),("Reverse_Band_Bench_Press","Pecho"),
        ("Reverse_Band_Deadlift","Espalda"),("Reverse_Barbell_Curl","Bíceps"),
        ("Reverse_Cable_Curl","Bíceps"),("Reverse_Crunch","Core"),
        ("Reverse_Flyes","Hombro"),("Reverse_Grip_Bent-Over_Rows","Espalda"),
        ("Reverse_Grip_Triceps_Pushdown","Tríceps"),("Reverse_Hyperextension","Espalda"),
        ("Ring_Dips","Tríceps"),("Romanian_Deadlift","Pierna"),
        ("Rope_Climb","Espalda"),("Rope_Crunch","Core"),
        ("Rope_Jumping","Cardio"),("Rowing_Stationary","Cardio"),
        ("Running_Treadmill","Cardio"),("Russian_Twist","Core"),
        ("Scapular_Pull-Up","Espalda"),("Seated_Band_Hamstring_Curl","Pierna"),
        ("Seated_Barbell_Military_Press","Hombro"),("Seated_Bent-Over_Rear_Delt_Raise","Hombro"),
        ("Seated_Cable_Rows","Espalda"),("Seated_Cable_Shoulder_Press","Hombro"),
        ("Seated_Calf_Raise","Pierna"),("Seated_Dumbbell_Curl","Bíceps"),
        ("Seated_Dumbbell_Press","Hombro"),("Seated_Leg_Curl","Pierna"),
        ("Seated_Side_Lateral_Raise","Hombro"),("Seated_Triceps_Press","Tríceps"),
        ("Side_Bridge","Core"),("Side_Jackknife","Core"),
        ("Side_Lateral_Raise","Hombro"),("Side_Leg_Raises","Pierna"),
        ("Single_Leg_Glute_Bridge","Pierna"),("Sit-Up","Core"),
        ("Sled_Push","Compuesto"),("Smith_Machine_Bench_Press","Pecho"),
        ("Smith_Machine_Bent_Over_Row","Espalda"),("Smith_Machine_Calf_Raise","Pierna"),
        ("Smith_Machine_Incline_Bench_Press","Pecho"),("Smith_Machine_Leg_Press","Pierna"),
        ("Smith_Machine_Overhead_Shoulder_Press","Hombro"),("Smith_Machine_Squat","Pierna"),
        ("Snatch","Compuesto"),("Snatch_Deadlift","Espalda"),
        ("Speed_Squats","Pierna"),("Spider_Curl","Bíceps"),
        ("Split_Jerk","Compuesto"),("Split_Jump","Pierna"),
        ("Split_Squats","Pierna"),("Split_Squat_with_Dumbbells","Pierna"),
        ("Squat_with_Bands","Pierna"),("Stairmaster","Cardio"),
        ("Standing_Barbell_Calf_Raise","Pierna"),("Standing_Biceps_Cable_Curl","Bíceps"),
        ("Standing_Cable_Wood_Chop","Core"),("Standing_Calf_Raises","Pierna"),
        ("Standing_Dumbbell_Calf_Raise","Pierna"),("Standing_Dumbbell_Press","Hombro"),
        ("Standing_Dumbbell_Triceps_Extension","Tríceps"),("Standing_Military_Press","Hombro"),
        ("Standing_One-Arm_Dumbbell_Triceps_Extension","Tríceps"),
        ("Standing_Overhead_Barbell_Triceps_Extension","Tríceps"),
        ("Stiff-Legged_Barbell_Deadlift","Pierna"),("Stiff-Legged_Dumbbell_Deadlift","Pierna"),
        ("Straight-Arm_Dumbbell_Pullover","Espalda"),("Straight-Arm_Pulldown","Espalda"),
        ("Sumo_Deadlift","Pierna"),("Sumo_Deadlift_with_Bands","Pierna"),
        ("Superman","Espalda"),("Suspended_Push-Up","Pecho"),
        ("Swiss_Ball_Dumbbell_Curl","Bíceps"),("T-Bar_Row","Espalda"),
        ("T-Bar_Row_with_Handle","Espalda"),("TRX_Suspended_Pushup","Pecho"),
        ("Thruster","Compuesto"),("Tire_Flip","Compuesto"),
        ("Triceps_Pushdown","Tríceps"),("Triceps_Pushdown_-_Rope_Attachment","Tríceps"),
        ("Underhand_Cable_Pulldowns","Espalda"),("Upright_Barbell_Row","Hombro"),
        ("V_Bar_Pulldown","Espalda"),("Weighted_Bench_Dip","Tríceps"),
        ("Weighted_Crunches","Core"),("Weighted_Jump_Squat","Pierna"),
        ("Weighted_Pull_Ups","Espalda"),("Weighted_Squat","Pierna"),
        ("Wide-Grip_Barbell_Bench_Press","Pecho"),("Wide-Grip_Decline_Barbell_Bench_Press","Pecho"),
        ("Wide-Grip_Lat_Pulldown","Espalda"),("Wide-Grip_Rear_Pull-Up","Espalda"),
        ("Wide-Grip_Standing_Barbell_Curl","Bíceps"),("Wide_Stance_Barbell_Squat","Pierna"),
        ("Windmills","Compuesto"),("Wrist_Roller","Compuesto"),
        ("Yoke_Walk","Compuesto"),("Zercher_Squats","Pierna"),
        ("Zottman_Curl","Bíceps"),("Zottman_Preacher_Curl","Bíceps"),
    ]
    conn = get_db()
    # Limpiamos antes de insertar para evitar duplicados rotos y asegurar que todo tenga el formato correcto
    conn.execute("DELETE FROM exercises")
    conn.commit()
    
    added = 0
    skipped = 0
    for name_only, mg in exercises_data:
        display_name = translate_name(name_only)
        existing = conn.execute("SELECT id FROM exercises WHERE name = ?", (display_name,)).fetchone()
        if not existing:
            conn.execute("INSERT INTO exercises (name, muscle_group) VALUES (?, ?)", (display_name, mg))
            added += 1
        else:
            skipped += 1
    conn.commit()
    conn.close()
    return jsonify({"success": True, "added": added, "skipped": skipped})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
