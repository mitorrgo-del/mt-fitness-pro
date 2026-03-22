import sqlite3
import os

DB_FILE = 'mtfitness.db'

def check():
    if not os.path.exists(DB_FILE):
        print(f"Error: {DB_FILE} no existe.")
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    try:
        ex_count = c.execute("SELECT count(*) FROM exercises").fetchone()[0]
        food_count = c.execute("SELECT count(*) FROM foods").fetchone()[0]
        users = c.execute("SELECT email, role, status FROM users").fetchall()
        
        print(f"Ejercicios: {ex_count}")
        print(f"Alimentos: {food_count}")
        print("Usuarios:")
        for u in users:
            print(f" - {u[0]} | {u[1]} | {u[2]}")
            
    except Exception as e:
        print(f"Error en consulta: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check()
