import requests
import base64

url = 'https://mt-fitness-pro.onrender.com/api/master/exec'
headers = {'Authorization': 'Bearer token-admin-123', 'Content-Type': 'application/json'}
python_code = """
import os
import sys
import psycopg2

try:
    db_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(db_url, sslmode='require')
    c = conn.cursor()
    
    # Try an insert to foods
    try:
        c.execute("INSERT INTO foods (name, category, kcal, protein, carbs, fat) VALUES ('test_food', 'Proteínas', 10, 10, 10, 10)")
        conn.commit()
        print("FOOD INSERT SUCCESS")
    except Exception as e:
        conn.rollback()
        print("FOOD INSERT ERROR:", e)
        
    # Try to check id column type
    c.execute("SELECT column_default FROM information_schema.columns WHERE table_name='foods' AND column_name='id'")
    print("FOODS id default:", c.fetchone())
    
    c.execute("SELECT column_default FROM information_schema.columns WHERE table_name='exercises' AND column_name='id'")
    print("EXERCISES id default:", c.fetchone())
    
    conn.close()
except Exception as main_e:
    print("Main Exception:", main_e)
"""

# Base64 encode the string literal
encoded = base64.b64encode(python_code.encode('utf-8')).decode('utf-8')

cmd = f"python3 -c \"import base64; exec(base64.b64decode('{encoded}').decode('utf-8'))\""

try:
    res = requests.post(url, headers=headers, json={
        'master_token': 'MT_MASTER_PRO_2026',
        'cmd': cmd
    })
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)
