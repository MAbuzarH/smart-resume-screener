"""
Screening Service

This module provides candidate screening analysis and explainability functionality.
It consumes results from existing services (TF-IDF, skill matching, weighted scoring)
to provide transparent candidate analysis with screening categories and explanations.

The screening analysis includes:
- Final match score breakdown
- Screening category (Strong/Moderate/Low Match)
- Matched and missing skills
- Human-readable explanation
- Transparent scoring rationale

This is a technical screening aid to support human review, not an automatic hiring decision.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from config import Config
from app.services.skill_matching_service import calculate_skill_match, SkillMatchResult

# Configure logging
logger = logging.getLogger(__name__)

# Extract screening thresholds from Config class
STRONG_MATCH_THRESHOLD = Config.STRONG_MATCH_THRESHOLD
MODERATE_MATCH_THRESHOLD = Config.MODERATE_MATCH_THRESHOLD


@dataclass
class ScreeningResult:
    """
    Data class for candidate screening analysis results.
    
    Attributes:
        final_score: Final weighted match score (0-100)
        tfidf_score: TF-IDF/cosine similarity score (0-100)
        skill_score: Skill match percentage (0-100)
        matched_skills: List of skills found in resume
        missing_skills: List of skills not found in resume
        required_skill_count: Total number of required skills
        matched_skill_count: Number of matched skills
        skill_match_percentage: Skill match percentage (0-100)
        category: Screening category (Strong Match, Moderate Match, Low Match, Not Scored)
        explanation: Human-readable explanation of the screening result
    """
    final_score: Optional[float]
    tfidf_score: Optional[float]
    skill_score: Optional[float]
    matched_skills: List[str]
    missing_skills: List[str]
    required_skill_count: int
    matched_skill_count: int
    skill_match_percentage: float
    category: str
    explanation: str


def get_screening_category(final_score: Optional[float]) -> str:
    """
    Determine screening category based on final match score.
    
    Args:
        final_score: Final weighted match score (0-100)
        
    Returns:
        Screening category: "Strong Match", "Moderate Match", "Low Match", or "Not Scored"
    """
    if final_score is None:
        return "Not Scored"
    
    # Validate score range
    if not isinstance(final_score, (int, float)):
        return "Not Scored"
    
    if final_score < 0 or final_score > 100:
        return "Not Scored"
    
    # Apply screening thresholds
    if final_score >= STRONG_MATCH_THRESHOLD:
        return "Strong Match"
    elif final_score >= MODERATE_MATCH_THRESHOLD:
        return "Moderate Match"
    else:
        return "Low Match"


def generate_explanation(
    category: str,
    tfidf_score: Optional[float],
    skill_score: Optional[float],
    matched_skill_count: int,
    required_skill_count: int,
    missing_skills: List[str]
) -> str:
    """
    Generate human-readable explanation based on screening results.
    
    The explanation is factual and transparent, based on actual scoring results.
    It does not make automatic hiring decisions but provides screening recommendations.
    
    Args:
        category: Screening category
        tfidf_score: TF-IDF/cosine similarity score
        skill_score: Skill match percentage
        matched_skill_count: Number of matched skills
        required_skill_count: Total number of required skills
        missing_skills: List of missing skills
        
    Returns:
        Human-readable explanation string
    """
    if category == "Not Scored":
        return "This application has not been scored yet. Resume-to-job matching analysis is required to generate a screening recommendation."
    
    if category == "Strong Match":
        base_explanation = "Strong Match. The candidate demonstrates high overall alignment with the job requirements."
        
        # Add specific details based on scores
        if skill_score and skill_score >= 80:
            base_explanation += " The candidate matches most of the required skills."
        elif skill_score and skill_score >= 60:
            base_explanation += " The candidate matches a good portion of the required skills."
        
        if tfidf_score and tfidf_score >= 80:
            base_explanation += " The resume shows strong textual similarity to the job description."
        elif tfidf_score and tfidf_score >= 60:
            base_explanation += " The resume shows reasonable textual similarity to the job description."
        
        if missing_skills:
            base_explanation += f" Some required skills are missing: {', '.join(missing_skills[:3])}."
        
        return base_explanation + " Requires human review to confirm fit for the specific role."
    
    elif category == "Moderate Match":
        base_explanation = "Moderate Match. The candidate shows reasonable alignment with the job requirements."
        
        # Add specific details
        if matched_skill_count > 0 and required_skill_count > 0:
            skill_ratio = matched_skill_count / required_skill_count
            if skill_ratio >= 0.7:
                base_explanation += " The candidate matches a good portion of the required skills."
            elif skill_ratio >= 0.5:
                base_explanation += " The candidate matches about half of the required skills."
            else:
                base_explanation += " The candidate matches fewer than half of the required skills."
        
        if missing_skills:
            if len(missing_skills) <= 3:
                base_explanation += f" Missing skills: {', '.join(missing_skills)}."
            else:
                base_explanation += f" Missing several skills including: {', '.join(missing_skills[:3])}."
        
        if tfidf_score and tfidf_score < 60:
            base_explanation += " The resume has limited textual similarity to the job description."
        
        return base_explanation + " Requires human review to assess overall fit for the role."
    
    else:  # Low Match
        base_explanation = "Low Match. The candidate has limited alignment with the job requirements."
        
        # Add specific details
        if matched_skill_count == 0 and required_skill_count > 0:
            base_explanation += " None of the required skills were found in the resume."
        elif matched_skill_count > 0 and required_skill_count > 0:
            skill_ratio = matched_skill_count / required_skill_count
            if skill_ratio < 0.3:
                base_explanation += " Very few of the required skills were found in the resume."
            else:
                base_explanation += " Only a small portion of the required skills were found in the resume."
        
        if missing_skills and len(missing_skills) > 0:
            if len(missing_skills) <= 3:
                base_explanation += f" Missing skills: {', '.join(missing_skills)}."
            else:
                base_explanation += f" Missing multiple skills including: {', '.join(missing_skills[:3])}."
        
        if tfidf_score and tfidf_score < 50:
            base_explanation += " The resume has very limited textual similarity to the job description."
        
        return base_explanation + " Requires human review to determine if there are other compensating factors."


def analyze_candidate(application, job) -> ScreeningResult:
    """
    Analyze a candidate's application against job requirements.
    
    This function consumes results from existing services to provide a comprehensive
    screening analysis with explainability. It does not duplicate scoring logic.
    
    Args:
        application: Application object with scoring fields
        job: Job object with requirements
        
    Returns:
        ScreeningResult containing comprehensive candidate analysis
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    try:
        # Extract scores from application (handle None values)
        final_score = application.final_match_score
        tfidf_score = application.similarity_score or application.match_score  # Use similarity_score or fall back to match_score
        skill_score = application.skill_match_score
        
        # Perform skill matching if resume text is available
        matched_skills = []
        missing_skills = []
        required_skill_count = 0
        matched_skill_count = 0
        skill_match_percentage = 0.0
        
        if application.resume_text and job.skills:
            skill_result = calculate_skill_match(application.resume_text, job.skills)
            matched_skills = skill_result.matched_skills
            missing_skills = skill_result.missing_skills
            required_skill_count = skill_result.required_count
            matched_skill_count = skill_result.matched_count
            skill_match_percentage = skill_result.skill_match_percentage
        elif job.skills:
            # If job has skills but no resume text, extract required skills
            from app.services.skill_matching_service import extract_skills_from_job
            required_skills = extract_skills_from_job(job.skills)
            required_skill_count = len(required_skills)
            matched_skill_count = 0
            matched_skills = []
            missing_skills = required_skills
            skill_match_percentage = 0.0
        
        # Determine screening category
        category = get_screening_category(final_score)
        
        # Generate explanation
        explanation = generate_explanation(
            category,
            tfidf_score,
            skill_score,
            matched_skill_count,
            required_skill_count,
            missing_skills
        )
        
        # Round scores for display
        if final_score is not None:
            final_score = round(final_score, 2)
        if tfidf_score is not None:
            tfidf_score = round(tfidf_score, 2)
        if skill_score is not None:
            skill_score = round(skill_score, 2)
        
        logger.info(f"Screening analysis completed for application {application.id}: {category}")
        
        return ScreeningResult(
            final_score=final_score,
            tfidf_score=tfidf_score,
            skill_score=skill_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            required_skill_count=required_skill_count,
            matched_skill_count=matched_skill_count,
            skill_match_percentage=skill_match_percentage,
            category=category,
            explanation=explanation
        )
        
    except Exception as e:
        logger.error(f"Error analyzing candidate application {application.id}: {str(e)}")
        # Return a safe default result
        return ScreeningResult(
            final_score=None,
            tfidf_score=None,
            skill_score=None,
            matched_skills=[],
            missing_skills=[],
            required_skill_count=0,
            matched_skill_count=0,
            skill_match_percentage=0.0,
            category="Not Scored",
            explanation="An error occurred during screening analysis. Please review the application manually."
        )


def get_screening_thresholds() -> Dict[str, float]:
    """
    Get the current screening threshold configuration.
    
    Returns:
        Dictionary containing screening thresholds
    """
    return {
        'strong_match_threshold': STRONG_MATCH_THRESHOLD,
        'moderate_match_threshold': MODERATE_MATCH_THRESHOLD
    }