from app import db


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

    def __repr__(self):
        return f'<Application {self.applicant_name} for Job {self.job_id}>'
# # from app import db

# # class Application(db.Model):
# #     """
# #     Application model for storing job applications.
# #     """
# #     __tablename__ = 'applications'

# #     id = db.Column(db.Integer, primary_key=True)
# #     job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
# #     applicant_name = db.Column(db.String(200), nullable=False)
# #     applicant_email = db.Column(db.String(200), nullable=False)
# #     resume_filename = db.Column(db.String(500), nullable=False)

# #     def __repr__(self):
# #         return f'<Application {self.applicant_name} for Job {self.job_id}>'

# from app import db


# class Application(db.Model):
#     """
#     Application model for storing job applications.
#     """
#     __tablename__ = 'applications'

#     id = db.Column(db.Integer, primary_key=True)

#     job_id = db.Column(
#         db.Integer,
#         db.ForeignKey('jobs.id'),
#         nullable=False
#     )

#     applicant_name = db.Column(
#         db.String(200),
#         nullable=False
#     )

#     applicant_email = db.Column(
#         db.String(200),
#         nullable=False
#     )

#     resume_filename = db.Column(
#         db.String(500),
#         nullable=False
#     )

#     # Relationship with Job model
#     job = db.relationship(
#         'Job',
#         backref=db.backref(
#             'applications',
#             lazy=True
#         )
#     )

#     def __repr__(self):
#         return f'<Application {self.applicant_name} for Job {self.job_id}>'