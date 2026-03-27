import requests
import time
import sqlite3
import json
import os
import instagram_uploader

# --- CONFIGURACIÓN ---
TOKEN = "8754695708:AAF2T37Dyt5x_ajLVlx43cbixFo-y2LveW0"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_PATH = "mtfitness.db"
CHECK_INTERVAL = 3 # Segundos entre polls

# Guardaremos el ID del admin en un archivito para que no se pierda al reiniciar
ADMIN_FILE = "telegram_admin.json"

def get_admin_id():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'r') as f:
            return json.load(f).get("chat_id")
    return None

def save_admin_id(chat_id):
    with open(ADMIN_FILE, 'w') as f:
        json.dump({"chat_id": chat_id}, f)

def send_msg(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    requests.post(url, json=payload)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def process_command(chat_id, text):
    text = text.lower()
    
    if text == "/start":
        save_admin_id(chat_id)
        send_msg(chat_id, "<b>¡Agente MT Fitness PRO Conectado!</b> 🦾🏁\n\nMiky, ahora recibirás aquí todas las propuestas de posts e informes de atletas.\n\nEscríbeme cualquier idea de post (ej: 'crea un post sobre glúteo') o usa /pendientes para ver qué tenemos en cola.")
        return

    if text == "/pendientes":
        conn = get_db()
        posts = conn.execute("SELECT * FROM social_media_posts WHERE status = 'DRAFT'").fetchall()
        conn.close()
        
        if not posts:
            send_msg(chat_id, "No hay posts pendientes de aprobación en este momento. 😴")
            return
            
        for p in posts:
            msg = f"📸 <b>PROPUESTA DE POST #{p['id']}</b>\n\n<b>Texto:</b>\n{p['caption']}\n\n<b>Hashtags:</b>\n{p['hashtags']}"
            markup = {
                "inline_keyboard": [[
                    {"text": "✅ Aprobar", "callback_data": f"approve_{p['id']}"},
                    {"text": "❌ Rechazar", "callback_data": f"reject_{p['id']}"}
                ]]
            }
            send_msg(chat_id, msg, markup)
        return

    # Si no es un comando, lo tratamos como una orden para el motor de marketing
    # Copiamos la lógica de flask_app.py
    caption = ""
    hashtags = ""
    
    if 'pierna' in text or 'gluteo' in text:
        caption = "🔬 ANALIZANDO EL TREN INFERIOR\n\nEl 90% de la gente entrena piernas, pero pocos dominan la HIPERTROFIA REAL. Para mutar no necesitas 25 máquinas, necesitas INTENSIDAD y BIOMECÁNICA.\n\nFrecuencia 2, enfoque en RPE 9-10 y tempo controlado. En MT Fitness PRO te diseñamos el plan exacto para que tus piernas sean la base de tu templo. 🏛️🔥\n\n¿Buscas resultados reales? Haz clic en el enlace."
        hashtags = "#CienciaFitness #LegDayExpert #MTFitnessPRO #HipertrofiaReal #EntrenadorPersonal"
    elif 'comida' in text or 'nutricion' in text or 'dietista' in text:
        caption = "🥑 NUTRICIÓN CON ESTRATEGIA, NO RESTRICCIÓN\n\n¿Sigues pensando que para definir hay que pasar hambre? Estás estancado porque tu metabolismo está en modo 'ahorro'.\n\nComo Dietista-Nutricionista, en MT Fitness PRO calculamos tus macros no solo para perder grasa, sino para mantener cada gramo de músculo. Gasolina de calidad para un cuerpo de élite. 🥩🔬\n\n👉🏻 Toca el enlace para tu plan nutricional."
        hashtags = "#NutricionCientifica #DietistaExperto #MTFitnessPRO #MacrosReales #Recomposicion"
    elif 'motivacion' in text or 'empezar' in text:
        caption = "🚀 LA DISCIPLINA VENCE A LA MOTIVACIÓN CADA DÍA\n\nNo esperes a estar motivado para venir a MT Fitness PRO. La motivación es una chispa, la DISCIPLINA es el fuego que dura 6 meses.\n\nEl tiempo va a pasar igual. ¿Dónde quieres estar en Septiembre? El Mario del futuro te dará las gracias por empezar HOY. 💪🏻🔥\n\nTu transformación empieza con un clic."
        hashtags = "#MentalityPRO #DisciplinaFitness #MTFitnessPRO #TransformacionReal #CoachMario"
    else:
        caption = "🔥 EL SECRETO DEL ÉXITO ES LA PROGRAMACIÓN\n\n¿Cansado de ir al gimnasio y no ver cambios? Tu cuerpo se ha adaptado a tu rutina cómoda. En MT Fitness PRO rompemos el estancamiento con SOBRECARGA PROGRESIVA y datos reales.\n\nNo entrenes para cansarte, entrena para MEJORAR. 🧬⚡\n\n👉🏻 Link en bio para empezar el cambio."
        hashtags = "#EntrenamientoInteligente #MTFitnessPRO #FitnessEspaña #ResultadosCientificos"

    conn = get_db()
    conn.execute("INSERT INTO social_media_posts (title, caption, hashtags, image_url, status) VALUES (?,?,?,?,?)",
                ("Orden Directa Miky", caption, hashtags, None, "PENDING"))
    conn.commit()
    conn.close()
    
    send_msg(chat_id, "📝 <b>¡RECIBIDO!</b> Estoy subiendo este post experto a tu Instagram ahora mismo, sin esperas...")
    
    # SUBIDA INMEDIATA (AUTO-APROBADA)
    try:
        instagram_uploader.upload_pending_posts()
    except Exception as e:
        print(f"Error subida inmediata: {e}")

def handle_callback(chat_id, data, msg_id):
    conn = get_db()
    
    if data.startswith("approve_"):
        post_id = data.split("_")[1]
        conn.execute("UPDATE social_media_posts SET status = 'PENDING' WHERE id = ?", (post_id,))
        conn.commit()
        requests.post(f"{BASE_URL}/editMessageText", json={
            "chat_id": chat_id, "message_id": msg_id, "text": "⏳ <b>¡CONECTANDO CON INSTAGRAM!</b> Estoy subiendo el post ahora mismo...", "parse_mode": "HTML"
        })
        # SUBIDA INMEDIATA
        try:
            instagram_uploader.upload_pending_posts()
        except Exception as e:
            print(f"Error subida inmediata: {e}")
    elif data.startswith("reject_"):
        post_id = data.split("_")[1]
        conn.execute("UPDATE social_media_posts SET status = 'REJECTED' WHERE id = ?", (post_id,))
        requests.post(f"{BASE_URL}/editMessageText", json={
            "chat_id": chat_id, "message_id": msg_id, "text": "❌ <b>Post descartado.</b>" , "parse_mode": "HTML"
        })
    
    conn.commit()
    conn.close()

def main():
    print("--- Agente de Telegram MT Fitness PRO Iniciado ---")
    offset = 0
    
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"
            res = requests.get(url).json()
            
            if "result" in res:
                for update in res["result"]:
                    offset = update["update_id"] + 1
                    
                    # Mensajes de texto
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        process_command(chat_id, text)
                    
                    # Clicks en botones (Callbacks)
                    if "callback_query" in update:
                        chat_id = update["callback_query"]["message"]["chat"]["id"]
                        data = update["callback_query"]["data"]
                        msg_id = update["callback_query"]["message"]["message_id"]
                        handle_callback(chat_id, data, msg_id)
                        
            time.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"Error en el bot: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
