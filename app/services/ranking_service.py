"""
Ranking Service

This module provides candidate ranking functionality for job applications.
It ranks candidates based on their final_match_score (or match_score for backward compatibility) for a specific job.

The ranking algorithm:
- Primary: Higher final_match_score = higher rank (uses match_score if final_match_score is NULL)
- Secondary: Lower application ID = higher rank (for ties)
- NULL scores: Appear after all valid scores
"""

import logging
from typing import List, Dict, Any, Optional
from app.models import Application

# Configure logging
logger = logging.getLogger(__name__)


def rank_candidates(applications: List[Application]) -> List[Dict[str, Any]]:
    """
    Rank candidates for a single job based on their final match scores.
    
    This function:
    - Accepts applications belonging to ONE job
    - Uses final_match_score if available, falls back to match_score for backward compatibility
    - Sorts candidates by score (highest to lowest)
    - Uses application ID as tie-breaker for deterministic ordering
    - Places candidates with NULL scores after those with valid scores
    - Assigns ranking positions (1, 2, 3, ...)
    - Returns ranked candidates with their rank information
    
    Ranking Rules:
    - Primary: Higher score = higher rank (final_match_score preferred, else match_score)
    - Secondary: Lower application ID = higher rank (for ties)
    - NULL scores: Appear after all valid scores (treated as -infinity)
    
    Args:
        applications: List of Application objects for a single job
        
    Returns:
        List of dictionaries containing:
        - 'application': The Application object
        - 'rank': The rank position (1-based)
        - 'match_score': The match score (may be None)
        - 'final_match_score': The final weighted score (may be None)
        
        Returns empty list if no applications provided.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    if not applications:
        logger.warning("Empty applications list provided to rank_candidates")
        return []
    
    try:
        # Separate applications with valid scores and NULL scores
        valid_scores = []
        null_scores = []
        
        for app in applications:
            # Use final_match_score if available, else fall back to match_score
            score = app.final_match_score if app.final_match_score is not None else app.match_score
            
            if score is not None:
                valid_scores.append((app, score))
            else:
                null_scores.append(app)
        
        # Sort valid scores by score DESC, then by id ASC (for tie-breaking)
        # This ensures deterministic ordering: higher scores first, and for ties,
        # the application with lower ID (earlier submission) gets higher rank
        valid_scores_sorted = sorted(
            valid_scores,
            key=lambda item: (-item[1], item[0].id)
        )
        
        # Sort NULL scores by id ASC (for consistency)
        null_scores_sorted = sorted(
            null_scores,
            key=lambda app: app.id
        )
        
        # Combine: valid scores first, then NULL scores
        all_sorted = [item[0] for item in valid_scores_sorted] + null_scores_sorted
        
        # Assign ranks
        ranked_candidates = []
        for rank, app in enumerate(all_sorted, start=1):
            # Use final_match_score if available, else match_score
            display_score = app.final_match_score if app.final_match_score is not None else app.match_score
            ranked_candidates.append({
                'application': app,
                'rank': rank,
                'match_score': app.match_score,
                'final_match_score': app.final_match_score
            })
        
        logger.info(f"Successfully ranked {len(ranked_candidates)} candidates")
        return ranked_candidates
        
    except Exception as e:
        logger.error(f"Error ranking candidates: {str(e)}")
        return []


def rank_applications_by_job(job_id: int) -> List[Dict[str, Any]]:
    """
    Rank all applications for a specific job.
    
    This is a convenience function that retrieves applications for a job
    and ranks them in a single call.
    
    Args:
        job_id: The ID of the job to rank applications for
        
    Returns:
        List of ranked candidates for the job.
        Returns empty list if job has no applications or job doesn't exist.
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    try:
        from app import db
        
        # Get all applications for this job
        applications = Application.query.filter_by(job_id=job_id).all()
        
        if not applications:
            logger.info(f"No applications found for job {job_id}")
            return []
        
        # Rank the applications
        ranked = rank_candidates(applications)
        
        return ranked
        
    except Exception as e:
        logger.error(f"Error ranking applications for job {job_id}: {str(e)}")
        return []


def rank_all_applications_by_job() -> Dict[int, List[Dict[str, Any]]]:
    """
    Rank applications for all jobs, grouped by job.
    
    This function retrieves all jobs and ranks their applications separately.
    Useful for displaying job-specific rankings on the applications page.
    
    Returns:
        Dictionary mapping job_id to list of ranked candidates for that job.
        Example: {1: [ranked_candidates_for_job_1], 2: [ranked_candidates_for_job_2]}
        
    Raises:
        No exceptions are raised to the caller. All errors are caught and logged.
    """
    try:
        from app import db
        from app.models import Job
        
        # Get all jobs
        jobs = Job.query.all()
        
        # Rank applications for each job
        rankings_by_job = {}
        for job in jobs:
            ranked = rank_applications_by_job(job.id)
            if ranked:
                rankings_by_job[job.id] = ranked
        
        logger.info(f"Ranked applications for {len(rankings_by_job)} jobs")
        return rankings_by_job
        
    except Exception as e:
        logger.error(f"Error ranking all applications by job: {str(e)}")
        return {}
