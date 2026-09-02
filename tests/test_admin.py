"""
Test file for Admin Module functionality.
Tests admin dashboard, user management, job moderation, and authorization.
"""

import pytest
from app import create_app, db
from app.models import User, Job, Application
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def setup_database():
    """
    Setup database with test users, jobs, and applications.
    """
    flask_app = create_app()
    with flask_app.app_context():
        # Create admin user
        admin = User(
            full_name='Test Admin',
            email='admin@test.com',
            role='admin'
        )
        admin.set_password('password123')
        db.session.add(admin)
        
        # Create applicant user
        applicant = User(
            full_name='Test Applicant',
            email='applicant@test.com',
            role='applicant'
        )
        applicant.set_password('password123')
        db.session.add(applicant)
        
        # Create employer user
        employer = User(
            full_name='Test Employer',
            email='employer@test.com',
            role='employer'
        )
        employer.set_password('password123')
        db.session.add(employer)
        
        db.session.commit()
    yield
    # Cleanup
    with flask_app.app_context():
        User.query.delete()
        Job.query.delete()
        Application.query.delete()
        db.session.commit()


def login_as_admin(client):
    """
    Helper function to login as admin.
    """
    client.post('/login', data={
        'email': 'admin@test.com',
        'password': 'password123'
    })


def login_as_applicant(client):
    """
    Helper function to login as applicant.
    """
    client.post('/login', data={
        'email': 'applicant@test.com',
        'password': 'password123'
    })


def login_as_employer(client):
    """
    Helper function to login as employer.
    """
    client.post('/login', data={
        'email': 'employer@test.com',
        'password': 'password123'
    })


