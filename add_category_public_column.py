import sqlite3
import os

DB_PATH = 'instance/ctf.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(category)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'is_public' not in columns:
            print("Adding is_public column to category table...")
            # Default to 0 (False) - Hidden by default
            cursor.execute("ALTER TABLE category ADD COLUMN is_public BOOLEAN DEFAULT 0")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column is_public already exists.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
