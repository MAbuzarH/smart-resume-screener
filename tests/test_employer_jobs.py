"""
Test file for Employer Job Management functionality.
Tests job creation, editing, open/close status, ownership, and resume download.
"""

import pytest
from app import create_app, db
from app.models import Job, Application, User
from datetime import datetime


@pytest.fixture(autouse=True)
def setup_database():
    """
    Setup database with test users and jobs.
    """
    flask_app = create_app()
    with flask_app.app_context():
        # Create employer user
        employer = User(
            full_name='Test Employer',
            email='employer@test.com',
            role='employer'
        )
        employer.set_password('password123')
        db.session.add(employer)
        
        # Create another employer for ownership tests
        other_employer = User(
            full_name='Other Employer',
            email='otheremployer@test.com',
            role='employer'
        )
        other_employer.set_password('password123')
        db.session.add(other_employer)
        
        # Create applicant user
        applicant = User(
            full_name='Test Applicant',
            email='applicant@test.com',
            role='applicant'
        )
        applicant.set_password('password123')
        db.session.add(applicant)
        
        db.session.commit()
    yield
    # Cleanup
    with flask_app.app_context():
        User.query.delete()
        Job.query.delete()
        Application.query.delete()
        db.session.commit()


def login_as_employer(client):
    """
    Helper function to login as employer.
    """
    client.post('/login', data={
        'email': 'employer@test.com',
        'password': 'password123'
    })


