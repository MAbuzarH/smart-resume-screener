"""
Integration test for the complete Smart Resume Scanner workflow.
Tests the entire pipeline from job creation to candidate analysis.
"""

import pytest
import os
from app import create_app, db
from app.models import Job, Application
from app.services import (
    extract_text_from_pdf,
    preprocess_text,
    calculate_match_score,
    calculate_skill_match,
    calculate_final_score,
    rank_applications_by_job,
    analyze_candidate,
    get_screening_category
)


def test_complete_workflow_integration():
    """
    Test the complete workflow from job creation to candidate analysis.
    This integration test verifies that all components work together.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Step 1: Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='We are looking for a Python developer with experience in Flask, SQL, and Git.',
            skills='Python, Flask, SQL, Git'
        )
        db.session.add(job)
        db.session.commit()
        
        # Step 2: Simulate resume text (in real scenario, this would come from PDF extraction)
        resume_text = '''
        John Doe
        john.doe@example.com
        
        EXPERIENCE
        Python Developer at Tech Corp (2020-2023)
        - Developed web applications using Python and Flask
        - Worked with SQL databases
        - Used Git for version control
        
        SKILLS
        Python, Flask, SQL, Git, REST API, AWS
        '''
        
        # Step 3: Preprocess resume text
        processed_resume = preprocess_text(resume_text)
        assert processed_resume is not None
        assert len(processed_resume) > 0
        
        # Step 4: Preprocess job description
        processed_job = preprocess_text(job.description)
        assert processed_job is not None
        assert len(processed_job) > 0
        
        # Step 5: Calculate TF-IDF match score
        tfidf_score = calculate_match_score(resume_text, job.description)
        assert tfidf_score is not None
        assert 0 <= tfidf_score <= 100
        
        # Step 6: Calculate skill match
        skill_result = calculate_skill_match(resume_text, job.skills)
        assert skill_result is not None
        assert 0 <= skill_result.skill_match_percentage <= 100
        assert skill_result.matched_count > 0
        assert skill_result.required_count > 0
        
        # Step 7: Calculate weighted final score
        final_score_result = calculate_final_score(tfidf_score, skill_result.skill_match_percentage)
        assert final_score_result is not None
        assert 0 <= final_score_result.final_score <= 100
        assert final_score_result.tfidf_weight == 0.40
        assert final_score_result.skill_weight == 0.60
        
        # Step 8: Create application with scores
        application = Application(
            job_id=job.id,
            applicant_name='John Doe',
            applicant_email='john.doe@example.com',
            resume_filename='test_resume.pdf',
            resume_text=resume_text,
            processed_resume_text=processed_resume,
            match_score=tfidf_score,
            similarity_score=tfidf_score,
            skill_match_score=skill_result.skill_match_percentage,
            final_match_score=final_score_result.final_score
        )
        db.session.add(application)
        db.session.commit()
        
        # Step 9: Verify application was saved
        saved_application = Application.query.get(application.id)
        assert saved_application is not None
        assert saved_application.final_match_score == final_score_result.final_score
        
        # Step 10: Test ranking
        ranked_candidates = rank_applications_by_job(job.id)
        assert len(ranked_candidates) == 1
        assert ranked_candidates[0]['application'].id == application.id
        assert ranked_candidates[0]['final_match_score'] == final_score_result.final_score
        
        # Step 11: Test screening category
        category = get_screening_category(final_score_result.final_score)
        assert category in ['Strong Match', 'Moderate Match', 'Low Match']
        
        # Step 12: Test candidate analysis
        screening_result = analyze_candidate(saved_application, job)
        assert screening_result is not None
        assert screening_result.final_score == final_score_result.final_score
        assert screening_result.category == category
        assert screening_result.matched_skill_count == skill_result.matched_count
        assert screening_result.required_skill_count == skill_result.required_count
        assert len(screening_result.matched_skills) > 0
        assert len(screening_result.explanation) > 0
        
        # Verify the screening category matches the threshold
        if final_score_result.final_score >= 80:
            assert screening_result.category == 'Strong Match'
        elif final_score_result.final_score >= 60:
            assert screening_result.category == 'Moderate Match'
        else:
            assert screening_result.category == 'Low Match'


def test_scoring_formula_correctness():
    """
    Test that the weighted scoring formula is mathematically correct.
    """
    # Test case 1: Both scores 100
    result = calculate_final_score(100.0, 100.0)
    expected = (100.0 * 0.40) + (100.0 * 0.60)
    assert abs(result.final_score - expected) < 0.01
    
    # Test case 2: Both scores 0
    result = calculate_final_score(0.0, 0.0)
    expected = (0.0 * 0.40) + (0.0 * 0.60)
    assert abs(result.final_score - expected) < 0.01
    
    # Test case 3: TF-IDF 100, Skill 0
    result = calculate_final_score(100.0, 0.0)
    expected = (100.0 * 0.40) + (0.0 * 0.60)
    assert abs(result.final_score - expected) < 0.01
    
    # Test case 4: TF-IDF 0, Skill 100
    result = calculate_final_score(0.0, 100.0)
    expected = (0.0 * 0.40) + (100.0 * 0.60)
    assert abs(result.final_score - expected) < 0.01
    
    # Test case 5: Realistic values
    result = calculate_final_score(75.0, 85.0)
    expected = (75.0 * 0.40) + (85.0 * 0.60)
    assert abs(result.final_score - expected) < 0.01


def test_ranking_order_with_multiple_candidates():
    """
    Test that candidates are ranked in correct order with multiple candidates.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create a job
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask'
        )
        db.session.add(job)
        db.session.commit()
        
        # Create applications with different scores
        app1 = Application(
            job_id=job.id,
            applicant_name='High Score',
            applicant_email='high@test.com',
            resume_filename='resume1.pdf',
            resume_text='Text',
            processed_resume_text='text',
            match_score=90.0,
            similarity_score=90.0,
            skill_match_score=95.0,
            final_match_score=93.0
        )
        
        app2 = Application(
            job_id=job.id,
            applicant_name='Medium Score',
            applicant_email='medium@test.com',
            resume_filename='resume2.pdf',
            resume_text='Text',
            processed_resume_text='text',
            match_score=70.0,
            similarity_score=70.0,
            skill_match_score=75.0,
            final_match_score=73.0
        )
        
        app3 = Application(
            job_id=job.id,
            applicant_name='Low Score',
            applicant_email='low@test.com',
            resume_filename='resume3.pdf',
            resume_text='Text',
            processed_resume_text='text',
            match_score=50.0,
            similarity_score=50.0,
            skill_match_score=55.0,
            final_match_score=53.0
        )
        
        app4 = Application(
            job_id=job.id,
            applicant_name='No Score',
            applicant_email='noscore@test.com',
            resume_filename='resume4.pdf',
            resume_text='Text',
            processed_resume_text='text',
            match_score=None,
            similarity_score=None,
            skill_match_score=None,
            final_match_score=None
        )
        
        db.session.add_all([app1, app2, app3, app4])
        db.session.commit()
        
        # Test ranking
        ranked = rank_applications_by_job(job.id)
        assert len(ranked) == 4
        
        # Verify order (highest score first, NULL last)
        assert ranked[0]['final_match_score'] == 93.0
        assert ranked[1]['final_match_score'] == 73.0
        assert ranked[2]['final_match_score'] == 53.0
        assert ranked[3]['final_match_score'] is None
        
        # Verify ranks
        assert ranked[0]['rank'] == 1
        assert ranked[1]['rank'] == 2
        assert ranked[2]['rank'] == 3
        assert ranked[3]['rank'] == 4
        
        # Verify correct applications
        assert ranked[0]['application'].applicant_name == 'High Score'
        assert ranked[1]['application'].applicant_name == 'Medium Score'
        assert ranked[2]['application'].applicant_name == 'Low Score'
        assert ranked[3]['application'].applicant_name == 'No Score'


