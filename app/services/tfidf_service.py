"""
TF-IDF Vectorization Service

This module provides TF-IDF (Term Frequency-Inverse Document Frequency) vectorization
for converting processed resume text and job descriptions into numerical vectors.
Uses scikit-learn's TfidfVectorizer for efficient and reliable TF-IDF computation.

The service ensures that both resume and job description vectors are created in the same
feature space using a shared vocabulary, which is essential for accurate similarity matching.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


def create_tfidf_vectors(resume_text: str, job_description: str) -> Optional[Dict[str, Any]]:
    """
    Create TF-IDF vectors for resume and job description using a shared vocabulary.
    
    This function:
    - Takes processed resume text and job description as input
    - Creates a TF-IDF vectorizer fitted on both documents
    - Transforms both documents into TF-IDF vectors in the same feature space
    - Returns the vectorizer and both vectors for further processing
    
    The shared vocabulary ensures that both vectors use the same feature indices,
    which is essential for accurate cosine similarity calculation in the next step.
    
    TF-IDF Configuration:
    - lowercase=False: Text is already preprocessed and lowercased in Steps 2 & 3
    - stop_words=None: Stop words already removed in preprocessing steps
    - ngram_range=(1,1): Using unigrams for simplicity and interpretability
    - min_df=1: Include all terms that appear in at least one document
    - use_idf=True: Enable IDF component for term importance weighting
    - smooth_idf=True: Add 1 to document frequencies to prevent division by zero
    - sublinear_tf=False: Use standard TF calculation (can be changed for sublinear scaling)
    
    Args:
        resume_text: Preprocessed resume text from Step 2
        job_description: Preprocessed job description from Step 3
        
    Returns:
        Dictionary containing:
        - 'vectorizer': The fitted TfidfVectorizer object
        - 'resume_vector': TF-IDF vector for the resume (sparse matrix)
        - 'job_vector': TF-IDF vector for the job description (sparse matrix)
        - 'vocabulary': The shared vocabulary mapping terms to feature indices
        
        Returns None if both inputs are empty or invalid.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if not resume_text or not job_description:
        logger.warning("Empty resume text or job description provided to create_tfidf_vectors")
        return None
    
    if not isinstance(resume_text, str) or not isinstance(job_description, str):
        logger.error("Invalid input types provided to create_tfidf_vectors")
        return None
    
    try:
        # Combine both documents for shared vocabulary creation
        documents = [resume_text, job_description]
        
        # Create TF-IDF vectorizer with appropriate configuration
        # Configuration rationale:
        # - lowercase=False: Text already preprocessed and lowercased
        # - stop_words=None: Stop words already removed in preprocessing
        # - ngram_range=(1,1): Unigrams for simplicity and interpretability
        # - min_df=1: Include all terms present in documents
        # - max_df=1.0: No upper frequency limit for this use case
        # - use_idf=True: Enable IDF for term importance
        # - smooth_idf=True: Prevent division by zero
        # - sublinear_tf=False: Standard TF calculation
        vectorizer = TfidfVectorizer(
            lowercase=False,
            stop_words=None,
            ngram_range=(1, 1),
            min_df=1,
            max_df=1.0,
            use_idf=True,
            smooth_idf=True,
            sublinear_tf=False
        )
        
        # Fit the vectorizer on both documents to create shared vocabulary
        vectorizer.fit(documents)
        
        # Transform both documents into TF-IDF vectors
        resume_vector = vectorizer.transform([resume_text])
        job_vector = vectorizer.transform([job_description])
        
        # Verify that both vectors have the same number of features
        if resume_vector.shape[1] != job_vector.shape[1]:
            logger.error(f"Vector shape mismatch: resume {resume_vector.shape[1]}, job {job_vector.shape[1]}")
            return None
        
        logger.info(f"Successfully created TF-IDF vectors with {resume_vector.shape[1]} features")
        logger.info(f"Resume vector non-zero elements: {resume_vector.nnz}")
        logger.info(f"Job vector non-zero elements: {job_vector.nnz}")
        
        return {
            'vectorizer': vectorizer,
            'resume_vector': resume_vector,
            'job_vector': job_vector,
            'vocabulary': vectorizer.vocabulary_
        }
        
    except ValueError as e:
        # Handle common TF-IDF errors like empty vocabulary
        if "empty vocabulary" in str(e).lower():
            logger.warning("Empty vocabulary error - documents may have no valid terms after preprocessing")
            return None
        else:
            logger.error(f"ValueError in TF-IDF vectorization: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error creating TF-IDF vectors: {str(e)}")
        return None


def get_vocabulary_size(vectorizer: TfidfVectorizer) -> int:
    """
    Get the size of the vocabulary from a fitted TF-IDF vectorizer.
    
    Args:
        vectorizer: A fitted TfidfVectorizer object
        
    Returns:
        Number of unique terms in the vocabulary, or 0 if vectorizer is not fitted
    """
    try:
        if hasattr(vectorizer, 'vocabulary_'):
            return len(vectorizer.vocabulary_)
        return 0
    except Exception as e:
        logger.error(f"Error getting vocabulary size: {str(e)}")
        return 0


def get_top_features(vectorizer: TfidfVectorizer, vector: csr_matrix, top_n: int = 10) -> list:
    """
    Get the top N features with highest TF-IDF scores from a vector.
    
    Args:
        vectorizer: A fitted TfidfVectorizer object
        vector: TF-IDF vector (sparse matrix)
        top_n: Number of top features to return
        
    Returns:
        List of tuples (feature, score) for the top N features
    """
    try:
        # Convert to dense array if sparse
        if hasattr(vector, 'toarray'):
            dense_vector = vector.toarray()[0]
        else:
            dense_vector = vector
            
        # Get feature names
        feature_names = vectorizer.get_feature_names_out()
        
        # Get indices of top features
        top_indices = np.argsort(dense_vector)[-top_n:][::-1]
        
        # Create list of (feature, score) tuples
        top_features = [
            (feature_names[i], dense_vector[i])
            for i in top_indices
        ]
        
        return top_features
    except Exception as e:
        logger.error(f"Error getting top features: {str(e)}")
        return []
