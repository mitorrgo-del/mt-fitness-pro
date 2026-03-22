import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'mtfitness.db')

def migrate():
    if not os.path.exists(DB_FILE):
        print("DB not found")
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE user_exercises ADD COLUMN target_muscles TEXT;")
        conn.commit()
        print("Migration successful: added target_muscles to user_exercises")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column already exists")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
