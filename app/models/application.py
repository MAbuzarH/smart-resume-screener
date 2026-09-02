from app import db
from datetime import datetime, timezone


class Application(db.Model):
    """
    Application model for storing job applications.
    """
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)

    job_id = db.Column(
        db.Integer,
        db.ForeignKey('jobs.id'),
        nullable=False
    )

    applicant_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=True  # Nullable for existing applications, will be populated via migration
    )

    applicant_name = db.Column(
        db.String(200),
        nullable=False
    )

    applicant_email = db.Column(
        db.String(200),
        nullable=False
    )

    resume_filename = db.Column(
        db.String(500),
        nullable=False
    )

    resume_text = db.Column(
        db.Text,
        nullable=True,
        default=''
    )

    processed_resume_text = db.Column(
        db.Text,
        nullable=True,
        default=''
    )

    match_score = db.Column(
        db.Float,
        nullable=True
    )
    
    # Additional scoring fields for weighted final scoring model
    # similarity_score: TF-IDF/cosine similarity score (0-100)
    similarity_score = db.Column(
        db.Float,
        nullable=True
    )
    
    # skill_match_score: Skill match percentage (0-100)
    skill_match_score = db.Column(
        db.Float,
        nullable=True
    )
    
    # final_match_score: Weighted final match score (0-100)
    final_match_score = db.Column(
        db.Float,
        nullable=True
    )
    
    # Application status
    status = db.Column(
        db.String(50),
        nullable=False,
        default='Submitted'
    )
    
    # Timestamps
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

    # Relationships
    applicant = db.relationship('User', backref='applications')

    def __repr__(self):
        return f'<Application {self.applicant_name} for Job {self.job_id}>'