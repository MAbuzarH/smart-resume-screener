"""
Matching Service

This module coordinates the complete resume-job matching pipeline.
It integrates text preprocessing, TF-IDF vectorization, and cosine similarity
to calculate a final match score percentage.

The service orchestrates:
- Resume text preprocessing (Step 2)
- Job description preprocessing (Step 3)
- TF-IDF vectorization (Step 4)
- Cosine similarity calculation (Step 5)
- Match score calculation and validation (Step 6)
"""

import logging
from typing import Optional
from app.services.text_preprocessor import preprocess_text, preprocess_job_description
from app.services.tfidf_service import create_tfidf_vectors
from app.services.similarity_service import calculate_cosine_similarity

# Configure logging
logger = logging.getLogger(__name__)


def calculate_match_score(resume_text: str, job_description: str) -> Optional[float]:
    """
    Calculate the match score percentage between a resume and job description.
    
    This function coordinates the complete matching pipeline:
    1. Preprocess resume text (Step 2)
    2. Preprocess job description (Step 3)
    3. Generate TF-IDF vectors (Step 4)
    4. Calculate cosine similarity (Step 5)
    5. Convert to percentage and round (Step 6)
    
    The match score formula is:
    match_score = cosine_similarity × 100
    
    The result is rounded to 2 decimal places and validated to be within [0, 100].
    
    Args:
        resume_text: Raw resume text extracted from PDF (Step 1)
        job_description: Raw job description text
        
    Returns:
        Match score as a float between 0 and 100, rounded to 2 decimal places.
        Returns None if any step in the pipeline fails.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if not resume_text or not job_description:
        logger.warning("Empty resume text or job description provided to calculate_match_score")
        return None
    
    if not isinstance(resume_text, str) or not isinstance(job_description, str):
        logger.error("Invalid input types provided to calculate_match_score")
        return None
    
    try:
        # Step 2: Preprocess resume text
        logger.info("Preprocessing resume text...")
        processed_resume = preprocess_text(resume_text)
        
        if not processed_resume:
            logger.warning("Resume text became empty after preprocessing")
            return None
        
        # Step 3: Preprocess job description
        logger.info("Preprocessing job description...")
        processed_job = preprocess_job_description(job_description)
        
        if not processed_job:
            logger.warning("Job description became empty after preprocessing")
            return None
        
        # Step 4: Generate TF-IDF vectors
        logger.info("Generating TF-IDF vectors...")
        tfidf_result = create_tfidf_vectors(processed_resume, processed_job)
        
        if tfidf_result is None:
            logger.warning("TF-IDF vectorization failed")
            return None
        
        # Step 5: Calculate cosine similarity
        logger.info("Calculating cosine similarity...")
        similarity = calculate_cosine_similarity(
            tfidf_result['resume_vector'],
            tfidf_result['job_vector']
        )
        
        if similarity is None:
            logger.warning("Cosine similarity calculation failed")
            return None
        
        # Step 6: Convert to percentage and round
        match_score = similarity * 100
        
        # Round to 2 decimal places
        match_score = round(match_score, 2)
        
        # Validate score is within expected range [0, 100]
        # Handle potential floating-point edge cases
        if match_score < 0:
            logger.warning(f"Match score {match_score} is below 0, clamping to 0")
            match_score = 0.0
        elif match_score > 100:
            logger.warning(f"Match score {match_score} is above 100, clamping to 100")
            match_score = 100.0
        
        # Check for NaN or infinity
        if not isinstance(match_score, float) or match_score != match_score:  # NaN check
            logger.error("Match score is NaN")
            return None
        
        logger.info(f"Successfully calculated match score: {match_score:.2f}%")
        return match_score
        
    except Exception as e:
        logger.error(f"Error calculating match score: {str(e)}")
        return None


def calculate_match_score_from_processed(processed_resume: str, processed_job: str) -> Optional[float]:
    """
    Calculate match score from already preprocessed text.
    
    This is a convenience function for cases where text has already been
    preprocessed (e.g., when processing existing applications).
    
    Args:
        processed_resume: Preprocessed resume text
        processed_job: Preprocessed job description
        
    Returns:
        Match score as a float between 0 and 100, rounded to 2 decimal places.
        Returns None if calculation fails.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if not processed_resume or not processed_job:
        logger.warning("Empty processed text provided to calculate_match_score_from_processed")
        return None
    
    try:
        # Skip preprocessing, go directly to TF-IDF
        tfidf_result = create_tfidf_vectors(processed_resume, processed_job)
        
        if tfidf_result is None:
            logger.warning("TF-IDF vectorization failed")
            return None
        
        similarity = calculate_cosine_similarity(
            tfidf_result['resume_vector'],
            tfidf_result['job_vector']
        )
        
        if similarity is None:
            logger.warning("Cosine similarity calculation failed")
            return None
        
        match_score = similarity * 100
        match_score = round(match_score, 2)
        
        # Validate range
        if match_score < 0:
            match_score = 0.0
        elif match_score > 100:
            match_score = 100.0
        
        # NaN check
        if not isinstance(match_score, float) or match_score != match_score:
            logger.error("Match score is NaN")
            return None
        
        logger.info(f"Calculated match score from processed text: {match_score:.2f}%")
        return match_score
        
    except Exception as e:
        logger.error(f"Error calculating match score from processed text: {str(e)}")
        return None
