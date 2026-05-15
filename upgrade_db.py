import sqlite3

def upgrade_db():
    try:
        conn = sqlite3.connect('instance/tulika.db')
        cursor = conn.cursor()
        
        # Add reset_code column
        cursor.execute("ALTER TABLE user ADD COLUMN reset_code VARCHAR(6);")
        print("Added reset_code column.")
        
        # Add reset_expiration column
        cursor.execute("ALTER TABLE user ADD COLUMN reset_expiration DATETIME;")
        print("Added reset_expiration column.")
        
        conn.commit()
        print("Database upgraded successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Columns already exist or error:", e)
        else:
            print("Error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade_db()
