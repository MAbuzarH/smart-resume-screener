"""
Test file for Ranking Service.
Tests candidate ranking functionality based on match scores.
"""

import pytest
from app.services.ranking_service import rank_candidates, rank_applications_by_job, rank_all_applications_by_job


def test_basic_ranking():
    """
    Test that basic ranking works with different scores.
    Applications: A=90, B=80, C=70
    Expected: A=Rank 1, B=Rank 2, C=Rank 3
    """
    # Create mock application objects
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, 90.0)
    app_b = MockApp(2, 80.0)
    app_c = MockApp(3, 70.0)
    
    applications = [app_a, app_b, app_c]
    ranked = rank_candidates(applications)
    
    # Verify ranking
    assert len(ranked) == 3
    assert ranked[0]['rank'] == 1
    assert ranked[0]['match_score'] == 90.0
    assert ranked[1]['rank'] == 2
    assert ranked[1]['match_score'] == 80.0
    assert ranked[2]['rank'] == 3
    assert ranked[2]['match_score'] == 70.0


def test_descending_order():
    """
    Test that ranking works with unordered input.
    Input: A=50, B=95, C=75
    Expected: B=Rank 1, C=Rank 2, A=Rank 3
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, 50.0)
    app_b = MockApp(2, 95.0)
    app_c = MockApp(3, 75.0)
    
    applications = [app_a, app_b, app_c]
    ranked = rank_candidates(applications)
    
    # Verify descending order
    assert ranked[0]['match_score'] == 95.0
    assert ranked[1]['match_score'] == 75.0
    assert ranked[2]['match_score'] == 50.0
    assert ranked[0]['rank'] == 1
    assert ranked[1]['rank'] == 2
    assert ranked[2]['rank'] == 3


def test_null_score():
    """
    Test that NULL scores appear after valid scores.
    Applications: A=90, B=NULL, C=70
    Expected: A=Rank 1, C=Rank 2, B=Rank 3
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, 90.0)
    app_b = MockApp(2, None)
    app_c = MockApp(3, 70.0)
    
    applications = [app_a, app_b, app_c]
    ranked = rank_candidates(applications)
    
    # Verify NULL score appears last
    assert ranked[0]['match_score'] == 90.0
    assert ranked[1]['match_score'] == 70.0
    assert ranked[2]['match_score'] is None
    assert ranked[0]['rank'] == 1
    assert ranked[1]['rank'] == 2
    assert ranked[2]['rank'] == 3


def test_same_score():
    """
    Test that tie handling is deterministic using application ID.
    Applications: A=85, B=85, C=70
    Verify: A and B remain adjacent, ordering is deterministic, C is below them.
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, 85.0)
    app_b = MockApp(2, 85.0)
    app_c = MockApp(3, 70.0)
    
    applications = [app_a, app_b, app_c]
    ranked = rank_candidates(applications)
    
    # Verify tie handling (lower ID gets higher rank)
    assert ranked[0]['match_score'] == 85.0
    assert ranked[1]['match_score'] == 85.0
    assert ranked[2]['match_score'] == 70.0
    
    # Verify deterministic ordering (lower ID first)
    assert ranked[0]['application'].id == 1
    assert ranked[1]['application'].id == 2
    assert ranked[2]['application'].id == 3
    
    # Verify ranks
    assert ranked[0]['rank'] == 1
    assert ranked[1]['rank'] == 2
    assert ranked[2]['rank'] == 3


def test_multiple_jobs():
    """
    Test that ranking is calculated independently for different jobs.
    Job A: Candidate 1=90, Candidate 2=80
    Job B: Candidate 3=95, Candidate 4=85
    Verify: Ranking is job-specific, not global.
    """
    class MockApp:
        def __init__(self, id, job_id, match_score):
            self.id = id
            self.job_id = job_id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    # Job A applications
    app1 = MockApp(1, 1, 90.0)
    app2 = MockApp(2, 1, 80.0)
    
    # Job B applications
    app3 = MockApp(3, 2, 95.0)
    app4 = MockApp(4, 2, 85.0)
    
    # Rank Job A applications
    job_a_ranked = rank_candidates([app1, app2])
    
    # Rank Job B applications
    job_b_ranked = rank_candidates([app3, app4])
    
    # Verify Job A ranking
    assert job_a_ranked[0]['match_score'] == 90.0
    assert job_a_ranked[1]['match_score'] == 80.0
    
    # Verify Job B ranking
    assert job_b_ranked[0]['match_score'] == 95.0
    assert job_b_ranked[1]['match_score'] == 85.0
    
    # Verify job-specific ranking (not global)
    # Candidate 3 (95) should NOT be mixed with Job A ranking
    assert all(ranked['application'].job_id == 1 for ranked in job_a_ranked)
    assert all(ranked['application'].job_id == 2 for ranked in job_b_ranked)


def test_empty_application_list():
    """
    Test that empty application list is handled without crashing.
    """
    ranked = rank_candidates([])
    
    assert ranked == []
    assert isinstance(ranked, list)


def test_single_application():
    """
    Test that a single application receives Rank 1.
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app = MockApp(1, 75.0)
    
    ranked = rank_candidates([app])
    
    assert len(ranked) == 1
    assert ranked[0]['rank'] == 1
    assert ranked[0]['match_score'] == 75.0


