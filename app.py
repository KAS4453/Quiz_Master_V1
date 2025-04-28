# app.py
# Import the required libraries
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
from datetime import datetime, date
import os
import random
import copy
import pytz

# Setting the timezone for the quiz
LOCAL_TZ = pytz.timezone('Asia/Kolkata')

# Setting up the Flask Application
app = Flask(__name__)
app.config['SECRET_KEY'] = '#KAS22f3000668'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initializing the database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

##########################################
#                MODELS                  #
##########################################

# User model for both Admin and Regular Users.
class User(db.Model):
    # Unique identifier for each user (primary key)
    id = db.Column(db.Integer, primary_key=True)
    # User's login name, must be unique and cannot be null
    username = db.Column(db.String(100), unique=True, nullable=False)
    # Password for user authentication, required field
    password = db.Column(db.String(100), nullable=False)
    # Full name of the user, optional field
    full_name = db.Column(db.String(100))
    # Educational or professional qualification of the user, optional field
    qualification = db.Column(db.String(100))
    # Date of birth of the user, stored as a Date type
    dob = db.Column(db.Date)
    # Role of the user (e.g., 'admin' or 'user'), required field with a max length of 20 characters
    role = db.Column(db.String(20), nullable=False)
    # Points earned by the user, defaults to 0 if not specified
    points = db.Column(db.Integer, default=0)
    # Establishing a one-to-many relationship with the Score model;
    # A user can have multiple score records. The 'backref' allows reverse access.
    scores = db.relationship('Score', backref='user', lazy=True, cascade="all, delete-orphan")

# Subject model for the subject
class Subject(db.Model):
    # Unique identifier for the subject (primary key)
    id = db.Column(db.Integer, primary_key=True)
    # Name of the subject; this field is required
    name = db.Column(db.String(100), nullable=False)
    # Detailed description of the subject; can include syllabus or other info
    description = db.Column(db.Text)
    # Establishes a one-to-many relationship with the Chapter model.
    # If a subject is deleted, all its associated chapters will also be deleted.
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")

# Chapter model
class Chapter(db.Model):
    # Unique identifier for the chapter (primary key)
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key to link the chapter to its subject; subject must exist
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    # Name of the chapter; required field
    name = db.Column(db.String(100), nullable=False)
    # Description of the chapter; optional field for additional details
    description = db.Column(db.Text)
    # One-to-many relationship with the Quiz model.
    # Deleting a chapter will cascade and delete all associated quizzes.
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True, cascade="all, delete-orphan")

# Quiz model
class Quiz(db.Model):
    # Allow extension of an existing table if necessary
    __table_args__ = {'extend_existing': True}
    # Unique identifier for the quiz (primary key)
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking the quiz to a specific chapter; chapter must exist
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    # Date on which the quiz is scheduled; defaults to today's date if not provided
    date_of_quiz = db.Column(db.Date, default=date.today)
    # Duration of the quiz formatted as "HH:MM"
    time_duration = db.Column(db.String(10))
    # Additional remarks or notes about the quiz
    remarks = db.Column(db.Text)
    # Limit on the number of questions in the quiz; required and defaults to 10
    question_limit = db.Column(db.Integer, nullable=False, default=10)
    # The scheduled start time for the quiz; this field is required
    scheduled_at = db.Column(db.DateTime, nullable=False)
    # One-to-many relationship with the Question model.
    # All questions linked to this quiz will be deleted if the quiz is removed.
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    # One-to-many relationship with the Score model.
    # Scores related to this quiz will also be removed if the quiz is deleted.
    scores = db.relationship('Score', backref='quiz', lazy=True, cascade="all, delete-orphan")

# Question model
class Question(db.Model):
    # Unique identifier for the question (primary key)
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking the question to a specific quiz; quiz must exist
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    # The text of the question; required field
    question_statement = db.Column(db.Text, nullable=False)
    # Options for the answer
    option1 = db.Column(db.String(200))
    option2 = db.Column(db.String(200))
    option3 = db.Column(db.String(200))
    option4 = db.Column(db.String(200))
    # Indicates the correct answer (e.g., 'option1'); helps in auto-grading
    correct_option = db.Column(db.String(20))
    # Explanation for the correct answer, providing additional context
    explanation = db.Column(db.Text)

# Score model
class Score(db.Model):
    # Unique identifier for the score record (primary key)
    id = db.Column(db.Integer, primary_key=True)
    # Foreign key linking the score to a specific quiz; quiz must exist
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    # Foreign key linking the score to a specific user; user must exist
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Timestamp when the quiz was attempted; defaults to current UTC time
    time_stamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    # The total score achieved by the user in the quiz
    total_scored = db.Column(db.Integer)

##########################################
#         INITIAL SETUP & DB             #
##########################################
# Create the tables and initialize the admin
@app.before_first_request
def create_tables():
    db.create_all()
    # Check if an admin user already exists
    admin = User.query.filter_by(role='admin').first()
    # If no admin exists, create a default admin use
    if not admin:
        default_admin = User(username='admin@example.com', password='admin', full_name='Quiz Master', role='admin')
        # Add the default admin to the session
        db.session.add(default_admin)
        # Commit the transaction to persist the admin
        db.session.commit()

