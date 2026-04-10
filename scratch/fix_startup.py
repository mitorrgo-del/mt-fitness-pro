
import os

filepath = 'flask_app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove '    sync_pro_exercises()' inside init_db
content = content.replace('    sync_pro_exercises()', '    # sync_pro_exercises() # Removed from startup')

# Remove 'init_db()' call at the global level
# This one might be tricky if there are multiple.
# Let's find 'init_db()\n' precisely.
content = content.replace('\ninit_db()', '\n# init_db() # Removed from global scope')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement done via script.")