def test_all_null_scores():
    """
    Test that applications with all NULL scores are handled.
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, None)
    app_b = MockApp(2, None)
    app_c = MockApp(3, None)
    
    applications = [app_a, app_b, app_c]
    ranked = rank_candidates(applications)
    
    # All should be ranked by ID
    assert len(ranked) == 3
    assert ranked[0]['application'].id == 1
    assert ranked[1]['application'].id == 2
    assert ranked[2]['application'].id == 3
    assert all(ranked[i]['match_score'] is None for i in range(3))


def test_mixed_null_and_valid_scores():
    """
    Test that mixed NULL and valid scores are handled correctly.
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, 85.0)
    app_b = MockApp(2, None)
    app_c = MockApp(3, 92.0)
    app_d = MockApp(4, None)
    app_e = MockApp(5, 78.0)
    
    applications = [app_a, app_b, app_c, app_d, app_e]
    ranked = rank_candidates(applications)
    
    # Valid scores should come first, sorted descending
    assert ranked[0]['match_score'] == 92.0
    assert ranked[1]['match_score'] == 85.0
    assert ranked[2]['match_score'] == 78.0
    
    # NULL scores should come last, sorted by ID
    assert ranked[3]['match_score'] is None
    assert ranked[4]['match_score'] is None
    assert ranked[3]['application'].id == 2
    assert ranked[4]['application'].id == 4


def test_return_structure():
    """
    Test that the function returns the expected structure.
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app = MockApp(1, 75.0)
    
    ranked = rank_candidates([app])
    
    # Verify structure
    assert 'application' in ranked[0]
    assert 'rank' in ranked[0]
    assert 'match_score' in ranked[0]
    
    # Verify types
    assert isinstance(ranked[0]['application'], MockApp)
    assert isinstance(ranked[0]['rank'], int)
    assert isinstance(ranked[0]['match_score'], float) or ranked[0]['match_score'] is None


def test_module_import():
    """
    Test that the ranking service can be imported.
    """
    from app.services import rank_candidates
    assert rank_candidates is not None
    assert callable(rank_candidates)


def test_function_signature():
    """
    Test that the rank_candidates function has the correct signature.
    """
    import inspect
    from app.services.ranking_service import rank_candidates
    
    sig = inspect.signature(rank_candidates)
    params = list(sig.parameters.keys())
    
    assert 'applications' in params
    assert len(params) == 1


def test_zero_score():
    """
    Test that zero scores are handled correctly.
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, 0.0)
    app_b = MockApp(2, 50.0)
    app_c = MockApp(3, 25.0)
    
    applications = [app_a, app_b, app_c]
    ranked = rank_candidates(applications)
    
    # Zero score should be treated as a valid score
    assert ranked[0]['match_score'] == 50.0
    assert ranked[1]['match_score'] == 25.0
    assert ranked[2]['match_score'] == 0.0


