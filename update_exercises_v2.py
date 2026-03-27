import sqlite3

def update_db():
    conn = sqlite3.connect('mtfitness.db')
    c = conn.cursor()
    
    # 1. Convertir grupos musculares existentes a MAYÚSCULAS y sin acentos
    muscle_map = {
        'Pecho': 'PECHO',
        'Espalda': 'ESPALDA',
        'Hombro': 'HOMBRO',
        'Pierna': 'PIERNA',
        'Glteo': 'PIERNA', # Unificamos o ponemos GLUTEOS
        'Bceps': 'BICEPS',
        'Trceps': 'TRICEPS',
        'Brazo': 'BRAZO',
        'Abdominales': 'ABDOMINALES'
    }
    
    # Actualizamos todos los registros actuales
    exercises = c.execute("SELECT id, muscle_group FROM exercises").fetchall()
    for ex_id, group in exercises:
        new_group = group.upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U')
        c.execute("UPDATE exercises SET muscle_group = ? WHERE id = ?", (new_group, ex_id))
    
    # 2. Añadir 10 de BICEPS
    biceps_new = [
        ('Curl de Bíceps con Barra EZ', 'BICEPS'),
        ('Curl Martillo Cruce al Pecho', 'BICEPS'),
        ('Curl Predicador en Máquina', 'BICEPS'),
        ('Curl Concentrado con Mancuerna', 'BICEPS'),
        ('Curl de Bíceps en Polea Baja', 'BICEPS'),
        ('Curl Spider con Mancuernas', 'BICEPS'),
        ('Curl Inclinado con Mancuernas (Banco 45º)', 'BICEPS'),
        ('Curl Zottman', 'BICEPS'),
        ('Curl de Bíceps con Banda de Resistencia', 'BICEPS'),
        ('Curl de Bíceps con Polea Alta (Doble)', 'BICEPS')
    ]
    
    # 3. Añadir 10 de TRICEPS
    triceps_new = [
        ('Dips en Paralelas (Tríceps focus)', 'TRICEPS'),
        ('Press Francés con Barra EZ', 'TRICEPS'),
        ('Extensión de Tríceps con Cuerda', 'TRICEPS'),
        ('Extensión Tras Nuca Mancuerna', 'TRICEPS'),
        ('Patada de Tríceps en Polea', 'TRICEPS'),
        ('Press Banca Agarre Cerrado', 'TRICEPS'),
        ('Extensión Tríceps Unilateral Polea', 'TRICEPS'),
        ('Copa de Tríceps Polea Baja', 'TRICEPS'),
        ('Flexiones Diamante', 'TRICEPS'),
        ('Fondos entre Bancos (Dips)', 'TRICEPS')
    ]
    
    # Insertamos si no existen
    for name, group in biceps_new + triceps_new:
        exists = c.execute("SELECT id FROM exercises WHERE name = ?", (name,)).fetchone()
        if not exists:
            c.execute("INSERT INTO exercises (name, muscle_group) VALUES (?, ?)", (name, group))
            print(f"Añadido: {name}")

    conn.commit()
    conn.close()
    print("Base de datos de ejercicios actualizada.")

if __name__ == "__main__":
    update_db()
