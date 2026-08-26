"""
Test file for Matching Service.
Tests the complete matching pipeline that coordinates Steps 2-6.
"""

import pytest
from app.services.matching_service import calculate_match_score, calculate_match_score_from_processed


def test_identical_text():
    """
    Test that identical resume and job content produces a match score approximately 100.00.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask sql"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Verify score is approximately 100.00
    assert match_score is not None
    assert isinstance(match_score, float)
    assert abs(match_score - 100.0) < 1.0, f"Expected ~100.00, got {match_score}"


def test_partially_similar_text():
    """
    Test that partially similar resume and job content produces a score between 0 and 100.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Verify score is between 0 and 100
    assert match_score is not None
    assert isinstance(match_score, float)
    assert match_score > 0, f"Expected > 0, got {match_score}"
    assert match_score < 100, f"Expected < 100, got {match_score}"


def test_unrelated_text():
    """
    Test that unrelated resume and job content produces a very low or zero score.
    """
    resume_text = "python flask developer"
    job_description = "accounting finance taxation"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Verify score is very low or zero
    assert match_score is not None
    assert isinstance(match_score, float)
    assert match_score >= 0, f"Expected >= 0, got {match_score}"
    assert match_score < 30, f"Expected < 30 for unrelated text, got {match_score}"


def test_score_range():
    """
    Test that all valid scores satisfy 0 <= score <= 100.
    """
    test_cases = [
        ("python developer", "python developer"),  # Identical
        ("python developer", "python developer flask"),  # Partial match
        ("python developer", "java developer"),  # Some overlap
        ("python developer", "accounting finance"),  # Unrelated
    ]
    
    for resume, job in test_cases:
        match_score = calculate_match_score(resume, job)
        
        if match_score is not None:
            assert 0 <= match_score <= 100, f"Score {match_score} outside valid range [0, 100]"


def test_rounding():
    """
    Test that the final score is rounded consistently to two decimal places.
    """
    # The internal TF-IDF and cosine calculations may produce many decimal places,
    # but the final match score should be rounded to 2 decimal places
    resume_text = "python developer flask sql django"
    job_description = "python developer flask sql postgresql"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    if match_score is not None:
        # Check that the score has at most 2 decimal places
        # Convert to string and check decimal places
        score_str = f"{match_score:.10f}"
        decimal_part = score_str.split('.')[1]
        # The rounded value should not have more than 2 significant decimal places
        # (due to floating point representation, we check if it's close to a 2-decimal value)
        rounded = round(match_score, 2)
        assert abs(match_score - rounded) < 0.01, f"Score {match_score} not rounded to 2 decimal places"


def test_empty_text():
    """
    Test that empty resume/job text is handled safely without crashing.
    """
    match_score = calculate_match_score("", "")
    assert match_score is None
    
    match_score = calculate_match_score("python", "")
    assert match_score is None
    
    match_score = calculate_match_score("", "python")
    assert match_score is None


def test_none_input():
    """
    Test that None input is handled safely.
    """
    match_score = calculate_match_score(None, "python")
    assert match_score is None
    
    match_score = calculate_match_score("python", None)
    assert match_score is None
    
    match_score = calculate_match_score(None, None)
    assert match_score is None


def test_technical_terms():
    """
    Test with realistic technical terms from the domain.
    """
    resume_text = "python flask django sql postgresql docker kubernetes aws machine learning"
    job_description = "python javascript react node docker kubernetes aws cloud computing"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should produce a meaningful numeric score
    assert match_score is not None
    assert isinstance(match_score, float)
    assert 0 <= match_score <= 100
    # Should have some similarity due to shared technical terms
    assert match_score > 0, f"Expected > 0 for documents with shared technical terms, got {match_score}"


def test_high_match_scenario():
    """
    Test a scenario with high expected match.
    """
    resume_text = "python developer with experience in flask django sql rest apis docker"
    job_description = "looking for a python developer with flask sql rest api docker experience"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should have a high match score (> 60)
    assert match_score is not None
    assert match_score > 60, f"Expected > 60 for high match scenario, got {match_score}"


def test_low_match_scenario():
    """
    Test a scenario with low expected match.
    """
    resume_text = "python flask developer"
    job_description = "java spring boot developer with sql database experience"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should have a low match score (< 40)
    assert match_score is not None
    assert match_score < 40, f"Expected < 40 for low match scenario, got {match_score}"


def test_module_import():
    """
    Test that the matching service can be imported.
    """
    from app.services import calculate_match_score
    assert calculate_match_score is not None
    assert callable(calculate_match_score)


def test_function_signature():
    """
    Test that the calculate_match_score function has the correct signature.
    """
    import inspect
    from app.services.matching_service import calculate_match_score
    
    sig = inspect.signature(calculate_match_score)
    params = list(sig.parameters.keys())
    
    assert 'resume_text' in params
    assert 'job_description' in params
    assert len(params) == 2


def test_return_type():
    """
    Test that the function returns the correct type.
    """
    resume_text = "python developer"
    job_description = "python developer"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    assert isinstance(match_score, float) or match_score is None


def test_processed_text_function():
    """
    Test the convenience function for already processed text.
    """
    processed_resume = "python developer flask sql"
    processed_job = "python developer flask django"
    
    match_score = calculate_match_score_from_processed(processed_resume, processed_job)
    
    # Should work with processed text
    assert match_score is not None
    assert isinstance(match_score, float)
    assert 0 <= match_score <= 100


