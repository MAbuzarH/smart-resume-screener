"""
Test file for TF-IDF Vectorization Service.
Tests TF-IDF vectorization functionality for resume and job description matching.
"""

import pytest
import numpy as np
from scipy.sparse import csr_matrix
from app.services.tfidf_service import create_tfidf_vectors, get_vocabulary_size, get_top_features


def test_basic_vectorization():
    """
    Test that basic TF-IDF vectorization works with simple inputs.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    # Verify the function runs successfully
    assert result is not None
    
    # Verify all required components are returned
    assert 'vectorizer' in result
    assert 'resume_vector' in result
    assert 'job_vector' in result
    assert 'vocabulary' in result
    
    # Verify the vectors are sparse matrices
    assert isinstance(result['resume_vector'], csr_matrix)
    assert isinstance(result['job_vector'], csr_matrix)
    
    # Verify the vocabulary is a dictionary
    assert isinstance(result['vocabulary'], dict)


def test_same_vector_space():
    """
    Test that resume and job vectors are in the same feature space.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    # Verify both vectors have the same number of features
    assert result['resume_vector'].shape[1] == result['job_vector'].shape[1]
    
    # Both should have 5 features (python, developer, flask, sql, django)
    assert result['resume_vector'].shape[1] == 5


def test_shared_vocabulary():
    """
    Test that common terms are represented in the shared vocabulary.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocabulary = result['vocabulary']
    
    # Verify common terms are in the vocabulary
    assert 'python' in vocabulary
    assert 'developer' in vocabulary
    assert 'flask' in vocabulary
    
    # Verify unique terms are also in the vocabulary
    assert 'sql' in vocabulary
    assert 'django' in vocabulary


def test_different_terms():
    """
    Test that terms appearing only in one document are represented.
    """
    resume_text = "python developer sql database"
    job_description = "react javascript frontend web"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocabulary = result['vocabulary']
    
    # Verify terms from both documents are in the vocabulary
    assert 'python' in vocabulary
    assert 'sql' in vocabulary
    assert 'react' in vocabulary
    assert 'javascript' in vocabulary
    
    # Verify vocabulary size includes all unique terms
    # python, developer, sql, database, react, javascript, frontend, web
    assert len(vocabulary) == 8


def test_empty_input():
    """
    Test that empty input is handled safely.
    """
    result = create_tfidf_vectors("", "")
    assert result is None
    
    result = create_tfidf_vectors("python", "")
    assert result is None
    
    result = create_tfidf_vectors("", "python")
    assert result is None


def test_none_input():
    """
    Test that None input is handled safely.
    """
    result = create_tfidf_vectors(None, "python")
    assert result is None
    
    result = create_tfidf_vectors("python", None)
    assert result is None
    
    result = create_tfidf_vectors(None, None)
    assert result is None


def test_identical_documents():
    """
    Test that identical documents produce structurally equivalent vectors.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask sql"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    # Get the vectors as dense arrays for comparison
    resume_dense = result['resume_vector'].toarray()[0]
    job_dense = result['job_vector'].toarray()[0]
    
    # Verify both vectors have the same shape
    assert resume_dense.shape == job_dense.shape
    
    # Verify the vectors are approximately equal (allowing for small numerical differences)
    np.testing.assert_array_almost_equal(resume_dense, job_dense, decimal=10)


def test_technical_terms():
    """
    Test that realistic technical terms are properly vectorized.
    """
    resume_text = "python flask django sql postgresql docker aws machine learning"
    job_description = "python javascript react node docker kubernetes aws cloud"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocabulary = result['vocabulary']
    
    # Verify technical terms are in the vocabulary
    technical_terms = [
        'python', 'flask', 'django', 'sql', 'postgresql', 
        'docker', 'aws', 'machine', 'learning',
        'javascript', 'react', 'node', 'kubernetes', 'cloud'
    ]
    
    for term in technical_terms:
        assert term in vocabulary, f"Technical term '{term}' not in vocabulary"


