"""
Test file for Screening Service.
Tests candidate screening analysis, categories, and explanation generation.
"""

import pytest
from app.services.screening_service import (
    analyze_candidate,
    get_screening_category,
    generate_explanation,
    ScreeningResult,
    get_screening_thresholds
)


def test_strong_match_category():
    """
    Test strong match category.
    Final score: 85
    Expected: Strong Match
    """
    category = get_screening_category(85.0)
    assert category == "Strong Match"


def test_moderate_match_category():
    """
    Test moderate match category.
    Final score: 70
    Expected: Moderate Match
    """
    category = get_screening_category(70.0)
    assert category == "Moderate Match"


def test_low_match_category():
    """
    Test low match category.
    Final score: 45
    Expected: Low Match
    """
    category = get_screening_category(45.0)
    assert category == "Low Match"


def test_exact_80_boundary():
    """
    Test exact 80 boundary.
    Final score: 80
    Expected: Strong Match (>= 80)
    """
    category = get_screening_category(80.0)
    assert category == "Strong Match"


def test_exact_60_boundary():
    """
    Test exact 60 boundary.
    Final score: 60
    Expected: Moderate Match (>= 60)
    """
    category = get_screening_category(60.0)
    assert category == "Moderate Match"


def test_score_100():
    """
    Test maximum score.
    Final score: 100
    Expected: Strong Match
    """
    category = get_screening_category(100.0)
    assert category == "Strong Match"


def test_score_0():
    """
    Test minimum score.
    Final score: 0
    Expected: Low Match
    """
    category = get_screening_category(0.0)
    assert category == "Low Match"


def test_null_score():
    """
    Test NULL score handling.
    Final score: None
    Expected: Not Scored
    """
    category = get_screening_category(None)
    assert category == "Not Scored"


def test_explanation_strong_match():
    """
    Test explanation generation for strong match.
    """
    explanation = generate_explanation(
        "Strong Match",
        85.0,
        90.0,
        4,
        5,
        ["git"]
    )
    
    assert "Strong Match" in explanation
    assert "human review" in explanation.lower()
    assert len(explanation) > 0


def test_explanation_moderate_match():
    """
    Test explanation generation for moderate match.
    """
    explanation = generate_explanation(
        "Moderate Match",
        70.0,
        65.0,
        3,
        5,
        ["docker", "aws"]
    )
    
    assert "Moderate Match" in explanation
    assert "human review" in explanation.lower()
    assert len(explanation) > 0


def test_explanation_low_match():
    """
    Test explanation generation for low match.
    """
    explanation = generate_explanation(
        "Low Match",
        40.0,
        30.0,
        1,
        5,
        ["python", "flask", "sql"]
    )
    
    assert "Low Match" in explanation
    assert "human review" in explanation.lower()
    assert len(explanation) > 0


def test_explanation_not_scored():
    """
    Test explanation generation for not scored.
    """
    explanation = generate_explanation(
        "Not Scored",
        None,
        None,
        0,
        0,
        []
    )
    
    assert "not been scored" in explanation.lower()
    assert len(explanation) > 0


def test_screening_thresholds():
    """
    Test that screening thresholds are correctly configured.
    """
    thresholds = get_screening_thresholds()
    
    assert 'strong_match_threshold' in thresholds
    assert 'moderate_match_threshold' in thresholds
    assert thresholds['strong_match_threshold'] == 80.0
    assert thresholds['moderate_match_threshold'] == 60.0


def test_empty_skills():
    """
    Test handling of empty skills.
    """
    explanation = generate_explanation(
        "Low Match",
        30.0,
        0.0,
        0,
        0,
        []
    )
    
    assert len(explanation) > 0
    assert "Low Match" in explanation


def test_invalid_score_handling():
    """
    Test handling of invalid scores.
    """
    # Negative score
    category = get_screening_category(-10.0)
    assert category == "Not Scored"
    
    # Score above 100
    category = get_screening_category(150.0)
    assert category == "Not Scored"
    
    # String score
    category = get_screening_category("invalid")
    assert category == "Not Scored"


def test_no_fabricated_scores():
    """
    Test that no scores are fabricated when data is missing.
    """
    # Create mock application with no scores
    class MockApp:
        def __init__(self):
            self.id = 1
            self.final_match_score = None
            self.similarity_score = None
            self.match_score = None
            self.skill_match_score = None
            self.resume_text = None
    
    class MockJob:
        def __init__(self):
            self.id = 1
            self.skills = "Python, Flask, SQL"
    
    app = MockApp()
    job = MockJob()
    
    result = analyze_candidate(app, job)
    
    assert result.final_score is None
    assert result.tfidf_score is None
    assert result.skill_score is None
    assert result.category == "Not Scored"
    assert "not been scored" in result.explanation.lower()


