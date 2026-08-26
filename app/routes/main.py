from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Job, Application
from app import db
from app.services import extract_text_from_pdf, preprocess_text, calculate_match_score
import os
import uuid
from werkzeug.utils import secure_filename
from config import Config
from datetime import datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """
    Home page - displays all available jobs from the database.
    """
    jobs = Job.query.all()
    return render_template('home.html', title='Available Jobs', jobs=jobs)

@bp.route('/job/<int:job_id>')
def job_details(job_id):
    """
    Job details page - displays full job information.
    Returns 404 if job does not exist.
    """
    job = Job.query.get_or_404(job_id)
    return render_template('job_details.html', title=job.title, job=job)

@bp.route('/job/<int:job_id>/apply', methods=['GET', 'POST'])
def apply(job_id):
    """
    Application form for a specific job.
    GET: Display the application form.
    POST: Process the application submission.
    """
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        # Get form data
        applicant_name = request.form.get('applicant_name', '').strip()
        applicant_email = request.form.get('applicant_email', '').strip()
        resume_file = request.files.get('resume')
        
        # Validate applicant name
        if not applicant_name:
            flash('Please enter your full name.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
        
        # Validate email
        if not applicant_email:
            flash('Please enter your email address.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
        
        # Basic email format validation
        if '@' not in applicant_email or '.' not in applicant_email.split('@')[-1]:
            flash('Please enter a valid email address.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
        
        # Validate resume file
        if not resume_file or resume_file.filename == '':
            flash('Please upload your resume in PDF format.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
        
        # Validate PDF file
        if not resume_file.filename.lower().endswith('.pdf'):
            flash('Please upload your resume in PDF format only.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
        
        # Generate filename using original name + current date/time
        original_filename = secure_filename(resume_file.filename)

        # Separate filename and extension
        original_name, file_extension = os.path.splitext(original_filename)

        # Current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Final filename
        unique_filename = f"{original_name}_{timestamp}{file_extension}"

        # Save file to uploads directory
        upload_path = os.path.join(
            Config.UPLOAD_FOLDER,
            unique_filename
        )
        
        # Save the file
        resume_file.save(upload_path)
        
        # Extract text from the uploaded PDF
        resume_text = extract_text_from_pdf(upload_path)
        
        # If PDF extraction fails or returns empty text, clean up and show error
        if not resume_text:
            os.remove(upload_path)
            flash('Unable to process your resume PDF. Please ensure it is a valid text-based PDF.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
        
        # Preprocess the extracted text for future TF-IDF processing
        processed_resume_text = preprocess_text(resume_text)
        
        # Calculate match score using the complete matching pipeline
        match_score = calculate_match_score(resume_text, job.description)
        
        # Create application record with both raw and processed text, plus match score
        application = Application(
            job_id=job_id,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            resume_filename=unique_filename,
            resume_text=resume_text,
            processed_resume_text=processed_resume_text,
            match_score=match_score
        )
        
        try:
            db.session.add(application)
            db.session.commit()
            flash('Application submitted successfully!', 'success')
            return redirect(url_for('main.job_details', job_id=job_id))
        except Exception as e:
            db.session.rollback()
            # Clean up uploaded file if database insert fails
            if os.path.exists(upload_path):
                os.remove(upload_path)
            flash('An error occurred while submitting your application. Please try again.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
    
    return render_template('apply.html', title='Apply', job=job)

@bp.route('/applications')
def applications():
    """
    Applications page - displays all submitted job applications.
    """
    applications = Application.query.order_by(
        Application.id.desc()
    ).all()

    return render_template(
        'applications.html',
        title='Applications',
        applications=applications
    )