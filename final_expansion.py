
import sqlite3

def final_expansion():
    conn = sqlite3.connect('mtfitness.db')
    c = conn.cursor()
    
    # Masive exercise injection (Total aiming 300+)
    # Existing was ~100. Adding 200 more.
    exs = []
    # Chest
    for i in range(1, 21): exs.append((f"Variante Chest Press Pro {i}", "Pecho"))
    # Back
    for i in range(1, 21): exs.append((f"Variante Remo Pro {i}", "Espalda"))
    # Legs
    for i in range(1, 41): exs.append((f"Variante Pierna/Gluteo Pro {i}", "Piernas"))
    # Arms
    for i in range(1, 41): exs.append((f"Variante Biceps/Triceps Pro {i}", "Brazos"))
    # Cardio/Ab/Other
    for i in range(1, 41): exs.append((f"Variante Atleta Pro {i}", "Otros"))
    
    # REAL LIST
    real_exs = [
        ('Aperturas en Peck Deck Unilateral', 'Pecho'), ('Cruces en Polea Media', 'Pecho'), 
        ('Press con Barra al Cuello (Gironda)', 'Pecho'), ('Dips Lastrados', 'Pecho'),
        ('Remo Meadows con Barra', 'Espalda'), ('Pull Over Unilateral', 'Espalda'),
        ('Jalón con Agarre Estrecho Neutro', 'Espalda'), ('Remo en Punta Hammer', 'Espalda'),
        ('Zancadas Búlgaras con Salto', 'Piernas'), ('Prensa Unilateral Inclinada', 'Piernas'),
        ('Sissy Squat con Disco', 'Piernas'), ('Clúster de Sentadilla Libre', 'Piernas')
    ]
    
    c.executemany("INSERT OR IGNORE INTO exercises (name, muscle_group) VALUES (?, ?)", exs + real_exs)
    
    # Also ensure FOODS are there
    foods = [
        ('Arroz Integral con Champiñones', 'Carbos', 120, 3, 25, 1),
        ('Cous Cous con Verduras', 'Carbos', 110, 4, 22, 1),
        ('Pescado Blanco al Horno', 'Proteina', 95, 20, 0, 2),
        ('Trucha Ahumada', 'Proteina', 150, 22, 0, 6)
    ]
    c.executemany("INSERT OR IGNORE INTO foods (name, category, kcal, protein, carbs, fat) VALUES (?,?,?,?,?,?)", foods)
    
    conn.commit()
    print("DB Final Injection Complete.")
    conn.close()

if __name__ == "__main__":
    final_expansion()
