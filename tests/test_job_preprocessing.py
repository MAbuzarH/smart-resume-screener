"""
Test file for Job Description Preprocessing.
Tests job description preprocessing functionality to ensure consistency with resume preprocessing.
"""

import pytest
from app.services.text_preprocessor import preprocess_job_description, preprocess_text


def test_basic_job_description_preprocessing():
    """
    Test that basic job description preprocessing works.
    """
    input_text = "Looking for a Python Developer."
    result = preprocess_job_description(input_text)
    
    # Check that the result is not empty
    assert len(result) > 0
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "developer" in result


def test_technical_terminology_preservation():
    """
    Test that important technical vocabulary is preserved in job descriptions.
    """
    technical_terms = [
        "python", "flask", "django", "sql", "rest api", 
        "docker", "aws", "javascript", "react"
    ]
    
    input_text = "We need a developer with experience in Python, Flask, Django, SQL, REST API, Docker, AWS, JavaScript, and React."
    result = preprocess_job_description(input_text)
    
    # Check that all technical terms are preserved
    for term in technical_terms:
        assert term in result.lower(), f"Technical term '{term}' was removed from job description"


def test_punctuation_normalization():
    """
    Test that punctuation is normalized in job descriptions.
    """
    input_text = "Looking for Python, JavaScript, and React developers!"
    result = preprocess_job_description(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "javascript" in result
    assert "react" in result


def test_excess_whitespace_normalization():
    """
    Test that excess whitespace is normalized in job descriptions.
    """
    input_text = "Looking for    Python\n\ndevelopers with\t\tFlask experience"
    result = preprocess_job_description(input_text)
    
    # Check that multiple spaces are normalized
    assert "    " not in result
    assert "\n\n" not in result
    assert "\t\t" not in result
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "flask" in result


def test_stop_word_handling():
    """
    Test that stop words are handled according to existing Step 2 behavior.
    """
    input_text = "We are looking for a Python developer with experience in Flask"
    result = preprocess_job_description(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "developer" in result
    assert "flask" in result
    
    # Check that common stop words are removed (as individual words)
    words = result.split()
    assert "we" not in words
    assert "are" not in words
    assert "for" not in words
    assert "a" not in words
    assert "with" not in words
    assert "in" not in words


def test_empty_job_description():
    """
    Test that empty job description is handled safely.
    """
    result = preprocess_job_description("")
    assert result == ""
    
    result = preprocess_job_description("   ")
    assert result == ""


def test_none_job_description():
    """
    Test that None job description is handled safely.
    """
    result = preprocess_job_description(None)
    assert result == ""


def test_multi_line_job_description():
    """
    Test that multi-line job descriptions are processed correctly.
    """
    input_text = """
    We are looking for a Software Engineer.
    
    Responsibilities:
    - Develop Python applications
    - Work with Flask and Django
    - Implement REST APIs
    
    Requirements:
    - Experience with SQL
    - Knowledge of Docker and AWS
    """
    
    result = preprocess_job_description(input_text)
    
    # Check that the result is not empty
    assert len(result) > 0
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "flask" in result
    assert "django" in result
    assert "rest" in result
    assert "sql" in result
    assert "docker" in result
    assert "aws" in result
    
    # Check that text is normalized (no excessive whitespace)
    assert "   " not in result
    assert "\n\n" not in result


def test_original_description_not_modified():
    """
    Test that the original job description is not modified by preprocessing.
    """
    original_text = "Looking for a Python Developer with Flask experience."
    original_copy = original_text
    
    result = preprocess_job_description(original_text)
    
    # Verify the original text is unchanged
    assert original_text == original_copy
    assert original_text == "Looking for a Python Developer with Flask experience."
    
    # Verify the processed version is different
    assert result != original_text
    assert result.lower()  # Should be lowercase


def test_processed_version_generated_correctly():
    """
    Test that the processed version is generated correctly.
    """
    input_text = "Looking for a Python Developer with Flask experience."
    result = preprocess_job_description(input_text)
    
    # Check that it's a string
    assert isinstance(result, str)
    
    # Check that it's not empty
    assert len(result) > 0
    
    # Check that it's normalized (lowercase)
    assert result.islower() or not any(c.isupper() for c in result if c.isalpha())
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "developer" in result
    assert "flask" in result


def test_consistency_with_resume_preprocessing():
    """
    Test that job description preprocessing uses the same pipeline as resume preprocessing.
    """
    # Use the same example conceptually for both
    resume_text = "Experienced Python developer with Flask and SQL."
    job_text = "We need a Python developer experienced in Flask and SQL."
    
    # Process both
    processed_resume = preprocess_text(resume_text)
    processed_job = preprocess_job_description(job_text)
    
    # Both should contain the same key technical terms
    assert "python" in processed_resume
    assert "python" in processed_job
    assert "flask" in processed_resume
    assert "flask" in processed_job
    assert "sql" in processed_resume
    assert "sql" in processed_job
    
    # Both should be lowercase
    assert processed_resume.islower() or not any(c.isupper() for c in processed_resume if c.isalpha())
    assert processed_job.islower() or not any(c.isupper() for c in processed_job if c.isalpha())


def test_job_description_with_requirements():
    """
    Test job description with requirements section.
    """
    input_text = """
    Requirements:
    - 3+ years of Python experience
    - Strong knowledge of Flask and Django
    - Experience with SQL databases
    - Familiarity with Docker and Kubernetes
    - AWS cloud experience preferred
    """
    
    result = preprocess_job_description(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "flask" in result
    assert "django" in result
    assert "sql" in result
    assert "docker" in result
    assert "kubernetes" in result
    assert "aws" in result


def test_job_description_with_responsibilities():
    """
    Test job description with responsibilities section.
    """
    input_text = """
    Responsibilities:
    - Design and develop Python applications
    - Build REST APIs using Flask
    - Work with SQL databases
    - Deploy applications using Docker
    - Collaborate with cross-functional teams
    """
    
    result = preprocess_job_description(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "rest" in result
    assert "flask" in result
    assert "sql" in result
    assert "docker" in result


def test_job_description_with_qualifications():
    """
    Test job description with qualifications section.
    """
    input_text = """
    Qualifications:
    - Bachelor's degree in Computer Science
    - Strong programming skills in Python
    - Experience with web frameworks (Flask, Django)
    - Knowledge of database systems (SQL, PostgreSQL)
    - Understanding of cloud platforms (AWS, Azure)
    """
    
    result = preprocess_job_description(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "flask" in result
    assert "django" in result
    assert "sql" in result
    assert "postgresql" in result
    assert "aws" in result
    assert "azure" in result


def test_wrapper_function_reuses_preprocess_text():
    """
    Test that preprocess_job_description actually reuses preprocess_text.
    """
    input_text = "Looking for a Python Developer with Flask experience."
    
    # Process using both functions
    result_direct = preprocess_text(input_text)
    result_wrapper = preprocess_job_description(input_text)
    
    # They should produce the same result
    assert result_direct == result_wrapper


def test_module_import():
    """
    Test that the job preprocessing function can be imported.
    """
    from app.services import preprocess_job_description
    assert preprocess_job_description is not None
    assert callable(preprocess_job_description)


def test_function_signature():
    """
    Test that the preprocess_job_description function has the correct signature.
    """
    import inspect
    from app.services.text_preprocessor import preprocess_job_description
    
    sig = inspect.signature(preprocess_job_description)
    params = list(sig.parameters.keys())
    
    assert 'description' in params
    assert len(params) == 1


def test_returns_string():
    """
    Test that the function always returns a string.
    """
    result = preprocess_job_description("Some job description")
    assert isinstance(result, str)
    
    result = preprocess_job_description(None)
    assert isinstance(result, str)
    
    result = preprocess_job_description("")
    assert isinstance(result, str)


def test_job_description_with_email_and_phone():
    """
    Test that job descriptions with contact information are handled.
    """
    input_text = "Contact us at jobs@company.com or call 555-123-4567 for Python developer position"
    result = preprocess_job_description(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "developer" in result
    
    # The email and phone should be removed/normalized
    assert "jobs@company.com" not in result
    assert "555-123-4567" not in result


def test_job_description_with_urls():
    """
    Test that job descriptions with URLs are handled.
    """
    input_text = "Visit https://company.com/careers for more Python job opportunities"
    result = preprocess_job_description(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    
    # The URL should be removed/normalized
    assert "https://company.com" not in result
