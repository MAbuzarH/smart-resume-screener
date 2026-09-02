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
- User authentication and role-based access control
- Secure password hashing
- Applicant and employer registration
- Recruiter dashboard with candidate ranking
- Resume text extraction and preprocessing
- TF-IDF vectorization and cosine similarity matching
- Skill-based matching system
- Weighted final scoring model
- Candidate screening and explainability
- Comprehensive test suite
- Employer job management (create, edit, open/close jobs)
- Job ownership and authorization
- Secure resume download
- Applicant management (dashboard, applications, duplicate prevention)
- Application ownership and status tracking

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

2. **Seed the database with sample data:**
   ```bash
   python scripts\seed_data.py
   ```

3. **Run the application:**
   ```bash
   python run.py
   ```

4. **Open your browser and navigate to:**
   ```
   http://127.0.0.1:5000
   ```

## Employer Management

Employers can manage their job postings through the employer dashboard:

### Creating Jobs
- Navigate to Dashboard → Create New Job
- Fill in job title, company, location, description, and required skills
- Jobs are automatically associated with the logged-in employer
- New jobs are created as "Open" by default

### Managing Jobs
- **Edit**: Modify job details (title, company, location, description, skills)
- **Open/Close**: Toggle job status to accept or stop accepting applications
- **View Candidates**: See ranked applicants for each job
- **Download Resumes**: Securely download applicant resumes (employer-only)

### Job Status
- **Open**: Visible in public job listings, accepting applications
- **Closed**: Hidden from public listings, not accepting new applications
- Existing applications and scoring data remain intact when jobs are closed

### Authorization
- Employers can only manage their own jobs
- Secure resume download with employer ownership verification
- Role-based access control enforced server-side

## Applicant Management

Applicants can manage their job search and applications through the applicant dashboard:

### Applicant Dashboard
- View all open job postings
- See application statistics (total applications, scored applications)
- Quick access to available jobs
- Navigate to "My Applications" page

### Browsing Jobs
- View all open job listings
- Filter by job status (only open jobs shown)
- View job details including:
  - Job title, company, location
  - Job description
  - Required skills
  - Job status (Open/Closed)

### Applying for Jobs
- Apply to open jobs only
- Form pre-populated with authenticated user information (name, email)
- Upload PDF resume
- Automatic duplicate application prevention
- Resume processing and scoring via existing pipeline

### My Applications
- View all submitted applications
- See application status (Submitted, etc.)
- View match scores and screening results
- Track application history
- Access application details

### Application Details
- View comprehensive application information
- See job details and requirements
- View match scores (TF-IDF, skill match, final score)
- See screening category and explanation
- View matched and missing skills
- Important notice about score interpretation

### Duplicate Prevention
- System prevents duplicate applications to the same job
- Clear message when duplicate submission attempted
- Protects against accidental multiple submissions

### Closed Job Protection
- Closed jobs not shown in open job listings
- Applications to closed jobs rejected
- Existing applications remain intact when jobs close
- Historical data preserved

### Application Status
- Status field tracks application lifecycle
- Default status: "Submitted"
- Extensible for future workflow enhancements
- Timestamps track application history

## Admin Management

Admins have platform-wide oversight and management capabilities:

### Admin Dashboard
- View platform statistics (users, jobs, applications)
- Monitor recent activity (users, jobs, applications)
- Quick access to user management and job moderation
- Database-derived real-time statistics

### User Management
- View all registered users with filtering by role and status
- Suspend user accounts (prevents login without data deletion)
- Reactivate suspended user accounts
- Delete user accounts (only when safe, with data integrity checks)
- Role-based filtering (Applicant, Employer, Admin)
- Status-based filtering (Active, Inactive)

### User Suspension/Activation
- Suspended users cannot log in
- Existing data (jobs, applications, resumes) preserved during suspension
- Reactivation restores full access without data loss
- Admin self-protection (cannot suspend/delete own account)
- Last admin protection (cannot suspend last active admin)

### Job Moderation
- View all job postings regardless of employer ownership
- Remove jobs from public listings (soft deletion via status change)
- Permanently delete jobs (only when safe, with application checks)
- Job status indicators (Open/Closed)
- Application counts per job
- Employer information display

### Platform Monitoring
- Real-time user statistics (total, applicants, employers, admins)
- Job statistics (total, open, closed)
- Application statistics (total, scored, unscored)
- Recent activity tracking (users, jobs, applications)
- Data integrity preservation

### Admin Authorization
- Admin-only access to all admin routes
- Server-side role verification
- Protected against unauthorized access
- Role-based redirect for unauthorized attempts

## Authentication

### Development Admin Account
After running the seed script, a development admin account is created:
- **Email:** admin@smartresume.com
- **Password:** admin123
- **Role:** Admin

**Note:** For testing purposes, additional admin accounts can be created manually through the database or by modifying the seed script. Admin accounts should only be created through controlled mechanisms, not public registration.

### User Roles
- **Applicant:** Can browse jobs and submit applications
- **Employer:** Can access the recruiter dashboard and view ranked candidates
- **Admin:** Has full system access (foundation for future admin features)

### Registration
Public registration is available for:
- Job Applicants
- Employers/Recruiters

Admin accounts cannot be created through public registration and must be created via the seed script or database operations.

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

## Testing

The project includes a comprehensive test suite. To run tests:

```bash
python -m pytest
```

The test suite covers:
- Database models (Job, Application, User)
- Authentication and authorization
- Resume parsing and text extraction
- Text preprocessing
- TF-IDF vectorization
- Cosine similarity matching
- Skill-based matching
- Weighted scoring models
- Candidate ranking
- Screening and explainability
- Dashboard functionality
- Integration tests

## Database Models

### Job Model
- `id`: Primary key
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `description`: Job description
- `skills`: Required skills
- `processed_description`: Preprocessed job description for TF-IDF
- `employer_id`: Foreign key to User (job owner)
- `is_open`: Job status (Open/Closed)
- `created_at`: Job creation timestamp
- `updated_at`: Last update timestamp

### Application Model
- `id`: Primary key
- `job_id`: Foreign key to Job
- `applicant_id`: Foreign key to User (application owner)
- `applicant_name`: Applicant's full name
- `applicant_email`: Applicant's email address
- `resume_filename`: Uploaded resume filename
- `resume_text`: Extracted resume text
- `processed_resume_text`: Preprocessed resume text
- `match_score`: Original TF-IDF match score (legacy)
- `similarity_score`: TF-IDF/cosine similarity score
- `skill_match_score`: Skill match percentage
- `final_match_score`: Weighted final match score
- `status`: Application status (Submitted, etc.)
- `created_at`: Application creation timestamp
- `updated_at`: Last update timestamp

### User Model
- `id`: Primary key
- `full_name`: User's full name
- `email`: User's email (unique)
- `password_hash`: Securely hashed password
- `role`: User role (applicant, employer, admin)
- `is_active`: Account status (suspended accounts cannot login)
- `created_at`: Account creation timestamp

## Development Notes

- The application uses the Flask application factory pattern
- SQLite database is stored in the `instance/` directory
- Uploaded resumes are stored in the `uploads/` directory
- The virtual environment `.venv/` should never be modified or deleted
- Passwords are securely hashed using Werkzeug's security functions
- Authentication is required for job applications and dashboard access
- The existing resume screening pipeline (PDF → Text → Preprocessing → TF-IDF → Similarity → Skill Matching → Scoring → Ranking → Screening) remains fully functional

## License

This is a university Final Year Project. All rights reserved.
