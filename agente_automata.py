import sqlite3
import time
import datetime
import os
import sys
import requests
import json
import random

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# --- CONFIGURACIÓN ---
import instagram_uploader
DB_PATH = os.path.join(application_path, 'mtfitness.db')
TOKEN = "8754695708:AAF2T37Dyt5x_ajLVlx43cbixFo-y2LveW0"
ADMIN_FILE = os.path.join(application_path, "telegram_admin.json")
INTERVALO_SEGUNDOS = 60 

def get_admin_id():
    if os.path.exists(ADMIN_FILE):
        try:
            with open(ADMIN_FILE, 'r') as f:
                return json.load(f).get("chat_id")
        except:
            return None
    return None

def send_telegram(text, reply_markup=None):
    chat_id = get_admin_id()
    if not chat_id:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generar_post_proactivo():
    """Crea un post automático si no hay ninguno hoy."""
    conn = get_db()
    c = conn.cursor()
    
    hoy = datetime.datetime.now().strftime('%Y-%m-%d')
    # Buscamos si ya hemos generado algo hoy
    q = "SELECT COUNT(*) as cuenta FROM social_media_posts WHERE date(created_at) = ?"
    result = c.execute(q, (hoy,)).fetchone()
    
    if result['cuenta'] == 0:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🤖 GENERANDO POST PROACTIVO DIARIO...")
        
        temas = [
            ("Piernas de Acero", "💥 El 90% de la gente se salta su día de tren inferior porque duele.\n\nEsa es exactamente la razón por la que tú deberías hacerlo el doble de fuerte. Las piernas son la base de tu templo. No construyas una mansión sobre gelatina. 🏛️🔥\n\n¿Estás listo para mutar? Únete al equipo PRO en el link.", "#LegDay #MTFitness"),
            ("Cocina Ganadora", "🍳 Abs are made in the kitchen! Puedes entrenar 3 horas al día, pero si tu nutrición es un desastre, solo estás perdiendo gasolina.\n\nEl secreto no es comer menos, es comer con ESTRATEGIA. Te enseño cómo mis atletas están recomponiendo su cuerpo sin pasar hambre. 🥑🥩", "#Nutricion #DietaFlexible"),
            ("Lunes de Guerra", "🚀 'Empiezo el lunes'. ¿Cuántas veces te has dicho eso?\n\nEl tiempo va a pasar de todas formas. Dentro de 6 meses desearás haber empezado HOY. No necesitas estar motivado todos los días, necesitas ser DISCIPLINADO. 💪🏻🔥", "#Motivacion #Disciplina"),
            ("Mentalidad de Atleta", "🔥 Hay dos tipos de personas en el gimnasio: las que levantan peso para cansarse y las que entrenan para TRANSFORMARSE.\n\nSi llevas meses estancado, tu cuerpo se ha adaptado. La clave del crecimiento es entrenar INTELIGENTE.", "#Entrenamiento #MTFitnessPRO")
        ]
        
        tema, caption, hashtags = random.choice(temas)
        
        c.execute("INSERT INTO social_media_posts (title, caption, hashtags, image_url, status) VALUES (?,?,?,?,?)",
                  (tema, caption, hashtags, None, "DRAFT"))
        post_id = c.lastrowid
        conn.commit()
        
        # NOTIFICAR POR TELEGRAM
        msg = f"<b>🤖 ¡REPORTE DIARIO DEL AGENTE!</b>\n\nHe redactado la propuesta de hoy sobre: <b>{tema}</b>\n\n<b>Contenido:</b>\n{caption}\n\n¿Lo subo ahora mismo a Instagram?"
        markup = {
            "inline_keyboard": [[
                {"text": "✅ Publicar YA", "callback_data": f"approve_{post_id}"},
                {"text": "❌ Descartar", "callback_data": f"reject_{post_id}"}
            ]]
        }
        send_telegram(msg, markup)
        
    conn.close()

def revisar_reportes_nuevos():
    conn = get_db()
    c = conn.cursor()
    # Menos de 5 minutos atrás para no repetir notificaciones
    hace_5_min = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    
    q = "SELECT r.*, u.name FROM reports r JOIN users u ON r.user_id = u.id WHERE r.date > ?"
    recs = c.execute(q, (hace_5_min,)).fetchall()
    
    for r in recs:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🔔 ALERTA ATLETA: {r['name']}")
        send_telegram(f"🔔 <b>¡NUEVO REPORTE!</b>\n\nEl atleta <b>{r['name']}</b> acaba de subir sus fotos y peso. ¡Échale un ojo!")
        
    conn.close()

def procesar_posts_programados():
    # Detectamos si hay algo que subir
    conn = get_db()
    c = conn.cursor()
    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    q = "SELECT COUNT(*) as cuenta FROM social_media_posts WHERE status = 'PENDING' AND (scheduled_date <= ? OR scheduled_date IS NULL)"
    res = c.execute(q, (ahora,)).fetchone()
    conn.close()

    if res['cuenta'] > 0:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📸 INICIANDO SUBIDA A INSTAGRAM...")
        try:
            instagram_uploader.upload_pending_posts()
        except Exception as e:
            print(f"ERROR: {e}")

def bucle_infinito():
    print("--- Agente Automata PRO v2.0 (MODO TELEGRAM ACTIVADO) ---")
    while True:
        try:
            generar_post_proactivo()
            revisar_reportes_nuevos()
            procesar_posts_programados()
            time.sleep(INTERVALO_SEGUNDOS)
        except Exception as e:
            print(f"ERROR EN EL BUCLE: {e}")
            time.sleep(10)

if __name__ == "__main__":
    bucle_infinito()