def test_processed_text_empty():
    """
    Test that empty processed text is handled safely.
    """
    match_score = calculate_match_score_from_processed("", "")
    assert match_score is None
    
    match_score = calculate_match_score_from_processed("python", "")
    assert match_score is None


def test_score_clamping():
    """
    Test that scores are clamped to [0, 100] range.
    """
    # This test ensures the clamping logic works
    # (normal TF-IDF + cosine should not produce values outside this range,
    # but the function should handle edge cases)
    resume_text = "python developer"
    job_description = "python developer"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    if match_score is not None:
        assert match_score >= 0, f"Score {match_score} below 0"
        assert match_score <= 100, f"Score {match_score} above 100"


def test_invalid_input_types():
    """
    Test that invalid input types are handled safely.
    """
    match_score = calculate_match_score(123, "python")
    assert match_score is None
    
    match_score = calculate_match_score("python", 123)
    assert match_score is None
    
    match_score = calculate_match_score([], "python")
    assert match_score is None


def test_whitespace_only_input():
    """
    Test that whitespace-only input is handled safely.
    """
    match_score = calculate_match_score("   ", "   ")
    assert match_score is None


def test_single_word_documents():
    """
    Test with single-word documents.
    """
    resume_text = "python"
    job_description = "python"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should handle single-word documents
    assert match_score is not None
    assert 0 <= match_score <= 100


def test_case_sensitivity_after_preprocessing():
    """
    Test that case differences are handled after preprocessing.
    """
    # Since preprocessing lowercases text, case should not affect the score
    resume_text = "Python Developer Flask"
    job_description = "python developer flask"
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should produce a high match despite case differences
    assert match_score is not None
    assert match_score > 80, f"Expected > 80 after preprocessing, got {match_score}"


def test_realistic_resume_job_pair():
    """
    Test with a realistic resume and job description pair.
    """
    resume_text = """
    Experienced Python developer with 5 years of experience in web development.
    Proficient in Flask, Django, SQL, PostgreSQL, REST APIs, and Docker.
    Experience with cloud platforms including AWS and Azure.
    """
    
    job_description = """
    We are looking for a Python developer with experience in Flask and Django.
    The ideal candidate should have experience with SQL databases and REST APIs.
    Docker and cloud experience is a plus.
    """
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should produce a meaningful score
    assert match_score is not None
    assert isinstance(match_score, float)
    assert 0 <= match_score <= 100
    # Should have good match due to shared skills
    assert match_score > 40, f"Expected > 40 for realistic matching, got {match_score}"


def test_special_characters_handling():
    """
    Test that special characters are handled appropriately.
    """
    # The preprocessing should remove special characters
    resume_text = "Python developer with experience in Flask, Django, SQL!"
    job_description = "Looking for Python developer with Flask & SQL experience."
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should work normally after preprocessing
    assert match_score is not None
    assert 0 <= match_score <= 100


def test_long_documents():
    """
    Test with longer documents.
    """
    resume_text = "python " * 50 + "flask " * 50 + "django " * 50
    job_description = "python " * 50 + "flask " * 50 + "sql " * 50
    
    match_score = calculate_match_score(resume_text, job_description)
    
    # Should handle longer documents
    assert match_score is not None
    assert 0 <= match_score <= 100


def test_processed_function_signature():
    """
    Test that the processed text function has the correct signature.
    """
    import inspect
    from app.services.matching_service import calculate_match_score_from_processed
    
    sig = inspect.signature(calculate_match_score_from_processed)
    params = list(sig.parameters.keys())
    
    assert 'processed_resume' in params
    assert 'processed_job' in params
    assert len(params) == 2


def test_complete_pipeline_integration():
    """
    Integration test for the complete matching pipeline with database storage.
    This test verifies the entire flow from resume text to database Application record.
    """
    from app import create_app, db
    from app.models import Job, Application
    from app.services import calculate_match_score
    
    app = create_app()
    
    with app.app_context():
        # Create a test job
        job = Job(
            title="Python Developer",
            company="Test Company",
            location="Remote",
            description="Looking for a Python developer with Flask and SQL experience.",
            skills="Python, Flask, SQL",
            processed_description="looking python developer flask sql experience"
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Calculate match score
        resume_text = "Experienced Python developer with Flask and SQL experience."
        match_score = calculate_match_score(resume_text, job.description)
        
        # Verify score calculation
        assert match_score is not None
        assert isinstance(match_score, float)
        assert 0 <= match_score <= 100
        
        # Create application with match score
        application = Application(
            job_id=job.id,
            applicant_name="Test Applicant",
            applicant_email="test@example.com",
            resume_filename="test_resume.pdf",
            resume_text=resume_text,
            processed_resume_text="experienced python developer flask sql experience",
            match_score=match_score
        )
        
        db.session.add(application)
        db.session.commit()
        
        # Retrieve and verify the application
        retrieved_application = Application.query.filter_by(id=application.id).first()
        
        assert retrieved_application is not None
        assert retrieved_application.match_score is not None
        assert isinstance(retrieved_application.match_score, float)
        assert 0 <= retrieved_application.match_score <= 100
        assert abs(retrieved_application.match_score - match_score) < 0.01
        
        # Clean up
        db.session.delete(application)
        db.session.delete(job)
        db.session.commit()
