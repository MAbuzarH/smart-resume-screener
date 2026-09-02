from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(db.Model):
    """
    User model for authentication and role-based access control.
    Supports applicant, employer, and admin roles.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    
    full_name = db.Column(
        db.String(200),
        nullable=False
    )
    
    email = db.Column(
        db.String(200),
        nullable=False,
        unique=True,
        index=True
    )
    
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )
    
    role = db.Column(
        db.String(50),
        nullable=False,
        default='applicant'
    )
    
    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    
    def set_password(self, password):
        """
        Hash and set the user's password.
        
        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.full_name} ({self.role})>'