def test_screening_threshold_boundaries():
    """
    Test screening category boundaries.
    """
    # Test exact boundaries
    assert get_screening_category(80.0) == 'Strong Match'
    assert get_screening_category(79.99) == 'Moderate Match'
    assert get_screening_category(60.0) == 'Moderate Match'
    assert get_screening_category(59.99) == 'Low Match'
    assert get_screening_category(100.0) == 'Strong Match'
    assert get_screening_category(0.0) == 'Low Match'
    assert get_screening_category(None) == 'Not Scored'
    
    # Test ranges
    assert get_screening_category(85.0) == 'Strong Match'
    assert get_screening_category(70.0) == 'Moderate Match'
    assert get_screening_category(40.0) == 'Low Match'


def test_null_score_handling():
    """
    Test that NULL scores are handled gracefully throughout the pipeline.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask'
        )
        db.session.add(job)
        db.session.commit()
        
        # Create application with NULL scores
        application = Application(
            job_id=job.id,
            applicant_name='Test Candidate',
            applicant_email='test@test.com',
            resume_filename='resume.pdf',
            resume_text='Text',
            processed_resume_text='text',
            match_score=None,
            similarity_score=None,
            skill_match_score=None,
            final_match_score=None
        )
        db.session.add(application)
        db.session.commit()
        
        # Test that screening analysis handles NULL gracefully
        screening = analyze_candidate(application, job)
        assert screening is not None
        assert screening.final_score is None
        assert screening.category == 'Not Scored'
        assert 'not been scored' in screening.explanation.lower()
        
        # Test that ranking handles NULL gracefully
        ranked = rank_applications_by_job(job.id)
        assert len(ranked) == 1
        assert ranked[0]['final_match_score'] is None


def test_components_persist_separately():
    """
    Test that component scores are persisted separately and not combined.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        job = Job(
            title='Software Engineer',
            company='Test Company',
            location='Test Location',
            description='Test description',
            skills='Python, Flask'
        )
        db.session.add(job)
        db.session.commit()
        
        application = Application(
            job_id=job.id,
            applicant_name='Test Candidate',
            applicant_email='test@test.com',
            resume_filename='resume.pdf',
            resume_text='Text',
            processed_resume_text='text',
            match_score=75.0,
            similarity_score=75.0,
            skill_match_score=85.0,
            final_match_score=81.0
        )
        db.session.add(application)
        db.session.commit()
        
        # Verify all scores are stored separately
        saved = Application.query.get(application.id)
        assert saved.match_score == 75.0
        assert saved.similarity_score == 75.0
        assert saved.skill_match_score == 85.0
        assert saved.final_match_score == 81.0
        
        # Verify they can be accessed independently
        assert saved.match_score is not None
        assert saved.similarity_score is not None
        assert saved.skill_match_score is not None
        assert saved.final_match_score is not None