import sys
import os

# Add the current directory to the system path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask app object from app.py
from app import app as application
