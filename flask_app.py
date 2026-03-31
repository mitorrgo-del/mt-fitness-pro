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

load_dotenv() # Carga .env de Render si existe

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
            # For Postgres, we use the cursor
            cur = self.conn.cursor()
            cur.execute(query, params)
            return cur
        else:
            return self.conn.execute(query, params)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()
    def fetchone(self, cur):
        res = cur.fetchone()
        return dict(res) if res else None
    def fetchall(self, cur):
        res = cur.fetchall()
        return [dict(r) for r in res]

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
    c = conn_wrap.cursor()
    
    # We will skip DROP tables in production normally, but for the first run:
    if os.environ.get('RESEED_DB'):
        c.execute("DROP TABLE IF EXISTS exercises")
        c.execute("DROP TABLE IF EXISTS foods")
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT, 
        role TEXT, status TEXT, token TEXT, phone TEXT, 
        objective_weight REAL, routine_weeks INTEGER DEFAULT 4, access_until TEXT,
        bot_active INTEGER DEFAULT 1
    )''')
    
    # PRO Exercises Catalog
    c.execute('''CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, muscle_group TEXT
    )''')
    
    # PRO Foods Catalog (per 100g)
    c.execute('''CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT,
        kcal REAL, protein REAL, carbs REAL, fat REAL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS measurements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, date TEXT DEFAULT CURRENT_TIMESTAMP,
        weight REAL, waist REAL, chest REAL, hip REAL, thigh REAL, biceps REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, date TEXT DEFAULT CURRENT_TIMESTAMP,
        weight REAL, photo_front TEXT, photo_side TEXT, photo_back TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # PRO Assigned Food Plans (Admin -> Client)
    c.execute('''CREATE TABLE IF NOT EXISTS user_foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, food_id INTEGER,
        meal_name TEXT, grams REAL, day_name TEXT DEFAULT 'Día 1',
        added_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(food_id) REFERENCES foods(id)
    )''')

    # PRO Assigned Workout Plans (Admin -> Client)
    c.execute('''CREATE TABLE IF NOT EXISTS user_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, exercise_id INTEGER,
        day_of_week TEXT, sets TEXT, reps TEXT, rest TEXT,
        target_muscles TEXT, set_type TEXT DEFAULT 'NORMAL', 
        combined_with INTEGER,
        added_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(exercise_id) REFERENCES exercises(id)
    )''')
    
    conn_wrap.commit() # Commit the creation of tables before attempting alteration
    
    # MIGRACIÓN: Añadir columnas si no existen
    columns_to_add = [
        ("user_exercises", "set_type TEXT DEFAULT 'NORMAL'"),
        ("user_exercises", "combined_with INTEGER"),
        ("user_exercises", "target_muscles TEXT"),
        ("user_foods", "day_name TEXT DEFAULT 'Día 1'"),
    ]
    for table, coldef in columns_to_add:
        try:
            conn_wrap.execute(f"ALTER TABLE {table} ADD COLUMN {coldef}")
            conn_wrap.commit()
        except:
            if conn_wrap.is_pg:
                # En Postgres es necesario hacer un ROLLBACK para seguir con la transacción.
                conn_wrap.conn.rollback()
            pass # Ya existe la columna

    # PRO Meal Tracking
    c.execute('''CREATE TABLE IF NOT EXISTS meal_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, date TEXT, meal_name TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # PRIVACY & COACHING CHAT
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, sender_role TEXT, message TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # PRO Workout Weight Logging
    c.execute('''CREATE TABLE IF NOT EXISTS workout_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, assignment_id INTEGER,
        set_number INTEGER, weight_kg REAL, date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(assignment_id) REFERENCES user_exercises(id)
    )''')

    # MARKETING LEADS
    c.execute('''CREATE TABLE IF NOT EXISTS marketing_leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        last_goal TEXT,
        status TEXT DEFAULT 'COLD',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_followup DATETIME
    )''')

    # --- SEEDING PRO DATA ---
    # Check if we have exercises
    count_ex = c.execute("SELECT count(*) FROM exercises").fetchone()[0]
    if count_ex == 0:
        exs = [
            # PECHO
            ('Press Banca Plano Barra', 'Pecho'), ('Press Banca Inclinado Barra', 'Pecho'), ('Press Banca Declinado Barra', 'Pecho'),
            ('Press Banca Plano Mancuernas', 'Pecho'), ('Press Banca Inclinado Mancuernas', 'Pecho'), ('Aperturas Planas', 'Pecho'),
            ('Aperturas Inclinadas', 'Pecho'), ('Cruces en Polea Alta', 'Pecho'), ('Cruces en Polea Baja', 'Pecho'),
            ('Peck Deck (Máquina)', 'Pecho'), ('Press Pecho Máquina Sentado', 'Pecho'), ('Fondos en Paralelas (Pecho)', 'Pecho'),
            ('Pullover con Mancuerna', 'Pecho'), ('Flexiones de Brazo', 'Pecho'), ('Flexiones Lastradas', 'Pecho'),
            # ESPALDA
            ('Dominadas Pronas', 'Espalda'), ('Dominadas Supinas', 'Espalda'), ('Dominadas Neutras', 'Espalda'),
            ('Jalón al Pecho Abierto', 'Espalda'), ('Jalón al Pecho Cerrado', 'Espalda'), ('Remo con Barra Pronom', 'Espalda'),
            ('Remo con Barra Supino', 'Espalda'), ('Remo en Punta (T-Bar)', 'Espalda'), ('Remo con Mancuerna a 1 Mano', 'Espalda'),
            ('Remo Gironda en Polea', 'Espalda'), ('Remo en Máquina Pecho Apoyado', 'Espalda'), ('Pull-down Brazos Rígidos', 'Espalda'),
            ('Peso Muerto Convencional', 'Espalda'), ('Hiperextensiones Lumbar', 'Espalda'), ('Encogimientos Hombro (Trapecio)', 'Espalda'),
            # PIERNA
            ('Sentadilla Libre Barra Alta', 'Pierna'), ('Sentadilla Frontal', 'Pierna'), ('Sentadilla Hack', 'Pierna'),
            ('Prensa Inclinada a 45º', 'Pierna'), ('Prensa Horizontal', 'Pierna'), ('Extensiones de Cuádriceps', 'Pierna'),
            ('Zancadas (Lunges) con Mancuernas', 'Pierna'), ('Zancadas en Multipower', 'Pierna'), ('Sentadilla Búlgara', 'Pierna'),
            ('Peso Muerto Rumano', 'Pierna'), ('Peso Muerto Piernas Rígidas', 'Pierna'), ('Curl Femoral Tumbado', 'Pierna'),
            ('Curl Femoral Sentado', 'Pierna'), ('Curl Femoral de Pie a 1 Pierna', 'Pierna'), ('Hip Thrust (Puente de Glúteo)', 'Pierna'),
            ('Patada de Glúteo en Polea', 'Pierna'), ('Elevación de Talones de Pie (Gemelo)', 'Pierna'), ('Elevación de Talones Sentado (Sóleo)', 'Pierna'),
            # HOMBRO
            ('Press Militar Barra', 'Hombro'), ('Press Militar Mancuernas', 'Hombro'), ('Press Arnold', 'Hombro'),
            ('Elevaciones Laterales Mancuernas', 'Hombro'), ('Elevaciones Laterales Polea', 'Hombro'), ('Elevaciones Frontales', 'Hombro'),
            ('Pájaros (Hombro Posterior)', 'Hombro'), ('Facepull', 'Hombro'), ('Remo al Mentón', 'Hombro'),
            # BICEPS
            ('Curl Bíceps Barra Z', 'Bíceps'), ('Curl Bíceps Mancuernas', 'Bíceps'), ('Curl Martillo', 'Bíceps'),
            ('Curl Concentrado', 'Bíceps'), ('Curl Predicador', 'Bíceps'), ('Curl en Polea Baja', 'Bíceps'),
            # TRICEPS
            ('Press Francés', 'Tríceps'), ('Extensión Polea Alta (Cuerda)', 'Tríceps'), ('Extensión Polea Alta (Barra)', 'Tríceps'),
            ('Patada de Tríceps', 'Tríceps'), ('Fondos entre Bancos', 'Tríceps'), ('Press Cerrado (Pecho/Tríceps)', 'Tríceps'),
            # CORE
            ('Crunch Abdominal', 'Core'), ('Plancha Isométrica', 'Core'), ('Elevación de Piernas', 'Core'),
            ('Rueda Abdominal', 'Core'), ('Oblicuos en Polea', 'Core')
        ]
        c.executemany("INSERT INTO exercises (name, muscle_group) VALUES (?, ?)", exs)

    # Check if we have foods
    count_foods = c.execute("SELECT count(*) FROM foods").fetchone()[0]
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
        c.executemany("INSERT INTO foods (name, category, kcal, protein, carbs, fat) VALUES (?, ?, ?, ?, ?, ?)", foods)

    # Ensure Admin exists
    exists_admin = c.execute("SELECT id FROM users WHERE email = 'mitorrgo@gmail.com'").fetchone()
    if not exists_admin:
        c.execute("INSERT INTO users (id, email, password, name, role, status, token) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
    
    conn.execute("INSERT INTO users (id, email, password, name, role, status, token, phone, objective_weight, routine_weeks, access_until) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (uid, data.get('email'), data.get('password'), data.get('name'), role, status, token, data.get('phone', ''), data.get('objective_weight', None), 4, None))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Registrado.', 'status': status, 'token': token, 'role': role, 'name': data.get('name')})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    user_row = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (data.get('email'), data.get('password'))).fetchone()
    conn.close()
    if user_row:
        user = dict(user_row)
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
            'days_left': calc_days_left(user.get('access_until'))
        })
    return jsonify({'error': 'Credenciales incorrectas'}), 401

@app.route('/api/profile/update', methods=['POST'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def update_profile(user):
    data = request.json
    conn = get_db()
    conn.execute('''UPDATE users SET 
        name = ?, surname = ?, age = ?, height = ?, current_weight = ?, objective = ? 
        WHERE id = ?''', 
        (data.get('name'), data.get('surname'), data.get('age'), data.get('height'), 
         data.get('current_weight'), data.get('objective'), user['id']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Perfil actualizado'})

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
    weight = request.form.get('weight')
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
        
    conn = get_db()
    conn.execute("INSERT INTO reports (user_id, weight, photo_front, photo_side, photo_back) VALUES (?, ?, ?, ?, ?)",
                 (user['id'], weight, front_filename, side_filename, back_filename))
    # Also log weight to measurements for graphing
    conn.execute("INSERT INTO measurements (user_id, weight) VALUES (?, ?)", (user['id'], weight))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Reporte semanal enviado correctamente'})

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
    import smtplib
    from email.mime.text import MIMEText
    try:
        msg = MIMEText(f"El cliente {client_name} ha realizado una consulta que el Bot no puede resolver de forma automatizada. Entra a la App MT Fitness para tomar el control del chat.")
        msg['Subject'] = f"ALERTA MT FITNESS: {client_name} necesita un Coach Humano"
        msg['From'] = "notify@mtfitness.com"
        msg['To'] = "mitorrgo@gmail.com"
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()
    except Exception as e:
        print(f"SMTP ERROR: {e}")

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
    target_user_info = conn.execute("SELECT bot_active, name FROM users WHERE id = ?", (target_id,)).fetchone()

    if request.method == 'POST':
        data = request.json
        user_msg = data.get('message')
        if not user_msg: return jsonify({'error': 'No message'}), 400
        
        # 1. Insert User Message
        try:
            conn.execute("INSERT INTO chat_messages (user_id, sender_role, message) VALUES (?, ?, ?)",
                         (target_id, user['role'], user_msg))
            conn.commit()
        except Exception as e:
            print(f"DATABASE ERROR (User Msg): {e}")
            return jsonify({'error': 'Database insertion failed'}), 500

        # 2. Bot Response Logic (Atomic Block)
        is_bot_on = 0
        try:
            is_bot_on = int(target_user_info['bot_active']) if (target_user_info and target_user_info['bot_active'] is not None) else 0
        except: pass

        if is_bot_on == 1:
            try:
                bot_reply = generate_bot_response(user_msg, target_user_info['name'] if target_user_info else 'Cliente')
                conn.execute("INSERT INTO chat_messages (user_id, sender_role, message) VALUES (?, ?, ?)",
                             (target_id, 'BOT', bot_reply))
                conn.commit()
                print(f"BOT SUCCESS: Replied to {target_id}")
            except Exception as e:
                print(f"BOT INDIVIDUAL ERROR: {e}")
        
        conn.close()
        return jsonify({'status': 'ok', 'message': 'Sent', 'response': 'Mensaje procesado'})
    else:
        msgs = conn.execute("SELECT * FROM chat_messages WHERE user_id = ? ORDER BY timestamp ASC", (target_id,)).fetchall()
        # COMPATIBILITY: Flutter expects a List, Web expects a Dict with bot_active
        is_flutter = 'flutter' in request.headers.get('User-Agent', '').lower() or request.args.get('format') == 'list'
        
        if is_flutter:
            conn.close()
            return jsonify([dict(m) for m in msgs])
        
        # Original format for Web
        try:
            bot_active = int(target_user_info['bot_active']) if (target_user_info and target_user_info['bot_active'] is not None) else 0
        except:
            bot_active = 0
            
        conn.close()
        return jsonify({'messages': [dict(m) for m in msgs], 'bot_active': bot_active})

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

@app.route('/descargar-app')
def download_app():
    return redirect("https://raw.githubusercontent.com/mitorrgo-del/mt-fitness-pro/740f8f4/app/MTFitness_PRO_v26_FINAL.apk", code=302)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