def test_result_structure():
    """
    Test that ScreeningResult has correct structure.
    """
    class MockApp:
        def __init__(self):
            self.id = 1
            self.final_match_score = 85.0
            self.similarity_score = 80.0
            self.match_score = 80.0
            self.skill_match_score = 90.0
            self.resume_text = "Python developer with Flask experience"
    
    class MockJob:
        def __init__(self):
            self.id = 1
            self.skills = "Python, Flask, SQL"
    
    app = MockApp()
    job = MockJob()
    
    result = analyze_candidate(app, job)
    
    assert hasattr(result, 'final_score')
    assert hasattr(result, 'tfidf_score')
    assert hasattr(result, 'skill_score')
    assert hasattr(result, 'matched_skills')
    assert hasattr(result, 'missing_skills')
    assert hasattr(result, 'required_skill_count')
    assert hasattr(result, 'matched_skill_count')
    assert hasattr(result, 'skill_match_percentage')
    assert hasattr(result, 'category')
    assert hasattr(result, 'explanation')


def test_module_import():
    """
    Test that the screening service can be imported.
    """
    from app.services import analyze_candidate, ScreeningResult, get_screening_category, get_screening_thresholds
    assert analyze_candidate is not None
    assert callable(analyze_candidate)
    assert ScreeningResult is not None
    assert get_screening_category is not None
    assert callable(get_screening_category)
    assert get_screening_thresholds is not None
    assert callable(get_screening_thresholds)


def test_function_signature():
    """
    Test that analyze_candidate has the correct signature.
    """
    import inspect
    from app.services.screening_service import analyze_candidate
    
    sig = inspect.signature(analyze_candidate)
    params = list(sig.parameters.keys())
    
    assert 'application' in params
    assert 'job' in params
    assert len(params) == 2


def test_score_rounding():
    """
    Test that scores are rounded to 2 decimal places.
    """
    class MockApp:
        def __init__(self):
            self.id = 1
            self.final_match_score = 85.456789
            self.similarity_score = 80.123456
            self.match_score = 80.123456
            self.skill_match_score = 90.987654
            self.resume_text = "Python developer with Flask experience"
    
    class MockJob:
        def __init__(self):
            self.id = 1
            self.skills = "Python, Flask, SQL"
    
    app = MockApp()
    job = MockJob()
    
    result = analyze_candidate(app, job)
    
    # Check that scores are rounded to 2 decimal places
    if result.final_score is not None:
        assert len(str(result.final_score).split('.')[-1]) <= 2
    if result.tfidf_score is not None:
        assert len(str(result.tfidf_score).split('.')[-1]) <= 2
    if result.skill_score is not None:
        assert len(str(result.skill_score).split('.')[-1]) <= 2


def test_explanation_factuality():
    """
    Test that explanations are factual and based on actual values.
    """
    # Test that explanation doesn't claim missing skills when none are missing
    explanation = generate_explanation(
        "Strong Match",
        90.0,
        100.0,
        5,
        5,
        []  # No missing skills
    )
    
    # Should not mention missing skills
    assert "missing" not in explanation.lower() or "no missing" in explanation.lower()
    
    # Test that explanation doesn't claim matched skills when none are matched
    explanation = generate_explanation(
        "Low Match",
        30.0,
        0.0,
        0,
        5,
        ["python", "flask", "sql", "docker", "aws"]
    )
    
    # Should acknowledge no matched skills
    assert "none" in explanation.lower() or "no" in explanation.lower()


def test_boundary_conditions():
    """
    Test boundary conditions for categories.
    """
    # Just above strong threshold
    assert get_screening_category(80.01) == "Strong Match"
    
    # Just below strong threshold
    assert get_screening_category(79.99) == "Moderate Match"
    
    # Just above moderate threshold
    assert get_screening_category(60.01) == "Moderate Match"
    
    # Just below moderate threshold
    assert get_screening_category(59.99) == "Low Match"


def test_explanation_length():
    """
    Test that explanations are concise but informative.
    """
    explanation = generate_explanation(
        "Moderate Match",
        70.0,
        65.0,
        3,
        5,
        ["docker", "aws"]
    )
    
    # Should be reasonable length (not too short, not too long)
    assert 50 < len(explanation) < 500


def test_no_hiring_decisions():
    """
    Test that explanations don't make automatic hiring decisions.
    """
    prohibited_phrases = [
        "should be hired",
        "reject this candidate",
        "definitely qualified",
        "unsuitable",
        "automatic hiring",
        "automatic rejection"
    ]
    
    explanation = generate_explanation(
        "Strong Match",
        90.0,
        95.0,
        5,
        5,
        []
    )
    
    explanation_lower = explanation.lower()
    for phrase in prohibited_phrases:
        assert phrase not in explanation_lower, f"Found prohibited phrase: {phrase}"


def test_explanation_uses_correct_categories():
    """
    Test that explanations use the correct category names for scored applications.
    """
    for category in ["Strong Match", "Moderate Match", "Low Match"]:
        explanation = generate_explanation(
            category,
            50.0,
            50.0,
            2,
            4,
            ["skill1", "skill2"]
        )
        assert category in explanation
    
    # Not Scored has a different explanation
    explanation = generate_explanation(
        "Not Scored",
        None,
        None,
        0,
        0,
        []
    )
    assert "not been scored" in explanation.lower()