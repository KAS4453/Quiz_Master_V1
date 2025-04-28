# Quiz Master (V1)

Quiz Master is a full-featured, web-based quiz management platform built with Flask, SQLAlchemy, Flask-Migrate, and Bootstrap. It allows administrators to create and manage subjects, chapters, quizzes, and questions, while regular users can register, attempt quizzes, and track their performance over time.

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Usage Guide](#usage-guide)
   - [User Workflow](#user-workflow)
   - [Admin Workflow](#admin-workflow)
7. [Project Structure](#project-structure)
8. [Technology Stack](#technology-stack)
9. [Contributing](#contributing)
10. [License](#license)

---

## Features

- **User Registration & Authentication**: Sign up, log in, and manage your profile.
- **Interactive Quizzes**: Timed quizzes with randomized question/option order, save-and-resume, and auto-submit on timeout.
- **Performance Analytics**: Visual charts of your quiz history and best scores per quiz.
- **Leaderboard**: See user rankings based on accumulated points.
- **Admin Dashboard**: Full CRUD for subjects, chapters, quizzes, and questions.
- **Admin Analytics**: Charts for overall counts, trends, subject analysis, and user activity logs.
- **Search & Filtering**: Admin search for users, subjects, and quizzes.
- **RESTful JSON APIs**: Endpoints for subjects, user scores, and overall quiz stats.

## Prerequisites

- Python 3.8+
- pip
- Virtual environment tool (optional but recommended)

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/KAS4453/Quiz_Master_V1.git
   cd quiz-master
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate    # on Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
   This will create `database.db` and set up the required tables.

---

## Configuration

- **Secret Key**: Located in `app.py` under `app.config['SECRET_KEY']`. Change it to a secure random value.
- **Database URI**: By default uses SQLite (`sqlite:///database.db`). Modify `app.config['SQLALCHEMY_DATABASE_URI']` in `app.py` to switch to another database (e.g., PostgreSQL).
- **Timezone**: Configured to Asia/Kolkata via `pytz`.

---

## Running the Application

```bash
export FLASK_APP=app.py
export FLASK_ENV=development  # enables debug mode
flask run
```

Open your browser at `http://127.0.0.1:5000/`.

---

## Usage Guide

### User Workflow

1. **Register**: Visit **Register** from the homepage, fill in your details, and submit.
2. **Login**: Go to **User Login**, enter your credentials, and access the User Dashboard.
3. **Browse Subjects**: From the dashboard, view available subjects and click **View Details**.
4. **Select Chapter**: In the subject page, choose a chapter to see available quizzes.
5. **Attempt Quiz**: Click **Attempt Quiz**, complete the timed quiz, and submit. You can save progress mid-quiz.
6. **View Results**: After submission, view detailed results with correct answers and explanations.
7. **Performance Tracking**: Access **My Scores** for a table of past attempts, and **View Performance** for interactive charts.
8. **Leaderboard**: See how you rank against other users by total points.
9. **Profile Management**: Edit or delete your profile via **Edit My Profile**.

### Admin Workflow

1. **Admin Login**: Click **Admin Login** and enter admin credentials (default: `admin@example.com` / `admin`).
2. **Dashboard**: Manage subjects via **Create Subject**, view existing ones in cards, and edit or delete.
3. **Chapters & Quizzes**: Drill into a subject to add/edit/delete chapters; inside a chapter, add/edit/delete quizzes.
4. **Questions**: For each quiz, manage its questions with rich forms supporting explanations.
5. **Analytics**:
   - **Summary Charts**: Quick overview of total subjects, quizzes, users, and attempts.
   - **Performance Dashboard**: In-depth charts for trends, subject analysis, leaderboard data, and difficulty metrics.
6. **User Management**:
   - **View Users**: List all users, edit or delete profiles.
   - **User Activities**: See detailed quiz attempt history per user.
7. **Search**: Quickly find users, subjects, or quizzes by keywords.
8. **Logout**: End your session securely.

---

## Project Structure

```
QuizMaster/
├── app.py            # Main application: models, routes, controllers
├── migrations/       # Database migration scripts
├── static/           # Static assets (CSS/JS/images)
└── templates/        # Jinja2 HTML templates
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── admin_*.html
    └── user_*.html
```

---

## Technology Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate
- **Frontend:** Bootstrap 4, Chart.js, Jinja2 templates
- **Database:** SQLite (default), other SQL databases supported via SQLAlchemy
- **Timezone:** pytz (Asia/Kolkata)

## License

This project is open-source and available under the MIT License. Feel free to use, modify, and distribute.
