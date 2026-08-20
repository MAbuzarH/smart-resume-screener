# Smart Resume Screener & Job Board

## Project Overview

Smart Resume Screener & Job Board is a web application that allows job seekers to browse job postings and submit applications with resume uploads. This is the prototype phase of a university Final Year Project.

## Prototype Scope

The prototype includes:
- Job board with job listings
- Job details page
- Job application form with PDF resume upload
- Applications listing page
- SQLite database for data persistence
- Basic responsive UI with Bootstrap 5

**Note:** This is the prototype foundation only. Advanced features will be implemented in the final project phase.

## Technology Stack

- **Backend:** Python 3.x, Flask
- **Database:** SQLite with Flask-SQLAlchemy
- **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2 templates
- **JavaScript:** Vanilla JavaScript
- **Architecture:** Application factory pattern

## Project Structure

```
Smart Resume Scanner/
│
├── .venv/                          # Virtual environment (DO NOT MODIFY)
│
├── app/
│   ├── __init__.py                 # Flask application factory
│   ├── models/
│   │   ├── __init__.py
│   │   ├── job.py                  # Job database model
│   │   └── application.py          # Application database model
│   ├── routes/
│   │   ├── __init__.py
│   │   └── main.py                 # Flask routes
│   ├── templates/
│   │   ├── base.html               # Base template with Bootstrap
│   │   ├── home.html               # Job board home page
│   │   ├── job_details.html        # Job details page
│   │   ├── apply.html              # Job application form
│   │   └── applications.html       # Applications listing
│   └── static/
│       ├── css/
│       │   └── style.css           # Custom styles
│       └── js/
│           └── main.js             # Custom JavaScript
│
├── uploads/                        # Resume upload directory
│   └── .gitkeep
│
├── instance/                       # Local application data
│   └── .gitkeep
│
├── tests/
│   ├── __init__.py
│   ├── test_jobs.py                # Job model tests
│   └── test_applications.py        # Application model tests
│
├── scripts/
│   └── seed_data.py                # Database seeding script
│
├── docs/
│   ├── SRS/                        # Software Requirements Specification
│   ├── design/                     # Design documentation
│   └── prototype/                  # Prototype documentation
│
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── config.py                       # Flask configuration
├── requirements.txt                # Python dependencies
├── run.py                          # Application entry point
└── README.md                       # This file
```

## Setup Instructions

1. **Clone or navigate to the project directory:**
   ```bash
   cd "d:/new FYP/prototype_phase/smart-resume-screener"
   ```

2. **Activate the virtual environment:**
   ```bash
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional):**
   ```bash
   copy .env.example .env
   # Edit .env with your configuration values
   ```

## How to Run

1. **Activate the virtual environment:**
   ```bash
   .venv\Scripts\activate
   ```

2. **Run the application:**
   ```bash
   python run.py
   ```

3. **Open your browser and navigate to:**
   ```
   http://127.0.0.1:5000
   ```

## Prototype Features

### Currently Implemented (Foundation Only)
- Project structure and architecture
- Database models (Job, Application)
- Route structure
- HTML templates with Bootstrap 5
- Configuration management
- Basic static assets

### To Be Implemented (Next Development Phase)
- Complete route logic
- Form handling and validation
- File upload functionality
- Database operations
- Seed data script execution

## Future Final Project Features

The following features will be implemented in the final project phase (NOT in prototype):

- User authentication and registration
- Employer dashboard
- Admin panel
- Resume parsing and text extraction
- PDF text extraction
- TF-IDF vectorization
- Cosine similarity matching
- Candidate ranking system
- Duplicate application checking
- Job editing and deletion
- Job open/closed status management
- Advanced NLP features

## Database Models

### Job Model
- `id`: Primary key
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `description`: Job description
- `skills`: Required skills

### Application Model
- `id`: Primary key
- `job_id`: Foreign key to Job
- `applicant_name`: Applicant's full name
- `applicant_email`: Applicant's email address
- `resume_filename`: Uploaded resume filename

## Development Notes

- The application uses the Flask application factory pattern
- SQLite database is stored in the `instance/` directory
- Uploaded resumes are stored in the `uploads/` directory
- The virtual environment `.venv/` should never be modified or deleted

## License

This is a university Final Year Project. All rights reserved.
