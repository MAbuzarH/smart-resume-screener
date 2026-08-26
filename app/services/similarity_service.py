"""
Cosine Similarity Service

This module provides cosine similarity calculation for TF-IDF vectors.
Uses scikit-learn's cosine_similarity for efficient and reliable similarity computation.

The service calculates the cosine similarity between resume and job description TF-IDF vectors,
which represents the mathematical similarity between the two documents in vector space.
"""

import logging
from typing import Optional
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


def calculate_cosine_similarity(resume_vector: csr_matrix, job_vector: csr_matrix) -> Optional[float]:
    """
    Calculate cosine similarity between resume and job TF-IDF vectors.
    
    This function:
    - Accepts TF-IDF vectors from Step 4
    - Calculates cosine similarity using scikit-learn
    - Returns a numeric similarity score between 0 and 1
    
    Cosine similarity measures the cosine of the angle between two vectors:
    cos_similarity = (A · B) / (||A|| × ||B||)
    
    Where:
    - A = resume TF-IDF vector
    - B = job TF-IDF vector
    - Values range from -1 to 1, but for TF-IDF vectors they range from 0 to 1
    
    Args:
        resume_vector: TF-IDF vector for the resume (sparse matrix from Step 4)
        job_vector: TF-IDF vector for the job description (sparse matrix from Step 4)
        
    Returns:
        Cosine similarity score as a float between 0 and 1.
        Returns None if calculation fails or input is invalid.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if resume_vector is None or job_vector is None:
        logger.warning("None vector provided to calculate_cosine_similarity")
        return None
    
    try:
        # Verify that both vectors are sparse matrices
        if not isinstance(resume_vector, csr_matrix) or not isinstance(job_vector, csr_matrix):
            logger.error("Vectors must be sparse matrices (csr_matrix)")
            return None
        
        # Verify that both vectors have the same number of features
        if resume_vector.shape[1] != job_vector.shape[1]:
            logger.error(f"Vector shape mismatch: resume {resume_vector.shape[1]}, job {job_vector.shape[1]}")
            return None
        
        # Check for zero vectors (empty documents)
        if resume_vector.nnz == 0 or job_vector.nnz == 0:
            logger.warning("One or both vectors are zero vectors (no meaningful terms)")
            return 0.0
        
        # Calculate cosine similarity using scikit-learn
        # cosine_similarity returns a 2D array, so we extract the scalar value
        similarity_matrix = cosine_similarity(resume_vector, job_vector)
        similarity_score = float(similarity_matrix[0, 0])
        
        # Ensure the score is within expected bounds [0, 1]
        # TF-IDF vectors should produce values in [0, 1], but we clamp for safety
        similarity_score = max(0.0, min(1.0, similarity_score))
        
        logger.info(f"Calculated cosine similarity: {similarity_score:.4f}")
        return similarity_score
        
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {str(e)}")
        return None


def calculate_similarity_from_text(resume_text: str, job_description: str) -> Optional[float]:
    """
    Convenience function to calculate similarity directly from processed text.
    
    This function combines Steps 4 and 5:
    1. Creates TF-IDF vectors from processed text
    2. Calculates cosine similarity between the vectors
    
    This is useful for integration testing and when the full pipeline needs to be
    executed without intermediate step storage.
    
    Args:
        resume_text: Preprocessed resume text from Step 2
        job_description: Preprocessed job description from Step 3
        
    Returns:
        Cosine similarity score as a float between 0 and 1.
        Returns None if any step fails.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    try:
        # Import here to avoid circular dependency
        from app.services.tfidf_service import create_tfidf_vectors
        
        # Create TF-IDF vectors
        tfidf_result = create_tfidf_vectors(resume_text, job_description)
        
        if tfidf_result is None:
            logger.warning("TF-IDF vectorization failed in calculate_similarity_from_text")
            return None
        
        # Calculate cosine similarity
        similarity = calculate_cosine_similarity(
            tfidf_result['resume_vector'],
            tfidf_result['job_vector']
        )
        
        return similarity
        
    except Exception as e:
        logger.error(f"Error in calculate_similarity_from_text: {str(e)}")
        return None


def interpret_similarity_score(score: float) -> str:
    """
    Provide a human-readable interpretation of the similarity score.
    
    This is a helper function for debugging and potential future UI use.
    The interpretation is qualitative and should not be used for automatic decision-making.
    
    Args:
        score: Cosine similarity score between 0 and 1
        
    Returns:
        Human-readable interpretation string
    """
    if score is None:
        return "Unable to calculate similarity"
    
    if score >= 0.8:
        return "Very High Match"
    elif score >= 0.6:
        return "High Match"
    elif score >= 0.4:
        return "Moderate Match"
    elif score >= 0.25:
        return "Low Match"
    else:
        return "Very Low Match"
