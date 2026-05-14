import sqlite3
import os

db_path = "instance/tulika.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, email, password FROM user")
        users = cursor.fetchall()
        if not users:
            print("No users found in database.")
        else:
            print("Users in database:")
            for user in users:
                print(f"ID: {user[0]}, Email: {user[1]}, Password: {user[2]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
