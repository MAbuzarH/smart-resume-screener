"""
Test file for Cosine Similarity Service.
Tests cosine similarity calculation functionality for resume and job description matching.
"""

import pytest
import numpy as np
from scipy.sparse import csr_matrix
from app.services.similarity_service import calculate_cosine_similarity, calculate_similarity_from_text, interpret_similarity_score


def test_identical_vectors():
    """
    Test that identical vectors produce similarity approximately 1.0.
    """
    # Create identical vectors
    vector_a = csr_matrix([[1, 2, 3]])
    vector_b = csr_matrix([[1, 2, 3]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Verify similarity is approximately 1.0
    assert similarity is not None
    assert abs(similarity - 1.0) < 0.001, f"Expected ~1.0, got {similarity}"


def test_completely_different_vectors():
    """
    Test that orthogonal vectors produce similarity approximately 0.0.
    """
    # Create orthogonal vectors
    vector_a = csr_matrix([[1, 0]])
    vector_b = csr_matrix([[0, 1]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Verify similarity is approximately 0.0
    assert similarity is not None
    assert abs(similarity - 0.0) < 0.001, f"Expected ~0.0, got {similarity}"


def test_partially_similar_vectors():
    """
    Test that partially similar vectors produce similarity between 0 and 1.
    """
    # Create partially similar vectors
    vector_a = csr_matrix([[1, 1, 0]])
    vector_b = csr_matrix([[1, 0, 1]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Verify similarity is between 0 and 1
    assert similarity is not None
    assert similarity > 0, f"Expected > 0, got {similarity}"
    assert similarity < 1, f"Expected < 1, got {similarity}"


def test_real_tfidf_output():
    """
    Test with actual TF-IDF output from Step 4.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    similarity = calculate_similarity_from_text(resume_text, job_description)
    
    # Verify a numeric score is returned
    assert similarity is not None
    assert isinstance(similarity, float)
    
    # Verify score is between 0 and 1
    assert similarity >= 0, f"Expected >= 0, got {similarity}"
    assert similarity <= 1, f"Expected <= 1, got {similarity}"
    
    # Verify score is greater than zero because documents share terms
    assert similarity > 0, f"Expected > 0 for documents with shared terms, got {similarity}"


def test_identical_text():
    """
    Test that identical processed text produces similarity approximately 1.0.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask sql"
    
    similarity = calculate_similarity_from_text(resume_text, job_description)
    
    # Verify similarity is approximately 1.0
    assert similarity is not None
    assert abs(similarity - 1.0) < 0.001, f"Expected ~1.0 for identical text, got {similarity}"


def test_unrelated_text():
    """
    Test that unrelated documents produce very low or zero similarity.
    """
    resume_text = "python flask developer"
    job_description = "accounting finance taxation"
    
    similarity = calculate_similarity_from_text(resume_text, job_description)
    
    # Verify score is very low or zero
    assert similarity is not None
    assert similarity >= 0, f"Expected >= 0, got {similarity}"
    assert similarity < 0.3, f"Expected < 0.3 for unrelated text, got {similarity}"


def test_zero_vector():
    """
    Test behavior when one vector contains no meaningful terms.
    """
    # Create a zero vector and a normal vector
    zero_vector = csr_matrix([[0, 0, 0]])
    normal_vector = csr_matrix([[1, 2, 3]])
    
    similarity = calculate_cosine_similarity(zero_vector, normal_vector)
    
    # Should return 0.0 for zero vectors
    assert similarity == 0.0, f"Expected 0.0 for zero vector, got {similarity}"


def test_none_input():
    """
    Test that None input is handled safely.
    """
    normal_vector = csr_matrix([[1, 2, 3]])
    
    similarity = calculate_cosine_similarity(None, normal_vector)
    assert similarity is None
    
    similarity = calculate_cosine_similarity(normal_vector, None)
    assert similarity is None
    
    similarity = calculate_cosine_similarity(None, None)
    assert similarity is None


def test_shape_mismatch():
    """
    Test that shape mismatch is handled safely.
    """
    vector_a = csr_matrix([[1, 2, 3]])
    vector_b = csr_matrix([[1, 2, 3, 4]])  # Different shape
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Should return None for shape mismatch
    assert similarity is None


def test_empty_text():
    """
    Test that empty text is handled safely.
    """
    similarity = calculate_similarity_from_text("", "")
    assert similarity is None
    
    similarity = calculate_similarity_from_text("python", "")
    assert similarity is None
    
    similarity = calculate_similarity_from_text("", "python")
    assert similarity is None


def test_sparse_matrix_efficiency():
    """
    Test that the function works efficiently with sparse matrices.
    """
    # Create larger sparse matrices
    vector_a = csr_matrix([[1, 0, 0, 0, 0, 2, 0, 0, 3, 0]])
    vector_b = csr_matrix([[1, 0, 0, 0, 0, 0, 2, 0, 0, 3]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Should work with sparse matrices
    assert similarity is not None
    assert 0 <= similarity <= 1


def test_high_similarity_case():
    """
    Test a case with high expected similarity.
    """
    # Vectors that should have high similarity
    vector_a = csr_matrix([[3, 2, 1]])
    vector_b = csr_matrix([[3, 2, 0]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Should have high similarity (> 0.8)
    assert similarity is not None
    assert similarity > 0.8, f"Expected > 0.8, got {similarity}"


def test_low_similarity_case():
    """
    Test a case with low expected similarity.
    """
    # Vectors that should have low similarity
    vector_a = csr_matrix([[1, 0, 0]])
    vector_b = csr_matrix([[0, 1, 1]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Should have low similarity (< 0.5)
    assert similarity is not None
    assert similarity < 0.5, f"Expected < 0.5, got {similarity}"


def test_module_import():
    """
    Test that the similarity service can be imported.
    """
    from app.services import calculate_cosine_similarity
    assert calculate_cosine_similarity is not None
    assert callable(calculate_cosine_similarity)


def test_function_signature():
    """
    Test that the calculate_cosine_similarity function has the correct signature.
    """
    import inspect
    from app.services.similarity_service import calculate_cosine_similarity
    
    sig = inspect.signature(calculate_cosine_similarity)
    params = list(sig.parameters.keys())
    
    assert 'resume_vector' in params
    assert 'job_vector' in params
    assert len(params) == 2


def test_return_type():
    """
    Test that the function returns the correct type.
    """
    vector_a = csr_matrix([[1, 2, 3]])
    vector_b = csr_matrix([[1, 2, 3]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    assert isinstance(similarity, float) or similarity is None


def test_interpret_similarity_score():
    """
    Test the interpret_similarity_score helper function.
    """
    high_score = 0.85
    medium_score = 0.65
    moderate_score = 0.45
    low_score = 0.35
    very_low_score = 0.15
    
    assert interpret_similarity_score(high_score) == "Very High Match"
    assert interpret_similarity_score(medium_score) == "High Match"
    assert interpret_similarity_score(moderate_score) == "Moderate Match"
    assert interpret_similarity_score(low_score) == "Low Match"
    assert interpret_similarity_score(very_low_score) == "Very Low Match"
    assert interpret_similarity_score(None) == "Unable to calculate similarity"


def test_complete_matching_pipeline():
    """
    Integration test for the complete matching pipeline.
    """
    resume_text = "Python developer with experience in Flask, Django, SQL, REST APIs and Docker"
    job_description = "Looking for a Python developer with Flask, SQL and REST API experience"
    
    similarity = calculate_similarity_from_text(resume_text, job_description)
    
    # Verify the complete pipeline works
    assert similarity is not None
    assert isinstance(similarity, float)
    assert 0 <= similarity <= 1
    
    # Should have some similarity due to shared terms
    assert similarity > 0, f"Expected > 0 for documents with shared terms, got {similarity}"
    
    # Should not be perfect match since terms differ
    assert similarity < 1.0, f"Expected < 1.0 for different documents, got {similarity}"


def test_convenience_function_signature():
    """
    Test that the convenience function has the correct signature.
    """
    import inspect
    from app.services.similarity_service import calculate_similarity_from_text
    
    sig = inspect.signature(calculate_similarity_from_text)
    params = list(sig.parameters.keys())
    
    assert 'resume_text' in params
    assert 'job_description' in params
    assert len(params) == 2


def test_normalization():
    """
    Test that cosine similarity is properly normalized.
    """
    # Create vectors of different magnitudes but same direction
    vector_a = csr_matrix([[1, 1, 1]])
    vector_b = csr_matrix([[2, 2, 2]])  # Same direction, double magnitude
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Should be 1.0 because cosine similarity is normalized
    assert abs(similarity - 1.0) < 0.001, f"Expected ~1.0 for normalized vectors, got {similarity}"


def test_negation_invariance():
    """
    Test that negating both vectors doesn't change similarity.
    """
    vector_a = csr_matrix([[1, 2, 3]])
    vector_b = csr_matrix([[1, 0, 1]])
    
    similarity1 = calculate_cosine_similarity(vector_a, vector_b)
    
    # Negate both vectors
    vector_a_negated = csr_matrix([[-1, -2, -3]])
    vector_b_negated = csr_matrix([[-1, 0, -1]])
    
    similarity2 = calculate_cosine_similarity(vector_a_negated, vector_b_negated)
    
    # TF-IDF vectors are non-negative, so this test verifies the implementation
    # (TF-IDF vectors won't have negative values, but the function should handle them)
    if similarity1 is not None and similarity2 is not None:
        assert abs(similarity1 - similarity2) < 0.001


def test_single_feature_vectors():
    """
    Test with vectors that have only one feature.
    """
    vector_a = csr_matrix([[1]])
    vector_b = csr_matrix([[1]])
    
    similarity = calculate_cosine_similarity(vector_a, vector_b)
    
    # Should be 1.0 for identical single-feature vectors
    assert similarity is not None
    assert abs(similarity - 1.0) < 0.001


def test_scaling_invariance():
    """
    Test that cosine similarity is invariant to scaling.
    """
    vector_a = csr_matrix([[1, 2, 3]])
    vector_b = csr_matrix([[1, 0, 1]])
    
    similarity1 = calculate_cosine_similarity(vector_a, vector_b)
    
    # Scale both vectors
    vector_a_scaled = csr_matrix([[2, 4, 6]])
    vector_b_scaled = csr_matrix([[2, 0, 2]])
    
    similarity2 = calculate_cosine_similarity(vector_a_scaled, vector_b_scaled)
    
    # Should be the same due to normalization
    assert similarity1 is not None
    assert similarity2 is not None
    assert abs(similarity1 - similarity2) < 0.001, f"Expected same similarity for scaled vectors, got {similarity1} vs {similarity2}"


def test_realistic_technical_terms():
    """
    Test with realistic technical terms from the domain.
    """
    resume_text = "python flask django sql postgresql docker kubernetes aws machine learning"
    job_description = "python javascript react node docker kubernetes aws cloud computing"
    
    similarity = calculate_similarity_from_text(resume_text, job_description)
    
    # Should have some similarity due to shared technical terms
    assert similarity is not None
    assert similarity > 0, f"Expected > 0 for documents with shared technical terms, got {similarity}"
    assert similarity < 1.0, f"Expected < 1.0 for different documents, got {similarity}"
