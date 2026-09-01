"""
Test file for Skill Matching Service.
Tests skill extraction, normalization, alias handling, and matching functionality.
"""

import pytest
from app.services.skill_matching_service import (
    calculate_skill_match,
    normalize_skill,
    extract_skills_from_job,
    tokenize_text,
    skill_present_in_text,
    SkillMatchResult
)


def test_basic_skill_matching():
    """
    Test basic skill matching with clear matches.
    Job skills: Python, Flask, SQL, Docker
    Resume: "Python developer with Flask and SQL experience."
    Expected: Matched (Python, Flask, SQL), Missing (Docker), 75%
    """
    job_skills = "Python, Flask, SQL, Docker"
    resume_text = "Python developer with Flask and SQL experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert isinstance(result, SkillMatchResult)
    assert result.required_count == 4
    assert result.matched_count == 3
    assert result.skill_match_percentage == 75.0
    assert "python" in result.matched_skills
    assert "flask" in result.matched_skills
    assert "sql" in result.matched_skills
    assert "docker" in result.missing_skills


def test_all_skills_match():
    """
    Test when all required skills are present.
    Job: Python, Flask, SQL
    Resume: "Python Flask SQL developer."
    Expected: 100%
    """
    job_skills = "Python, Flask, SQL"
    resume_text = "Python Flask SQL developer."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 3
    assert result.matched_count == 3
    assert result.skill_match_percentage == 100.0
    assert len(result.missing_skills) == 0


def test_no_skills_match():
    """
    Test when no required skills are present.
    Job: Python, Flask, SQL
    Resume: "Accounting finance taxation."
    Expected: 0%
    """
    job_skills = "Python, Flask, SQL"
    resume_text = "Accounting finance taxation."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 3
    assert result.matched_count == 0
    assert result.skill_match_percentage == 0.0
    assert len(result.matched_skills) == 0
    assert len(result.missing_skills) == 3


def test_partial_match():
    """
    Test partial skill matching.
    Job: Python, Django, PostgreSQL, Docker, AWS
    Resume: "Python developer with Django and PostgreSQL experience."
    Expected: 3/5 = 60%
    """
    job_skills = "Python, Django, PostgreSQL, Docker, AWS"
    resume_text = "Python developer with Django and PostgreSQL experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 5
    assert result.matched_count == 3
    assert result.skill_match_percentage == 60.0
    assert "python" in result.matched_skills
    assert "django" in result.matched_skills
    assert "postgresql" in result.matched_skills
    assert "docker" in result.missing_skills
    assert "aws" in result.missing_skills


def test_case_insensitivity():
    """
    Test that matching is case-insensitive.
    Job: Python, Flask
    Resume: "PYTHON DEVELOPER WITH FLASK EXPERIENCE."
    Expected: Both skills should match.
    """
    job_skills = "Python, Flask"
    resume_text = "PYTHON DEVELOPER WITH FLASK EXPERIENCE."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 2
    assert result.matched_count == 2
    assert result.skill_match_percentage == 100.0
    assert "python" in result.matched_skills
    assert "flask" in result.matched_skills


def test_whitespace_handling():
    """
    Test that skills with extra whitespace are normalized correctly.
    Job skills: " Python ,  Flask ,  SQL "
    Resume: "Python developer with Flask and SQL experience."
    Expected: All skills should match.
    """
    job_skills = " Python ,  Flask ,  SQL "
    resume_text = "Python developer with Flask and SQL experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 3
    assert result.matched_count == 3
    assert result.skill_match_percentage == 100.0


def test_multi_word_skills():
    """
    Test multi-word skill matching (simplified to word-based).
    Job: Machine Learning, Data Analysis, REST API
    Resume: "Experience in machine learning and REST API development."
    Expected: Machine Learning → Matched (as words), REST API → Matched (as words), Data Analysis → Missing
    """
    job_skills = "Machine Learning, Data Analysis, REST API"
    resume_text = "Experience in machine learning and REST API development."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    # With word-based tokenization, check individual words
    assert result.required_count == 3
    assert result.matched_count >= 2  # Should match at least some words
    assert result.skill_match_percentage > 0


def test_javascript_java_distinction():
    """
    Test that Java does NOT incorrectly match JavaScript.
    Job: Java
    Resume: "JavaScript developer"
    Expected: 0% (Java should not match JavaScript)
    """
    job_skills = "Java"
    resume_text = "JavaScript developer"
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 1
    assert result.matched_count == 0
    assert result.skill_match_percentage == 0.0
    assert "java" in result.missing_skills


def test_skill_alias_javascript():
    """
    Test that skill alias for JavaScript works.
    Job: JavaScript
    Resume: "Experienced JavaScript developer."
    Expected: Matched (direct match)
    """
    job_skills = "JavaScript"
    resume_text = "Experienced JavaScript developer."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 1
    assert result.matched_count == 1
    assert result.skill_match_percentage == 100.0


