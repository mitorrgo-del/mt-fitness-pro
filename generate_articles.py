import sqlite3
import datetime
import os
import random

# Configuración de la DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'mtfitness.db')

def add_articles():
    # Usar detect_types para asegurar manejo de strings
    conn = sqlite3.connect(DB_FILE)
    conn.text_factory = str # Asegurar que maneja correctamente los encodings
    c = conn.cursor()
    
    # Limpiar antiguos para asegurar que las nuevas imágenes carguen
    c.execute("DELETE FROM articles")
    
    date_now = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Banco de artículos con imágenes VERIFICADAS y estéticas
    pool = [
        (
            "Suplementación de Élite: Creatina Monohidrato",
            "La creatina es el suplemento con más evidencia para ganar fuerza. Ayuda a regenerar el ATP celular, permitiendo series más intensas y una recuperación más rápida.",
            "Suplementación",
            date_now,
            "https://images.unsplash.com/photo-1593095394411-3c120627e770?q=80&w=800&auto=format&fit=crop" # Nueva imagen verificada de botes suplementos
        ),
        (
            "El Arte del Pre-Entreno: Energía Real",
            "No se trata solo de cafeína. Combinar hidratos de carbono complejos con citrulina malato puede marcar la diferencia en el bombeo y la resistencia muscular.",
            "Suplementación",
            date_now,
            "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=800&auto=format&fit=crop"
        ),
        (
            "Proteína de Suero: ¿Cuándo es mejor?",
            "Post-entreno o como snack, la proteína de suero es la forma más rápida de aportar aminoácidos a tus músculos. Aprende a elegir la que mejor se adapte a tu digestión.",
            "Nutrición",
            date_now,
            "https://images.unsplash.com/photo-1593096589165-056eb5cc0629?q=80&w=800&auto=format&fit=crop"
        ),
        (
            "Dominando la Sentadilla: Piernas de Hierro",
            "La profundidad y la posición de los pies son clave. Un buen apoyo y control del core transformarán tu tren inferior radicalmente.",
            "Entrenamiento",
            date_now,
            "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=800&auto=format&fit=crop"
        )
    ]
    
    # Insertar 3 aleatorios
    selected = random.sample(pool, 3)
    
    for title, content, cat, date, img in selected:
        c.execute("INSERT INTO articles (title, content, category, date, image_url) VALUES (?, ?, ?, ?, ?)",
                  (title, content, cat, date, img))
        print(f"Propagado con imagen: {title}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_articles()
