from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import uuid
import datetime
from functools import wraps

app = Flask(__name__, static_folder='app')
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'mtfitness.db')

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Force Re-Seed for expanded catalog
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
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, date TEXT,
        weight REAL, waist REAL, chest REAL, hip REAL, thigh REAL, biceps REAL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    # PRO Assigned Food Plans (Admin -> Client)
    c.execute('''CREATE TABLE IF NOT EXISTS user_foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, food_id INTEGER,
        day_name TEXT, meal_name TEXT, grams REAL,
        added_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(food_id) REFERENCES foods(id)
    )''')

    # PRO Assigned Workout Plans (Admin -> Client)
    c.execute('''CREATE TABLE IF NOT EXISTS user_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, exercise_id INTEGER,
        day_of_week TEXT, target_muscles TEXT, sets TEXT, reps TEXT, rest TEXT,
        added_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(exercise_id) REFERENCES exercises(id)
    )''')
    
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

    # AI BLOG ARTICLES
    c.execute('''CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, content TEXT, category TEXT, date TEXT,
        image_url TEXT
    )''')
    
    # SOCIAL MEDIA AGENT POSTS
    c.execute('''CREATE TABLE IF NOT EXISTS social_media_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        caption TEXT,
        image_url TEXT,
        status TEXT DEFAULT 'DRAFT', -- DRAFT, APPROVED, POSTED, REJECTED
        scheduled_date TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')

    # Forzar re-sembrado masivo para V16
    force_reseeding = True
    if force_reseeding:
        c.execute("DELETE FROM exercises")
    # Forzar re-sembrado masivo para V18 - CATÁLOGO MAESTRO EXTREMO
    force_reseeding = True
    if force_reseeding:
        c.execute("DELETE FROM exercises")
        exs = [
            # --- PECHO (25+) ---
            ('Press Banca Plano Barra', 'Pecho'), ('Press Banca Inclinado Barra', 'Pecho'), ('Press Banca Declinado Barra', 'Pecho'),
            ('Press Banca Plano Mancuernas', 'Pecho'), ('Press Banca Inclinado Mancuernas', 'Pecho'), ('Press Banca Declinado Mancuernas', 'Pecho'),
            ('Aperturas Planas Mancuernas', 'Pecho'), ('Aperturas Inclinadas Mancuernas', 'Pecho'), ('Cruces Poleas Altas', 'Pecho'),
            ('Cruces Poleas Bajas', 'Pecho'), ('Cruces Poleas Medias', 'Pecho'), ('Peck Deck Máquina', 'Pecho'),
            ('Press Pecho Máquina Sentado', 'Pecho'), ('Press Inclinado Máquina', 'Pecho'), ('Press Pecho Convergente Hammer', 'Pecho'),
            ('Press Inclinado Convergente Hammer', 'Pecho'), ('Fondos Paralelas Pecho', 'Pecho'), ('Pullover Mancuerna', 'Pecho'),
            ('Press Svend Disco', 'Pecho'), ('Flexiones Clásicas', 'Pecho'), ('Flexiones Diamante', 'Pecho'),
            ('Flexiones Inclinadas', 'Pecho'), ('Flexiones Declinadas', 'Pecho'), ('Press Landmine Pecho', 'Pecho'),
            ('Aperturas Máquina Contractora', 'Pecho'), ('Press Banca Smith Machine', 'Pecho'), ('Press Inclinado Smith Machine', 'Pecho'),

            # --- ESPALDA (25+) ---
            ('Dominadas Pronas', 'Espalda'), ('Dominadas Supinas', 'Espalda'), ('Dominadas Neutras', 'Espalda'),
            ('Jalón al Pecho Abierto', 'Espalda'), ('Jalón al Pecho Cerrado', 'Espalda'), ('Jalón al Pecho Supino', 'Espalda'),
            ('Remo con Barra Pronom', 'Espalda'), ('Remo con Barra Supino', 'Espalda'), ('Remo Mancuerna a 1 Mano', 'Espalda'),
            ('Remo Gironda Polea Baja', 'Espalda'), ('Remo en Punta Barra T', 'Espalda'), ('Remo Máquina Pecho Apoyado', 'Espalda'),
            ('Remo Convergente Hammer Alta', 'Espalda'), ('Remo Convergente Hammer Baja', 'Espalda'), ('Pull-over Polea Alta Brazos Rígidos', 'Espalda'),
            ('Peso Muerto Convencional', 'Espalda'), ('Peso Muerto Sumo', 'Espalda'), ('Rack Pulls', 'Espalda'),
            ('Hiperextensiones Lumbar', 'Espalda'), ('Buenos Días Barra', 'Espalda'), ('Encogimientos Barra Hombro', 'Espalda'),
            ('Encogimientos Mancuernas Trapecio', 'Espalda'), ('Remo al Mentón Trapecio', 'Espalda'), ('Remo Pendlay', 'Espalda'),
            ('Jalón tras Nuca Polea', 'Espalda'), ('Remo con Barra Smith Machine', 'Espalda'),

            # --- HOMBRO (25+) ---
            ('Press Militar Barra de Pie', 'Hombro'), ('Press Militar Barra Sentado', 'Hombro'), ('Press Militar Mancuernas', 'Hombro'),
            ('Press Arnold Mancuernas', 'Hombro'), ('Press Militar Máquina', 'Hombro'), ('Elevaciones Laterales Mancuernas', 'Hombro'),
            ('Elevaciones Laterales Polea', 'Hombro'), ('Elevaciones Laterales Máquina', 'Hombro'), ('Elevaciones Frontales Barra', 'Hombro'),
            ('Elevaciones Frontales Mancuernas', 'Hombro'), ('Elevaciones Frontales Disco', 'Hombro'), ('Pájaros Mancuernas Posterior', 'Hombro'),
            ('Pájaros Polea Posterior', 'Hombro'), ('Facepull Polea Alta', 'Hombro'), ('Peck Deck Inverso Posterior', 'Hombro'),
            ('Remo al Mentón Barra Z', 'Hombro'), ('Remo al Mentón Polea', 'Hombro'), ('Rotación Externa Polea Manguito', 'Hombro'),
            ('Press Militar Smith Machine', 'Hombro'), ('Elevaciones Laterales Unilaterales', 'Hombro'), ('Vuelos Frontales Polea', 'Hombro'),
            ('Cruces Posteriores Poleas', 'Hombro'), ('Press Militar Unilateral Mancuerna', 'Hombro'), ('Paseo del Granjero Hombros', 'Hombro'),
            ('Levantamiento Frontal Martillo', 'Hombro'),

            # --- BICEPS (25+) ---
            ('Curl Bíceps Barra Recta', 'Biceps'), ('Curl Bíceps Barra Z', 'Biceps'), ('Curl Bíceps Mancuernas', 'Biceps'),
            ('Curl Bíceps Alterno', 'Biceps'), ('Curl Martillo Mancuernas', 'Biceps'), ('Curl Martillo Polea Cuerda', 'Biceps'),
            ('Curl Bíceps Polea Baja Barra', 'Biceps'), ('Curl Bíceps Polea Alta Doble', 'Biceps'), ('Curl Predicador Barra Z', 'Biceps'),
            ('Curl Predicador Máquina', 'Biceps'), ('Curl Concentrado Mancuerna', 'Biceps'), ('Curl Bíceps Inclinado Mancuernas', 'Biceps'),
            ('Curl Bíceps Spider Barra Z', 'Biceps'), ('Curl Bíceps Zottman', 'Biceps'), ('Curl Bíceps Landmine', 'Biceps'),
            ('Curl Bíceps Unilateral Polea', 'Biceps'), ('Curl Bíceps en Banco Scott', 'Biceps'), ('Curl Bíceps Prono barra', 'Biceps'),
            ('Curl Bíceps con Disco', 'Biceps'), ('Drag Curl Barra', 'Biceps'), ('Curl Bíceps Waiter', 'Biceps'),
            ('Curl Bíceps 21s Barra Z', 'Biceps'), ('Curl Bíceps Arrastre Mancuernas', 'Biceps'), ('Curl Bíceps Maquina sentado', 'Biceps'),
            ('Curl Bíceps Polea Baja agarre inverso', 'Biceps'),

            # --- TRICEPS (25+) ---
            ('Press Francés Barra Z', 'Triceps'), ('Extensión Polea Alta Barra', 'Triceps'), ('Extensión Polea Alta Cuerda', 'Triceps'),
            ('Extensión Polea Alta Inverso', 'Triceps'), ('Extensión tras nuca Mancuerna', 'Triceps'), ('Extensión tras nuca Polea', 'Triceps'),
            ('Patada Tríceps Mancuerna', 'Triceps'), ('Patada Tríceps Polea', 'Triceps'), ('Fondos Paralelas Tríceps', 'Triceps'),
            ('Fondos entre Bancos Dips', 'Triceps'), ('Press Cerrado Barra Tríceps', 'Triceps'), ('Press Francés Mancuernas', 'Triceps'),
            ('Extensión Tríceps Unilateral Polea', 'Triceps'), ('Press California', 'Triceps'), ('Extensión Tríceps Máquina', 'Triceps'),
            ('Press Cerrado Smith Machine', 'Triceps'), ('Press Francés Banco Inclinado', 'Triceps'), ('Extensión Tríceps con banda', 'Triceps'),
            ('Copa Tríceps a dos manos', 'Triceps'), ('Extensión Tríceps a una mano polea', 'Triceps'), ('Fondos Tríceps Maquina', 'Triceps'),
            ('Patada Tríceps Máquina', 'Triceps'), ('Press JM Arrastre', 'Triceps'), ('Extensiones Tríceps Katana', 'Triceps'),
            ('Press Francés en suelo Mancuernas', 'Triceps'),

            # --- CUADRICEPS (25+) ---
            ('Sentadilla Libre Barra Alta', 'Cuadriceps'), ('Sentadilla Frontal Barra', 'Cuadriceps'), ('Sentadilla Hack Máquina', 'Cuadriceps'),
            ('Prensa Inclinada 45', 'Cuadriceps'), ('Prensa Horizontal Piernas', 'Cuadriceps'), ('Extensiones Cuádriceps Máquina', 'Cuadriceps'),
            ('Sentadilla Búlgara Mancuernas', 'Cuadriceps'), ('Sentadilla Smith Machine', 'Cuadriceps'), ('Zancadas Mancuernas pierna', 'Cuadriceps'),
            ('Sentadilla Goblet', 'Cuadriceps'), ('Sissy Squat', 'Cuadriceps'), ('Step Up Cajón Mancuernas', 'Cuadriceps'),
            ('Zancadas Caminando con Barra', 'Cuadriceps'), ('Sentadilla Sumo Mancuerna', 'Cuadriceps'), ('Sentadilla Zercher', 'Cuadriceps'),
            ('Prensa Unilateral', 'Cuadriceps'), ('Sentadilla con Cinturón Maquina', 'Cuadriceps'), ('Sentadilla Pendular', 'Cuadriceps'),
            ('Zancadas hacia atrás Mancuernas', 'Cuadriceps'), ('Sentadilla isométrica pared', 'Cuadriceps'), ('Salto al cajón Box Jump', 'Cuadriceps'),
            ('Extensiones Cuádriceps Unilateral', 'Cuadriceps'), ('Sentadilla Hack Smith', 'Cuadriceps'), ('Prensa Hack Inversa', 'Cuadriceps'),
            ('Split Squat con Barra', 'Cuadriceps'),

            # --- ISQUIOS / FEMORAL (25+) ---
            ('Peso Muerto Rumano Barra', 'Femoral'), ('Peso Muerto Rumano Mancuernas', 'Femoral'), ('Curl Femoral Tumbado Máquina', 'Femoral'),
            ('Curl Femoral Sentado Máquina', 'Femoral'), ('Curl Femoral de Pie Unilateral', 'Femoral'), ('Peso Muerto Piernas Rígidas', 'Femoral'),
            ('Curl Femoral Fitball', 'Femoral'), ('Curl Nórdico Isquios', 'Femoral'), ('Glute Ham Raise GHR', 'Femoral'),
            ('Buenos Días sentado Barra', 'Femoral'), ('Peso Muerto Rumano Unilateral', 'Femoral'), ('Curl Femoral Banda Elástica', 'Femoral'),
            ('Peso Muerto Barra Hexagonal', 'Femoral'), ('Curl Femoral con Mancuerna entre pies', 'Femoral'), ('Hiperextensiones Enfoque Femoral', 'Femoral'),
            ('Peso Muerto Rumano Smith Machine', 'Femoral'), ('Curl Femoral Polea Baja', 'Femoral'), ('Peso Muerto Slider', 'Femoral'),
            ('Extensiones Cadera Banco', 'Femoral'), ('Zancada Larga Isquios', 'Femoral'), ('Step Up Enfoque Isquio', 'Femoral'),
            ('Pull through Polea Baja', 'Femoral'), ('Peso Muerto Convencional Enfoque Isquio', 'Femoral'), ('Curl Femoral Maquina Convergente', 'Femoral'),
            ('Peso Muerto Piernas Rígidas Mancuernas', 'Femoral'),

            # --- GLUTEO (25+) ---
            ('Hip Thrust Barra', 'Gluteo'), ('Hip Thrust Máquina', 'Gluteo'), ('Hip Thrust Smith Machine', 'Gluteo'),
            ('Puente de Glúteo Barra', 'Gluteo'), ('Patada Glúteo Polea Baja', 'Gluteo'), ('Patada Glúteo Máquina', 'Gluteo'),
            ('Abducción de Cadera Máquina', 'Gluteo'), ('Abducción de Cadera Polea', 'Gluteo'), ('Clamshells con Banda', 'Gluteo'),
            ('Monster Walk Banda', 'Gluteo'), ('Frog Pumps Glúteo', 'Gluteo'), ('Zancada Lateral Mancuerna', 'Gluteo'),
            ('Peso Muerto Rumano Unilateral Gluteo', 'Gluteo'), ('Puente de Glúteo Unilateral', 'Gluteo'), ('Patada de Glúteo Suelo', 'Gluteo'),
            ('Step Up Glúteo Alto', 'Gluteo'), ('Abducción Cadera Suelo', 'Gluteo'), ('Hiperextensiones Glúteo 45', 'Gluteo'),
            ('Sentadilla Sumo Kettlebell', 'Gluteo'), ('Zancada Cruzada Curtsy', 'Gluteo'), ('Apertura Cadera sentado banda', 'Gluteo'),
            ('Patada Glúteo Maquina Smith', 'Gluteo'), ('Empuje de cadera maquina convergente', 'Gluteo'), ('Abducción Maquina Sentado', 'Gluteo'),
            ('Puente de Glúteo Isométrico', 'Gluteo'),

            # --- ABDUCTORES (25+) ---
            ('Abducción de Cadera Máquina', 'Abductores'), ('Abducción con Banda Elástica', 'Abductores'), ('Monster Walk banda', 'Abductores'),
            ('Clamshells (Almejas) banda', 'Abductores'), ('Abducción en Polea Baja', 'Abductores'), ('Elevación de pierna lateral suelo', 'Abductores'),
            ('Plancha lateral con abducción', 'Abductores'), ('Abducción en Máquina Sentado', 'Abductores'), ('Separación de piernas con banda', 'Abductores'),
            ('Caminata lateral con banda tobillos', 'Abductores'), ('Paseo lateral banda rodillas', 'Abductores'), ('Abducción de cadera de pie polea', 'Abductores'),
            ('Abducción en banco inclinado', 'Abductores'), ('Abducción isométrica contra pared', 'Abductores'), ('Salto lateral abductor', 'Abductores'),
            ('Elevación de cadera abductora', 'Abductores'), ('Abducción de pierna polea media', 'Abductores'), ('Patada abductora maquina smith', 'Abductores'),
            ('Aperturas abductoras en suelo', 'Abductores'), ('Circunducción de cadera banda', 'Abductores'), ('Abducción dinámica polea', 'Abductores'),
            ('Estocada lateral abductora', 'Abductores'), ('Elevación de pierna acostado', 'Abductores'), ('Abducción maquina convergente', 'Abductores'),
            ('Pulsos abductores con banda', 'Abductores'),

            # --- ADUCTORES (25+) ---
            ('Adducción de Cadera Máquina', 'Aductores'), ('Adducción con Balón entre piernas', 'Aductores'), ('Adducción en Polea Baja', 'Aductores'),
            ('Copenhague Plank (Aductores)', 'Aductores'), ('Adducción en Suelo pierna cruzada', 'Aductores'), ('Adducción con Banda Elástica', 'Aductores'),
            ('Sentadilla Sumo (enfoque aductor)', 'Aductores'), ('Prensa con pies anchos aductor', 'Aductores'), ('Zancada lateral enfoque aductor', 'Aductores'),
            ('Adducción isométrica sentado', 'Aductores'), ('Adducción de cadera de pie polea', 'Aductores'), ('Adducción en anillo de pilates', 'Aductores'),
            ('Aperturas aductoras en suelo', 'Aductores'), ('Adducción con disco entre rodillas', 'Aductores'), ('Deslizamiento aductor con trapo', 'Aductores'),
            ('Plancha aductora asistida', 'Aductores'), ('Aducción en banco plano suelo', 'Aductores'), ('Caminata aductora cruzada', 'Aductores'),
            ('Aducción dinámica polea baja', 'Aductores'), ('Sentadilla Cossack aductores', 'Aductores'), ('Adducción maquina específica', 'Aductores'),
            ('Elevación lateral pierna inferior', 'Aductores'), ('Aducción con kettlebell', 'Aductores'), ('Pulsos aductores balón', 'Aductores'),
            ('Estiramiento activo aductor', 'Aductores'),

            # --- CARDIO (25+) ---
            ('Cinta de Correr (Caminar)', 'Cardio'), ('Cinta de Correr (Correr)', 'Cardio'), ('Bicicleta Estática', 'Cardio'),
            ('Bicicleta de Spinning', 'Cardio'), ('Elíptica Máquina', 'Cardio'), ('Escaladora (StepMill)', 'Cardio'),
            ('Remo en Máquina (Cardio)', 'Cardio'), ('Air Bike (Asault)', 'Cardio'), ('Ski Erg Máquina', 'Cardio'),
            ('Cinta Curva (Self-Powered)', 'Cardio'), ('Máquina de Step Clásica', 'Cardio'), ('Bicicleta Reclinada', 'Cardio'),
            ('Máquina de Remo Hidráulica', 'Cardio'), ('Cinta de Correr inclinada', 'Cardio'), ('Saltos de Comba (Cardio)', 'Cardio'),
            ('Boxeo Saco (Cardio)', 'Cardio'), ('Burpees (Cardio)', 'Cardio'), ('Mountain Climbers (Cardio)', 'Cardio'),
            ('Jumping Jacks (Cardio)', 'Cardio'), ('Natación Máquina', 'Cardio'), ('Ciclismo en Máquina', 'Cardio'),
            ('Entrenamiento HIIT (Cardio)', 'Cardio'), ('Cardio Funcional', 'Cardio'), ('Aeróbic Máquina', 'Cardio'),
            ('Simulador de Escalada', 'Cardio')
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

    conn.commit()
    conn.close()

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


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Ruta no encontrada', 'path': request.path}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/api/auth/register', methods=['POST'], strict_slashes=False)
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
    return jsonify({'message': 'Registrado.', 'status': status, 'token': token, 'role': role, 'name': data.get('name'), 'id': uid})

@app.route('/api/auth/login', methods=['POST'], strict_slashes=False)
def login():
    data = request.json
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (data.get('email'), data.get('password'))).fetchone()
    conn.close()
    if user:
        if user['status'] != 'APPROVED': return jsonify({'error': 'Cuenta pendiente.'}), 403
        
        # Check Expiration (only for clients)
        if user['role'] == 'CLIENT' and user['access_until']:
            expiration = datetime.datetime.strptime(user['access_until'], '%Y-%m-%d')
            if datetime.datetime.now() > expiration:
                return jsonify({'error': 'Suscripción caducada. Contacta con tu Coach.'}), 403

        return jsonify({'token': user['token'], 'role': user['role'], 'name': user['name'], 'email': user['email'], 'id': user['id']})
    return jsonify({'error': 'Credenciales incorrectas'}), 401

@app.route('/api/admin/users', methods=['GET'])
@require_auth(roles=['ADMIN'])
def admin_get_users(admin):
    conn = get_db()
    users = conn.execute("SELECT id, email, name, role, status, phone, objective_weight, routine_weeks, access_until FROM users").fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])

@app.route('/api/admin/approve/<target_id>', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_approve_user(admin, target_id):
    conn = get_db()
    conn.execute("UPDATE users SET status = 'APPROVED' WHERE id = ?", (target_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Aprobado'})

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
@app.route('/api/admin/foods', methods=['GET'])
@require_auth(roles=['ADMIN'])
def catalog_foods(admin):
    conn = get_db(); recs = conn.execute("SELECT * FROM foods ORDER BY category, name").fetchall(); conn.close()
    return jsonify([dict(r) for r in recs])

@app.route('/api/admin/assign_food', methods=['POST'])
@require_auth(roles=['ADMIN'])
def assign_food(admin):
    data = request.json
    conn = get_db()
    # Support backward compatibility by defaulting to "Día 1" if not provided
    day_name = data.get('day_name', 'Día 1')
    conn.execute("INSERT INTO user_foods (user_id, food_id, day_name, meal_name, grams) VALUES (?, ?, ?, ?, ?)", 
                 (data['user_id'], data['food_id'], day_name, data['meal_name'], data['grams']))
    conn.commit(); conn.close()
    return jsonify({'message': 'Alimento asignado a la comida'})

@app.route('/api/admin/remove_food/<int:id>', methods=['DELETE'])
@require_auth(roles=['ADMIN'])
def remove_food(admin, id):
    conn = get_db(); conn.execute("DELETE FROM user_foods WHERE id = ?", (id,)); conn.commit(); conn.close()
    return jsonify({'message': 'Alimento eliminado'})

@app.route('/api/client/my_plan', methods=['GET'])
@require_auth(roles=['CLIENT', 'ADMIN'])
def client_plan(user):
    target_id = request.args.get('user_id', user['id'])
    conn = get_db()
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    q = """
        SELECT f.name, f.category, uf.day_name, uf.meal_name, uf.grams, uf.id as assignment_id,
               (f.kcal * uf.grams / 100.0) as calc_kcal,
               (f.protein * uf.grams / 100.0) as calc_protein,
               (f.carbs * uf.grams / 100.0) as calc_carbs,
               (f.fat * uf.grams / 100.0) as calc_fat,
               EXISTS(SELECT 1 FROM meal_logs WHERE user_id = ? AND date = ? AND meal_name = uf.meal_name) as is_completed
        FROM foods f JOIN user_foods uf ON f.id = uf.food_id
        WHERE uf.user_id = ?
        ORDER BY uf.day_name, uf.meal_name, f.name
    """
    plan = conn.execute(q, (target_id, date_str, target_id)).fetchall()
    conn.close()
    return jsonify([dict(p) for p in plan])

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

@app.route('/api/admin/assign_exercise', methods=['POST'])
@require_auth(roles=['ADMIN'])
def assign_exercise(admin):
    data = request.json
    conn = get_db()
    target_muscles = data.get('target_muscles', '')
    conn.execute("INSERT INTO user_exercises (user_id, exercise_id, day_of_week, target_muscles, sets, reps, rest) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                 (data['user_id'], data['exercise_id'], data['day_of_week'], target_muscles, data['sets'], data['reps'], data.get('rest', '')))
    conn.commit(); conn.close()
    return jsonify({'message': 'Ejercicio configurado'})

@app.route('/api/client/my_workout', methods=['GET'])
@require_auth(roles=['ADMIN', 'CLIENT'])
def client_workout(user):
    target_id = request.args.get('user_id', user['id'])
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT ue.id as assignment_id, e.name, e.muscle_group, ue.day_of_week, ue.target_muscles, ue.sets, ue.reps, ue.rest
        FROM user_exercises ue
        JOIN exercises e ON ue.exercise_id = e.id
        WHERE ue.user_id = ?
        ORDER BY ue.day_of_week
    ''', (target_id,))
    data = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(data)

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

