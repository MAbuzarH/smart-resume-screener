from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import logging

db = SQLAlchemy()

def create_app(config_class=Config):
    """
    Application factory pattern for Flask.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Import models so SQLAlchemy knows about them
    from app.models import Job, Application, User

    # Register blueprints
    from app.routes.main import bp as main_bp
    from app.auth.routes import bp as auth_bp
    from app.admin import bp as admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
