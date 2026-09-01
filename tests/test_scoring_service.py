"""
Test file for Scoring Service.
Tests weighted final scoring functionality, validation, and edge cases.
"""

import pytest
import math
from app.services.scoring_service import (
    calculate_final_score,
    calculate_final_score_from_raw,
    FinalScoreResult,
    validate_score_range,
    get_scoring_weights,
    validate_weights
)


def test_basic_weighted_score():
    """
    Test basic weighted score calculation.
    TF-IDF = 80, Skill = 90
    Expected: 86 (80 × 0.40 + 90 × 0.60 = 32 + 54 = 86)
    """
    tfidf_score = 80.0
    skill_score = 90.0
    
    result = calculate_final_score(tfidf_score, skill_score)
    
    assert isinstance(result, FinalScoreResult)
    assert result.tfidf_score == 80.0
    assert result.skill_score == 90.0
    assert result.tfidf_weight == 0.40
    assert result.skill_weight == 0.60
    assert result.final_score == 86.0


def test_both_scores_100():
    """
    Test when both scores are 100.
    TF-IDF = 100, Skill = 100
    Expected: 100 (100 × 0.40 + 100 × 0.60 = 40 + 60 = 100)
    """
    tfidf_score = 100.0
    skill_score = 100.0
    
    result = calculate_final_score(tfidf_score, skill_score)
    
    assert result.final_score == 100.0
    assert result.tfidf_score == 100.0
    assert result.skill_score == 100.0


def test_both_scores_0():
    """
    Test when both scores are 0.
    TF-IDF = 0, Skill = 0
    Expected: 0 (0 × 0.40 + 0 × 0.60 = 0 + 0 = 0)
    """
    tfidf_score = 0.0
    skill_score = 0.0
    
    result = calculate_final_score(tfidf_score, skill_score)
    
    assert result.final_score == 0.0
    assert result.tfidf_score == 0.0
    assert result.skill_score == 0.0


def test_only_tfidf():
    """
    Test when only TF-IDF score is present.
    TF-IDF = 100, Skill = 0
    Expected: 40 (100 × 0.40 + 0 × 0.60 = 40 + 0 = 40)
    """
    tfidf_score = 100.0
    skill_score = 0.0
    
    result = calculate_final_score(tfidf_score, skill_score)
    
    assert result.final_score == 40.0
    assert result.tfidf_score == 100.0
    assert result.skill_score == 0.0


def test_only_skill_match():
    """
    Test when only skill match is present.
    TF-IDF = 0, Skill = 100
    Expected: 60 (0 × 0.40 + 100 × 0.60 = 0 + 60 = 60)
    """
    tfidf_score = 0.0
    skill_score = 100.0
    
    result = calculate_final_score(tfidf_score, skill_score)
    
    assert result.final_score == 60.0
    assert result.tfidf_score == 0.0
    assert result.skill_score == 100.0


def test_realistic_score():
    """
    Test realistic score calculation.
    TF-IDF = 78.50, Skill = 85.00
    Expected: 82.40 (78.50 × 0.40 + 85.00 × 0.60 = 31.40 + 51.00 = 82.40)
    """
    tfidf_score = 78.50
    skill_score = 85.00
    
    result = calculate_final_score(tfidf_score, skill_score)
    
    expected_final = (78.50 * 0.40) + (85.00 * 0.60)
    assert abs(result.final_score - expected_final) < 0.01
    assert result.tfidf_score == 78.50
    assert result.skill_score == 85.00


def test_score_range_validation():
    """
    Test that final score is within valid range [0, 100].
    """
    # Test maximum range
    result = calculate_final_score(100.0, 100.0)
    assert 0 <= result.final_score <= 100
    
    # Test minimum range
    result = calculate_final_score(0.0, 0.0)
    assert 0 <= result.final_score <= 100
    
    # Test mid-range
    result = calculate_final_score(50.0, 50.0)
    assert 0 <= result.final_score <= 100


