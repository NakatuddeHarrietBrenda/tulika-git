from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)

    CORS(app)

    import os
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "tulika-secret-key")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "tulika-master-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tulika.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Email Configuration
    import os
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # IMPORT ROUTES
    from app.routes.auth_routes import auth_bp
    from app.routes.analytics_routes import analytics_bp
    from app.routes.recommendation_routes import recommendation_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(recommendation_bp)

    with app.app_context():
        from app.models.user_model import User
        from app.models.activity_log import ActivityLog
        db.create_all()
        
        # Create default admin if no users exist
        if not User.query.first():
            admin = User(email="admin@tulikatours.com")
            admin.set_password("password123")
            db.session.add(admin)
            db.session.commit()
            print("Default admin created (Hashed): admin@tulikatours.com / password123")

    return app