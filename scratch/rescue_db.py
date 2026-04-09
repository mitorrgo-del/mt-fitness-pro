import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        # Intentar cargar desde la ruta específica si no está en os.environ
        load_dotenv('.env')
        db_url = os.environ.get('DATABASE_URL')
        
    if not db_url:
        # Probar en app/.env
        load_dotenv('app/.env')
        db_url = os.environ.get('DATABASE_URL')

    if not db_url:
        raise Exception("DATABASE_URL not found in .env or environment!")
        
    conn = psycopg2.connect(db_url, sslmode='require', cursor_factory=RealDictCursor)
    return conn

try:
    conn = get_db()
    c = conn.cursor()
    
    # 1. Total assignments
    c.execute("SELECT COUNT(*) FROM workout_assignments")
    count = c.fetchone()['count']
    print(f"TOTAL_ASSIGNMENTS: {count}")
    
    # 2. Orphans check
    c.execute("""
        SELECT COUNT(*) as orphans
        FROM workout_assignments wa 
        LEFT JOIN exercises e ON wa.exercise_id = e.id 
        WHERE e.id IS NULL
    """)
    orphans = c.fetchone()['orphans']
    print(f"ORPHAN_ROUTINES: {orphans}")
    
    conn.close()
except Exception as e:
    print(f"CRITICAL_ERROR: {e}")
