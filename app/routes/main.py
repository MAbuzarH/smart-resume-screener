from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.models import Job, Application, User
from app import db
from app.services import extract_text_from_pdf, preprocess_text, calculate_match_score, rank_all_applications_by_job, rank_applications_by_job, calculate_skill_match, calculate_final_score, analyze_candidate, get_screening_category
from app.auth.helpers import login_required, role_required, get_current_user
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from config import Config
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """
    Home page - displays all available open jobs from the database.
    """
    jobs = Job.query.filter_by(is_open=True).all()
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
@role_required('applicant')
def apply(job_id):
    """
    Application form for a specific job.
    GET: Display the application form.
    POST: Process the application submission.
    """
    job = Job.query.get_or_404(job_id)
    
    # Check if job is open
    if not job.is_open:
        flash('This job is currently closed and not accepting new applications.', 'warning')
        return redirect(url_for('main.job_details', job_id=job_id))
    
    # Check for duplicate application
    current_user = get_current_user()
    existing_application = Application.query.filter_by(
        job_id=job_id,
        applicant_id=current_user.id
    ).first()
    
    if existing_application:
        flash('You have already applied for this position.', 'info')
        return redirect(url_for('main.job_details', job_id=job_id))
    
    if request.method == 'POST':
        # Get form data - use authenticated user info where possible
        applicant_name = request.form.get('applicant_name', current_user.full_name).strip()
        applicant_email = request.form.get('applicant_email', current_user.email).strip()
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
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

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
            applicant_id=current_user.id,
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            resume_filename=unique_filename,
            resume_text=resume_text,
            processed_resume_text=processed_resume_text,
            match_score=match_score,  # Original TF-IDF score (preserved for backward compatibility)
            similarity_score=match_score,  # TF-IDF score (renamed for clarity)
            skill_match_score=skill_match_score,  # Skill match percentage
            final_match_score=final_match_score,  # Weighted final score
            status='Submitted'
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
@login_required
def application_details(application_id):
    """
    Candidate screening analysis page - displays detailed analysis for a specific application.
    """
    try:
        current_user = get_current_user()
        application = Application.query.get_or_404(application_id)
        job = application.job
        
        # Verify access permissions
        # Employers can view applications for their jobs
        # Applicants can view their own applications
        # Admins can view all applications
        if current_user.role == 'applicant':
            if application.applicant_id != current_user.id:
                flash('You do not have permission to view this application.', 'danger')
                return redirect(url_for('main.applicant_applications'))
        elif current_user.role == 'employer':
            if job.employer_id != current_user.id:
                flash('You do not have permission to view this application.', 'danger')
                return redirect(url_for('main.dashboard'))
        
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
    Recruiter dashboard - displays employer's jobs and candidate rankings.
    GET: Display employer's jobs and candidate rankings for selected job.
    """
    try:
        current_user = get_current_user()
        
        # Get jobs belonging to the current employer (or all jobs for admin)
        if current_user.role == 'admin':
            jobs = Job.query.all()
        else:
            jobs = Job.query.filter_by(employer_id=current_user.id).all()
        
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
            
            # Verify employer owns the job (unless admin)
            if current_user.role != 'admin' and selected_job.employer_id != current_user.id:
                flash('You do not have permission to view this job.', 'danger')
                return redirect(url_for('main.dashboard'))
            
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


@bp.route('/employer/jobs/create', methods=['GET', 'POST'])
@login_required
@role_required('employer', 'admin')
def create_job():
    """
    Create a new job posting.
    GET: Display job creation form.
    POST: Process job creation and associate with employer.
    """
    current_user = get_current_user()
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        company = request.form.get('company', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        
        # Validate title
        if not title:
            flash('Job title is required.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        if len(title) > 200:
            flash('Job title is too long.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        # Validate company
        if not company:
            flash('Company name is required.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        if len(company) > 200:
            flash('Company name is too long.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        # Validate location
        if not location:
            flash('Location is required.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        if len(location) > 200:
            flash('Location is too long.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        # Validate description
        if not description:
            flash('Job description is required.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        # Validate skills
        if not skills:
            flash('Required skills are required.', 'danger')
            return render_template('create_job.html', title='Create Job')
        
        # Create job with employer association
        job = Job(
            title=title,
            company=company,
            location=location,
            description=description,
            skills=skills,
            employer_id=current_user.id,
            is_open=True
        )
        
        try:
            db.session.add(job)
            db.session.commit()
            flash('Job created successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating job: {str(e)}")
            flash('An error occurred while creating the job. Please try again.', 'danger')
            return render_template('create_job.html', title='Create Job')
    
    return render_template('create_job.html', title='Create Job')


@bp.route('/employer/jobs/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('employer', 'admin')
def edit_job(job_id):
    """
    Edit an existing job posting.
    GET: Display job edit form.
    POST: Process job edit.
    """
    current_user = get_current_user()
    job = Job.query.get_or_404(job_id)
    
    # Verify employer owns the job (unless admin)
    if current_user.role != 'admin' and job.employer_id != current_user.id:
        flash('You do not have permission to edit this job.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        company = request.form.get('company', '').strip()
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        skills = request.form.get('skills', '').strip()
        
        # Validate title
        if not title:
            flash('Job title is required.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        if len(title) > 200:
            flash('Job title is too long.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        # Validate company
        if not company:
            flash('Company name is required.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        if len(company) > 200:
            flash('Company name is too long.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        # Validate location
        if not location:
            flash('Location is required.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        if len(location) > 200:
            flash('Location is too long.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        # Validate description
        if not description:
            flash('Job description is required.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        # Validate skills
        if not skills:
            flash('Required skills are required.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
        
        # Update job fields
        job.title = title
        job.company = company
        job.location = location
        job.description = description
        job.skills = skills
        job.updated_at = datetime.now(timezone.utc)
        
        try:
            db.session.commit()
            flash('Job updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating job: {str(e)}")
            flash('An error occurred while updating the job. Please try again.', 'danger')
            return render_template('edit_job.html', title='Edit Job', job=job)
    
    return render_template('edit_job.html', title='Edit Job', job=job)


@bp.route('/employer/jobs/<int:job_id>/toggle-status', methods=['POST'])
@login_required
@role_required('employer', 'admin')
def toggle_job_status(job_id):
    """
    Toggle job open/closed status.
    Only the job owner can perform this action.
    """
    current_user = get_current_user()
    job = Job.query.get_or_404(job_id)
    
    # Verify employer owns the job (unless admin)
    if current_user.role != 'admin' and job.employer_id != current_user.id:
        flash('You do not have permission to modify this job.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Toggle status
    job.is_open = not job.is_open
    job.updated_at = datetime.now(timezone.utc)
    
    try:
        db.session.commit()
        status = 'opened' if job.is_open else 'closed'
        flash(f'Job has been {status} successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling job status: {str(e)}")
        flash('An error occurred while updating the job status. Please try again.', 'danger')
    
    return redirect(url_for('main.dashboard', job_id=job_id))


@bp.route('/employer/jobs/<int:job_id>/applicants')
@login_required
@role_required('employer', 'admin')
def employer_job_applicants(job_id):
    """
    View applicants for a specific job (employer view).
    Only the job owner can access this page.
    """
    current_user = get_current_user()
    job = Job.query.get_or_404(job_id)
    
    # Verify employer owns the job (unless admin)
    if current_user.role != 'admin' and job.employer_id != current_user.id:
        flash('You do not have permission to view applicants for this job.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Rank applications for this specific job
    ranked_candidates = rank_applications_by_job(job_id)
    
    # Add screening category to each candidate
    for candidate in ranked_candidates:
        if candidate['final_match_score'] is not None:
            candidate['screening_category'] = get_screening_category(candidate['final_match_score'])
        else:
            candidate['screening_category'] = 'Not Scored'
    
    return render_template(
        'employer_applicants.html',
        title=f'Applicants - {job.title}',
        job=job,
        ranked_candidates=ranked_candidates
    )


@bp.route('/employer/applications/<int:application_id>/resume')
@login_required
@role_required('employer', 'admin')
def download_resume(application_id):
    """
    Secure resume download for employers.
    Only the job owner can download resumes for their jobs.
    """
    current_user = get_current_user()
    application = Application.query.get_or_404(application_id)
    job = application.job
    
    # Verify employer owns the job (unless admin)
    if current_user.role != 'admin' and job.employer_id != current_user.id:
        flash('You do not have permission to download this resume.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Check if resume file exists
    upload_path = os.path.join(Config.UPLOAD_FOLDER, application.resume_filename)
    
    if not os.path.exists(upload_path):
        flash('Resume file not found.', 'danger')
        return redirect(url_for('main.employer_job_applicants', job_id=job.id))
    
    try:
        return send_file(
            upload_path,
            as_attachment=True,
            download_name=application.resume_filename
        )
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        flash('An error occurred while downloading the resume. Please try again.', 'danger')
        return redirect(url_for('main.employer_job_applicants', job_id=job.id))


@bp.route('/applicant/dashboard')
@login_required
@role_required('applicant')
def applicant_dashboard():
    """
    Applicant dashboard - shows available jobs and application summary.
    """
    try:
        current_user = get_current_user()
        
        # Get all open jobs
        open_jobs = Job.query.filter_by(is_open=True).all()
        
        # Get applicant's applications
        applicant_applications = Application.query.filter_by(applicant_id=current_user.id).all()
        
        # Calculate application statistics
        total_applications = len(applicant_applications)
        scored_applications = sum(1 for app in applicant_applications if app.final_match_score is not None)
        
        return render_template(
            'applicant_dashboard.html',
            title='Applicant Dashboard',
            open_jobs=open_jobs,
            applicant_applications=applicant_applications,
            total_applications=total_applications,
            scored_applications=scored_applications
        )
    except Exception as e:
        logger.error(f"Error loading applicant dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard. Please try again.', 'danger')
        return redirect(url_for('main.index'))


@bp.route('/applicant/applications')
@login_required
@role_required('applicant')
def applicant_applications():
    """
    My Applications page - shows applicant's submitted applications.
    """
    try:
        current_user = get_current_user()
        
        # Get applicant's applications with job information
        applications = Application.query.filter_by(applicant_id=current_user.id).order_by(Application.created_at.desc()).all()
        
        return render_template(
            'applicant_applications.html',
            title='My Applications',
            applications=applications
        )
    except Exception as e:
        logger.error(f"Error loading applicant applications: {str(e)}")
        flash('An error occurred while loading your applications. Please try again.', 'danger')
        return redirect(url_for('main.applicant_dashboard'))


@bp.route('/applicant/applications/<int:application_id>')
@login_required
@role_required('applicant')
def applicant_application_details(application_id):
    """
    Applicant-facing application detail page.
    Shows applicant's own application information.
    """
    try:
        current_user = get_current_user()
        application = Application.query.get_or_404(application_id)
        
        # Verify ownership
        if application.applicant_id != current_user.id:
            flash('You do not have permission to view this application.', 'danger')
            return redirect(url_for('main.applicant_applications'))
        
        job = application.job
        
        # Generate screening result for display
        screening_result = analyze_candidate(application, job)
        
        return render_template(
            'applicant_application_details.html',
            title=f'Application - {job.title}',
            application=application,
            job=job,
            screening=screening_result
        )
    except Exception as e:
        logger.error(f"Error loading applicant application details for application {application_id}: {str(e)}")
        flash('An error occurred while loading the application details. Please try again.', 'danger')
        return redirect(url_for('main.applicant_applications'))