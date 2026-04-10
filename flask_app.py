from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import sqlite3
import os
import uuid
import datetime
import werkzeug.utils
from functools import wraps
from ai_services import analyze_goal_with_ai, simulate_payment_and_unlock
from exercises_data import exercises_data
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
try:
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
except Exception as e:
    print(f"Aviso: No se pudo crear UPLOAD_FOLDER (entorno de solo lectura): {e}")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
class DbWrapper:
    def __init__(self, conn, is_pg):
        self.conn = conn
        self.is_pg = is_pg
    def cursor(self):
        return self.conn.cursor()
    def execute(self, query, params=()):
        if self.is_pg:
            query = query.replace('?', '%s').replace('DATETIME', 'TIMESTAMP')
            query = query.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY').replace('DATETIME', 'TIMESTAMP')
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

def sync_pro_exercises():
    """Sincroniza el catálogo de ejercicios con sus imágenes."""
    conn = get_db()
    
    import os
    exercises_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'exercises')
    available_files = []
    if os.path.exists(exercises_dir):
        available_files = os.listdir(exercises_dir)

    def find_icon(name, muscle):
        name_lower = name.lower()
        
        # Mapeos directos de términos comunes
        mappings = {
            'press de banca': 'bench_press',
            'mancuerna': 'dumbbell',
            'barra': 'barbell',
            'polea': 'cable',
            'sentadilla': 'squat',
            'peso muerto': 'deadlift',
            'biceps': 'curl',
            'curvada': 'ez_bar',
            'z': 'ez_bar',
            'jalón': 'pulldown',
            'remo': 'row',
            'aperturas': 'fly',
            'hombro': 'shoulder_press',
            'militar': 'military_press',
            'zancada': 'lunge',
            'prensa': 'leg_press',
            'isquios': 'leg_curl',
            'cuadriceps': 'leg_extension',
            'fondos': 'dip',
            'dominadas': 'pullup',
            'flexiones': 'pushup'
        }

        # Intentar encontrar el archivo más descriptivo
        best_match = None
        for fname in available_files:
            clean_fname = fname.lower().replace('_', ' ')
            
            # Si el nombre en español contiene la palabra clave y el archivo también
            matched_keywords = 0
            for sp, en in mappings.items():
                if sp in name_lower and en in clean_fname:
                    matched_keywords += 1
            
            if matched_keywords > 0:
                # Si es un match exacto (ej: Barbell Curl)
                if 'barra' in name_lower and 'barbell' in clean_fname and 'curl' in clean_fname: return fname
                if 'mancuerna' in name_lower and 'dumbbell' in clean_fname and 'curl' in clean_fname: return fname
                if 'banca' in name_lower and 'bench press' in clean_fname: return fname
                if 'inclinado' in name_lower and 'incline' in clean_fname: return fname
                if 'declinado' in name_lower and 'decline' in clean_fname: return fname
                if 'smith' in name_lower and 'smith' in clean_fname: return fname
                
                best_match = fname

        if best_match: return best_match
        
        # Fallback por musculo
        muscle_icons = {
            'Pecho': 'pecho_icon_1775126194087.png',
            'Espalda': 'espalda_icon_1775126212481.png',
            'Hombro': 'hombro_icon_1775126243283.png',
            'Pierna': 'pierna_icon_1775126227797.png',
            'Biceps': 'biceps_icon_1775126261867.png',
            'Triceps': 'triceps_icon_1775126276135.png',
            'Core': 'core_icon_1775126289413.png'
        }
        return muscle_icons.get(muscle, 'logo.png')

    print(f"MIGRATION: Sincronizando {len(exercises_data)} ejercicios de forma segura...")
    for name, muscle in exercises_data:
        icon = find_icon(name, muscle)
        try:
            res = conn.execute("SELECT id FROM exercises WHERE name = " + ("%s" if conn.is_pg else "?"), (name,)).fetchone()
            if not res:
                conn.execute("INSERT INTO exercises (name, muscle_group, icon_path) VALUES (" + ("%s, %s, %s" if conn.is_pg else "?, ?, ?") + ")",
                             (name, muscle, icon))
            else:
                conn.execute("UPDATE exercises SET icon_path = " + ("%s" if conn.is_pg else "?") + ", muscle_group = " + ("%s" if conn.is_pg else "?") + " WHERE name = " + ("%s" if conn.is_pg else "?"),
                             (icon, muscle, name))
        except Exception as e:
            print(f"Error syncing {name}: {e}")

    conn.commit()
    
    conn.commit()
    print("MIGRATION: Ejercicios e imágenes sincronizados.")
    conn.close()


