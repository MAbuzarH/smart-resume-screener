from app import db
from datetime import datetime, timezone


class Job(db.Model):
    """
    Job model for storing job postings.
    """
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, nullable=False)
    processed_description = db.Column(db.Text, nullable=True, default='')
    
    # Job ownership and status
    employer_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True  # Nullable for existing jobs, will be populated via migration
    )
    
    is_open = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship with applications
    applications = db.relationship('Application', backref='job', lazy=True)
    
    # Relationship with employer
    employer = db.relationship('User', backref='jobs')

    def __repr__(self):
        return f'<Job {self.title} at {self.company}>'
