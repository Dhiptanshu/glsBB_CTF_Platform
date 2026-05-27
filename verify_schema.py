import sqlite3
import os

db_path = 'ctf.db'
if not os.path.exists(db_path):
    print("Database file does not exist yet (expected if not initialized).")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(challenge)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'free_hint' in columns:
            print("SUCCESS: 'free_hint' column exists.")
        else:
            print(f"FAILURE: 'free_hint' column MISSING. Columns found: {columns}")
    except Exception as e:
        print(f"Error checking schema: {e}")
    finally:
        conn.close()
