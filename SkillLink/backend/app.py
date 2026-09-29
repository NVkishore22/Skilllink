from flask import Flask, render_template, request, redirect, jsonify, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import os
from pymongo import MongoClient

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.secret_key = 'your-production-secret-key-here'
# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kishorenalabothula33@gmail.com'
app.config['MAIL_PASSWORD'] = 'dbty eedp pqfc cycq'

def send_email(to_email, subject, body):
    try:
        username = app.config.get('MAIL_USERNAME')
        password = app.config.get('MAIL_PASSWORD')
        if username and password and to_email:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = username
            msg['To'] = to_email
            msg.set_content(body)

            server = smtplib.SMTP(app.config.get('MAIL_SERVER'), app.config.get('MAIL_PORT'))
            try:
                if app.config.get('MAIL_USE_TLS'):
                    server.starttls()
                server.login(username, password)
                server.send_message(msg)
            finally:
                server.quit()
    except Exception as e:
        print(f'Email error: {e}')

# MongoDB connection
client = MongoClient(os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'))
db = client.SkillLink
users_collection = db.users
profiles_collection = db.profiles
jobs_collection = db.jobs
notifications_collection = db.notifications
applications_collection = db.applications

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.role = user_data.get('role')
        self.email = user_data.get('email')
        self.password = user_data.get('password')
        self.is_verified = user_data.get('is_verified', True)

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password, pwd)
    
    @property
    def profile(self):
        return profiles_collection.find_one({'user_id': self.id})

    @staticmethod
    def get(user_id):
        user_data = users_collection.find_one({'id': user_id})
        return User(user_data) if user_data else None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        if users_collection.find_one({'email': data['email']}):
            flash('Email already registered')
            return redirect('/signup')
        user_id = str(uuid.uuid4())
        user_doc = {
            'id': user_id,
            'role': data['role'],
            'email': data['email'],
            'password': generate_password_hash(data['password']),
            'is_verified': True
        }
        users_collection.insert_one(user_doc)
        u = User(user_doc)
        login_user(u)
        return redirect('/')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        user_data = users_collection.find_one({'email': email})
        if user_data:
            u = User(user_data)
            if u.check_password(request.form['password']):
                login_user(u)
                return redirect('/')
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            data = request.form
            
            # Validate required fields
            required_fields = ['name', 'email', 'mobile', 'location']
            if current_user.role == 'worker':
                required_fields.append('skills')
            elif current_user.role == 'employer':
                required_fields.extend(['workplace_name', 'description'])
            
            for field in required_fields:
                if not data.get(field, '').strip():
                    flash(f'{field.title().replace("_", " ")} is required')
                    return redirect('/profile')
            
            profile_doc = {
                'user_id': current_user.id,
                'role': current_user.role,
                'name': data.get('name', '').strip(),
                'location': data.get('location', '').strip(),
                'mobile': data.get('mobile', '').strip(),
                'email': data.get('email', '').strip()
            }
            
            if current_user.role == 'worker':
                profile_doc['skills'] = data.get('skills', '').strip()
            elif current_user.role == 'employer':
                profile_doc['workplace_name'] = data.get('workplace_name', '').strip()
                profile_doc['description'] = data.get('description', '').strip()
            
            profiles_collection.replace_one({'user_id': current_user.id}, profile_doc, upsert=True)
            flash('Profile updated successfully!')
        except Exception as e:
            flash('Error updating profile')
            print(f'Profile error: {e}')
        return redirect('/profile')
    
    profile = profiles_collection.find_one({'user_id': current_user.id})
    return render_template('profile.html', profile=profile)

@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    q_location = request.args.get('location')
    q_title = request.args.get('title')
    
    query = {}
    if q_location:
        query['location'] = {'$regex': q_location, '$options': 'i'}
    if q_title:
        query['title'] = {'$regex': q_title, '$options': 'i'}
    
    jobs = list(jobs_collection.find(query))
    return render_template('jobs.html', jobs=jobs)

