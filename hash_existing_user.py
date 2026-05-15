import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models.user_model import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(email="nakatuddeharriet936@gmail.com").first()
    if user:
        print(f"Updating user: {user.email}")
        user.set_password("tulika123456789")
        db.session.commit()
        print("Password hashed and saved successfully!")
    else:
        print("User not found.")
