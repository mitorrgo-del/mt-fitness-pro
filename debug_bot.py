import sqlite3
import json

DB_FILE = 'mtfitness.db'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_bot_response(message, client_name):
    txt = message.lower()
    if any(k in txt for k in ['dolor', 'lesion', 'ayuda', 'problema', 'queja', 'coach', 'humano', 'entrenador']):
        return "He notificado al Coach sobre esto. En breve se pondrá en contacto contigo por aquí para analizarlo en detalle."
    if any(k in txt for k in ['rutina', 'cambiar', 'ejercicio', 'entrenamiento']):
        return "Soy tu Asistente de MT FITNESS coach. No puedo alterar tus planes directamente. He avisado al Coach para que revise tu petición."
    if any(k in txt for k in ['comida', 'dieta', 'hambre', 'peso']):
        return "La nutrición es la clave. Si necesitas ajustes en los gramos, dímelo y lo consultaré con el Coach."
    return f"Hola, {client_name}. Soy el Asistente de MT FITNESS coach. ¿En qué puedo ayudarte hoy?"

def simulate_chat(user_id, message):
    conn = get_db()
    try:
        user_info = conn.execute("SELECT bot_active, name, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_info:
            print("User not found")
            return

        print(f"Simulating for {user_info['name']} (Bot active: {user_info['bot_active']})")
        
        # Insert user message
        conn.execute("INSERT INTO chat_messages (user_id, sender_role, message) VALUES (?, ?, ?)",
                     (user_id, user_info['role'], message))
        
        # Bot logic
        is_bot_on = int(user_info['bot_active']) if user_info['bot_active'] is not None else 0
        if is_bot_on == 1:
            reply = generate_bot_response(message, user_info['name'])
            print(f"Bot will reply: {reply}")
            conn.execute("INSERT INTO chat_messages (user_id, sender_role, message) VALUES (?, ?, ?)",
                         (user_id, 'BOT', reply))
        
        conn.commit()
        print("Commit successful")
        
        # Verify
        msgs = conn.execute("SELECT * FROM chat_messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT 2", (user_id,)).fetchall()
        for m in msgs:
            print(f"Msg: {m['sender_role']}: {m['message']}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Roger's ID
    simulate_chat('926cc1bc-fcc0-4072-8e19-e87f79655232', 'Hola bot')
