import sqlite3

def add_role_to_db():
    try:
        conn = sqlite3.connect('instance/tulika.db')
        cursor = conn.cursor()
        
        # Add role column
        cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(50) DEFAULT 'admin';")
        print("Added role column.")
        
        # Make Harriet the super_admin
        cursor.execute("UPDATE user SET role = 'super_admin' WHERE email = 'nakatuddeharriet936@gmail.com';")
        print("Set Harriet as super_admin.")
        
        conn.commit()
        print("Database upgraded successfully.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Role column already exists.")
            # Still try to update Harriet
            cursor.execute("UPDATE user SET role = 'super_admin' WHERE email = 'nakatuddeharriet936@gmail.com';")
            conn.commit()
            print("Set Harriet as super_admin.")
        else:
            print("Error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    add_role_to_db()