def init_db():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print("Production DB (Postgres) detected. Assuming migrations are handled or running init...")
    
    conn_wrap = get_db()
    if not conn_wrap or not conn_wrap.conn:
        print("CRITICAL: Database connection failed during init_db")
        return
    
    c = conn_wrap 
    
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
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, muscle_group TEXT, icon_path TEXT
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
        weight REAL, photo_front TEXT, photo_side TEXT, photo_back TEXT,
        biceps REAL, thigh REAL, hip REAL, waist REAL
    )''')

    # Add missing columns to reports safely
    for col in ['biceps', 'thigh', 'hip', 'waist']:
        try:
            conn_wrap.execute(f"ALTER TABLE reports ADD COLUMN {col} REAL")
        except: pass

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

    
    # MIGRACIÓN SEGURA OPTIMIZADA
    def run_migrations():
        tables_to_check = ["user_exercises", "user_foods", "users", "reports", "exercises"]
        existing_cols = {}
        for table in tables_to_check:
            try:
                if conn_wrap.is_pg:
                    c_check = conn_wrap.cursor()
                    c_check.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'")
                    existing_cols[table] = [r['column_name'] for r in c_check.fetchall()]
                else:
                    c_check = conn_wrap.cursor()
                    c_check.execute(f"PRAGMA table_info({table})")
                    existing_cols[table] = [col['name'] for col in c_check.fetchall()]
            except: existing_cols[table] = []

        columns_to_add = [
            ("user_exercises", "set_type", "TEXT DEFAULT 'NORMAL'"),
            ("user_exercises", "combined_with", "INTEGER"),
            ("user_exercises", "target_muscles", "TEXT"),
            ("user_foods", "day_name", "TEXT DEFAULT 'Día 1'"),
            ("users", "surname", "TEXT"),
            ("users", "age", "INTEGER"), ("users", "height", "REAL"),
            ("users", "current_weight", "REAL"), ("users", "objective", "TEXT"),
            ("users", "profile_image", "TEXT"), ("users", "biceps", "REAL"),
            ("users", "thigh", "REAL"), ("users", "hip", "REAL"), ("users", "waist", "REAL"),
            ("reports", "biceps", "REAL"), ("reports", "thigh", "REAL"),
            ("reports", "hip", "REAL"), ("reports", "waist", "REAL"),
            ("exercises", "icon_path", "TEXT"),
        ]
        
        for table, col, defn in columns_to_add:
            if table in existing_cols and col not in existing_cols[table]:
                try:
                    conn_wrap.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
                    conn_wrap.commit()
                except: pass

    run_migrations()

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
    # --- REGLA DE VIERNES O INICIO DE MES ---
    now = datetime.datetime.now()
    is_friday = now.weekday() == 4
    is_start_of_month = now.day == 1
    
    if not is_friday and not is_start_of_month:
        return jsonify({'error': 'Los reportes solo pueden enviarse los Viernes o el día 1 de cada mes.'}), 403
    
    # --- REGLA DE 1 VEZ POR DÍA ---
    conn = get_db()
    today_str = now.strftime('%Y-%m-%d')
    existing = conn.execute("SELECT id FROM reports WHERE user_id = ? AND date(date) = ?", (user['id'], today_str)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Ya has enviado tu reporte de hoy.'}), 403

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

@app.route('/uploads/<path:filename>')
@app.route('/api/uploads/<path:filename>')
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
    # Use localized date or provided date
    date_str = data.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    status = data.get('status', True) # True to check, False to uncheck
    
    conn = get_db()
    c = conn.cursor()
    
    if status:
        # Check if already logged to avoid dupes
        exists = c.execute("SELECT 1 FROM meal_logs WHERE user_id = ? AND date = ? AND meal_name = ?", (user['id'], date_str, meal_name)).fetchone()
        if not exists:
            c.execute("INSERT INTO meal_logs (user_id, date, meal_name) VALUES (?, ?, ?)", (user['id'], date_str, meal_name))
            conn.commit()
    else:
        c.execute("DELETE FROM meal_logs WHERE user_id = ? AND date = ? AND meal_name = ?", (user['id'], date_str, meal_name))
        conn.commit()
        
    conn.close()
    return jsonify({'message': 'Registro de comida actualizado', 'status': status})

@app.route('/api/client/meal_logs', methods=['GET'])
@require_auth(roles=['CLIENT', 'ADMIN'])
def get_meal_logs(user):
    target_id = request.args.get('user_id', user['id'])
    date_str = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    conn = get_db()
    logs = conn.execute("SELECT meal_name FROM meal_logs WHERE user_id = ? AND date = ?", (target_id, date_str)).fetchall()
    conn.close()
    return jsonify([l['meal_name'] for l in logs])

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
    cur = conn.execute('''
        SELECT ue.id as assignment_id, e.name, e.muscle_group, e.icon_path, ue.day_of_week, ue.sets, ue.reps, ue.rest, 
               ue.target_muscles, ue.set_type, ue.combined_with
        FROM user_exercises ue
        JOIN exercises e ON ue.exercise_id = e.id
        WHERE ue.user_id = ?
        ORDER BY ue.day_of_week, ue.id
    ''', (target_id,))
    data = conn.fetchall(cur)
    conn.close()
    return jsonify(data)

def _get_diet_data_logic(user):
    target_id = request.args.get('user_id', user['id'])
    conn = get_db()
    cur = conn.execute('''
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
    data = conn.fetchall(cur)
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

