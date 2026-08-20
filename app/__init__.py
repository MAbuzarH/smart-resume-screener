from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    """
    Application factory pattern for Flask.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLAlchemy with the app
    db.init_app(app)

    # Import models so SQLAlchemy knows about them
    from app.models import Job, Application

    # Register blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
