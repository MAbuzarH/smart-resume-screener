"""
Resume Parser Service

This module provides PDF text extraction functionality for processing uploaded resumes.
Uses PyMuPDF for reliable PDF text extraction.
"""

import pymupdf  # PyMuPDF (formerly fitz)
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file to extract text from.
        
    Returns:
        Extracted text as a string, or None if extraction fails.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if not file_path:
        logger.error("Empty file path provided to extract_text_from_pdf")
        return None
    
    try:
        # Open the PDF file
        doc = pymupdf.open(file_path)
        
        # Check if the document is empty
        if doc.page_count == 0:
            logger.warning(f"PDF file is empty: {file_path}")
            doc.close()
            return None
        
        # Extract text from all pages
        extracted_text = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():  # Only add non-empty text
                extracted_text.append(text)
        
        # Close the document
        doc.close()
        
        # Combine all page text with newlines
        full_text = "\n\n".join(extracted_text)
        
        # Check if we got any meaningful text
        if not full_text.strip():
            logger.warning(f"No text extracted from PDF: {file_path}")
            return None
        
        logger.info(f"Successfully extracted text from PDF: {file_path}")
        return full_text
        
    except pymupdf.FileDataError:
        logger.error(f"Invalid or corrupted PDF file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        return None
