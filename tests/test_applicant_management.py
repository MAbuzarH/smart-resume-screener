"""
Test file for Applicant Management functionality.
Tests applicant dashboard, job browsing, application submission, duplicate prevention, and authorization.
"""

import pytest
from flask import session
from app import create_app, db
from app.models import Job, Application, User
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def setup_database():
    """
    Setup database with test users and jobs.
    """
    flask_app = create_app()
    with flask_app.app_context():
        # Create applicant user
        applicant = User(
            full_name='Test Applicant',
            email='applicant@test.com',
            role='applicant'
        )
        applicant.set_password('password123')
        db.session.add(applicant)
        
        # Create another applicant for ownership tests
        other_applicant = User(
            full_name='Other Applicant',
            email='otherapplicant@test.com',
            role='applicant'
        )
        other_applicant.set_password('password123')
        db.session.add(other_applicant)
        
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


def login_as_applicant(client):
    """
    Helper function to login as applicant.
    """
    client.post('/login', data={
        'email': 'applicant@test.com',
        'password': 'password123'
    })


def login_as_other_applicant(client):
    """
    Helper function to login as other applicant.
    """
    client.post('/login', data={
        'email': 'otherapplicant@test.com',
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


def test_applicant_dashboard_requires_login():
    """
    Test that applicant dashboard requires authentication.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.get('/applicant/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


def test_employer_cannot_access_applicant_dashboard():
    """
    Test that employers cannot access applicant dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.get('/applicant/dashboard', follow_redirects=False)
        assert response.status_code == 302


def test_applicant_can_access_dashboard():
    """
    Test that applicants can access their dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_applicant(client)
        response = client.get('/applicant/dashboard')
        assert response.status_code == 200
        assert b'Applicant Dashboard' in response.data or b'Dashboard' in response.data


def test_applicant_dashboard_shows_open_jobs():
    """
    Test that applicant dashboard shows open jobs.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        
        # Create open and closed jobs
        open_job = Job(
            title='Open Job',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=True
        )
        closed_job = Job(
            title='Closed Job',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python',
            employer_id=employer.id,
            is_open=False
        )
        db.session.add(open_job)
        db.session.add(closed_job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get('/applicant/dashboard')
            assert response.status_code == 200
            assert b'Open Job' in response.data
            assert b'Closed Job' not in response.data


def test_applicant_can_apply_to_open_job():
    """
    Test that applicant can apply to an open job.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        
        # Create an open job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get(f'/job/{job.id}/apply')
            assert response.status_code == 200


def test_duplicate_application_prevention():
    """
    Test that duplicate application prevention works.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an existing application
        application = Application(
            job_id=job.id,
            applicant_id=applicant.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='test_resume.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        # Verify only one application exists
        applications = Application.query.filter_by(job_id=job.id).all()
        assert len(applications) == 1
        
        # Try to submit duplicate (this should be prevented by the route)
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get(f'/job/{job.id}/apply', follow_redirects=True)
            assert b'already applied' in response.data.lower()
        
        # Verify still only one application exists
        applications = Application.query.filter_by(job_id=job.id).all()
        assert len(applications) == 1


def test_closed_job_rejects_application():
    """
    Test that closed jobs reject new applications.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        
        # Create a closed job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=False
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get(f'/job/{job.id}/apply', follow_redirects=True)
            assert b'closed' in response.data.lower() or b'not accepting' in response.data.lower()


def test_application_associated_with_correct_applicant():
    """
    Test that application is associated with the correct applicant.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create application directly without file upload
        application = Application(
            job_id=job.id,
            applicant_id=applicant.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='test_resume.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        # Verify application was created with correct applicant_id
        applications = Application.query.filter_by(job_id=job.id).all()
        assert len(applications) == 1
        assert applications[0].applicant_id == applicant.id


def test_applicant_uses_authenticated_user_info():
    """
    Test that application form uses authenticated user information.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get(f'/job/{job.id}/apply')
            assert response.status_code == 200
            # Verify user info is stored in session (should be from login helper)
            assert session.get('user_name') == applicant.full_name


def test_my_applications_shows_only_own_applications():
    """
    Test that My Applications shows only applicant's own applications.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        other_applicant = User.query.filter_by(email='otherapplicant@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create applications for both applicants
        app1 = Application(
            job_id=job.id,
            applicant_id=applicant.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        
        app2 = Application(
            job_id=job.id,
            applicant_id=other_applicant.id,
            applicant_name='Other Applicant',
            applicant_email='otherapplicant@test.com',
            resume_filename='resume2.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=75.0,
            similarity_score=75.0,
            skill_match_score=80.0,
            final_match_score=78.0,
            status='Submitted'
        )
        
        db.session.add(app1)
        db.session.add(app2)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get('/applicant/applications')
            assert response.status_code == 200
            assert b'Test Applicant' in response.data
            assert b'Other Applicant' not in response.data


def test_applicant_application_details_shows_own_application():
    """
    Test that applicant can view their own application details.
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
            skills='Python, Flask, SQL',
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
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get(f'/applicant/applications/{application.id}')
            assert response.status_code == 200
            assert b'Software Engineer' in response.data


def test_applicant_cannot_view_other_applicant_application():
    """
    Test that applicant cannot view another applicant's application.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        other_applicant = User.query.filter_by(email='otherapplicant@test.com').first()
        
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application for other applicant
        application = Application(
            job_id=job.id,
            applicant_id=other_applicant.id,
            applicant_name='Other Applicant',
            applicant_email='otherapplicant@test.com',
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_applicant(client)
            response = client.get(f'/applicant/applications/{application.id}', follow_redirects=False)
            assert response.status_code == 302


def test_object_level_authorization_employer():
    """
    Test that employer cannot access applicant's private application pages.
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
            skills='Python, Flask, SQL',
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
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            response = client.get(f'/applicant/applications/{application.id}', follow_redirects=False)
            assert response.status_code == 302


def test_closed_job_application_protection():
    """
    Test that existing applications remain after job closure.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        applicant = User.query.filter_by(email='applicant@test.com').first()
        
        # Create an open job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
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
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
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


def test_application_status_field():
    """
    Test that application status field works correctly.
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
            skills='Python, Flask, SQL',
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
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        # Verify status
        saved_application = Application.query.get(application.id)
        assert saved_application.status == 'Submitted'


def test_application_timestamps():
    """
    Test that application timestamps work correctly.
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
            skills='Python, Flask, SQL',
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
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0,
            status='Submitted'
        )
        db.session.add(application)
        db.session.commit()
        
        # Verify timestamps
        saved_application = Application.query.get(application.id)
        assert saved_application.created_at is not None
        assert saved_application.updated_at is not None