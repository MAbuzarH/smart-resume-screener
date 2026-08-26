"""
Seed data script for populating the database with sample job postings.
This script inserts at least five sample jobs into the database.
"""

import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Job
from app.services import preprocess_job_description


def seed_jobs():
    """
    Seed the database with sample job postings.
    Includes duplicate protection based on title + company.
    """
    app = create_app()
    
    with app.app_context():
        sample_jobs = [
            {
                'title': 'Software Engineer',
                'company': 'TechNova Solutions',
                'location': 'Lahore, Pakistan',
                'description': 'We are looking for a Software Engineer to design, develop, test, and maintain reliable web and software applications. The candidate should be comfortable working with programming languages, databases, APIs, debugging, and software development practices.',
                'skills': 'Python, Flask, SQL, Git, REST API, JavaScript, Problem Solving'
            },
            {
                'title': 'Web Developer',
                'company': 'Digital Horizon',
                'location': 'Islamabad, Pakistan',
                'description': 'We are seeking a Web Developer to build and maintain responsive websites and web applications. The candidate should understand frontend development, backend integration, databases, responsive design, and modern web development practices.',
                'skills': 'HTML, CSS, JavaScript, Bootstrap, Python, Flask, SQL, Git'
            },
            {
                'title': 'Python Developer',
                'company': 'CodeCraft Technologies',
                'location': 'Karachi, Pakistan',
                'description': 'We are looking for a Python Developer to develop backend applications and services. The candidate will work with Python programming, APIs, databases, debugging, testing, and software development workflows.',
                'skills': 'Python, Flask, Django, SQL, REST API, Git, APIs, Testing'
            },
            {
                'title': 'Database Administrator',
                'company': 'DataCore Systems',
                'location': 'Lahore, Pakistan',
                'description': 'We are seeking a Database Administrator to manage database systems, monitor performance, maintain data integrity, perform backups, troubleshoot database issues, and support application teams.',
                'skills': 'SQL, SQLite, MySQL, PostgreSQL, Database Management, Backup, Security, Troubleshooting'
            },
            {
                'title': 'UI/UX Designer',
                'company': 'Creative Pixel Studio',
                'location': 'Islamabad, Pakistan',
                'description': 'We are looking for a UI/UX Designer to create intuitive and responsive digital experiences. The candidate should be able to understand user requirements, create wireframes and prototypes, design interfaces, and collaborate with development teams.',
                'skills': 'UI Design, UX Design, Figma, Wireframing, Prototyping, User Research, Responsive Design'
            }
        ]
        
        print("Seeding sample jobs...")
        
        for job_data in sample_jobs:
            # Check if job already exists (duplicate protection)
            existing_job = Job.query.filter_by(
                title=job_data['title'],
                company=job_data['company']
            ).first()
            
            if existing_job:
                # Update existing job with processed description if missing
                if not existing_job.processed_description:
                    existing_job.processed_description = preprocess_job_description(existing_job.description)
                    db.session.commit()
                    print(f"Updated (added processed description): {job_data['title']}")
                else:
                    print(f"Skipped (already exists): {job_data['title']}")
            else:
                # Preprocess the job description
                processed_description = preprocess_job_description(job_data['description'])
                
                job = Job(
                    title=job_data['title'],
                    company=job_data['company'],
                    location=job_data['location'],
                    description=job_data['description'],
                    skills=job_data['skills'],
                    processed_description=processed_description
                )
                db.session.add(job)
                db.session.commit()
                print(f"Added: {job_data['title']}")
        
        print("Sample job seeding completed successfully.")


if __name__ == '__main__':
    seed_jobs()
