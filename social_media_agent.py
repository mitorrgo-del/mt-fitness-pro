import sqlite3
import random
import os

# CONFIGURACIÓN
DB_FILE = 'mtfitness.db'
POSTS_DIR = 'social_media_posts'

def get_random_exercise():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    ex = c.execute("SELECT * FROM exercises ORDER BY RANDOM() LIMIT 1").fetchone()
    conn.close()
    return ex

def generate_caption(exercise):
    templates = [
        "🔥 ¡DOMINA LA TÉCNICA DE {name}! El grupo muscular {muscle} no se construye solo con peso, sino con ejecución perfecta. 💪 #MTFitness #CoachMitor #TrainingHard",
        "🚀 Hoy toca {name}. Un básico imprescindible para tu rutina de {muscle}. ¿Cuántas series tienes hoy en tu plan? 🏋️‍♂️ #MTFitness #FitnessTips #Motivacion",
        "💡 Tip de Coach: En el {name}, controla siempre la fase de bajada. ¡Dale caña a esos {muscle}! 🔥 #Focus #GymLife #MTFitness"
    ]
    template = random.choice(templates)
    return template.format(name=exercise['name'], muscle=exercise['muscle_group'])

def create_post_proposal():
    ex = get_random_exercise()
    if not ex:
        return "No hay ejercicios en la DB."

    caption = generate_caption(ex)
    
    # Lista de imágenes de alta calidad (mockup)
    images = [
        "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=800",
        "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?q=80&w=800",
        "https://images.unsplash.com/photo-1541534741688-6078c64b52df?q=80&w=800",
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?q=80&w=800"
    ]
    image_url = random.choice(images)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO social_media_posts (title, caption, image_url, status)
        VALUES (?, ?, ?, ?)
    """, (f"Post: {ex['name']}", caption, image_url, 'DRAFT'))
    conn.commit()
    conn.close()
    
    return f"Propuesta de post para '{ex['name']}' guardada en la base de datos."

if __name__ == "__main__":
    status = create_post_proposal()
    print(status)