def test_vocabulary_size_function():
    """
    Test the get_vocabulary_size helper function.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocab_size = get_vocabulary_size(result['vectorizer'])
    
    # Should have 5 unique terms
    assert vocab_size == 5


def test_top_features_function():
    """
    Test the get_top_features helper function.
    """
    resume_text = "python developer flask sql database"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    top_features = get_top_features(result['vectorizer'], result['resume_vector'], top_n=3)
    
    # Verify we get the requested number of features
    assert len(top_features) == 3
    
    # Verify each feature is a tuple with (feature_name, score)
    for feature, score in top_features:
        assert isinstance(feature, str)
        assert isinstance(score, (float, np.floating))
        assert score > 0  # TF-IDF scores should be positive


def test_single_document_terms():
    """
    Test that terms appearing in only one document are handled correctly.
    """
    resume_text = "python flask"
    job_description = "django react"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocabulary = result['vocabulary']
    
    # All terms should be in the vocabulary
    assert 'python' in vocabulary
    assert 'flask' in vocabulary
    assert 'django' in vocabulary
    assert 'react' in vocabulary
    
    # Vocabulary should have 4 terms
    assert len(vocabulary) == 4


def test_repeated_terms():
    """
    Test that repeated terms in documents are handled correctly.
    """
    resume_text = "python python python developer"
    job_description = "python developer developer flask"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocabulary = result['vocabulary']
    
    # Unique terms should be in vocabulary
    assert 'python' in vocabulary
    assert 'developer' in vocabulary
    assert 'flask' in vocabulary
    
    # Vocabulary should have 3 unique terms
    assert len(vocabulary) == 3


def test_case_sensitivity():
    """
    Test that the vectorizer handles case appropriately.
    """
    # Since preprocessing already lowercases text, all terms should be lowercase
    resume_text = "python developer flask"
    job_description = "python developer django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocabulary = result['vocabulary']
    
    # All terms should be lowercase in vocabulary
    for term in vocabulary:
        assert term.islower() or not term.isalpha()


def test_module_import():
    """
    Test that the TF-IDF service can be imported.
    """
    from app.services import create_tfidf_vectors
    assert create_tfidf_vectors is not None
    assert callable(create_tfidf_vectors)


def test_function_signature():
    """
    Test that the create_tfidf_vectors function has the correct signature.
    """
    import inspect
    from app.services.tfidf_service import create_tfidf_vectors
    
    sig = inspect.signature(create_tfidf_vectors)
    params = list(sig.parameters.keys())
    
    assert 'resume_text' in params
    assert 'job_description' in params
    assert len(params) == 2


def test_sparse_matrix_properties():
    """
    Test that the returned vectors have proper sparse matrix properties.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    resume_vector = result['resume_vector']
    job_vector = result['job_vector']
    
    # Verify sparse matrix properties
    assert resume_vector.shape[0] == 1  # Single document
    assert job_vector.shape[0] == 1  # Single document
    assert resume_vector.shape[1] > 0  # Has features
    assert job_vector.shape[1] > 0  # Has features
    
    # Verify they are sparse matrices
    assert isinstance(resume_vector, csr_matrix)
    assert isinstance(job_vector, csr_matrix)


def test_invalid_input_types():
    """
    Test that invalid input types are handled safely.
    """
    result = create_tfidf_vectors(123, "python")
    assert result is None
    
    result = create_tfidf_vectors("python", 123)
    assert result is None
    
    result = create_tfidf_vectors([], "python")
    assert result is None


def test_realistic_resume_job_pair():
    """
    Test with a realistic resume and job description pair.
    """
    resume_text = "experienced python developer flask django sql postgresql docker kubernetes aws"
    job_description = "looking for python developer experienced in flask django sql databases docker kubernetes aws cloud"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    # Verify successful vectorization
    assert result is not None
    
    # Verify shared vocabulary contains key terms
    vocabulary = result['vocabulary']
    key_terms = ['python', 'developer', 'flask', 'django', 'sql', 'docker', 'kubernetes', 'aws']
    
    for term in key_terms:
        assert term in vocabulary, f"Key term '{term}' missing from vocabulary"
    
    # Verify both vectors have the same feature space
    assert result['resume_vector'].shape[1] == result['job_vector'].shape[1]


def test_whitespace_only_input():
    """
    Test that whitespace-only input is handled safely.
    """
    result = create_tfidf_vectors("   ", "   ")
    # This should return None since there are no valid terms
    assert result is None


def test_special_characters():
    """
    Test that special characters are handled appropriately.
    """
    # Since preprocessing removes special characters, this tests
    # that the TF-IDF service handles preprocessed text correctly
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    # Should work normally with preprocessed text
    assert result is not None
    assert result['vocabulary'] is not None


def test_feature_index_consistency():
    """
    Test that the same term maps to the same feature index in both vectors.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    vocabulary = result['vocabulary']
    
    # Get feature indices for common terms
    python_index = vocabulary['python']
    developer_index = vocabulary['developer']
    flask_index = vocabulary['flask']
    
    # Verify indices are consistent (they should be the same for both vectors)
    assert python_index == vocabulary['python']
    assert developer_index == vocabulary['developer']
    assert flask_index == vocabulary['flask']
    
    # Verify indices are unique
    indices = [vocabulary['python'], vocabulary['developer'], vocabulary['flask'], 
                vocabulary['sql'], vocabulary['django']]
    assert len(indices) == len(set(indices)), "Feature indices should be unique"


def test_return_structure():
    """
    Test that the function returns the expected structure.
    """
    resume_text = "python developer flask sql"
    job_description = "python developer flask django"
    
    result = create_tfidf_vectors(resume_text, job_description)
    
    # Verify all expected keys are present
    expected_keys = ['vectorizer', 'resume_vector', 'job_vector', 'vocabulary']
    for key in expected_keys:
        assert key in result, f"Expected key '{key}' not in result"
    
    # Verify no unexpected keys are present
    assert set(result.keys()) == set(expected_keys)