def test_negative_score():
    """
    Test that negative scores are handled (though they shouldn't occur in practice).
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, -10.0)
    app_b = MockApp(2, 50.0)
    app_c = MockApp(3, 25.0)
    
    applications = [app_a, app_b, app_c]
    ranked = rank_candidates(applications)
    
    # Negative score should still be sorted correctly
    assert ranked[0]['match_score'] == 50.0
    assert ranked[1]['match_score'] == 25.0
    assert ranked[2]['match_score'] == -10.0


def test_rank_applications_by_job():
    """
    Test the convenience function for ranking applications by job.
    """
    from app import create_app, db
    from app.models import Job, Application
    
    app = create_app()
    
    with app.app_context():
        # Create a test job
        job = Job(
            title="Test Job",
            company="Test Company",
            location="Remote",
            description="Test description",
            skills="Python",
            processed_description="test description"
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Rank applications for this job (should be empty)
        ranked = rank_applications_by_job(job.id)
        
        assert ranked == []
        
        # Clean up
        db.session.delete(job)
        db.session.commit()


def test_rank_all_applications_by_job():
    """
    Test the function for ranking all applications grouped by job.
    """
    from app import create_app, db
    from app.models import Job, Application
    
    app = create_app()
    
    with app.app_context():
        # Rank all applications by job
        rankings = rank_all_applications_by_job()
        
        # Should return a dict (may be empty or contain existing applications)
        assert isinstance(rankings, dict)


def test_integration_with_database():
    """
    Integration test for complete ranking pipeline with database.
    """
    from app import create_app, db
    from app.models import Job, Application
    
    app = create_app()
    
    with app.app_context():
        # Create a test job
        job = Job(
            title="Python Developer",
            company="Test Company",
            location="Remote",
            description="Looking for Python developer with Flask and SQL experience.",
            skills="Python, Flask, SQL",
            processed_description="looking python developer flask sql experience"
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Create test applications with different match scores
        app1 = Application(
            job_id=job.id,
            applicant_name="Candidate A",
            applicant_email="a@example.com",
            resume_filename="resume_a.pdf",
            resume_text="Experienced Python developer with Flask and SQL experience.",
            processed_resume_text="experienced python developer flask sql experience",
            match_score=91.50
        )
        
        app2 = Application(
            job_id=job.id,
            applicant_name="Candidate B",
            applicant_email="b@example.com",
            resume_filename="resume_b.pdf",
            resume_text="Python developer with some Flask experience.",
            processed_resume_text="python developer flask experience",
            match_score=84.20
        )
        
        app3 = Application(
            job_id=job.id,
            applicant_name="Candidate C",
            applicant_email="c@example.com",
            resume_filename="resume_c.pdf",
            resume_text="Junior Python developer.",
            processed_resume_text="junior python developer",
            match_score=76.35
        )
        
        db.session.add(app1)
        db.session.add(app2)
        db.session.add(app3)
        db.session.commit()
        
        # Rank applications for this job
        ranked = rank_applications_by_job(job.id)
        
        # Verify ranking
        assert len(ranked) == 3
        assert ranked[0]['rank'] == 1
        assert ranked[0]['match_score'] == 91.50
        assert ranked[0]['application'].applicant_name == "Candidate A"
        
        assert ranked[1]['rank'] == 2
        assert ranked[1]['match_score'] == 84.20
        assert ranked[1]['application'].applicant_name == "Candidate B"
        
        assert ranked[2]['rank'] == 3
        assert ranked[2]['match_score'] == 76.35
        assert ranked[2]['application'].applicant_name == "Candidate C"
        
        # Clean up
        db.session.delete(app1)
        db.session.delete(app2)
        db.session.delete(app3)
        db.session.delete(job)
        db.session.commit()


def test_ranking_stability():
    """
    Test that ranking is stable across multiple calls.
    """
    class MockApp:
        def __init__(self, id, match_score):
            self.id = id
            self.match_score = match_score
            self.final_match_score = None  # New field, None for legacy apps
    
    app_a = MockApp(1, 85.0)
    app_b = MockApp(2, 85.0)
    app_c = MockApp(3, 70.0)
    
    applications = [app_a, app_b, app_c]
    
    # Rank multiple times
    ranked1 = rank_candidates(applications)
    ranked2 = rank_candidates(applications)
    ranked3 = rank_candidates(applications)
    
    # Verify stability
    assert ranked1 == ranked2 == ranked3