@app.route('/api/client/log_workout', methods=['POST', 'DELETE'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def log_workout(user):
    data = request.json
    assignment_id = data.get('assignment_id')
    date_str = data.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    
    if not assignment_id:
        return jsonify({'error': 'Missing assignment_id'}), 400
        
    conn = get_db()
    if request.method == 'POST':
        # Accept single weight/reps or a list of logs
        weight = data.get('weight')
        reps = data.get('reps')
        set_num = data.get('set_number', 1)
        
        if weight is not None and reps is not None:
            # Single log entry
            conn.execute('''
                INSERT INTO workout_logs (user_id, assignment_id, set_number, weight_kg, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['id'], assignment_id, set_num, float(weight), date_str))
        else:
            # List of logs fallback
            logs = data.get('logs', [])
            for log in logs:
                conn.execute('''
                    INSERT INTO workout_logs (user_id, assignment_id, set_number, weight_kg, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user['id'], assignment_id, log.get('set', 1), float(log.get('weight', 0)), date_str))
        conn.commit()
    else: # DELETE
        conn.execute("DELETE FROM workout_logs WHERE user_id = ? AND assignment_id = ? AND date = ?", (user['id'], assignment_id, date_str))
        conn.commit()
        
    conn.close()
    return jsonify({'success': True})

@app.route('/api/client/workout_status', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def get_workout_status(user):
    target_id = request.args.get('user_id', user['id'])
    date_str = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    conn = get_db()
    # Return distinct assignment_ids that have logs for today
    logs = conn.execute("SELECT DISTINCT assignment_id FROM workout_logs WHERE user_id = ? AND date = ?", (target_id, date_str)).fetchall()
    conn.close()
    return jsonify([l['assignment_id'] for l in logs])

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
        conn.execute("UPDATE users SET phone = ?, objective_weight = ? WHERE id = ?", 
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
    country = "Desconocido"
    try:
        res = requests.get(f'http://ip-api.com/json/{ip}?fields=country', timeout=1)
        if res.status_code == 200:
            country = res.json().get('country', 'Desconocido')
    except: pass
    
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS metrics (key TEXT UNIQUE, value INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS visitor_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, ip TEXT, country TEXT)''')
    
    # Manejo seguro para INSERT en cualquier base de datos (Postgres o SQLite) sin requerir comandos OR IGNORE inseguros
    check_metric = conn.execute('''SELECT value FROM metrics WHERE key = 'total_visits' ''')
    if not conn.fetchone(check_metric):
        conn.execute('''INSERT INTO metrics (key, value) VALUES ('total_visits', 0)''')
        
    conn.execute('''UPDATE metrics SET value = value + 1 WHERE key = 'total_visits' ''')
    conn.execute('''INSERT INTO visitor_logs (ip, country) VALUES (?, ?)''', (ip, country))
    conn.commit()
    
    result = conn.execute('''SELECT value FROM metrics WHERE key = 'total_visits' ''')
    row = conn.fetchone(result)
    visits = row['value'] if getattr(conn, 'is_pg', False) or (isinstance(row, dict)) else row[0]
    conn.close()
    
    return jsonify({"visits": visits, "country": country})

@app.route('/api/get_stats', methods=['GET'])
def get_stats():
    conn = get_db()
    result_countries = conn.execute('''SELECT country, COUNT(*) as count FROM visitor_logs GROUP BY country ORDER BY count DESC''')
    
    countries_list = []
    for row in conn.fetchall(result_countries):
        c_name = row['country'] if isinstance(row, dict) else row[0]
        c_count = row['count'] if isinstance(row, dict) else row[1]
        countries_list.append({"country": c_name, "count": c_count})
        
    result_total = conn.execute('''SELECT value FROM metrics WHERE key = 'total_visits' ''')
    row_t = conn.fetchone(result_total)
    total = 0
    if row_t:
        total = row_t['value'] if isinstance(row_t, dict) else row_t[0]
        
    conn.close()
    return jsonify({"total_visits": total, "countries": countries_list})

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

@app.route('/descargar-app')
def download_app_v110():
    return send_from_directory(app.static_folder, 'MT_Fitness_PRO_v1.1.0.apk', as_attachment=True)

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/master/repair_db')
def repair_db():
    master_token = request.args.get('token')
    if master_token != "MT_MASTER_REPAIR_2026":
        return "Unauthorized", 401
        
    conn = get_db()
    try:
        # Detectar el desplazamiento (offset) usando el wrapper seguro
        result = conn.execute("SELECT MIN(id) as first_id FROM exercises")
        row = conn.fetchone(result)
        current_min_id = row['first_id'] if (row and isinstance(row, dict)) else (row[0] if row else None)
        
        if current_min_id is None:
            return "No hay ejercicios en la DB para reparar."
        
        # Si el anterior empezaba en 1, el offset es current_min_id - 1
        offset = current_min_id - 1
        print(f"REPAIR: Detectado offset de {offset}")
        
        if offset > 0:
            # Shift exercise_id in user_exercises asegurando compatibilidad PG
            conn.execute("UPDATE user_exercises SET exercise_id = exercise_id + " + ("%s" if getattr(conn, 'is_pg', False) else "?") + " WHERE exercise_id < " + ("%s" if getattr(conn, 'is_pg', False) else "?"), (offset, current_min_id))
            conn.commit()
            return f"Base de Datos reparada. Offset aplicado: {offset}"
        else:
            return "No se detectó desplazamiento de IDs. La DB parece estar en orden."
    except Exception as e:
        return f"Error en reparación: {str(e)}"
    finally:
        conn.close()
@app.route('/api/generate_marketing', methods=['GET', 'POST'], strict_slashes=False)
def generate_marketing():
    data = request.json
    topic = data.get('topic')
    type = data.get('type') # 'blog' or 'instagram'
    if not topic:
        return jsonify({"error": "Topic required"}), 400
    if type == 'blog':
        prompt = f"Escribe un artículo de blog SEO de unas 300 palabras sobre '{topic}' para el entrenador Miguel Torres. Usa un tono motivador, profesional y directo. No uses la palabra 'ciencia'. Enfócate en resultados y alto rendimiento."
    else:
        prompt = f"Genera un post de Instagram rompedor sobre '{topic}' para Miguel Torres. Incluye un gancho inicial, 3 puntos clave, llamada a la acción y 5 hashtags virales del sector fitness (vete directamente al grano)."
    try:
        if "sk-proj" in OPENAI_API_KEY:
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
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/seed_exercises', methods=['GET'])
def seed_exercises():
    sync_pro_exercises()
    return jsonify({"success": True, "message": "Ejercicios sincronizados"})


@app.route('/debug_version')
def debug_version():
    return "MT FITNESS PRO v1.2.8 LIVE"

@app.route('/download_app')
def download_app():
    import os
    try:
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'MT_Fitness_PRO_v1.2.4.apk', as_attachment=True)
    except Exception as e:
        return str(e), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
else:
    try:
        init_db()
    except Exception as e:
        print(f"Error initializing DB: {e}")