def test_invalid_input_none():
    """
    Test handling of None inputs.
    """
    result = calculate_final_score(None, 90.0)
    assert result.tfidf_score == 0.0
    assert result.skill_score == 90.0
    assert result.final_score == 54.0  # 0 × 0.40 + 90 × 0.60
    
    result = calculate_final_score(80.0, None)
    assert result.tfidf_score == 80.0
    assert result.skill_score == 0.0
    assert result.final_score == 32.0  # 80 × 0.40 + 0 × 0.60
    
    result = calculate_final_score(None, None)
    assert result.tfidf_score == 0.0
    assert result.skill_score == 0.0
    assert result.final_score == 0.0


def test_invalid_input_negative():
    """
    Test handling of negative values.
    """
    result = calculate_final_score(-10.0, 90.0)
    assert result.tfidf_score == 0.0  # Invalid negative converted to 0
    assert result.skill_score == 90.0
    assert result.final_score == 54.0
    
    result = calculate_final_score(80.0, -5.0)
    assert result.tfidf_score == 80.0
    assert result.skill_score == 0.0  # Invalid negative converted to 0
    assert result.final_score == 32.0


def test_invalid_input_above_100():
    """
    Test handling of values above 100.
    """
    result = calculate_final_score(150.0, 90.0)
    assert result.tfidf_score == 0.0  # Invalid >100 converted to 0
    assert result.skill_score == 90.0
    assert result.final_score == 54.0
    
    result = calculate_final_score(80.0, 120.0)
    assert result.tfidf_score == 80.0
    assert result.skill_score == 0.0  # Invalid >100 converted to 0
    assert result.final_score == 32.0


def test_invalid_input_nan():
    """
    Test handling of NaN values.
    """
    result = calculate_final_score(float('nan'), 90.0)
    assert result.tfidf_score == 0.0  # NaN converted to 0
    assert result.skill_score == 90.0
    assert result.final_score == 54.0
    
    result = calculate_final_score(80.0, float('nan'))
    assert result.tfidf_score == 80.0
    assert result.skill_score == 0.0  # NaN converted to 0
    assert result.final_score == 32.0


def test_invalid_input_infinity():
    """
    Test handling of infinite values.
    """
    result = calculate_final_score(float('inf'), 90.0)
    assert result.tfidf_score == 0.0  # Infinity converted to 0
    assert result.skill_score == 90.0
    assert result.final_score == 54.0
    
    result = calculate_final_score(80.0, float('inf'))
    assert result.tfidf_score == 80.0
    assert result.skill_score == 0.0  # Infinity converted to 0
    assert result.final_score == 32.0


def test_weight_validation():
    """
    Test that configured weights total 1.0.
    """
    assert validate_weights() == True
    
    weights = get_scoring_weights()
    assert weights['tfidf_weight'] == 0.40
    assert weights['skill_weight'] == 0.60
    assert abs(weights['tfidf_weight'] + weights['skill_weight'] - 1.0) < 0.001


def test_rounding():
    """
    Test two-decimal rounding consistency.
    """
    # Test that rounding is applied
    result = calculate_final_score(80.123456, 90.987654)
    assert len(str(result.final_score).split('.')[-1]) <= 2  # Max 2 decimal places
    
    # Test specific rounding
    result = calculate_final_score(80.456, 90.125)
    # Expected: (80.456 × 0.40) + (90.125 × 0.60) = 32.1824 + 54.075 = 86.2574 ≈ 86.26
    assert abs(result.final_score - 86.26) < 0.01


def test_calculate_final_score_from_raw():
    """
    Test convenience function that accepts raw cosine similarity (0-1).
    """
    cosine_similarity = 0.80  # 80% as raw similarity
    skill_match_percentage = 90.0
    
    result = calculate_final_score_from_raw(cosine_similarity, skill_match_percentage)
    
    # Should convert cosine similarity to percentage (0.80 × 100 = 80)
    assert result.tfidf_score == 80.0
    assert result.skill_score == 90.0
    assert result.final_score == 86.0  # Same as test_basic_weighted_score