def test_empty_resume():
    """
    Test that empty resume is handled safely.
    Expected: 0 matched skills, 0% match.
    """
    job_skills = "Python, Flask, SQL"
    resume_text = ""
    
    result = calculate_skill_match(resume_text, job_skills)
    
    # Empty resume returns empty result
    assert result.matched_count == 0
    assert result.skill_match_percentage == 0.0


def test_empty_job_skills():
    """
    Test that empty job skills are handled without division by zero.
    Expected: 0% match, no crash.
    """
    job_skills = ""
    resume_text = "Python developer with Flask experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 0
    assert result.matched_count == 0
    assert result.skill_match_percentage == 0.0


def test_none_inputs():
    """
    Test that None inputs are handled safely.
    """
    result = calculate_skill_match(None, "Python, Flask")
    # With valid job skills but None resume, should process job skills but match 0
    assert result.required_count == 2
    assert result.matched_count == 0
    assert result.skill_match_percentage == 0.0
    
    result = calculate_skill_match("Python developer", None)
    # With None job skills, should return empty result
    assert result.required_count == 0
    assert result.skill_match_percentage == 0.0


def test_realistic_resume_job():
    """
    Test with realistic resume and job description.
    Job skills: Python, Flask, SQL, REST API, Docker, AWS, Git
    Resume: "Software developer with 3 years of experience building Python and Flask applications. Strong SQL knowledge and experience developing REST APIs. Familiar with Git and Docker."
    Expected: Matched skills based on actual presence in resume.
    """
    job_skills = "Python, Flask, SQL, REST API, Docker, AWS, Git"
    resume_text = "Software developer with 3 years of experience building Python and Flask applications. Strong SQL knowledge and experience developing REST APIs. Familiar with Git and Docker."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 7
    assert result.matched_count > 0
    assert result.skill_match_percentage > 0
    assert "python" in result.matched_skills
    assert "flask" in result.matched_skills
    assert "sql" in result.matched_skills
    assert "docker" in result.matched_skills
    assert "git" in result.matched_skills


def test_normalize_skill():
    """
    Test skill normalization function.
    """
    assert normalize_skill("Python") == "python"
    assert normalize_skill("PYTHON") == "python"
    assert normalize_skill(" Flask ") == "flask"
    assert normalize_skill("REST API") == "rest api"
    assert normalize_skill("Machine Learning") == "machine learning"
    assert normalize_skill("JavaScript") == "javascript"
    assert normalize_skill("") == ""
    assert normalize_skill(None) == ""


def test_extract_skills_from_job():
    """
    Test skill extraction from job skills string.
    """
    job_skills = "Python, Flask, SQL, Docker, AWS"
    skills = extract_skills_from_job(job_skills)
    
    assert len(skills) == 5
    assert "python" in skills
    assert "flask" in skills
    assert "sql" in skills
    assert "docker" in skills
    assert "aws" in skills


def test_extract_skills_with_whitespace():
    """
    Test skill extraction with extra whitespace.
    """
    job_skills = " Python ,  Flask ,  SQL "
    skills = extract_skills_from_job(job_skills)
    
    assert len(skills) == 3
    assert "python" in skills
    assert "flask" in skills
    assert "sql" in skills


def test_tokenize_text():
    """
    Test text tokenization.
    """
    text = "Python developer with Flask and SQL experience."
    tokens = tokenize_text(text)
    
    assert len(tokens) > 0
    assert "python" in tokens
    assert "developer" in tokens
    assert "flask" in tokens
    assert "sql" in tokens


def test_tokenize_multi_word_skills():
    """
    Test that text tokenization produces individual words.
    """
    text = "Experience in machine learning and REST API development."
    tokens = tokenize_text(text)
    
    # With simplified tokenization, we get individual words
    assert "machine" in tokens
    assert "learning" in tokens
    assert "rest" in tokens
    assert "api" in tokens


def test_skill_present_in_text():
    """
    Test skill presence checking.
    """
    tokens = ["python", "developer", "flask", "sql", "experience"]
    
    assert skill_present_in_text("python", tokens) == True
    assert skill_present_in_text("flask", tokens) == True
    assert skill_present_in_text("sql", tokens) == True
    assert skill_present_in_text("docker", tokens) == False


def test_skill_present_multi_word():
    """
    Test multi-word skill presence checking (word-based).
    """
    tokens = ["machine", "learning", "rest", "api", "developer"]
    
    # With word-based approach, check for individual words
    assert skill_present_in_text("machine", tokens) == True
    assert skill_present_in_text("learning", tokens) == True
    assert skill_present_in_text("rest", tokens) == True
    assert skill_present_in_text("api", tokens) == True
    assert skill_present_in_text("data", tokens) == False


def test_skill_present_java_javascript():
    """
    Test that Java doesn't match JavaScript.
    """
    tokens = ["javascript", "developer", "react", "node"]
    
    assert skill_present_in_text("java", tokens) == False
    assert skill_present_in_text("javascript", tokens) == True


