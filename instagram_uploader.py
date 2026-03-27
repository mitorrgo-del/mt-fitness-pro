from instagrapi import Client
import os
import sqlite3
import time
import json
import requests

# SESIÓN DEL NAVEGADOR
SESSION_ID = "41956480253%3AZ8lRbflfJJ6Ztp%3A28%3AAYg8VzOLkXMIye48OTbmrGeQqRRKczF7cl0lKlq7cw"
IG_USERNAME = "mtfitnesspro_oficial"

def send_telegram(text, token="8754695708:AAF2T37Dyt5x_ajLVlx43cbixFo-y2LveW0"):
    admin_file = "telegram_admin.json"
    if not os.path.exists(admin_file): return
    with open(admin_file, 'r') as f:
        chat_id = json.load(f).get("chat_id")
    if not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=5)
    except: pass

def get_client():
    cl = Client()
    # Inyección forzada y silenciosa (sin verificaciones que den error)
    try:
        print("InstaUploader: Conexión blindada en curso...")
        # Saltamos la validación interna de instagrapi para evitar el error 'pinned_channels_info'
        cl.set_settings({})
        cl.set_cookie("sessionid", SESSION_ID)
        cl.set_cookie("ds_user_id", "41956480253")
        cl.set_cookie("csrftoken", "ihKcHHn3EXiH0BqKfEK4rE5EYXzxidPG")
        print(f"InstaUploader: Sesión inyectada. Pasando a publicar...")
        return cl
    except Exception as e:
        print(f"InstaUploader: Error crítico al inyectar: {e}")
        return None

def upload_pending_posts():
    conn = sqlite3.connect('mtfitness.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    posts = c.execute("SELECT * FROM social_media_posts WHERE status = 'PENDING'").fetchall()
    if not posts:
        conn.close()
        return
        
    print(f"InstaUploader: Detectados {len(posts)} posts. Subiendo...")
    cl = get_client()
    if not cl:
        conn.close()
        return

    for p in posts:
        try:
            image_path = p['image_url']
            if not image_path or not os.path.exists(image_path):
                image_path = "app/ai_demo.png" 
            
            text = f"{p['caption']}\n\n{p['hashtags']}"
            
            print(f"Subiendo post #{p['id']}...")
            # Aquí ocurre la magia: publicamos sin pedir permisos cada vez
            cl.photo_upload(image_path, text)
            
            c.execute("UPDATE social_media_posts SET status = 'PUBLISHED' WHERE id = ?", (p['id'],))
            conn.commit()
            send_telegram(f"✅ <b>¡PUBLICADO AUTOMÁTICAMENTE!</b>\nPost: <b>'{p['title']}'</b> ya está en tu Instagram.")
            
        except Exception as e:
            print(f"Fallo en subida post {p['id']}: {e}")
            if "login_required" in str(e).lower():
                send_telegram("⚠️ <b>SESIÓN CADUCADA:</b> Miky, por favor dale a refrescar (F5) en tu Instagram del PC un segundo para que pueda reconectar.")
            
    conn.close()

if __name__ == "__main__":
    upload_pending_posts()