def test_calculate_final_score_from_raw_invalid():
    """
    Test convenience function with invalid raw similarity.
    """
    result = calculate_final_score_from_raw(float('nan'), 90.0)
    assert result.tfidf_score == 0.0
    assert result.skill_score == 90.0
    assert result.final_score == 54.0


def test_validate_score_range():
    """
    Test score range validation function.
    """
    # Valid scores
    assert validate_score_range(50.0, "test") == True
    assert validate_score_range(0.0, "test") == True
    assert validate_score_range(100.0, "test") == True
    
    # Invalid scores
    assert validate_score_range(None, "test") == False
    assert validate_score_range(-10.0, "test") == False
    assert validate_score_range(150.0, "test") == False
    assert validate_score_range(float('nan'), "test") == False
    assert validate_score_range(float('inf'), "test") == False
    assert validate_score_range("invalid", "test") == False


def test_result_structure():
    """
    Test that FinalScoreResult has correct structure.
    """
    result = calculate_final_score(80.0, 90.0)
    
    assert hasattr(result, 'tfidf_score')
    assert hasattr(result, 'skill_score')
    assert hasattr(result, 'tfidf_weight')
    assert hasattr(result, 'skill_weight')
    assert hasattr(result, 'final_score')
    
    assert isinstance(result.tfidf_score, float)
    assert isinstance(result.skill_score, float)
    assert isinstance(result.tfidf_weight, float)
    assert isinstance(result.skill_weight, float)
    assert isinstance(result.final_score, float)


def test_module_import():
    """
    Test that the scoring service can be imported.
    """
    from app.services import calculate_final_score, FinalScoreResult, get_scoring_weights, validate_weights
    assert calculate_final_score is not None
    assert callable(calculate_final_score)
    assert FinalScoreResult is not None
    assert get_scoring_weights is not None
    assert callable(get_scoring_weights)
    assert validate_weights is not None
    assert callable(validate_weights)


def test_function_signature():
    """
    Test that calculate_final_score has the correct signature.
    """
    import inspect
    from app.services.scoring_service import calculate_final_score
    
    sig = inspect.signature(calculate_final_score)
    params = list(sig.parameters.keys())
    
    assert 'tfidf_score' in params
    assert 'skill_score' in params
    assert len(params) == 2


def test_score_clamping():
    """
    Test that final score is clamped to [0, 100] range.
    """
    # Even with extreme inputs, final score should be clamped
    # (though inputs should be validated first)
    result = calculate_final_score(100.0, 100.0)
    assert result.final_score <= 100.0
    
    result = calculate_final_score(0.0, 0.0)
    assert result.final_score >= 0.0


def test_decimal_precision():
    """
    Test that scores maintain appropriate decimal precision.
    """
    result = calculate_final_score(78.456789, 85.234567)
    
    # Individual scores should be rounded to 2 decimal places
    assert len(str(result.tfidf_score).split('.')[-1]) <= 2
    assert len(str(result.skill_score).split('.')[-1]) <= 2
    assert len(str(result.final_score).split('.')[-1]) <= 2


def test_weighted_formula_correctness():
    """
    Test that the weighted formula is mathematically correct.
    """
    test_cases = [
        (80.0, 90.0, 86.0),
        (100.0, 100.0, 100.0),
        (0.0, 0.0, 0.0),
        (100.0, 0.0, 40.0),
        (0.0, 100.0, 60.0),
        (50.0, 50.0, 50.0),
    ]
    
    for tfidf, skill, expected in test_cases:
        result = calculate_final_score(tfidf, skill)
        assert abs(result.final_score - expected) < 0.01, \
            f"Failed for TF-IDF={tfidf}, Skill={skill}: expected {expected}, got {result.final_score}"


def test_score_immutability():
    """
    Test that result values are not references to input values.
    """
    tfidf_score = 80.0
    skill_score = 90.0
    
    result = calculate_final_score(tfidf_score, skill_score)
    
    # Modify original values
    tfidf_score = 100.0
    skill_score = 100.0
    
    # Result should not be affected
    assert result.tfidf_score == 80.0
    assert result.skill_score == 90.0