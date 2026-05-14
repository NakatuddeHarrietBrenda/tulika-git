from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app.models.user_model import User
from app import db

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

    new_user = User(
        email=email,
        password=password
    )

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

    if user.password != password:
        return jsonify({
            "error": "Incorrect password"
        }), 401

    token = create_access_token(identity=user.email)

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

    # Generate secure token
    s = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY', 'default-secret-key'))
    token = s.dumps(email, salt='password-reset-salt')

    # Send email
    reset_link = f"http://localhost:3000/reset-password/{token}"
    
    from flask_mail import Message
    from app import mail
    
    msg = Message("Tulika Tours: Password Reset Request", recipients=[email])
    msg.body = f"Hello,\n\nTo reset your password, please click the following link:\n{reset_link}\n\nIf you did not make this request then simply ignore this email and no changes will be made."
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        return jsonify({"error": "Failed to send reset email. Please check server logs."}), 500

    return jsonify({"message": "If that email exists, a reset link has been sent."})

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("new_password")

    if not token or not new_password:
        return jsonify({"error": "Missing token or new password"}), 400

    s = URLSafeTimedSerializer(current_app.config.get('SECRET_KEY', 'default-secret-key'))
    
    try:
        # Token expires in 1 hour (3600 seconds)
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        return jsonify({"error": "The reset link has expired."}), 400
    except BadSignature:
        return jsonify({"error": "Invalid reset link."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found."}), 404

    user.password = new_password
    db.session.commit()

    return jsonify({"message": "Password successfully reset."})