# ---- ADMIN DELETE OPs ----
@app.route('/api/admin/remove_food/<int:id>', methods=['DELETE'])
@require_auth(roles=['ADMIN'])
def admin_remove_food(admin, id):
    conn = get_db()
    conn.execute("DELETE FROM user_foods WHERE id = ?", (id,))
    conn.commit(); conn.close()
    return jsonify({'message': 'Alimento borrado'})

@app.route('/api/admin/remove_exercise/<int:id>', methods=['DELETE'])
@require_auth(roles=['ADMIN'])
def admin_remove_exercise(admin, id):
    conn = get_db()
    conn.execute("DELETE FROM user_exercises WHERE id = ?", (id,))
    conn.execute("DELETE FROM workout_logs WHERE assignment_id = ?", (id,))
    conn.commit(); conn.close()
    return jsonify({'message': 'Ejercicio borrado'})

# ---- CHAT SYSTEM WITH AI BOT ----
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

@app.route('/api/chat', methods=['GET', 'POST'], strict_slashes=False)
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
        return jsonify({'status': 'ok', 'message': 'Sent'})
    else:
        msgs = conn.execute("SELECT * FROM chat_messages WHERE user_id = ? ORDER BY timestamp ASC", (target_id,)).fetchall()
        # Aseguramos que bot_active sea siempre un entero (0 o 1) para el frontend
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

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(app.static_folder, 'manifest.json')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