# Route to view details for a specific subject
@app.route('/admin/subject/view/<int:subject_id>')
def view_subject(subject_id):
    # Check if the current session has an admin role
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the subject by its ID, or return a 404 error if not founds
    subject = Subject.query.get_or_404(subject_id)
    # Render the template to display subject details along with its chapters
    return render_template('subject_details.html', subject=subject)

# View details for a specific chapter (list its quizzes)
@app.route('/admin/chapter/view/<int:chapter_id>')
def view_chapter(chapter_id):
    # Ensure that only an admin can access this route
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the chapter by its ID or return a 404 error if not found
    chapter = Chapter.query.get_or_404(chapter_id)
    # Render the template showing details of the chapter and its quizzes
    return render_template('chapter_details.html', chapter=chapter)

# View details for a specific quiz (list its questions)
@app.route('/admin/quiz/view/<int:quiz_id>')
def view_quiz(quiz_id):
    # Only allow admin users to access this route
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the quiz by its ID or return a 404 error if not found
    quiz = Quiz.query.get_or_404(quiz_id)
    # Render the template to display quiz details including its questions
    return render_template('quiz_details.html', quiz=quiz)

# Route to view all questions for a specific chapter by aggregating questions from all its quizzes
@app.route('/admin/chapter/questions/<int:chapter_id>')
def view_chapter_questions(chapter_id):
    # Verify that the user is an admin before allowing access
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the chapter using its ID or return a 404 error if not found
    chapter = Chapter.query.get_or_404(chapter_id)
    questions = []
    # Loop through each quiz in the chapter and collect all questions
    for quiz in chapter.quizzes:
        questions.extend(quiz.questions)
    # Render the template to display all questions associated with the chapter
    return render_template('chapter_questions.html', chapter=chapter, questions=questions)


##########################################
#            ROUTES - PUBLIC             #
##########################################

# Route for the home page. Renders the main index page.
@app.route('/')
def index():
    return render_template('index.html')

# Admin login route.
# Handles both GET and POST requests for admin login.
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # If the form is submitted (POST request)
    if request.method == 'POST':
        # Get username and password from the submitted form
        username  = request.form['username']
        password  = request.form['password']
        # Query the database for a user matching the provided credentials
        user = User.query.filter_by(username=username, password=password).first()
        # Check if user exists and if the role is admin
        if user and user.role == 'admin':
            # Set session variables for logged in admin
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Logged in as admin.', 'success')
            # Redirect to the admin dashboard after successful login
            return redirect(url_for('admin_dashboard'))
        else:
            # Display error message if credentials are invalid
            flash('Invalid credentials for admin.', 'danger')
    # Render the login page with "Admin" as the login type if GET request or after an error
    return render_template('login.html', login_type="Admin")

# User login route.
# Processes both GET and POST requests for user login.
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    # If the form is submitted (POST request)
    if request.method == 'POST':
        # Retrieve username and password from the login form
        username  = request.form['username']
        password  = request.form['password']
        # Look up the user in the database
        user = User.query.filter_by(username=username, password=password).first()
        # Check if user exists and if the role is user
        if user and user.role == 'user':
            # Store user ID and role in the session for authentication
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Logged in as user.', 'success')
            # Redirect to the user dashboard upon successful login
            return redirect(url_for('user_dashboard'))
        else:
            # If credentials are incorrect, flash an error message
            flash('Invalid credentials for user.', 'danger')
    # Render the login page with "User" as the login type
    return render_template('login.html', login_type="User")

# User registration route.
# Allows new users to sign up by providing their details.
@app.route('/register', methods=['GET', 'POST'])
def register():
    # If the registration form is submitted
    if request.method == 'POST':
        # Get the username/email from the form and remove extra whitespace
        username = request.form.get('username').strip()
        # Check if username/email already exists
        if User.query.filter_by(username=username).first():
            flash("This email is already registered. Please choose a different email.", "warning")
            return render_template('register.html')
        # Retrieve and clean up the rest of the form data
        password = request.form.get('password').strip()
        full_name = request.form.get('full_name').strip()
        qualification = request.form.get('qualification').strip()
        dob_str = request.form.get('dob').strip()
        # Convert the date string to a date object, if provided
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        
        # Create a new user with role 'user'
        new_user = User(username=username, password=password, full_name=full_name,
                        qualification=qualification, dob=dob, role='user')
        # Add the new user to the session
        db.session.add(new_user)
        # Save the new user to the database
        db.session.commit()
        flash("Registered successfully. Please log in.", "success")
        # Redirect to the user login page after successful registration
        return redirect(url_for('user_login'))
    # Render the registration form if it's a GET request or if registration fails
    return render_template('register.html')

# Logout Route
# Clears the current session and redirects the user to the home page.
@app.route('/logout')
def logout():
    # Clear all session data to log the user out
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

##########################################
#            ADMIN ROUTES                #
##########################################

# Route for the admin dashboard.
# Only accessible if the current session role is 'admin'.
# Fetches all subjects to display on the dashboard.
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        # If the user is not an admin, show an unauthorized access message and redirect.
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve all subjects from the database.
    subjects = Subject.query.all()
    # Render the admin dashboard template with the list of subjects.
    return render_template('admin_dashboard.html', subjects=subjects)

