import sqlite3
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        print("Migrating Postgres...")
        conn = psycopg2.connect(db_url)
    else:
        print("Migrating SQLite...")
        conn = sqlite3.connect('mtfitness.db')
    
    cur = conn.cursor()
    
    cols = ['biceps', 'thigh', 'hip', 'waist']
    for col in cols:
        try:
            cur.execute(f"ALTER TABLE reports ADD COLUMN {col} REAL")
            print(f"Added column {col}")
        except Exception as e:
            print(f"Column {col} might already exist: {e}")
            
    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == '__main__':
    migrate()
