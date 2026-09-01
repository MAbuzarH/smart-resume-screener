"""
Scoring Service

This module provides weighted final scoring functionality for combining
TF-IDF/cosine similarity scores with skill match percentages into a
single final match score.

The weighted scoring model uses configurable weights defined in config.py:
- TF-IDF/Cosine Similarity: 40%
- Skill Match Percentage: 60%

This weighting prioritizes skill matching because the presence of required
skills is more directly relevant to job qualification than general textual
similarity. TF-IDF similarity remains important for capturing broader
contextual overlap between resume and job description.
"""

import logging
import math
from typing import Optional, Dict, Any
from dataclasses import dataclass

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Extract weights from Config class
TFIDF_WEIGHT = Config.TFIDF_WEIGHT
SKILL_WEIGHT = Config.SKILL_WEIGHT

# Validate weights at module import time
if abs(TFIDF_WEIGHT + SKILL_WEIGHT - 1.0) > 0.001:
    raise ValueError(
        f"Scoring weights must sum to 1.0. "
        f"Current: TFIDF_WEIGHT={TFIDF_WEIGHT}, SKILL_WEIGHT={SKILL_WEIGHT}, "
        f"Sum={TFIDF_WEIGHT + SKILL_WEIGHT}"
    )


@dataclass
class FinalScoreResult:
    """
    Data class for final scoring results.
    
    Attributes:
        tfidf_score: TF-IDF/cosine similarity score (0-100)
        skill_score: Skill match percentage (0-100)
        tfidf_weight: Weight applied to TF-IDF score (0-1)
        skill_weight: Weight applied to skill score (0-1)
        final_score: Weighted final match score (0-100)
    """
    tfidf_score: float
    skill_score: float
    tfidf_weight: float
    skill_weight: float
    final_score: float


def validate_score_range(score: float, score_name: str) -> bool:
    """
    Validate that a score is within the valid range [0, 100].
    
    Args:
        score: The score to validate
        score_name: Name of the score for error messages
        
    Returns:
        True if score is valid, False otherwise
    """
    if score is None:
        logger.warning(f"{score_name} is None")
        return False
    
    if not isinstance(score, (int, float)):
        logger.warning(f"{score_name} is not a number: {type(score)}")
        return False
    
    if math.isnan(score):
        logger.warning(f"{score_name} is NaN")
        return False
    
    if math.isinf(score):
        logger.warning(f"{score_name} is infinite")
        return False
    
    if score < 0:
        logger.warning(f"{score_name} is negative: {score}")
        return False
    
    if score > 100:
        logger.warning(f"{score_name} exceeds 100: {score}")
        return False
    
    return True


def calculate_final_score(
    tfidf_score: Optional[float],
    skill_score: Optional[float]
) -> FinalScoreResult:
    """
    Calculate final weighted match score from TF-IDF and skill scores.
    
    This function combines TF-IDF/cosine similarity score and skill match
    percentage using configurable weights:
    
    final_score = (tfidf_score × tfidf_weight) + (skill_score × skill_weight)
    
    Where:
    - tfidf_weight = 0.40 (40%)
    - skill_weight = 0.60 (60%)
    
    Args:
        tfidf_score: TF-IDF/cosine similarity score (0-100, as percentage)
        skill_score: Skill match percentage (0-100)
        
    Returns:
        FinalScoreResult containing component scores, weights, and final score
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    # Validate TF-IDF score
    if not validate_score_range(tfidf_score, "TF-IDF score"):
        logger.warning(f"Invalid TF-IDF score: {tfidf_score}. Using 0.0.")
        tfidf_score = 0.0
    
    # Validate skill score
    if not validate_score_range(skill_score, "Skill score"):
        logger.warning(f"Invalid skill score: {skill_score}. Using 0.0.")
        skill_score = 0.0
    
    # Calculate weighted final score
    # Convert to float for precision
    tfidf_score = float(tfidf_score)
    skill_score = float(skill_score)
    
    # Apply weights
    weighted_tfidf = tfidf_score * TFIDF_WEIGHT
    weighted_skill = skill_score * SKILL_WEIGHT
    
    # Calculate final score
    final_score = weighted_tfidf + weighted_skill
    
    # Round to 2 decimal places
    tfidf_score = round(tfidf_score, 2)
    skill_score = round(skill_score, 2)
    final_score = round(final_score, 2)
    
    # Ensure final score is within valid range
    if final_score < 0:
        final_score = 0.0
        logger.warning(f"Final score was negative after calculation. Setting to 0.0.")
    elif final_score > 100:
        final_score = 100.0
        logger.warning(f"Final score exceeded 100 after calculation. Setting to 100.0.")
    
    logger.info(
        f"Final score calculation: TF-IDF={tfidf_score:.2f}×{TFIDF_WEIGHT:.2f} + "
        f"Skill={skill_score:.2f}×{SKILL_WEIGHT:.2f} = {final_score:.2f}"
    )
    
    return FinalScoreResult(
        tfidf_score=tfidf_score,
        skill_score=skill_score,
        tfidf_weight=TFIDF_WEIGHT,
        skill_weight=SKILL_WEIGHT,
        final_score=final_score
    )


def calculate_final_score_from_raw(
    cosine_similarity: Optional[float],
    skill_match_percentage: Optional[float]
) -> FinalScoreResult:
    """
    Calculate final weighted match score from raw cosine similarity and skill match.
    
    This is a convenience function that accepts cosine similarity (0-1) instead
    of the percentage (0-100), converting it internally.
    
    Args:
        cosine_similarity: Cosine similarity score (0-1)
        skill_match_percentage: Skill match percentage (0-100)
        
    Returns:
        FinalScoreResult containing component scores, weights, and final score
    """
    # Convert cosine similarity to percentage (0-100)
    if cosine_similarity is not None and validate_score_range(cosine_similarity, "Cosine similarity"):
        tfidf_score = cosine_similarity * 100
    else:
        tfidf_score = 0.0
    
    return calculate_final_score(tfidf_score, skill_match_percentage)


def get_scoring_weights() -> Dict[str, float]:
    """
    Get the current scoring weights configuration.
    
    Returns:
        Dictionary containing TF-IDF and skill weights
    """
    return {
        'tfidf_weight': TFIDF_WEIGHT,
        'skill_weight': SKILL_WEIGHT
    }


def validate_weights() -> bool:
    """
    Validate that scoring weights are properly configured.
    
    Returns:
        True if weights are valid (sum to 1.0), False otherwise
    """
    total_weight = TFIDF_WEIGHT + SKILL_WEIGHT
    
    if abs(total_weight - 1.0) > 0.001:
        logger.error(
            f"Scoring weights do not sum to 1.0. "
            f"TFIDF_WEIGHT={TFIDF_WEIGHT}, SKILL_WEIGHT={SKILL_WEIGHT}, Sum={total_weight}"
        )
        return False
    
    logger.info(f"Scoring weights validated: TFIDF={TFIDF_WEIGHT:.2f}, Skill={SKILL_WEIGHT:.2f}")
    return True