init_db()
@app.route('/api/articles', methods=['GET'])
def get_articles():
    conn = get_db()
    recs = conn.execute("SELECT * FROM articles ORDER BY date DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in recs])

@app.route('/api/admin/generate_articles', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_generate_articles(admin):
    import datetime
    conn = get_db()
    c = conn.cursor()
    date_now = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Banco de artículos con imágenes de alta calidad (identificables)
    pool_articles = [
        ("Nutrición Peri-entrenamiento: Qué comer antes y después", 
         "Para maximizar el rendimiento, consume una mezcla de hidratos de absorción rápida y proteína 90 mins antes. Después, prioriza la proteína para detener el catabolismo.", 
         "Nutrición", date_now, 
         "https://images.unsplash.com/photo-1532384748853-8f54a8f476e2?q=80&w=800&auto=format&fit=crop"),
        
        ("El Mito de las Repeticiones: ¿Fuerza o Hipertrofia?", 
         "La ciencia demuestra que el factor clave es la intensidad y cercanía al fallo muscular, no solo el número de repeticiones.", 
         "Científico", date_now, 
         "https://images.unsplash.com/photo-1541534741688-6078c64b52df?q=80&w=800&auto=format&fit=crop"),
        
        ("Suplementación de Élite: Todo sobre la Creatina",
         "La creatina monohidrato es el suplemento Rey. Ayuda a regenerar el ATP y mejorar la hidratación intracelular, aumentando tu rendimiento en un 10-15%.",
         "Suplementación", date_now,
         "https://images.unsplash.com/photo-1593095394411-3c120627e770?q=80&w=800&auto=format&fit=crop"),

        ("Pre-Entreno: ¿Gasolina o solo Estimulantes?",
         "Un buen pre-entreno debe contener citrulina, beta-alanina y quizás cafeína. Aprende a no depender de ellos pero a usarlos cuando el entreno lo requiere.",
         "Suplementación", date_now,
         "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=800&auto=format&fit=crop"),

        ("Batch Cooking: Ahorra horas en la cocina",
         "Preparar tus tuppers el domingo es la clave del éxito. Proteína limpia y carbos complejos para que no falles en tu dieta diaria.",
         "Nutrición", date_now,
         "https://images.unsplash.com/photo-1547592166-23ac45744acd?q=80&w=800&auto=format&fit=crop")
    ]
    
    import random
    new_articles = random.sample(pool_articles, 2) # Genera 2 aleatorios cada vez
    
    for title, content, cat, date, img in new_articles:
        exists = c.execute("SELECT 1 FROM articles WHERE title = ?", (title,)).fetchone()
        if not exists:
            c.execute("INSERT INTO articles (title, content, category, date, image_url) VALUES (?, ?, ?, ?, ?)", (title, content, cat, date, img))
    
    conn.commit(); conn.close()
    return jsonify({'status': 'generated'})

# --- SOCIAL MEDIA AGENT ENDPOINTS ---
@app.route('/api/admin/social_posts', methods=['GET'])
@require_auth(roles=['ADMIN'])
def admin_get_social_posts(admin):
    conn = get_db()
    posts = conn.execute("SELECT * FROM social_media_posts ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(p) for p in posts])

@app.route('/api/admin/social_posts/approve/<int:post_id>', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_approve_post(admin, post_id):
    conn = get_db()
    conn.execute("UPDATE social_media_posts SET status = 'APPROVED' WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Post aprobado.'})

@app.route('/api/admin/social_posts/reject/<int:post_id>', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_reject_post(admin, post_id):
    conn = get_db()
    conn.execute("UPDATE social_media_posts SET status = 'REJECTED' WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Post rechazado.'})

@app.route('/api/admin/social_posts/generate', methods=['POST'])
@require_auth(roles=['ADMIN'])
def admin_trigger_social_gen(admin):
    import subprocess
    try:
        # Ejecutamos el agente como un proceso independiente
        subprocess.run(["python", "social_media_agent.py"], check=True)
        return jsonify({'message': 'Generación activada con éxito.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
