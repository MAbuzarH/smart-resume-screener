"""
Text Preprocessing Service

This module provides text preprocessing functionality for normalizing resume text and job descriptions.
Uses NLTK for natural language processing tasks including stop word removal and tokenization.
Focuses on preserving technical terminology while cleaning text for TF-IDF processing.
"""

import re
import string
import logging
from typing import Optional
import nltk
from nltk.corpus import stopwords

# Configure logging
logger = logging.getLogger(__name__)

# Download required NLTK data if not already downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    logger.info("Downloading NLTK stopwords...")
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    logger.info("Downloading NLTK punkt_tab tokenizer...")
    nltk.download('punkt_tab', quiet=True)

# Common technical terms to preserve (case-insensitive matching)
TECHNICAL_TERMS = {
    'python', 'java', 'javascript', 'typescript', 'c', 'c++', 'c#', 'ruby', 'php', 'swift',
    'go', 'rust', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'lua', 'haskell',
    'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express', 'rails',
    'node', 'jquery', 'bootstrap', 'tailwind', 'svelte', 'next', 'nuxt',
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
    'sqlite', 'oracle', 'mariadb', 'dynamodb', 'firebase', 'graphql',
    'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean', 'linode',
    'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab', 'github', 'bitbucket',
    'ci/cd', 'devops', 'terraform', 'ansible', 'chef', 'puppet',
    'machine learning', 'ml', 'deep learning', 'ai', 'artificial intelligence',
    'data science', 'nlp', 'natural language processing', 'computer vision',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
    'matplotlib', 'seaborn', 'jupyter', 'spark', 'hadoop', 'kafka',
    'linux', 'unix', 'windows', 'macos', 'android', 'ios', 'web',
    'api', 'rest', 'graphql', 'soap', 'grpc', 'json', 'xml', 'yaml',
    'html', 'css', 'sass', 'less', 'webpack', 'babel', 'vite',
    'git', 'svn', 'mercurial', 'version control', 'agile', 'scrum',
    'tdd', 'bdd', 'unit testing', 'integration testing', 'e2e testing',
    'microservices', 'serverless', 'monolith', 'architecture', 'design patterns',
    'oop', 'functional programming', 'reactive programming', 'async', 'multithreading'
}

# Get English stop words
STOP_WORDS = set(stopwords.words('english'))


def preprocess_text(text: Optional[str]) -> str:
    """
    Preprocess raw resume text for TF-IDF and similarity matching.
    
    This function:
    - Converts text to lowercase
    - Normalizes whitespace and line breaks
    - Removes unnecessary punctuation
    - Removes common English stop words
    - Preserves technical terminology
    - Tokenizes and rejoins text appropriately
    
    Args:
        text: Raw extracted resume text, or None/empty string.
        
    Returns:
        Preprocessed text suitable for TF-IDF processing.
        Returns empty string for None or empty input.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if not text or not isinstance(text, str):
        logger.warning("Empty or invalid text provided to preprocess_text")
        return ""
    
    try:
        # Convert to lowercase
        text = text.lower()
        
        # Normalize line breaks - replace multiple newlines with single space
        text = re.sub(r'\n+', ' ', text)
        
        # Normalize tabs and multiple spaces
        text = re.sub(r'\t+', ' ', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common email patterns (preserve the domain parts which might be technical)
        text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', ' email ', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', ' phone ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+|www\.\S+', ' url ', text)
        
        # Remove special characters but preserve word boundaries and technical terms
        # Keep letters, numbers, spaces, and common technical characters
        text = re.sub(r'[^\w\s+#.-]', ' ', text)
        
        # Simple tokenization by splitting on whitespace
        tokens = text.split()
        
        # Remove stop words while preserving technical terms
        filtered_tokens = []
        for token in tokens:
            # Clean the token of any remaining punctuation
            clean_token = token.strip(string.punctuation)
            
            # Keep the token if it's a technical term
            if clean_token.lower() in TECHNICAL_TERMS:
                filtered_tokens.append(clean_token.lower())
            # Keep the token if it's not a stop word and not just punctuation
            elif clean_token.lower() not in STOP_WORDS and clean_token:
                # Keep single character tokens if they might be technical (like 'c', 'r', 'go')
                if len(clean_token) > 1 or clean_token.lower() in {'c', 'r', 'go'}:
                    filtered_tokens.append(clean_token.lower())
        
        # Join tokens back into text
        processed_text = ' '.join(filtered_tokens)
        
        # Final cleanup of any remaining multiple spaces
        processed_text = re.sub(r' +', ' ', processed_text).strip()
        
        if not processed_text:
            logger.warning("Text became empty after preprocessing")
            return ""
        
        logger.info(f"Successfully preprocessed text (length: {len(processed_text)})")
        return processed_text
        
    except Exception as e:
        logger.error(f"Error preprocessing text: {str(e)}")
        return ""


def preprocess_job_description(description: Optional[str]) -> str:
    """
    Preprocess job description text for TF-IDF and similarity matching.
    
    This is a wrapper function that reuses the existing preprocess_text() function
    to ensure consistent preprocessing between resumes and job descriptions.
    
    The goal is to ensure that both resume text and job description text go through
    the same normalization pipeline for accurate similarity matching.
    
    Args:
        description: Raw job description text, or None/empty string.
        
    Returns:
        Preprocessed job description suitable for TF-IDF processing.
        Returns empty string for None or empty input.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    logger.info("Preprocessing job description using standard preprocessing pipeline")
    return preprocess_text(description)