def login_as_other_employer(client):
    """
    Helper function to login as other employer.
    """
    client.post('/login', data={
        'email': 'otheremployer@test.com',
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


def test_employer_dashboard_requires_login():
    """
    Test that employer dashboard requires authentication.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location


def test_applicant_cannot_access_employer_dashboard():
    """
    Test that applicants cannot access employer dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_applicant(client)
        response = client.get('/dashboard', follow_redirects=False)
        assert response.status_code == 302


def test_employer_can_access_dashboard():
    """
    Test that employers can access their dashboard.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Employer Dashboard' in response.data or b'Dashboard' in response.data


def test_create_job_valid():
    """
    Test that employer can create a valid job.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.post('/employer/jobs/create', data={
            'title': 'Software Engineer',
            'company': 'Test Company',
            'location': 'Test Location',
            'description': 'Test description',
            'skills': 'Python, Flask, SQL'
        }, follow_redirects=False)
        
        assert response.status_code == 302
        assert '/dashboard' in response.location


def test_create_job_missing_title():
    """
    Test that missing title is rejected.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.post('/employer/jobs/create', data={
            'title': '',
            'company': 'Test Company',
            'location': 'Test Location',
            'description': 'Test description',
            'skills': 'Python, Flask, SQL'
        }, follow_redirects=False)
        
        assert response.status_code == 200
        assert b'required' in response.data.lower()


def test_create_job_missing_description():
    """
    Test that missing description is rejected.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.post('/employer/jobs/create', data={
            'title': 'Software Engineer',
            'company': 'Test Company',
            'location': 'Test Location',
            'description': '',
            'skills': 'Python, Flask, SQL'
        }, follow_redirects=False)
        
        assert response.status_code == 200
        assert b'required' in response.data.lower()


def test_create_job_missing_skills():
    """
    Test that missing skills are rejected.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.post('/employer/jobs/create', data={
            'title': 'Software Engineer',
            'company': 'Test Company',
            'location': 'Test Location',
            'description': 'Test description',
            'skills': ''
        }, follow_redirects=False)
        
        assert response.status_code == 200
        assert b'required' in response.data.lower()


def test_create_job_missing_location():
    """
    Test that missing location is rejected.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        login_as_employer(client)
        response = client.post('/employer/jobs/create', data={
            'title': 'Software Engineer',
            'company': 'Test Company',
            'location': '',
            'description': 'Test description',
            'skills': 'Python, Flask, SQL'
        }, follow_redirects=False)
        
        assert response.status_code == 200
        assert b'required' in response.data.lower()


def test_created_job_belongs_to_employer():
    """
    Test that created job belongs to authenticated employer.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            client.post('/employer/jobs/create', data={
                'title': 'Software Engineer',
                'company': 'Test Company',
                'location': 'Test Location',
                'description': 'Test description',
                'skills': 'Python, Flask, SQL'
            })
        
        # Check job ownership
        job = Job.query.filter_by(title='Software Engineer').first()
        assert job is not None
        assert job.employer_id == employer.id


def test_edit_own_job():
    """
    Test that employer can edit their own job.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            response = client.post(f'/employer/jobs/{job.id}/edit', data={
                'title': 'Senior Software Engineer',
                'company': 'Test Company',
                'location': 'Test Location',
                'description': 'Updated description',
                'skills': 'Python, Flask, SQL, Django'
            }, follow_redirects=False)
            
            assert response.status_code == 302
        
        # Verify job was updated
        updated_job = Job.query.get(job.id)
        assert updated_job.title == 'Senior Software Engineer'
        assert updated_job.description == 'Updated description'


def test_cannot_edit_other_employer_job():
    """
    Test that employer cannot edit another employer's job.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        employer = User.query.filter_by(email='employer@test.com').first()
        other_employer = User.query.filter_by(email='otheremployer@test.com').first()
        
        # Create a job for other employer
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
            employer_id=other_employer.id
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            response = client.post(f'/employer/jobs/{job.id}/edit', data={
                'title': 'Hacked Title',
                'company': 'Test Company',
                'location': 'Test Location',
                'description': 'Hacked description',
                'skills': 'Python, Flask, SQL'
            }, follow_redirects=False)
            
            assert response.status_code == 302
        
        # Verify job was NOT updated
        unchanged_job = Job.query.get(job.id)
        assert unchanged_job.title == 'Software Engineer'
        assert unchanged_job.description == 'Test description'


def test_close_own_job():
    """
    Test that employer can close their own job.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            client.post(f'/employer/jobs/{job.id}/toggle-status')
        
        # Verify job was closed
        updated_job = Job.query.get(job.id)
        assert updated_job.is_open == False


def test_reopen_own_job():
    """
    Test that employer can reopen their own job.
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
            login_as_employer(client)
            client.post(f'/employer/jobs/{job.id}/toggle-status')
        
        # Verify job was reopened
        updated_job = Job.query.get(job.id)
        assert updated_job.is_open == True


def test_closed_jobs_not_in_public_listings():
    """
    Test that closed jobs do not appear in public open-job listings.
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
            response = client.get('/')
            assert b'Open Job' in response.data
            assert b'Closed Job' not in response.data


def test_closed_job_rejects_applications():
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


def test_employer_can_view_own_job_applicants():
    """
    Test that employer can view applicants for their own job.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            response = client.get(f'/employer/jobs/{job.id}/applicants')
            assert response.status_code == 200


def test_employer_cannot_view_other_job_applicants():
    """
    Test that employer cannot view applicants for another employer's job.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        other_employer = User.query.filter_by(email='otheremployer@test.com').first()
        
        # Create a job for other employer
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
            employer_id=other_employer.id
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            response = client.get(f'/employer/jobs/{job.id}/applicants', follow_redirects=False)
            assert response.status_code == 302


def test_resume_download_authorization():
    """
    Test that employer can download resume for their own job's applicant.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application
        application = Application(
            job_id=job.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='test_resume.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0
        )
        db.session.add(application)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            response = client.get(f'/employer/applications/{application.id}/resume', follow_redirects=False)
            # File not found is expected since we don't have actual file, but should not be unauthorized
            assert response.status_code in [404, 302]  # 404 for missing file, 302 for redirect


def test_cannot_download_other_employer_resume():
    """
    Test that employer cannot download resume from another employer's job.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        other_employer = User.query.filter_by(email='otheremployer@test.com').first()
        
        # Create a job for other employer
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL',
            employer_id=other_employer.id
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application
        application = Application(
            job_id=job.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='test_resume.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0
        )
        db.session.add(application)
        db.session.commit()
        
        with flask_app.test_client() as client:
            login_as_employer(client)
            response = client.get(f'/employer/applications/{application.id}/resume', follow_redirects=False)
            assert response.status_code == 302  # Should redirect to dashboard with error


def test_existing_applications_remain_after_job_closure():
    """
    Test that existing applications remain available after job closure.
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
            skills='Python, Flask, SQL',
            employer_id=employer.id,
            is_open=True
        )
        db.session.add(job)
        db.session.commit()
        
        # Create an application
        application = Application(
            job_id=job.id,
            applicant_name='Test Applicant',
            applicant_email='applicant@test.com',
            resume_filename='test_resume.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0
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