# Admin search route.
# Allows an admin to search for users, subjects, and quizzes based on a query.
@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    # Ensure that only admin users can access this route.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Dictionary to hold search results.
    results = {}
    # Initialize the search query string as empty.
    query = ""
    # Process the search form submission.
    if request.method == 'POST':
        query = request.form['query']
        # Search for users whose username contains the query.
        results['users'] = User.query.filter(User.username.contains(query)).all()
        # Search for subjects whose name contains the query.
        results['subjects'] = Subject.query.filter(Subject.name.contains(query)).all()
        # Search for quizzes whose remarks contain the query.
        results['quizzes'] = Quiz.query.filter(Quiz.remarks.contains(query)).all()
    # Render the search results page with the query and results.
    return render_template('admin_search.html', results=results, query=query)

# Admin summary charts (using Chart.js).
# Displays various summary statistics using charts.
@app.route('/admin/charts')
def admin_charts():
    # Check admin access.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Get counts for various entities.
    subject_count = Subject.query.count()
    chapter_count = Chapter.query.count()
    quiz_count = Quiz.query.count()
    question_count = Question.query.count()
    user_count = User.query.filter_by(role='user').count()
    score_count = Score.query.count()
    # Render the charts page with the calculated statistics.
    return render_template('admin_charts.html', 
                           subject_count=subject_count,
                           chapter_count=chapter_count, 
                           quiz_count=quiz_count,
                           question_count=question_count, 
                           user_count=user_count,
                           score_count=score_count)

# Admin route to see user activities
@app.route('/admin/user_activities')
def admin_user_activities():
    # Verify that the session belongs to an admin.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Fetch all users with role 'user'
    users = User.query.filter_by(role='user').all()
    # Render the user activities template with the list of users.
    return render_template('admin_user_activities.html', users=users)

# Admin route to view users.
@app.route('/admin/users')
def admin_users():
    # Ensure admin access.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve all users with role 'user'.
    users = User.query.filter_by(role='user').all()
    # Render the admin users page with the list of users.
    return render_template('admin_users.html', users=users)

# Admin route to edit the user
@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    # Confirm that the current session is an admin.
    if session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('admin_login'))
    # Retrieve the user to be edited; return 404 if not found.
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        new_username = request.form.get('username').strip()
        # Check for duplicate email/username in the system.
        duplicate = User.query.filter(User.username == new_username, User.id != user.id).first()
        if duplicate:
            flash("This email is already used by another user. Please choose a different email.", "warning")
            return render_template('admin_edit_user.html', user=user)
        
        # Update user details.
        user.full_name = request.form.get('full_name').strip()
        user.username = new_username
        user.qualification = request.form.get('qualification').strip()
        dob_str = request.form.get('dob').strip()
        # If a date is provided, convert it to a date object.
        if dob_str:
            user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        db.session.commit()
        flash("User profile updated successfully.", "success")
        # Redirect back to the users listing.
        return redirect(url_for('admin_users'))
    # Render the edit user form.
    return render_template('admin_edit_user.html', user=user)

# Admin allowed to delete the user
@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    # Verify the session belongs to an admin. Flash an error message if not authorized.  
    if session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        # Redirect to admin login.
        return redirect(url_for('admin_login'))
    # Retrieve the user by ID or return a 404 error if not found.
    user = User.query.get_or_404(user_id)
    # Delete all associated scores before deleting the user.
    Score.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    # Delete the user from the session.
    db.session.delete(user)
    db.session.commit()
    flash("User profile deleted successfully.", "info")
    # Redirect back to the users listing.
    return redirect(url_for('admin_users'))

# ---------------------- CRUD for Subjects -----------------------------
# Admin Route to Create Subject
@app.route('/admin/subject/create', methods=['GET', 'POST'])
def create_subject():
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        # Redirect to admin login.
        return redirect(url_for('admin_login'))
    # If the form is submitted, get the subject name and subject description from the form and create a new Subject
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        subject = Subject(name=name, description=description)
        db.session.add(subject)
        db.session.commit()
        flash('Subject created successfully.', 'success')
        # Redirect to the subject view page.
        return redirect(url_for('view_subject', subject_id=subject.id))
    # Render the subject creation template for GET requests.
    return render_template('create_subject.html')

