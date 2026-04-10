
import os

filepath = 'flask_app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'init_db()' in line and '#' not in line:
        # Check if it's the global call or the one in the else block
        # Actually, let's just comment ALL of them except the one in the maintenance route.
        if 'def' not in line: # don't comment the definition
            line = line.replace('init_db()', '# init_db() # Disabled for serverless stability')
    new_lines.append(line)

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("All init_db() calls commented out (excluding definition).")
