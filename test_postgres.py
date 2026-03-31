import requests
import base64

url = 'https://mt-fitness-pro.onrender.com/api/master/exec'
headers = {'Authorization': 'Bearer token-admin-123', 'Content-Type': 'application/json'}

python_code = """
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    db_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(db_url, sslmode='require', cursor_factory=RealDictCursor)
    c = conn.cursor()
    
    # Check sequences
    c.execute("SELECT table_name, column_name, column_default FROM information_schema.columns WHERE table_name IN ('user_foods', 'user_exercises') AND column_name='id'")
    print("IDS:", c.fetchall())
    
    # Try an insert to user_foods (this is where it was 500-ing)
    try:
        # Note: we need a real user_id or 'test-dummy'
        c.execute("INSERT INTO user_foods (user_id, food_id, meal_name, grams, day_name) VALUES ('test-dummy-123', 1, 'test', 100, 'Dia 1')")
        conn.commit()
        print("INSERT SUCCESS")
    except Exception as e:
        conn.rollback()
        print("INSERT ERROR:", e)
    
    conn.close()
except Exception as main_e:
    print("Main Exception:", main_e)
"""

encoded = base64.b64encode(python_code.encode('utf-8')).decode('utf-8')
cmd = f"python3 -c \"import base64; exec(base64.b64decode('{encoded}').decode('utf-8'))\""

try:
    res = requests.post(url, headers=headers, json={
        'master_token': 'MT_MASTER_PRO_2026',
        'cmd': cmd
    })
    print(res.text)
except Exception as e:
    print("Error:", e)
