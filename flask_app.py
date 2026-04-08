from flask import Flask, request, jsonify, send_from_directory, redirect
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS user_foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, food_id INTEGER,
        meal_name TEXT, grams REAL, day_name TEXT DEFAULT 'Día 1',
        added_date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')


    # PRO Assigned Workout Plans (Admin -> Client)
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS user_exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, exercise_id INTEGER,
        day_of_week TEXT, sets TEXT, reps TEXT, rest TEXT,
        target_muscles TEXT, set_type TEXT DEFAULT 'NORMAL', 
        combined_with INTEGER,
        added_date TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn_wrap.commit()


    
    # MIGRACIÓN SEGURA: Añadir columnas si no existen
    def column_exists(table, column):
        try:
            if conn_wrap.is_pg:
                c_check = conn_wrap.cursor()
                c_check.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
                res = c_check.fetchone()
                return res is not None
            else:
                c_check = conn_wrap.cursor()
                c_check.execute(f"PRAGMA table_info({table})")
                cols = c_check.fetchall()
                return any(col['name'] == column for col in cols)
        except Exception as e:
            print(f"Error checking column {column} in {table}: {e}")
            return False


    columns_to_add = [
        ("user_exercises", "set_type", "TEXT DEFAULT 'NORMAL'"),
        ("user_exercises", "combined_with", "INTEGER"),
        ("user_exercises", "target_muscles", "TEXT"),
        ("user_foods", "day_name", "TEXT DEFAULT 'Día 1'"),
        ("users", "surname", "TEXT"),
        ("users", "age", "INTEGER"),
        ("users", "height", "REAL"),
        ("users", "current_weight", "REAL"),
        ("users", "objective", "TEXT"),
        ("users", "profile_image", "TEXT"),
        ("users", "biceps", "REAL"),
        ("users", "thigh", "REAL"),
        ("users", "hip", "REAL"),
        ("users", "waist", "REAL"),
        ("reports", "biceps", "REAL"),
        ("reports", "thigh", "REAL"),
        ("reports", "hip", "REAL"),
        ("reports", "waist", "REAL"),
    ]
    for table, col, defn in columns_to_add:
        if not column_exists(table, col):
            try:
                print(f"MIGRATION: Adding column {col} to {table}...")
                conn_wrap.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
                conn_wrap.commit()
            except Exception as e:
                print(f"Failed to add {col} to {table}: {e}")
                if conn_wrap.is_pg: conn_wrap.conn.rollback()
        else:
            print(f"DEBUG: Column {col} already exists in {table}")


    # PRO Meal Tracking
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS meal_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, date TEXT, meal_name TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')


    # PRIVACY & COACHING CHAT
    conn_wrap.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, sender_role TEXT, message TEXT,