def test_skill_match_result_structure():
    """
    Test that SkillMatchResult has correct structure.
    """
    job_skills = "Python, Flask"
    resume_text = "Python developer with Flask experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert hasattr(result, 'required_skills')
    assert hasattr(result, 'matched_skills')
    assert hasattr(result, 'missing_skills')
    assert hasattr(result, 'matched_count')
    assert hasattr(result, 'required_count')
    assert hasattr(result, 'skill_match_percentage')
    
    assert isinstance(result.required_skills, list)
    assert isinstance(result.matched_skills, list)
    assert isinstance(result.missing_skills, list)
    assert isinstance(result.matched_count, int)
    assert isinstance(result.required_count, int)
    assert isinstance(result.skill_match_percentage, float)


def test_skill_percentage_rounding():
    """
    Test that skill percentage is rounded to 2 decimal places.
    """
    # Create a scenario that would produce a non-integer percentage
    job_skills = "Python, Flask, SQL"
    resume_text = "Python developer"  # Only 1 out of 3 = 33.33%
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.skill_match_percentage == 33.33


def test_module_import():
    """
    Test that the skill matching service can be imported.
    """
    from app.services import calculate_skill_match, SkillMatchResult
    assert calculate_skill_match is not None
    assert callable(calculate_skill_match)
    assert SkillMatchResult is not None


def test_function_signature():
    """
    Test that calculate_skill_match has the correct signature.
    """
    import inspect
    from app.services.skill_matching_service import calculate_skill_match
    
    sig = inspect.signature(calculate_skill_match)
    params = list(sig.parameters.keys())
    
    assert 'resume_text' in params
    assert 'job_skills' in params
    assert len(params) == 2


def test_duplicate_skills_in_job():
    """
    Test that duplicate skills in job skills are handled.
    """
    job_skills = "Python, Python, Flask, Flask"
    resume_text = "Python developer with Flask experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    # Should handle duplicates (may count as 2 required skills)
    assert result.required_count == 4
    assert result.matched_count == 4  # Both Python and Flask match
    assert result.skill_match_percentage == 100.0


def test_skill_order_independence():
    """
    Test that skill matching is independent of skill order.
    """
    job_skills1 = "Python, Flask, SQL"
    job_skills2 = "SQL, Python, Flask"
    resume_text = "Python developer with Flask and SQL experience."
    
    result1 = calculate_skill_match(resume_text, job_skills1)
    result2 = calculate_skill_match(resume_text, job_skills2)
    
    # Should produce same match count
    assert result1.matched_count == result2.matched_count
    assert result1.skill_match_percentage == result2.skill_match_percentage


def test_single_skill():
    """
    Test with a single required skill.
    """
    job_skills = "Python"
    resume_text = "Python developer with Flask experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 1
    assert result.matched_count == 1
    assert result.skill_match_percentage == 100.0


def test_large_skill_list():
    """
    Test with a large list of skills.
    """
    job_skills = "Python, Flask, Django, SQL, PostgreSQL, Docker, Kubernetes, AWS, Git, REST API, JavaScript, React, Node.js, Redis, MongoDB, GraphQL, TensorFlow, PyTorch, Pandas, NumPy"
    resume_text = "Python developer with Flask and SQL experience using Git for version control."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    assert result.required_count == 20
    assert result.matched_count > 0
    assert result.skill_match_percentage > 0
    assert result.skill_match_percentage < 100


def test_skill_alias_variations():
    """
    Test various skill aliases.
    """
    # Test common variations
    assert normalize_skill("js") == "javascript"
    assert normalize_skill("node") == "node.js"
    assert normalize_skill("reactjs") == "react"
    assert normalize_skill("restful api") == "rest api"
    assert normalize_skill("ml") == "machine learning"
    assert normalize_skill("ai") == "artificial intelligence"
    assert normalize_skill("docker compose") == "docker"
    assert normalize_skill("k8s") == "kubernetes"


def test_skill_with_numbers():
    """
    Test skills that include numbers.
    """
    job_skills = "Python 3, HTML5, CSS3"
    resume_text = "Python 3 developer with HTML5 and CSS3 experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    # Numbers should be preserved or normalized appropriately
    assert result.required_count == 3
    assert result.matched_count > 0


def test_hyphenated_skills():
    """
    Test hyphenated compound skills.
    """
    job_skills = "Co-Working, Self-Driven"
    resume_text = "Experience in co-working environments and self-driven projects."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    # Hyphens should be preserved in normalized form
    assert result.required_count == 2
    assert result.matched_count > 0


def test_skill_result_immutability():
    """
    Test that result lists are separate copies, not references.
    """
    job_skills = "Python, Flask, SQL"
    resume_text = "Python developer with Flask experience."
    
    result = calculate_skill_match(resume_text, job_skills)
    
    # Modify one of the lists
    original_length = len(result.matched_skills)
    result.matched_skills.append("docker")
    
    # Verify it doesn't affect future calls
    result2 = calculate_skill_match(resume_text, job_skills)
    assert len(result2.matched_skills) == original_length
