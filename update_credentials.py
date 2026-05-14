import sqlite3
import os

def update_admin_credentials(new_email, new_password):
    db_path = "instance/tulika.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Update the user with ID 1 (the default admin)
        cursor.execute(
            "UPDATE user SET email = ?, password = ? WHERE id = 1",
            (new_email, new_password)
        )
        
        conn.commit()
        print(f"Successfully updated admin credentials!")
        print(f"New Email: {new_email}")
        print(f"New Password: {new_password}")
        
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # CHANGE THESE VALUES TO YOUR DESIRED CREDENTIALS
    NEW_EMAIL = "nakatuddeharriet936@gmail.com"
    NEW_PASSWORD = "tulika123456789"
    
    update_admin_credentials(NEW_EMAIL, NEW_PASSWORD)
