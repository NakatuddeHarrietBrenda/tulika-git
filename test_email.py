import os
from flask import Flask
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

print(f"Testing email for: {app.config['MAIL_USERNAME']}")
print(f"Using password: {'[SET]' if app.config['MAIL_PASSWORD'] else '[NOT SET]'}")

with app.app_context():
    msg = Message("Test Email", recipients=[app.config['MAIL_USERNAME']])
    msg.body = " Reset code forTulika Dashboard."
    try:
        mail.send(msg)
        print("SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"FAILED: {str(e)}")
