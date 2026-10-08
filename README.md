# Kenneth Dike Library — Intelligent Library Management System

CSC 302 Group A10 project starter.

## Stack
- Python 3
- Flask
- Flask-SQLAlchemy
- PostgreSQL (recommended for the final build)
- SQLite fallback for quick local demonstration
- HTML/CSS/Bootstrap/JavaScript

## Features in this starter
- Professional KDL-themed landing page
- Login with role-based demo accounts
- Patron dashboard
- Catalogue search and filters
- Book details and availability
- Reservation workflow
- Officer circulation dashboard
- Admin dashboard
- Simple recommendation engine based on department + subject/borrowing history
- Seed/demo data

## Demo accounts
All demo accounts use password: `password`

- Patron: `E054579`
- Officer: `OFF001`
- Admin: `ADM001`

## Run

### 1. Create a virtual environment
Windows:
    python -m venv .venv
    .venv\Scripts\activate

Linux/macOS:
    python3 -m venv .venv
    source .venv/bin/activate

### 2. Install dependencies
    pip install -r requirements.txt

### 3. Configure database
Copy `.env.example` to `.env`.

For quick demonstration, leave DATABASE_URL unset and the app uses SQLite.

For the intended final architecture, set:
    DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/kdl_ilms

### 4. Start
    python app.py

Open:
    http://127.0.0.1:5000

## Important project note
This is a simulated academic prototype. It does not connect to Kenneth Dike Library's internal UIILS data and uses synthetic records for demonstration.
