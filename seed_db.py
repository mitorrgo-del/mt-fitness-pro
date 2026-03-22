
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'mtfitness.db')

def seed_master_v20():
    print(f"Connecting to {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    print("Clearing existing exercises...")
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
            ('Remo con Barra Prono', 'Espalda'), ('Remo con Barra Supino', 'Espalda'), ('Remo Mancuerna a 1 Mano', 'Espalda'),
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

            # --- FEMORAL (25+) ---
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

            # --- GEMELO (25+) ---
            ('Elevación Talones Pie Máquina', 'Gemelo'), ('Elevación Talones Sentado Máquina', 'Gemelo'), ('Elevación Talones Prensa', 'Gemelo'),
            ('Elevación Talones Burro Donkey', 'Gemelo'), ('Elevación Talones Unilateral de pie', 'Gemelo'), ('Elevación Talones Barra', 'Gemelo'),
            ('Elevación Talones Smith Machine', 'Gemelo'), ('Saltos de Comba Gemelo', 'Gemelo'), ('Caminata de Puntillas', 'Gemelo'),
            ('Elevación Talones Mancuernas', 'Gemelo'), ('Flexión Plantar con Banda', 'Gemelo'), ('Elevación Talones Banco Inclinado', 'Gemelo'),
            ('Elevación Talones Maquina Hack', 'Gemelo'), ('Elevación Talones sentado barra', 'Gemelo'), ('Elevación Talones de pie disco', 'Gemelo'),
            ('Saltos a la caja gemelo', 'Gemelo'), ('Paseo del Granjero de puntillas', 'Gemelo'), ('Elevación Talones Una pierna Prensa', 'Gemelo'),
            ('Elevación Talones polea baja', 'Gemelo'), ('Elevación Talones maquina escaladora', 'Gemelo'), ('Salto vertical gemelo', 'Gemelo'),
            ('Flexión plantar maquina asistida', 'Gemelo'), ('Elevación Talones en escalón', 'Gemelo'), ('Elevación Talones Hack Inversa', 'Gemelo'),
            ('Tirones de gemelo en polea', 'Gemelo'),

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
    
    print(f"Injecting {len(exs)} normalized exercises...")
    c.executemany("INSERT INTO exercises (name, muscle_group) VALUES (?, ?)", exs)
    conn.commit()
    
    count = c.execute("SELECT count(*) FROM exercises").fetchone()[0]
    print(f"Injection complete. Total exercises in DB: {count}")
    
    # Verificar categorías
    cats = c.execute("SELECT DISTINCT muscle_group FROM exercises").fetchall()
    print(f"Verified Categories: {[cat[0] for cat in cats]}")
    
    conn.close()

if __name__ == "__main__":
    seed_master_v20()