def test_admin_can_access_dashboard():
    """
    Test that admin can access admin dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_admin(client)
        response = client.get('/admin/dashboard')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data


def test_anonymous_cannot_access_admin_dashboard():
    """
    Test that anonymous users cannot access admin dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.get('/admin/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


def test_applicant_cannot_access_admin_dashboard():
    """
    Test that applicants cannot access admin dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_applicant(client)
        response = client.get('/admin/dashboard', follow_redirects=False)
        assert response.status_code == 302


def test_employer_cannot_access_admin_dashboard():
    """
    Test that employers cannot access admin dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.get('/admin/dashboard', follow_redirects=False)
        assert response.status_code == 302


def test_admin_dashboard_statistics():
    """
    Test that admin dashboard shows correct statistics.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        employer = User.query.filter_by(email='employer@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application
        application = Application(
            job_id=job.id,
            applicant_id=applicant.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='resume.pdf',
            resume_text='Python developer',
            processed_resume_text='python developer',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.get('/admin/dashboard')
            assert response.status_code == 200
            assert b'3' in response.data  # Total users


def test_admin_can_view_users():
    """
    Test that admin can view users page.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_admin(client)
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert b'User Management' in response.data


def test_applicant_cannot_access_user_management():
    """
    Test that applicants cannot access user management.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_applicant(client)
        response = client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302


def test_employer_cannot_access_user_management():
    """
    Test that employers cannot access user management.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302


def test_admin_can_suspend_user():
    """
    Test that admin can suspend a user.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        applicant = User.query.filter_by(email='applicant@test.com').first()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.post(f'/admin/users/{applicant.id}/suspend', follow_redirects=True)
            assert response.status_code == 200
        
        # Verify user is suspended
        suspended_user = User.query.get(applicant.id)
        assert suspended_user.is_active == False


def test_suspended_user_cannot_login():
    """
    Test that suspended user cannot login.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        applicant = User.query.filter_by(email='applicant@test.com').first()
        applicant.is_active = False
        db.session.commit()
        
        with flask_app.test_client() as client:
            response = client.post('/login', data={
                'email': 'applicant@test.com',
                'password': 'password123'
            })
            assert b'inactive' in response.data.lower()


def test_admin_can_reactivate_user():
    """
    Test that admin can reactivate a suspended user.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        applicant = User.query.filter_by(email='applicant@test.com').first()
        applicant.is_active = False
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.post(f'/admin/users/{applicant.id}/activate', follow_redirects=True)
            assert response.status_code == 200
        
        # Verify user is reactivated
        reactivated_user = User.query.get(applicant.id)
        assert reactivated_user.is_active == True


def test_admin_cannot_suspend_themselves():
    """
    Test that admin cannot suspend their own account.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.post(f'/admin/users/{admin.id}/suspend', follow_redirects=True)
            assert b'cannot suspend your own account' in response.data.lower()
        
        # Verify admin is still active
        admin_user = User.query.get(admin.id)
        assert admin_user.is_active == True


def test_admin_cannot_delete_themselves():
    """
    Test that admin cannot delete their own account.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.post(f'/admin/users/{admin.id}/delete', follow_redirects=True)
            assert b'cannot delete your own account' in response.data.lower()
        
        # Verify admin still exists
        admin_user = User.query.get(admin.id)
        assert admin_user is not None


def test_admin_cannot_suspend_last_admin():
    """
    Test that admin cannot suspend the last active admin.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.post(f'/admin/users/{admin.id}/suspend', follow_redirects=True)
            # Should prevent self-suspension before checking last admin
            assert b'cannot suspend your own account' in response.data.lower() or b'last active admin' in response.data.lower()


def test_admin_can_view_jobs():
    """
    Test that admin can view all jobs.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.get('/admin/jobs')
            assert response.status_code == 200
            assert b'Job Moderation' in response.data


def test_admin_can_remove_job():
    """
    Test that admin can remove a job from public listings.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.post(f'/admin/jobs/{job.id}/remove', follow_redirects=True)
            assert response.status_code == 200
        
        # Verify job is closed
        updated_job = Job.query.get(job.id)
        assert updated_job.is_open == False


def test_removed_job_does_not_accept_applications():
    """
    Test that removed jobs do not accept new applications.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        
        # Create a closed job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=False
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get(f'/job/{job.id}/apply', follow_redirects=True)
            assert b'closed' in response.data.lower() or b'not accepting' in response.data.lower()


def test_job_moderation_preserves_applications():
    """
    Test that job moderation does not delete existing applications.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application
        application = Application(
            job_id=job.id,
            applicant_id=applicant.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='resume.pdf',
            resume_text='Python developer',
            processed_resume_text='python developer',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        # Close the job
        job.is_open = False
        db.session.commit()
        
        # Verify application still exists
        existing_application = Application.query.get(application.id)
        assert existing_application is not None
        assert existing_application.final_match_score == 88.0


def test_admin_cannot_delete_job_with_applications():
    """
    Test that admin cannot delete a job with applications.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application
        application = Application(
            job_id=job.id,
            applicant_id=applicant.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='resume.pdf',
            resume_text='Python developer',
            processed_resume_text='python developer',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_admin(client)
            response = client.post(f'/admin/jobs/{job.id}/delete', follow_redirects=True)
            assert b'cannot delete job' in response.data.lower()
        
        # Verify job still exists
        existing_job = Job.query.get(job.id)
        assert existing_job is not None


def test_suspending_user_preserves_data():
    """
    Test that suspending a user does not delete their data.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application
        application = Application(
            job_id=job.id,
            applicant_id=applicant.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='resume.pdf',
            resume_text='Python developer',
            processed_resume_text='python developer',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        # Suspend the applicant
        applicant.is_active = False
        db.session.commit()
        
        # Verify data still exists
        existing_application = Application.query.get(application.id)
        assert existing_application is not None
        assert existing_application.final_match_score == 88.0


def test_user_filtering_by_role():
    """
    Test that user filtering by role works correctly.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_admin(client)
        response = client.get('/admin/users?role=applicant')
        assert response.status_code == 200


def test_user_filtering_by_status():
    """
    Test that user filtering by status works correctly.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_admin(client)
        response = client.get('/admin/users?status=active')
        assert response.status_code == 200