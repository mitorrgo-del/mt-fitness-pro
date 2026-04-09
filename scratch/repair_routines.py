import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        load_dotenv('.env')
        db_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(db_url, sslmode='require', cursor_factory=RealDictCursor)

try:
    conn = get_db()
    c = conn.cursor()
    
    # 1. Ver qué ejercicios tenemos en rutinas que no existen en el catálogo
    print("Buscando rutinas desvinculadas...")
    c.execute("""
        SELECT COUNT(*) as broken 
        FROM user_exercises 
        WHERE exercise_id NOT IN (SELECT id FROM exercises)
    """)
    broken = c.fetchone()['broken']
    print(f"Rutinas rotas encontradas: {broken}")
    
    if broken > 0:
        print("Intentando reparación automática por cercanía de IDs o nombres...")
        # Nota: Esta es una reparación compleja. Si no tenemos el nombre en user_exercises,
        # dependemos de que los IDs coincidan o de un backup.
        # ¿Tenemos backup? Voy a mirar si hay una tabla vieja o algo.
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%old%'")
        # (Esto es para Postgres, sería :)
        c.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%old%'")
        backups = c.fetchall()
        print(f"Tablas de backup encontradas: {backups}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
