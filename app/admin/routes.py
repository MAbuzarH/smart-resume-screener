"""
Admin routes for platform administration and monitoring.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.auth.helpers import login_required, role_required, get_current_user
from app.models import User, Job, Application
from app import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """
    Admin dashboard with platform statistics.
    """
    try:
        # User statistics
        total_users = User.query.count()
        total_applicants = User.query.filter_by(role='applicant').count()
        total_employers = User.query.filter_by(role='employer').count()
        total_admins = User.query.filter_by(role='admin').count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # Job statistics
        total_jobs = Job.query.count()
        open_jobs = Job.query.filter_by(is_open=True).count()
        closed_jobs = Job.query.filter_by(is_open=False).count()
        
        # Application statistics
        total_applications = Application.query.count()
        scored_applications = Application.query.filter(Application.final_match_score.isnot(None)).count()
        unscored_applications = total_applications - scored_applications
        
        # Recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()
        recent_applications = Application.query.order_by(Application.created_at.desc()).limit(5).all()
        
        return render_template(
            'admin_dashboard.html',
            title='Admin Dashboard',
            total_users=total_users,
            total_applicants=total_applicants,
            total_employers=total_employers,
            total_admins=total_admins,
            active_users=active_users,
            total_jobs=total_jobs,
            open_jobs=open_jobs,
            closed_jobs=closed_jobs,
            total_applications=total_applications,
            scored_applications=scored_applications,
            unscored_applications=unscored_applications,
            recent_users=recent_users,
            recent_jobs=recent_jobs,
            recent_applications=recent_applications
        )
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {str(e)}")
        flash('An error occurred while loading the dashboard. Please try again.', 'danger')
        return redirect(url_for('main.index'))


@bp.route('/users')
@login_required
@role_required('admin')
def users():
    """
    User management page - view all users with filtering.
    """
    try:
        role_filter = request.args.get('role', 'all')
        status_filter = request.args.get('status', 'all')
        
        # Build query
        query = User.query
        
        if role_filter != 'all':
            query = query.filter_by(role=role_filter)
        
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'inactive':
            query = query.filter_by(is_active=False)
        
        users = query.order_by(User.created_at.desc()).all()
        
        return render_template(
            'admin_users.html',
            title='User Management',
            users=users,
            role_filter=role_filter,
            status_filter=status_filter
        )
    except Exception as e:
        logger.error(f"Error loading user management: {str(e)}")
        flash('An error occurred while loading users. Please try again.', 'danger')
        return redirect(url_for('admin.dashboard'))


@bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@login_required
@role_required('admin')
def suspend_user(user_id):
    """
    Suspend a user account.
    """
    try:
        current_user = get_current_user()
        user = User.query.get_or_404(user_id)
        
        # Prevent self-suspension
        if user.id == current_user.id:
            flash('You cannot suspend your own account.', 'danger')
            return redirect(url_for('admin.users'))
        
        # Prevent suspending the last active admin
        if user.role == 'admin':
            active_admins = User.query.filter_by(role='admin', is_active=True).count()
            if active_admins <= 1:
                flash('You cannot suspend the last active admin account.', 'danger')
                return redirect(url_for('admin.users'))
        
        user.is_active = False
        db.session.commit()
        
        flash(f'User {user.full_name} has been suspended.', 'success')
        return redirect(url_for('admin.users'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error suspending user {user_id}: {str(e)}")
        flash('An error occurred while suspending the user. Please try again.', 'danger')
        return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/activate', methods=['POST'])
@login_required
@role_required('admin')
def activate_user(user_id):
    """
    Reactivate a suspended user account.
    """
    try:
        user = User.query.get_or_404(user_id)
        
        user.is_active = True
        db.session.commit()
        
        flash(f'User {user.full_name} has been reactivated.', 'success')
        return redirect(url_for('admin.users'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error activating user {user_id}: {str(e)}")
        flash('An error occurred while reactivating the user. Please try again.', 'danger')
        return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    """
    Delete a user account (destructive operation).
    Note: This is a permanent deletion and may affect related data.
    """
    try:
        current_user = get_current_user()
        user = User.query.get_or_404(user_id)
        
        # Prevent self-deletion
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'danger')
            return redirect(url_for('admin.users'))
        
        # Prevent deleting the last active admin
        if user.role == 'admin':
            active_admins = User.query.filter_by(role='admin', is_active=True).count()
            if active_admins <= 1:
                flash('You cannot delete the last active admin account.', 'danger')
                return redirect(url_for('admin.users'))
        
        # Check for related data
        user_jobs = Job.query.filter_by(employer_id=user.id).count()
        user_applications = Application.query.filter_by(applicant_id=user.id).count()
        
        if user_jobs > 0 or user_applications > 0:
            flash(f'Cannot delete user with {user_jobs} jobs and {user_applications} applications. Please suspend the account instead.', 'warning')
            return redirect(url_for('admin.users'))
        
        # Delete user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {user.full_name} has been deleted.', 'success')
        return redirect(url_for('admin.users'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        flash('An error occurred while deleting the user. Please try again.', 'danger')
        return redirect(url_for('admin.users'))


@bp.route('/jobs')
@login_required
@role_required('admin')
def jobs():
    """
    Job moderation page - view all jobs.
    """
    try:
        jobs = Job.query.order_by(Job.created_at.desc()).all()
        
        return render_template(
            'admin_jobs.html',
            title='Job Moderation',
            jobs=jobs
        )
    except Exception as e:
        logger.error(f"Error loading job moderation: {str(e)}")
        flash('An error occurred while loading jobs. Please try again.', 'danger')
        return redirect(url_for('admin.dashboard'))


@bp.route('/jobs/<int:job_id>/remove', methods=['POST'])
@login_required
@role_required('admin')
def remove_job(job_id):
    """
    Remove/close a job (soft deletion via status change).
    """
    try:
        job = Job.query.get_or_404(job_id)
        
        # Close the job (soft deletion)
        job.is_open = False
        db.session.commit()
        
        flash(f'Job "{job.title}" has been removed from public listings.', 'success')
        return redirect(url_for('admin.jobs'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing job {job_id}: {str(e)}")
        flash('An error occurred while removing the job. Please try again.', 'danger')
        return redirect(url_for('admin.jobs'))


@bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_job(job_id):
    """
    Permanently delete a job (destructive operation).
    Note: This will delete the job and its applications.
    """
    try:
        job = Job.query.get_or_404(job_id)
        
        # Count applications
        application_count = Application.query.filter_by(job_id=job_id).count()
        
        if application_count > 0:
            flash(f'Cannot delete job with {application_count} applications. Please remove the job from public listings instead.', 'warning')
            return redirect(url_for('admin.jobs'))
        
        # Delete job
        db.session.delete(job)
        db.session.commit()
        
        flash(f'Job "{job.title}" has been permanently deleted.', 'success')
        return redirect(url_for('admin.jobs'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        flash('An error occurred while deleting the job. Please try again.', 'danger')
        return redirect(url_for('admin.jobs'))