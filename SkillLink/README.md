# SkillLink - Job Portal Application

## Project Structure

### Backend (Flask Application)
- **Location**: `/backend/`
- **Main File**: `app.py`
- **Templates**: HTML files in `/backend/templates/`
- **Static Files**: CSS in `/backend/static/`
- **Database**: SQLite in `/backend/instance/`
- **Dependencies**: `requirements.txt`

### Frontend (Landing Page)
- **Location**: `/frontend/`
- **Main File**: `index.html`
- **Deployment**: `Procfile`, `run.bat`

## Features
- Phone-based authentication (no OTP)
- Role-based profiles (Employer/Job Seeker)
- Job posting and application system
- Real-time notifications
- Direct contact between employers and candidates

## Setup Instructions

### Backend Setup
1. Navigate to backend folder: `cd backend`
2. Install dependencies: `pip install -r requirements.txt`
3. Run application: `python app.py`
4. Access at: `http://localhost:5000`

### Frontend Setup
1. Open `frontend/index.html` in browser
2. Or use `frontend/run.bat` to start backend

## Technology Stack
- **Backend**: Flask, SQLAlchemy, SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Phone-based login
- **Database**: SQLite with user profiles, jobs, notifications

## Usage
1. **Sign Up**: Choose role (Employer/Job Seeker) and create account
2. **Complete Profile**: Fill all required profile information
3. **Job Seekers**: Browse jobs, apply, receive notifications
4. **Employers**: Post jobs, receive applications with candidate details
5. **Communication**: Direct phone/email contact between parties