@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'employer':
        flash('Only employers can post jobs')
        return redirect('/jobs')
    
    # Check if profile is completed
    profile = profiles_collection.find_one({'user_id': current_user.id})
    if not profile:
        flash('Please complete your profile before posting jobs')
        return redirect('/profile')
    
    if request.method == 'POST':
        data = request.form
        job_doc = {
            'title': data['title'],
            'location': data['location'],
            'description': data['description'],
            'employer_id': current_user.id,
            'created_at': datetime.utcnow()
        }
        job_id = str(uuid.uuid4())
        job_doc['id'] = job_id
        jobs_collection.insert_one(job_doc)
        
        # Notify job seekers with employer details
        employer_profile = current_user.profile
        employer_name = employer_profile.get('name') if employer_profile else current_user.email
        employer_phone = employer_profile.get('mobile') if employer_profile else 'Not provided'
        employer_email = employer_profile.get('email') if employer_profile else 'Not provided'
        employer_location = employer_profile.get('location') if employer_profile else 'Not provided'
        
        message = f"New Job Posted: {data['title']}\nLocation: {data['location']}\nEmployer: {employer_name}\nPhone: {employer_phone}\nEmail: {employer_email}\nCompany Location: {employer_location}"
        
        workers = users_collection.find({
            'role': 'worker',
            'id': {'$ne': current_user.id}  # Exclude the employer
        })
        
        notified_users = set()  # Track notified users to prevent duplicates
        for worker in workers:
            if worker['id'] not in notified_users:
                notification_doc = {
                    'id': str(uuid.uuid4()),
                    'user_id': worker['id'],
                    'message': message,
                    'is_read': False,
                    'created_at': datetime.utcnow().isoformat()
                }
                notifications_collection.insert_one(notification_doc)
                notified_users.add(worker['id'])
                
                # Send email notification
                worker_profile = profiles_collection.find_one({'user_id': worker['id']})
                if worker_profile and worker_profile.get('email'):
                    send_email(worker_profile['email'], f"New Job: {data['title']}", message)
        
        flash('Job posted successfully!')
        return redirect('/jobs')
    
    return render_template('post_job.html')

@app.route('/jobs/<job_id>/apply', methods=['POST'])
@login_required
def apply_job(job_id):
    # Check if profile is completed
    profile = profiles_collection.find_one({'user_id': current_user.id})
    if not profile:
        return jsonify({"status": "Error", "message": "Please complete your profile before applying"})
    
    # Check if already applied
    existing_application = applications_collection.find_one({
        'job_id': job_id,
        'applicant_id': current_user.id
    })
    if existing_application:
        return jsonify({"status": "Error", "message": "You have already applied for this job"})
    
    job = jobs_collection.find_one({'id': job_id})
    if job and job.get('employer_id'):
        # Record the application
        application_doc = {
            'id': str(uuid.uuid4()),
            'job_id': job_id,
            'applicant_id': current_user.id,
            'applied_at': datetime.utcnow()
        }
        applications_collection.insert_one(application_doc)
        
        profile = current_user.profile
        applicant_name = profile.get('name') if profile else current_user.email
        applicant_phone = profile.get('mobile') if profile else 'Not provided'
        applicant_email = profile.get('email') if profile else 'Not provided'
        applicant_skills = profile.get('skills') if profile else 'Not provided'
        
        message = f"New Application for {job['title']}\nApplicant: {applicant_name}\nPhone: {applicant_phone}\nEmail: {applicant_email}\nSkills: {applicant_skills}"
        
        notification_doc = {
            'id': str(uuid.uuid4()),
            'user_id': job['employer_id'],
            'message': message,
            'is_read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        notifications_collection.insert_one(notification_doc)
        
        # Send email notification to employer
        employer_profile = profiles_collection.find_one({'user_id': job['employer_id']})
        if employer_profile and employer_profile.get('email'):
            send_email(employer_profile['email'], f"New Application for {job['title']}", message)
    return jsonify({"status": "Applied"})



@app.route('/notifications')
@login_required
def notifications():
    user_notifications = list(notifications_collection.find(
        {'user_id': current_user.id}
    ).sort('created_at', -1))
    return render_template('notifications.html', notifications=user_notifications)

@app.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notifications_collection.update_one(
        {'id': notification_id},
        {'$set': {'is_read': True}}
    )
    return redirect('/notifications')

@app.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        count = notifications_collection.count_documents({
            'user_id': current_user.id,
            'is_read': False
        })
        return {'notification_count': count}
    return {'notification_count': 0}

if __name__ == '__main__':
    print("MongoDB SkillLink App Starting...")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=False, threaded=True, use_reloader=False)