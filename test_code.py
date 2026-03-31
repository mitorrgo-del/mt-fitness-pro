import requests
import base64

url = 'https://mt-fitness-pro.onrender.com/api/master/exec'
headers = {'Authorization': 'Bearer token-admin-123', 'Content-Type': 'application/json'}

python_code = """
try:
    with open('flask_app.py', 'r') as f:
        content = f.read()
        print('FILE EXISTS, length:', len(content))
        print('contains try except for assign_food:', "try:" in content and "assign_food" in content)
except Exception as e:
    print('Error:', e)
"""

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
    print("Error:", e)
