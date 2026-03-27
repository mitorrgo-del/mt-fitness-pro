import requests
import time
import os

# --- CONFIGURACIÓN DEL AGENTE MAESTRO ---
# Sustituye con tu URL real de Cloudflare si lo ejecutas desde fuera
API_BASE_URL = "http://localhost:5000/api" 
JWT_TOKEN = "ADMIN_DEV_TOKEN" # El token de tu usuario admin
MASTER_TOKEN = "MT_MASTER_PRO_2026"

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def ejecutar_comando(cmd):
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "cmd": cmd,
        "master_token": MASTER_TOKEN
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/master/exec", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json().get('output', 'Sin salida.')
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        return f"Error de conexión: {e}"

def menu_maestro():
    clear_console()
    print("==========================================")
    print("   AGENTE MAESTRO MT FITNESS PRO v1.0    ")
    print("==========================================")
    print(" Conectado al servidor de producción.")
    print(" Escribe 'exit' para salir.")
    print("------------------------------------------")
    
    while True:
        cmd = input("MAESTRO > ")
        if cmd.lower() == 'exit':
            break
        
        print("\nEjecutando...")
        resultado = ejecutar_comando(cmd)
        print("--- SALIDA DEL SERVIDOR ---")
        print(resultado)
        print("---------------------------\n")

if __name__ == "__main__":
    menu_maestro()
