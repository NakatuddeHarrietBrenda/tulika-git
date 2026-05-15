from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
import random
from datetime import datetime, timedelta

from app.models.user_model import User
from app.models.activity_log import ActivityLog
from app import db, mail
from flask_mail import Message

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def home():
    return jsonify({
        "message": "Tulika Tours ML API"
    })

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "error": "User already exists"
        }), 400

    new_user = User(email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully"
    })

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    if not user.check_password(password):
        # Log failed attempt
        log = ActivityLog(user_email=email, action="FAILED LOGIN ATTEMPT", ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
        return jsonify({
            "error": "Incorrect password"
        }), 401

    token = create_access_token(identity=user.email)

    # Log successful login
    log = ActivityLog(user_email=email, action="SUCCESSFUL LOGIN", ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    # Send Login Notification
    try:
        msg = Message("New Login Detected: Tulika Dashboard", recipients=[current_app.config.get('MAIL_USERNAME')])
        msg.body = f"Hello Admin,\n\nA new login was detected for {user.email} from IP {request.remote_addr} at {log.timestamp}."
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send login notification: {e}")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.email
    })

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        # Prevent email enumeration by returning a success message anyway
        return jsonify({"message": "If that email exists, a reset link has been sent."})

    # Generate 6-digit code
    reset_code = str(random.randint(100000, 999999))
    user.reset_code = reset_code
    user.reset_expiration = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    # Send email
    from flask_mail import Message
    from app import mail
    
    msg = Message("Tulika Tours: Password Reset Code", recipients=[email])
    msg.body = f"Hello,\n\nYour password reset code is: {reset_code}\n\nThis code will expire in 10 minutes. If you did not make this request then simply ignore this email and no changes will be made."
    
    # Log the request
    log = ActivityLog(user_email=email, action="PASSWORD RESET REQUESTED", ip_address=request.remote_addr)
    db.session.add(log)
    db.session.commit()

    try:
        print(f"Attempting to send email to {email} using {current_app.config.get('MAIL_USERNAME')}")
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"CRITICAL EMAIL FAILURE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to send reset email: {str(e)}"}), 500

    return jsonify({"message": "If that email exists, a reset link has been sent."})

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")
    new_password = data.get("new_password")

    if not email or not code or not new_password:
        return jsonify({"error": "Missing email, code, or new password"}), 400

    user = User.query.filter_by(email=email).first()
    
    if not user or user.reset_code != code:
        return jsonify({"error": "Invalid reset code or email."}), 400

    if user.reset_expiration and datetime.utcnow() > user.reset_expiration:
        return jsonify({"error": "Reset code has expired."}), 400

    user.set_password(new_password)
    user.reset_code = None
    user.reset_expiration = None
    db.session.commit()

    return jsonify({"message": "Password successfully reset."})