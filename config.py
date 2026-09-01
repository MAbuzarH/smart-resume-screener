import os

class Config:
    """
    Configuration class for Flask application.
    Uses environment variables where appropriate.
    """
    # Flask secret key - should be set via environment variable in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'instance', 'smart_resume.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    
    # Scoring weights for final match score calculation
    # These weights must sum to 1.0 and are validated at application startup
    TFIDF_WEIGHT = 0.40  # TF-IDF/Cosine similarity weight (40%)
    SKILL_WEIGHT = 0.60  # Skill matching weight (60%)
    
    # Screening category thresholds for candidate analysis
    # These thresholds determine the screening category based on final match score
    STRONG_MATCH_THRESHOLD = 80.0  # 80-100% = Strong Match
    MODERATE_MATCH_THRESHOLD = 60.0  # 60-79.99% = Moderate Match, below 60% = Low Match
