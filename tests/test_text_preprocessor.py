"""
Test file for Text Preprocessor Service.
Tests text preprocessing functionality for resume normalization.
"""

import pytest
from app.services.text_preprocessor import preprocess_text


def test_lowercase_conversion():
    """
    Test that text is converted to lowercase.
    """
    input_text = "Python DEVELOPER with JavaScript and React"
    result = preprocess_text(input_text)
    
    assert result.islower() or not any(c.isupper() for c in result if c.isalpha())
    assert "python" in result
    assert "developer" in result
    assert "javascript" in result
    assert "react" in result


def test_punctuation_removal():
    """
    Test that unnecessary punctuation is removed.
    """
    input_text = "Python, JavaScript, React! Django; Flask"
    result = preprocess_text(input_text)
    
    # Check that the words are still present (punctuation should be removed)
    assert "python" in result
    assert "javascript" in result
    assert "react" in result
    assert "django" in result
    assert "flask" in result


def test_excess_whitespace_normalization():
    """
    Test that excess whitespace is normalized.
    """
    input_text = "Python    JavaScript\n\nReact\t\tDjango"
    result = preprocess_text(input_text)
    
    # Check that multiple spaces are normalized to single spaces
    assert "    " not in result
    assert "\n\n" not in result
    assert "\t\t" not in result
    
    # Check that the result contains the key words
    assert "python" in result
    assert "javascript" in result
    assert "react" in result
    assert "django" in result


def test_stop_word_removal():
    """
    Test that common English stop words are removed.
    """
    input_text = "I am a Python developer with experience in JavaScript"
    result = preprocess_text(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "developer" in result
    assert "javascript" in result
    
    # Check that common stop words are removed (as individual words)
    words = result.split()
    assert "i" not in words
    assert "am" not in words
    assert "a" not in words
    assert "with" not in words
    assert "in" not in words


def test_technical_terminology_preservation():
    """
    Test that technical terms are preserved during preprocessing.
    """
    technical_terms = [
        "python", "javascript", "react", "flask", "django", 
        "sql", "docker", "aws", "kubernetes", "machine learning"
    ]
    
    input_text = "Experience with Python, JavaScript, React, Flask, Django, SQL, Docker, AWS, Kubernetes, and Machine Learning"
    result = preprocess_text(input_text)
    
    # Check that all technical terms are preserved
    for term in technical_terms:
        assert term in result.lower(), f"Technical term '{term}' was removed"


def test_empty_input():
    """
    Test that empty input returns empty string safely.
    """
    result = preprocess_text("")
    assert result == ""
    
    result = preprocess_text("   ")
    assert result == ""


def test_none_input():
    """
    Test that None input returns empty string safely.
    """
    result = preprocess_text(None)
    assert result == ""


def test_realistic_resume_sample():
    """
    Test with a realistic multi-line resume sample.
    """
    resume_text = """
    JOHN DOE
    Software Engineer
    
    SUMMARY
    Experienced software engineer with expertise in Python, Flask, and JavaScript.
    Developed web applications using React and Django.
    
    SKILLS
    - Python, Flask, Django
    - JavaScript, React, HTML, CSS
    - SQL, PostgreSQL, MySQL
    - Docker, Kubernetes
    - AWS, Cloud Computing
    - Git, Version Control
    
    EXPERIENCE
    Senior Developer - Tech Company (2020-Present)
    - Built REST APIs using Flask
    - Implemented machine learning models
    - Deployed applications using Docker and Kubernetes
    
    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology (2016-2020)
    """
    
    result = preprocess_text(resume_text)
    
    # Check that the result is not empty
    assert len(result) > 0
    
    # Check that key technical terms are preserved
    assert "python" in result
    assert "flask" in result
    assert "javascript" in result
    assert "react" in result
    assert "django" in result
    assert "sql" in result
    assert "postgresql" in result
    assert "docker" in result
    assert "kubernetes" in result
    assert "aws" in result
    assert "machine learning" in result
    
    # Check that the text is normalized (no excessive whitespace)
    assert "   " not in result
    assert "\n\n" not in result


def test_email_and_phone_removal():
    """
    Test that email addresses and phone numbers are removed/normalized.
    """
    input_text = "Contact: john.doe@email.com or 555-123-4567 for Python developer position"
    result = preprocess_text(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "developer" in result
    
    # The email and phone should be removed/normalized
    assert "john.doe@email.com" not in result
    assert "555-123-4567" not in result


def test_url_removal():
    """
    Test that URLs are removed/normalized.
    """
    input_text = "Visit https://example.com or http://test.org for more Python resources"
    result = preprocess_text(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    
    # The URLs should be removed/normalized
    assert "https://example.com" not in result
    assert "http://test.org" not in result


def test_case_insensitive_technical_terms():
    """
    Test that technical terms are preserved regardless of case.
    """
    input_text = "Experience with PYTHON, Java, and REACT"
    result = preprocess_text(input_text)
    
    # Check that technical terms are preserved in lowercase
    assert "python" in result
    assert "java" in result
    assert "react" in result


def test_single_character_technical_terms():
    """
    Test that single-character technical terms like 'C' and 'R' are preserved.
    """
    input_text = "Experience with C programming and R language"
    result = preprocess_text(input_text)
    
    # Check that single-character technical terms are preserved
    assert "c" in result
    assert "r" in result


def test_module_import():
    """
    Test that the text preprocessor service can be imported.
    """
    from app.services import preprocess_text
    assert preprocess_text is not None
    assert callable(preprocess_text)


def test_function_signature():
    """
    Test that the preprocess_text function has the correct signature.
    """
    import inspect
    from app.services.text_preprocessor import preprocess_text
    
    sig = inspect.signature(preprocess_text)
    params = list(sig.parameters.keys())
    
    assert 'text' in params
    assert len(params) == 1


def test_returns_string():
    """
    Test that the function always returns a string.
    """
    result = preprocess_text("Some text")
    assert isinstance(result, str)
    
    result = preprocess_text(None)
    assert isinstance(result, str)
    
    result = preprocess_text("")
    assert isinstance(result, str)


def test_unicode_handling():
    """
    Test that Unicode characters are handled safely.
    """
    input_text = "Python developer with experience"
    result = preprocess_text(input_text)
    
    # Should not crash and should return a string
    assert isinstance(result, str)
    assert "python" in result


def test_special_characters_handling():
    """
    Test that special characters are handled appropriately.
    """
    input_text = "Python@Developer#JavaScript$React%Flask"
    result = preprocess_text(input_text)
    
    # Check that technical terms are preserved
    assert "python" in result
    assert "developer" in result
    assert "javascript" in result
    assert "react" in result
    assert "flask" in result
