import sqlite3
import os

db_path = 'instance/ctf.db'

def check_and_fix():
    if not os.path.exists(db_path):
        print("Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check columns
        cursor.execute("PRAGMA table_info(challenge)")
        columns = [info[1] for info in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        if 'free_hint' not in columns:
            print("Column 'free_hint' is MISSING. Attempting to add it...")
            try:
                cursor.execute("ALTER TABLE challenge ADD COLUMN free_hint VARCHAR(500)")
                conn.commit()
                print("SUCCESS: Added 'free_hint' column.")
            except Exception as e:
                print(f"FAILED to add column: {e}")
        else:
            print("Column 'free_hint' ALREADY EXISTS.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    check_and_fix()
