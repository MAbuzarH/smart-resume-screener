from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Job, Application
from app import db
from app.services import extract_text_from_pdf, preprocess_text, calculate_match_score, rank_all_applications_by_job, rank_applications_by_job, calculate_skill_match, calculate_final_score, analyze_candidate, get_screening_category
from app.auth.helpers import login_required, role_required
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from config import Config
from datetime import datetime

logger = logging.getLogger(__name__)

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
@login_required
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
        
        # Calculate TF-IDF match score using the complete matching pipeline
        match_score = calculate_match_score(resume_text, job.description)
        
        # Calculate skill match score
        skill_match_result = calculate_skill_match(resume_text, job.skills)
        skill_match_score = skill_match_result.skill_match_percentage
        
        # Calculate final weighted score
        final_score_result = calculate_final_score(match_score, skill_match_score)
        final_match_score = final_score_result.final_score
        
        # Create application record with all scoring information
        application = Application(
            job_id=job_id,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            resume_filename=unique_filename,
            resume_text=resume_text,
            processed_resume_text=processed_resume_text,
            match_score=match_score,  # Original TF-IDF score (preserved for backward compatibility)
            similarity_score=match_score,  # TF-IDF score (renamed for clarity)
            skill_match_score=skill_match_score,  # Skill match percentage
            final_match_score=final_match_score  # Weighted final score
        )
        
        try:
            db.session.add(application)
            db.session.commit()
            flash('Application submitted successfully!', 'success')
            return redirect(url_for('main.job_details', job_id=job_id))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting application for {applicant_name}: {str(e)}")
            # Clean up uploaded file if database insert fails
            if os.path.exists(upload_path):
                os.remove(upload_path)
            flash('An error occurred while submitting your application. Please try again.', 'danger')
            return render_template('apply.html', title='Apply', job=job)
    
    return render_template('apply.html', title='Apply', job=job)

@bp.route('/applications')
def applications():
    """
    Applications page - displays all submitted job applications ranked by job.
    Applications are grouped by job and ranked within each job by match score.
    """
    # Rank applications grouped by job
    rankings_by_job = rank_all_applications_by_job()
    
    # If no rankings but there are applications, show them unranked
    if not rankings_by_job:
        from app.models import Application
        applications = Application.query.order_by(Application.id.desc()).all()
        return render_template(
            'applications.html',
            title='Applications',
            applications=applications,
            rankings_by_job=None
        )
    
    return render_template(
        'applications.html',
        title='Applications',
        rankings_by_job=rankings_by_job,
        applications=None
    )


@bp.route('/job/<int:job_id>/applications')
def job_applications(job_id):
    """
    Job-specific applications page - displays candidates ranked for a specific job.
    """
    job = Job.query.get_or_404(job_id)
    
    # Rank applications for this specific job
    ranked_candidates = rank_applications_by_job(job_id)
    
    return render_template(
        'job_applications.html',
        title=f'Applications - {job.title}',
        job=job,
        ranked_candidates=ranked_candidates
    )


@bp.route('/application/<int:application_id>')
def application_details(application_id):
    """
    Candidate screening analysis page - displays detailed analysis for a specific application.
    """
    try:
        application = Application.query.get_or_404(application_id)
        job = application.job
        
        # Generate candidate screening analysis
        screening_result = analyze_candidate(application, job)
        
        return render_template(
            'application_details.html',
            title=f'Candidate Analysis - {application.applicant_name}',
            application=application,
            job=job,
            screening=screening_result
        )
    except Exception as e:
        logger.error(f"Error loading application details for application {application_id}: {str(e)}")
        flash('An error occurred while loading the candidate analysis. Please try again.', 'danger')
        return redirect(url_for('main.applications'))


@bp.route('/dashboard', methods=['GET'])
@role_required('employer', 'admin')
def dashboard():
    """
    Recruiter dashboard - displays job selection and candidate rankings.
    GET: Display job selection form and candidate rankings for selected job.
    """
    try:
        # Get all available jobs
        jobs = Job.query.all()
        
        # Get selected job from query parameters
        selected_job_id = request.args.get('job_id', type=int)
        
        # Get filter from query parameters
        filter_category = request.args.get('filter', 'all')
        
        selected_job = None
        ranked_candidates = []
        summary_stats = None
        top_candidates = []
        
        if selected_job_id:
            selected_job = Job.query.get_or_404(selected_job_id)
            
            # Rank applications for this specific job
            ranked_candidates = rank_applications_by_job(selected_job_id)
            
            # Calculate summary statistics
            total_applications = len(ranked_candidates)
            scored_applications = sum(1 for c in ranked_candidates if c['final_match_score'] is not None)
            
            # Count screening categories
            strong_matches = 0
            moderate_matches = 0
            low_matches = 0
            not_scored = 0
            
            for candidate in ranked_candidates:
                if candidate['final_match_score'] is not None:
                    category = get_screening_category(candidate['final_match_score'])
                    if category == "Strong Match":
                        strong_matches += 1
                    elif category == "Moderate Match":
                        moderate_matches += 1
                    elif category == "Low Match":
                        low_matches += 1
                else:
                    not_scored += 1
            
            summary_stats = {
                'total_applications': total_applications,
                'scored_applications': scored_applications,
                'strong_matches': strong_matches,
                'moderate_matches': moderate_matches,
                'low_matches': low_matches,
                'not_scored': not_scored
            }
            
            # Get top 3 candidates
            top_candidates = ranked_candidates[:3]
            
            # Add screening category to top candidates
            for candidate in top_candidates:
                if candidate['final_match_score'] is not None:
                    candidate['screening_category'] = get_screening_category(candidate['final_match_score'])
                else:
                    candidate['screening_category'] = 'Not Scored'
            
            # Apply filtering if specified
            if filter_category != 'all':
                filtered_candidates = []
                for candidate in ranked_candidates:
                    if candidate['final_match_score'] is not None:
                        category = get_screening_category(candidate['final_match_score'])
                        if category.lower() == filter_category.lower():
                            filtered_candidates.append(candidate)
                    elif filter_category == 'not_scored' and candidate['final_match_score'] is None:
                        filtered_candidates.append(candidate)
                ranked_candidates = filtered_candidates
            
            # Add screening category to each candidate for display
            for candidate in ranked_candidates:
                if candidate['final_match_score'] is not None:
                    candidate['screening_category'] = get_screening_category(candidate['final_match_score'])
                else:
                    candidate['screening_category'] = 'Not Scored'
        
        return render_template(
            'dashboard.html',
            title='Recruiter Dashboard',
            jobs=jobs,
            selected_job=selected_job,
            ranked_candidates=ranked_candidates,
            summary_stats=summary_stats,
            top_candidates=top_candidates,
            filter_category=filter_category
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard. Please try again.', 'danger')
        return redirect(url_for('main.index'))