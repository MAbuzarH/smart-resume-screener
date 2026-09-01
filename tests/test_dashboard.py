"""
Test file for Dashboard functionality.
Tests recruiter dashboard, job selection, candidate ranking, and filtering.
"""

import pytest
from app import create_app, db
from app.models import Job, Application


def test_dashboard_route_loads():
    """
    Test that dashboard route loads successfully.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Recruiter Dashboard' in response.data


def test_dashboard_displays_jobs():
    """
    Test that dashboard displays available jobs.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create a test job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL'
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            response = client.get('/dashboard')
            assert response.status_code == 200
            assert b'Software Engineer' in response.data or b'software engineer' in response.data.lower()


def test_selecting_valid_job_displays_candidates():
    """
    Test that selecting a valid job displays its candidates.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create a test job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask, SQL'
        )
        db.session.add(job)
        db.session.commit()
        
        # Create test applications
        app1 = Application(
            job_id=job.id,
            applicant_name='Ali Khan',
            applicant_email='ali@test.com',
            resume_filename='resume1.pdf',
            resume_text='Python developer with Flask experience',
            processed_resume_text='python developer flask experience',
            match_score=85.0,
            similarity_score=85.0,
            skill_match_score=90.0,
            final_match_score=88.0
        )
        
        db.session.add(app1)
        db.session.commit()
        
        with flask_app.test_client() as client:
            response = client.get(f'/dashboard?job_id={job.id}')
            assert response.status_code == 200
            assert b'Ali Khan' in response.data


def test_empty_job_has_proper_empty_state_message():
    """
    Test that an empty job has a proper empty-state message.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create a job with no applications
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask'
        )
        db.session.add(job)
        db.session.commit()
        
        with flask_app.test_client() as client:
            response = client.get(f'/dashboard?job_id={job.id}')
            assert response.status_code == 200
            assert b'No applications have been submitted' in response.data


def test_invalid_job_id_handled_safely():
    """
    Test that invalid job IDs are handled safely.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        # Test with non-existent job ID
        response = client.get('/dashboard?job_id=9999')
        # Should handle gracefully (200, 404, or redirect 302)
        assert response.status_code in [200, 404, 302]


def test_existing_application_functionality_still_works():
    """
    Test that existing application functionality still works.
    """
    flask_app = create_app()
    
    # Test home page
    with flask_app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
    
    # Test applications page
    with flask_app.test_client() as client:
        response = client.get('/applications')
        assert response.status_code == 200


def test_module_import():
    """
    Test that dashboard route can be imported.
    """
    from app.routes.main import bp
    assert bp is not None