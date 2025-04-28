# Quiz Application

This project is a web-based quiz management system built with Flask. It provides separate interfaces for administrators and regular users. Administrators can create, update, and delete subjects, chapters, quizzes, and questions, as well as view performance statistics. Regular users can register, log in, attempt quizzes, view their performance, and track scores on a leaderboard.

---

## Features

- **User Authentication:**  
  - Admin and user login systems with session management.
  - User registration and profile editing.

- **Quiz Management:**  
  - Admin can create and manage subjects, chapters, quizzes, and questions.
  - Randomized order of quiz questions and options for each attempt.
  - Quiz attempt interface with auto-submission on time expiry.

- **Performance Tracking:**  
  - Score recording and accumulation.
  - Performance dashboards and charts for both users and admins.
  - Leaderboard displaying user rankings based on points.

- **API Endpoints:**  
  - Endpoints for retrieving subjects, quiz statistics, and user scores in JSON format.

- **Database Integration:**  
  - Uses SQLite with SQLAlchemy ORM.
  - Database migrations managed via Flask-Migrate.

---

## Technologies Used

- **Flask:** Web framework to build the application.
- **SQLAlchemy:** ORM for interacting with the SQLite database.
- **Flask-Migrate:** Database migration tool.
- **Jinja2:** Templating engine for rendering HTML pages.
- **Chart.js:** Library for generating performance charts (integrated within templates).
- **Other Libraries:** pytz for timezone handling, datetime for date and time operations, and additional utilities like random and copy.

---

## Installation

1. **Clone the repository:**

2. **Create a virtual environment:**
    ```
    python -m venv venv
    # For Linux
    source venv/bin/activate  
    # For Windows
    venv\Scripts\activate
    ```
3. **Install the dependencies:**
    ```
    pip install -r requirements.txt
    ```
4. **Setup the database:**
    The database will be automatically created on the first request. To initialize the database with a default admin user, run:
    ```
    flask run
    ```
    Then, access the application in your browser.

## Usage

1. **Run the application:**
    ```
    python app.py
    ```
    The app will start in debug mode by default and listen on http://127.0.0.1:5000.

2. **Access the application:**
    
    Admin Interface:
    Navigate to /admin/login to log in as an admin. A default admin user is created automatically with the following credentials:

    Username: admin@example.com

    Password: admin

    User Interface:
    Navigate to /user/login to log in as a regular user or /register to create a new user account.

3. **Navigation:**
    Explore available subjects and quizzes.

    Admin users can manage content and view performance charts.

    Users can attempt quizzes, view scores, and check leaderboard rankings.

## Database Migrations

    The project uses Flask-Migrate to handle database migrations. Use the following commands to manage migrations:  
 1. **Initial Migrations:**
    ```
    flask db init
    ```
2. **Generate a Migration:**
    ```
    flask db migrate -m "Initial migration."
    ```
3. **Apply the migration:**
    ```
    flask db upgrade
    ```

#### Project Structure

    quiz_master_22f3000668/
    ├── app.py
    ├── config.py
    ├── requirements.txt
    ├── migrations/
    ├── static/
    │   ├── css/
    │   │   └── custom.css
    │   ├── js/
    │   │   └── main.js
    │   └── images/
    │       └── background.jpg
    └── templates/
        ├── base.html
        ├── index.html
        ├── login.html
        ├── register.html
        ├── user_dashboard.html
        ├── admin_dashboard.html
        ├── edit_user_profile.html
        ├── admin_edit_user.html
        ├── admin_users.html
        ├── view_subjects.html
        ├── view_subject_public.html
        ├── create_subject.html
        ├── edit_subject.html
        ├── create_chapter.html
        ├── edit_chapter.html
        ├── create_quiz.html
        ├── edit_quiz.html
        ├── view_quiz.html
        ├── attempt_quiz.html 
        ├── user_quiz_performance.html
        ├── performance_dashboard.html
        └── leaderboard.html