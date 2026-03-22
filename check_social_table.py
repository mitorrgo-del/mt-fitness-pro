import sqlite3
DB_FILE = 'mtfitness.db'
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='social_media_posts'")
table = c.fetchone()
if table:
    print("Table 'social_media_posts' exists.")
    count = c.execute("SELECT count(*) FROM social_media_posts").fetchone()[0]
    print(f"Post count: {count}")
else:
    print("Table 'social_media_posts' does not exist.")
conn.close()