# Admin Route to edit the Subject
@app.route('/admin/subject/edit/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the subject by its ID or return a 404 error.
    subject = Subject.query.get_or_404(subject_id)
    # If the form is submitted, update the subject name and subject description from the form
    if request.method == 'POST':
        subject.name = request.form.get('name')
        subject.description = request.form.get('description')
        db.session.commit()
        flash('Subject updated successfully.', 'success')
        # Redirect to the subject view page.
        return redirect(url_for('view_subject', subject_id=subject.id))
    # Render the subject edit template if the request is GET.
    return render_template('edit_subject.html', subject=subject)

# Admin Route to Delete the subject
@app.route('/admin/subject/delete/<int:subject_id>')
def delete_subject(subject_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the subject or return a 404 error if not found.
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully.', 'info')
    # Redirect back to the admin dashboard.
    return redirect(url_for('admin_dashboard'))

# ---------------------- CRUD for Chapters -----------------------------
# Admin Create a Chapter
@app.route('/admin/chapter/create/<int:subject_id>', methods=['GET', 'POST'])
def create_chapter(subject_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the subject or return a 404 error if not found.
    subject = Subject.query.get_or_404(subject_id)
    # If the form data is submitted, get chapter name and Chapter description form the form.
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        chapter = Chapter(name=name, description=description, subject=subject)
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter created successfully.', 'success')
        return redirect(url_for('view_subject', subject_id=subject.id))
    # Render the chapter creation template for GET requests.
    return render_template('create_chapter.html', subject=subject)

# Admin Edit a Chapter
@app.route('/admin/chapter/edit/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the chapter by its ID or return a 404 error.
    chapter = Chapter.query.get_or_404(chapter_id)
    # If the form data is submitted, update the chapter name and chapter description from the form.
    if request.method == 'POST':
        chapter.name = request.form.get('name')
        chapter.description = request.form.get('description')
        # Update any additional fields if needed.
        db.session.commit()
        flash('Chapter updated successfully.', 'success')
        return redirect(url_for('view_subject', subject_id=chapter.subject.id))
    # Render the chapter edit template if the request is GET.
    return render_template('edit_chapter.html', chapter=chapter)

# Admin Delete a Chapter
@app.route('/admin/chapter/delete/<int:chapter_id>')
def delete_chapter(chapter_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the chapter or return a 404 error if not found.
    chapter = Chapter.query.get_or_404(chapter_id)
    subject_id = chapter.subject.id
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully.', 'info')
    # Redirect to the subject view page.
    return redirect(url_for('view_subject', subject_id=subject_id))

# ---------------------- CRUD for Quizzes -----------------------------
# Admin Create a Quiz
@app.route('/admin/quiz/create/<int:chapter_id>', methods=['GET', 'POST'])
def create_quiz(chapter_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    chapter = Chapter.query.get_or_404(chapter_id)
    # If form data is submitted, process the quiz creation form submission by parsing and localizing date/time inputs, setting defaults, and flashing an error if the scheduled time is missing.
    if request.method == 'POST':
        date_str = request.form.get('date_of_quiz')
        if date_str:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            quiz_date = LOCAL_TZ.localize(dt)
        else:
            quiz_date = datetime.now(LOCAL_TZ)
        time_duration = request.form['time_duration']
        remarks = request.form['remarks']
        question_limit = request.form.get('question_limit', type=int) or 10
        scheduled_at_str = request.form.get('scheduled_at')
        if scheduled_at_str:
            scheduled_dt = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            scheduled_at = LOCAL_TZ.localize(scheduled_dt)
        else:
            flash("Scheduled time is required.", "danger")
            return render_template('create_quiz.html', chapter=chapter)
        # Create a new Quiz object with the collected data.
        quiz = Quiz(chapter=chapter, date_of_quiz=quiz_date, time_duration=time_duration,
                    remarks=remarks, question_limit=question_limit, scheduled_at=scheduled_at)
        # Add the new quiz to the session.
        db.session.add(quiz)
        db.session.commit()
        flash('Quiz created successfully.', 'success')
        # Redirect to the chapter view page.
        return redirect(url_for('view_chapter', chapter_id=chapter.id))
    # Render the quiz creation template for GET requests.
    return render_template('create_quiz.html', chapter=chapter)

# Admin Edit the Quiz
@app.route('/admin/quiz/edit/<int:quiz_id>', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the quiz by its ID or return a 404 error.
    quiz = Quiz.query.get_or_404(quiz_id)
    # When the form is submitted via a POST request, the code updates quiz details by parsing and validating the submitted form data.
    if request.method == 'POST':
        date_str = request.form.get('date_of_quiz')
        if date_str:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            quiz.date_of_quiz = dt
        quiz.time_duration = request.form.get('time_duration')
        quiz.remarks = request.form.get('remarks')
        quiz.question_limit = request.form.get('question_limit', type=int)
        scheduled_at_str = request.form.get('scheduled_at')
        if scheduled_at_str:
            scheduled_dt = datetime.strptime(scheduled_at_str, '%Y-%m-%dT%H:%M')
            quiz.scheduled_at = LOCAL_TZ.localize(scheduled_dt)
        db.session.commit()
        flash('Quiz updated successfully.', 'success')
          # Redirect to the quiz view page.
        return redirect(url_for('view_quiz', quiz_id=quiz.id))
    # Render the quiz edit template if the request is GET.
    return render_template('edit_quiz.html', quiz=quiz)

# Admin
@app.route('/admin/quiz/delete/<int:quiz_id>')
def delete_quiz(quiz_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the quiz by its ID or return a 404 error.
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter.id
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully.', 'info')
      # Redirect to the chapter view page.
    return redirect(url_for('view_chapter', chapter_id=chapter_id))



# ---------------------- CRUD for Questions -----------------------------
# Route for creating a new question for a given quiz.
@app.route('/admin/question/create/<int:quiz_id>', methods=['GET', 'POST'])
def create_question(quiz_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the quiz by its ID or return a 404 error.
    quiz = Quiz.query.get_or_404(quiz_id)
    # If the form is submitted, get the question text, the options and the explanation from the form.
    if request.method == 'POST':
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form['correct_option']
        # Now include the explanation field.
        explanation = request.form.get('explanation')  # Explanation is optional.
        
        question = Question(
            quiz=quiz,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
            explanation=explanation
        )
        db.session.add(question)
        db.session.commit()
        flash("Question created successfully.", "success")
        # Redirect to the quiz view page.
        return redirect(url_for('view_quiz', quiz_id=quiz.id))
    # Render the question creation template if the request is GET.
    return render_template('create_question.html', quiz=quiz)

# Route for editing an existing question for a given quiz.
@app.route('/admin/question/edit/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the question by its ID or return a 404 error.
    question = Question.query.get_or_404(question_id)
    # If the form has been submitted, update the question and the options.
    if request.method == 'POST':
        question.question_statement = request.form.get('question_statement')
        question.option1 = request.form.get('option1')
        question.option2 = request.form.get('option2')
        question.option3 = request.form.get('option3')
        question.option4 = request.form.get('option4')
        question.correct_option = request.form.get('correct_option')
        question.explanation = request.form.get('explanation')
        db.session.commit()
        flash('Question updated successfully.', 'success')
        # Redirect to the quiz view page.
        return redirect(url_for('view_quiz', quiz_id=question.quiz.id))
    # Render the question edit template if the request is GET.
    return render_template('edit_question.html', question=question)

# Define the route for deleting a question.
@app.route('/admin/question/delete/<int:question_id>')
def delete_question(question_id):
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('admin_login'))
    # Retrieve the question by its ID or return a 404 error.
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz.id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully.', 'info')
    # Redirect to the quiz view page.
    return redirect(url_for('view_quiz', quiz_id=quiz_id))

# Route for the performance dashboard which shows various performance metrics.
@app.route('/admin/performance_dashboard')
def performance_dashboard():
    #  Verify if the current user is an admin. Flash an error message if not authorized.
    if session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('admin_login'))
    
    # Quiz Performance Trends: average score per day
    scores = Score.query.order_by(Score.time_stamp_of_attempt).all()
    from collections import defaultdict
    daily_scores = defaultdict(list)
    for s in scores:
        day = s.time_stamp_of_attempt.strftime("%Y-%m-%d")
        daily_scores[day].append(s.total_scored)
    daily_labels = sorted(daily_scores.keys())
    daily_avg = [sum(daily_scores[day]) / len(daily_scores[day]) for day in daily_labels]

    # Category/Subject Analysis: average score per subject
    subjects = Subject.query.all()
    subject_labels = []
    subject_avg = []
    subject_attempts = []
    for subject in subjects:
        all_scores = []
        attempt_count = 0
        for chapter in subject.chapters:
            for quiz in chapter.quizzes:
                for score in quiz.scores:
                    all_scores.append(score.total_scored)
                attempt_count += len(quiz.scores)
        if all_scores:
            subject_labels.append(subject.name)
            subject_avg.append(sum(all_scores) / len(all_scores))
            subject_attempts.append(attempt_count)
    
    # Leaderboard: users ranked by points
    users = User.query.filter_by(role='user').order_by(User.points.desc()).all()
    leaderboard_names = [user.full_name for user in users]
    leaderboard_points = [user.points for user in users]

    # Dummy data for Quiz Completion Time (in seconds) and Question Difficulty Analysis (in percentage)
    quiz_completion_labels = ["Quiz A", "Quiz B", "Quiz C"]
    quiz_completion_times = [300, 450, 350]  # Example: average completion times
    question_difficulty_labels = ["Q1", "Q2", "Q3", "Q4"]
    question_difficulty_data = [25, 40, 15, 20]  # Example: percentage of incorrect responses

    return render_template("performance_dashboard.html",
                           daily_labels=daily_labels,
                           daily_avg=daily_avg,
                           subject_labels=subject_labels,
                           subject_avg=subject_avg,
                           subject_attempts=subject_attempts,
                           leaderboard_names=leaderboard_names,
                           leaderboard_points=leaderboard_points,
                           quiz_completion_labels=quiz_completion_labels,
                           quiz_completion_times=quiz_completion_times,
                           question_difficulty_labels=question_difficulty_labels,
                           question_difficulty_data=question_difficulty_data)

# (Optional) API endpoint: Get all subjects as JSON
@app.route('/api/subjects')
def api_subjects():
    subjects = Subject.query.all()
    data = []
    for sub in subjects:
        data.append({'id': sub.id, 'name': sub.name, 'description': sub.description})
    return jsonify(data)

##########################################
#            USER ROUTES                 #
##########################################

# User dashboard route, which displays the dashboard page for a logged-in user.
@app.route('/user/dashboard')
def user_dashboard():
    #  Verify if the current user is a user. Flash an error message if not authorized.
    if session.get('role') != 'user':
        flash('Please log in as a user.', 'danger')
        return redirect(url_for('user_login'))
    # Retrieve all subjects from the database.
    subjects = Subject.query.all()
    # Render the user dashboard template, passing the subjects.
    return render_template('user_dashboard.html', subjects=subjects)

# Route for attempting a quiz. It handles both GET (display quiz) and POST (submit quiz) requests.
@app.route('/user/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attempt_quiz(quiz_id):
    # Verify if the current user is a user. Flash an error message if not authorized.
    if session.get('role') != 'user':
        flash('Please log in as a user.', 'danger')
        #  Redirect to the user login page.
        return redirect(url_for('user_login'))
    # Retrieve the quiz by quiz_id or return 404 if not found.
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Prevent early access to the quiz based on its scheduled start time.
    # Get the current time in the defined local timezone.
    current_time = datetime.now(LOCAL_TZ)
    # Get the quiz's scheduled start time.
    quiz_start = quiz.scheduled_at
    # If the scheduled time has no timezone info, localize it to the defined timezone.
    if quiz_start.tzinfo is None:
        quiz_start = LOCAL_TZ.localize(quiz_start)
    # Compare current time with the quiz start time. Inform the user if quiz isn't available.
    if current_time < quiz_start:
        flash("This quiz is not yet available. Please come back at the scheduled time.", "warning")
        # Redirect to the user dashboard.
        return redirect(url_for('user_dashboard'))
    
    # Define session keys to store the fixed order of quiz questions and randomized options.
    quiz_order_key = f"quiz_order_{quiz_id}"
    quiz_options_key = f"quiz_options_{quiz_id}"
    
    # On first load, if the order or options are not already in the session, generate and store them.
    if quiz_order_key not in session or quiz_options_key not in session:
        # Get all question IDs and shuffle thier order.
        question_ids = [q.id for q in quiz.questions]
        random.shuffle(question_ids)
        # If a question limit is set and is less than total questions, limit the questions to that number.
        if quiz.question_limit and quiz.question_limit < len(question_ids):
            question_ids = question_ids[:quiz.question_limit]
        # Save the fixed order of questions in the session.
        session[quiz_order_key] = question_ids
        
        # Build a mapping of question id to randomized options.
        # Initialize an empty dictionary to hold options mapping.
        options_mapping = {}
        # Iterate over each question in the quiz.
        for q in quiz.questions:
            # Process only if the question is in the selected order.
            if q.id in session[quiz_order_key]:
                # Initialize a list to hold the options for the question.
                opts = []
                if q.option1:
                    opts.append(('option1', q.option1))
                if q.option2:
                    opts.append(('option2', q.option2))
                if q.option3:
                    opts.append(('option3', q.option3))
                if q.option4:
                    opts.append(('option4', q.option4))
                # Randomize the order of options.
                random.shuffle(opts)
                # Map the string version of question id to its randomized options.
                options_mapping[str(q.id)] = opts
        # Save the options mapping in the session.
        session[quiz_options_key] = options_mapping
    
    # Retrieve the fixed question order and options mapping from session.
    quiz_order = session.get(quiz_order_key, [])
    options_mapping = session.get(quiz_options_key, {})
    
    # Reconstruct the list of questions in the randomized order with their corresponding options.
    # Initialize an empty list to hold the reconstructed questions.
    randomized_questions = []
    # Iterate over each question ID in the fixed order.
    for qid in quiz_order:
        # Find the question object matching the current id. If the question exists, append a dictionary containing question details, include the question ID, question text, randomized options, correct answer identifier and explanation text for the answer.
        question_obj = next((q for q in quiz.questions if q.id == qid), None)
        if question_obj:
            randomized_questions.append({
                'id': question_obj.id,
                'question_statement': question_obj.question_statement,
                'options': options_mapping.get(str(question_obj.id), []),
                'correct_option': question_obj.correct_option,
                'explanation': question_obj.explanation
            })
    
    # Calculate total_seconds from quiz.time_duration (format "HH:MM")
    parts = quiz.time_duration.split(':')
    total_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60

    # Handle form submission when the user interacts with the quiz.
    if request.method == 'POST':
        # If the request method is POST, save the current answers in the session without final submission if the user clicked the 'save' button. 
        if 'save' in request.form:
            # Save current answers to session; do not finalize submission.
            saved_answers = {}
            for q in randomized_questions:
                ans = request.form.get(str(q['id']))
                if ans:
                    saved_answers[str(q['id'])] = ans
            session['saved_answers'] = saved_answers
            flash("Your answers have been saved.", "success")
            return redirect(url_for('attempt_quiz', quiz_id=quiz.id))
        # If the user clicked the 'submit' button, retrieve saved answers if they exist; otherwise, collect answers from the form.
        elif 'submit' in request.form:
            # Final submission: use saved answers if available; if not, get current answers.
            saved_answers = session.get('saved_answers', {})
            # If there are no saved answers, loop through each question, get the answer from the form. If an answer exists, save it in the dictionary.
            if not saved_answers:
                for q in randomized_questions:
                    ans = request.form.get(str(q['id']))
                    if ans:
                        saved_answers[str(q['id'])] = ans
            score = 0
            for q in randomized_questions:
                # If the saved answer for the question matches the correct option, increment the score.
                if saved_answers.get(str(q['id'])) == q['correct_option']:
                    score += 1
            user = User.query.get(session['user_id'])
            user.points += score * 10  # Award points (example: 10 per correct answer)
            new_score = Score(quiz_id=quiz.id, user_id=user.id, total_scored=score)
            db.session.add(new_score)
            db.session.commit()
            flash(f'You scored {score} out of {len(randomized_questions)}.', 'success')
            # Clear quiz-specific session data since the quiz is now submitted.
            session.pop('saved_answers', None)
            session.pop(quiz_order_key, None)
            session.pop(quiz_options_key, None)
            # Redirect to the public view of the chapter associated with the quiz.
            return redirect(url_for('view_chapter_public', chapter_id=quiz.chapter.id))
    
    # Retrieve any saved answers to pre-fill the form.
    saved_answers = session.get('saved_answers', {})
    # Render the quiz attempt template with the quiz details, randomized questions, saved answers, and total duration.
    return render_template('attempt_quiz.html',
                           quiz=quiz,
                           questions=randomized_questions,
                           saved_answers=saved_answers,
                           total_seconds=total_seconds)

# Route for editing the user's profile.
@app.route('/user/profile/edit', methods=['GET', 'POST'])
def edit_user_profile():
    # Verify if the current user is a user. Flash an error message if not authorized.
    if session.get('role') != 'user':
        flash("Unauthorized access!", "danger")
        # Redirect to the user login page.
        return redirect(url_for('user_login'))
    user = User.query.get_or_404(session['user_id'])
    # If the form is submitted, get and clean the new username from the form.
    if request.method == 'POST':
        new_username = request.form.get('username').strip()
        # Check if the new username is used by another user
        duplicate = User.query.filter(User.username == new_username, User.id != user.id).first()
        # If a duplicate exists, flash a warning.
        if duplicate:
            flash("This email is already used by another user. Please choose a different email.", "warning")
            # Re-render the profile edit page.
            return render_template('edit_user_profile.html', user=user)
        # Update the user's profile fields with the form data.
        user.full_name = request.form.get('full_name').strip()
        user.username = new_username
        user.qualification = request.form.get('qualification').strip()
        # Get the date of birth as a string.
        dob_str = request.form.get('dob').strip()
        # If a date is provided, convert it to a date object.
        if dob_str:
            user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        db.session.commit()
        flash("Profile updated successfully.", "success")
        # Redirect to the user dashboard.
        return redirect(url_for('user_dashboard'))
    # Render the profile edit template for GET requests.
    return render_template('edit_user_profile.html', user=user)

# Route for deleting the user's profile.
@app.route('/user/profile/delete', methods=['POST'])
def delete_user_profile():
    # Verify if the current user is a user. Flash an error message if not authorized.
    if session.get('role') != 'user':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('user_login'))
    user = User.query.get_or_404(session['user_id'])
    db.session.delete(user)
    db.session.commit()
    session.clear()  # Log the user out
    flash("Your profile has been deleted.", "info")
    # Redirect to the home page.
    return redirect(url_for('index'))

@app.route('/user/scores')
def user_scores():
    # Verify if the current user is a user. Flash an error message if not authorized.
    if session.get('role') != 'user':
        flash('Please log in as a user.', 'danger')
        return redirect(url_for('user_login'))
    # Retrieve all scores for the logged-in user.
    scores = Score.query.filter_by(user_id=session['user_id']).all()
    # Render the template with the scores.
    return render_template('user_scores.html', scores=scores)

# Route for displaying the user's quiz performance.
@app.route('/user/quiz/performance')
def user_quiz_performance():
    # Verify if the current user is a user. Flash an error message if not authorized.
    if session.get('role') != 'user':
        flash("Please log in as a user.", "danger")
        return redirect(url_for('user_login'))
    user = User.query.get_or_404(session['user_id'])
    
    # Query the Score table: for each quiz, get the maximum score for this user.
    best_scores = db.session.query(
        Score.quiz_id,
        func.max(Score.total_scored).label("best_score")
    ).filter(Score.user_id == user.id).group_by(Score.quiz_id).all()
    
    # Build a list of tuples: (quiz_date, quiz_name, best_score)
    performance_data = []
    # Iterate over each quiz and its best score.
    for quiz_id, best_score in best_scores:
        quiz = Quiz.query.get(quiz_id)
        # Use a quiz.name attribute if available; otherwise, default to "Quiz #id".
        quiz_name = getattr(quiz, 'name', f'Quiz #{quiz.id}')
        # Use quiz.date_of_quiz as the release date.
        performance_data.append((quiz.date_of_quiz, quiz_name, best_score))
    
    # Sort by release date (ascending)
    performance_data.sort(key=lambda x: x[0])
    
    # Prepare separate lists for labels (quiz names) and scores for Chart.js visualization.
    labels = [item[1] for item in performance_data]
    scores = [item[2] for item in performance_data]
    
    # Render the quiz performance template with the prepared labels and scores.
    return render_template("user_quiz_performance.html", labels=labels, scores=scores)

# Public Route to view details of a subject (accessible to all users).
@app.route('/subject/<int:subject_id>')
def view_subject_public(subject_id):
    # Retrieve the subject or return 404 if not found.
    subject = Subject.query.get_or_404(subject_id)
    # Render the subject view template.
    return render_template('view_subject.html', subject=subject)

# Public view of a chapter (for users) to see available quizzes
@app.route('/chapter/<int:chapter_id>')
def view_chapter_public(chapter_id):
    # Retrieve the chapter or return 404 if not found.
    chapter = Chapter.query.get_or_404(chapter_id)
    # Render the chapter view template.
    return render_template('view_chapter.html', chapter=chapter)

# Optional API endpoint for getting user scores as JSON for a given user.
@app.route('/api/user/<int:user_id>/scores')
def api_user_scores(user_id):
    # Retrieve all scores for the specified user.
    scores = Score.query.filter_by(user_id=user_id).all()
    # Initialize an empty list to store score data.
    data = []
    # Iterate over each score, append a dictionary with score details, include quiz ID, score and the timestamp. 
    for s in scores:
        data.append({
            'quiz_id': s.quiz_id,
            'score': s.total_scored,
            'attempt_time': s.time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M:%S')
        })
    # Return the score data as a JSON response.
    return jsonify(data)

# API endpoint to get overall quiz statistics as JSON.
@app.route('/api/quiz_stats')
def api_quiz_stats():
    # Count the total number of subjects, chapters, quizzes, questions, users and quiz attempts.
    subjects = Subject.query.count()
    chapters = Chapter.query.count()
    quizzes = Quiz.query.count()
    questions = Question.query.count()
    users = User.query.filter_by(role='user').count()
    scores = Score.query.count()
    # Return the statistics as a JSON object.
    return jsonify({
        'subjects': subjects,
        'chapters': chapters,
        'quizzes': quizzes,
        'questions': questions,
        'users': users,
        'scores': scores
    })

# Route for auto-submitting a quiz when the time expires.
@app.route('/user/quiz/<int:quiz_id>/auto_submit', methods=['GET'])
def auto_submit_quiz(quiz_id):
    # Flash an info message indicating auto-submission.
    flash("Time's up! Your quiz was auto‑submitted.", "info")
    # Retrieve the quiz or return 404 if not found.
    quiz = Quiz.query.get_or_404(quiz_id)
    # Retrieve any saved answers from the session.
    saved_answers = session.get('saved_answers', {})
    # Convert the quiz questions to a list.
    questions = list(quiz.questions)
    # Shuffle the questions randomly.
    random.shuffle(questions)
    # Apply question limit if necessary.
    if quiz.question_limit and quiz.question_limit < len(questions):
        questions = questions[:quiz.question_limit]
    # Initialize the score counter.
    score = 0
    # Iterate over each question. If the saved answer matches the correct option, increment the score.
    for q in questions:
        if saved_answers.get(str(q.id)) == q.correct_option:
            score += 1
    # Retrieve the current user.
    user = User.query.get(session['user_id'])
    # Award points based on the score.
    user.points += score * 10
    # Create a new score record.
    new_score = Score(quiz_id=quiz.id, user_id=user.id, total_scored=score)
    db.session.add(new_score)
    db.session.commit()
    # Remove saved answers from the session.
    session.pop('saved_answers', None)
    # Remove the quiz start time key from the session if present.
    session.pop(f'quiz_start_{quiz_id}', None)
    # Flash the auto-submission score.
    flash(f'Auto‑submitted: You scored {score} out of {len(questions)}.', 'success')
    # Redirect to the public view of the quiz's chapter.
    return redirect(url_for('view_chapter_public', chapter_id=quiz.chapter.id))

# Route to view the quiz results.
@app.route('/user/quiz/results/<int:quiz_id>')
def quiz_results(quiz_id):
    # For demonstration, retrieve the quiz and its questions. Retrieve the quiz by ID or return 404.
    quiz = Quiz.query.get_or_404(quiz_id)
    # In a real app, retrieve the user's submitted answers and compare them.
    return render_template('quiz_results.html', quiz=quiz)

# Route for the user's overall performance.
@app.route('/user/performance')
def user_performance():
    # Verify if the current user is a user. Flash an error message if not authorized.
    if session.get('role') != 'user':
        flash("Please log in as a user.", "danger")
        return redirect(url_for('user_login'))
    user = User.query.get_or_404(session['user_id'])
    # Retrieve all quiz scores for the user, sorted by timestamp
    scores = Score.query.filter_by(user_id=user.id).order_by(Score.time_stamp_of_attempt).all()
    # Prepare lists of labels (timestamps) and corresponding scores for visualization.
    labels = [score.time_stamp_of_attempt.strftime("%Y-%m-%d %H:%M") for score in scores]
    data = [score.total_scored for score in scores]
    # Render the performance template.
    return render_template("user_performance.html", labels=labels, data=data)

# Route for displaying the leaderboard.
@app.route('/leaderboard')
def leaderboard():
    # Verify if the current user is a user. Flash an error message if not authorized.
    if not session.get('user_id'):
        flash("Please log in to view the leaderboard.", "warning")
        return redirect(url_for('user_login'))
    
    # Subquery: For each user and quiz, get the maximum score.
    subq = (
        db.session.query(
            Score.user_id,
            Score.quiz_id,
            func.max(Score.total_scored).label("best_score")
        )
        .group_by(Score.user_id, Score.quiz_id)
        .subquery()
    )
    
    # Main query: Left outer join all users with the subquery, using COALESCE to treat null as 0.
    leaderboard_data = (
        db.session.query(
            User.full_name,
            func.coalesce(func.sum(subq.c.best_score), 0).label("total_points")
        )
        .filter(User.role == 'user')
        .outerjoin(subq, User.id == subq.c.user_id)
        .group_by(User.id)
        .order_by(func.coalesce(func.sum(subq.c.best_score), 0).desc())
        .all()
    )
    # Render the leaderboard template with the gathered leaderboard data.
    return render_template("leaderboard.html", leaderboard_data=leaderboard_data)

##########################################
#             MAIN FUNCTION              #
##########################################

if __name__ == '__main__':
    app.run(debug=True)