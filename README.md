# LMS Demo — Full-Stack Learning Management System

A production-oriented LMS prototype with FastAPI backend, React frontend, JWT auth, and role-based access control.

---

## Architecture Overview

```
Browser (React + Vite)
    │  HTTPS / JSON API
    ▼
FastAPI (Python 3.12)
    │  SQLAlchemy 2.x ORM
    ▼
SQLite (dev) / PostgreSQL (prod)
```

- Access tokens stored in memory (never localStorage)
- Refresh tokens in HttpOnly cookies, hashed on server
- All authorization enforced on the backend

---

## Technology Stack

| Layer      | Technology                                          |
|------------|-----------------------------------------------------|
| Backend    | Python 3.12, FastAPI, SQLAlchemy 2, Alembic         |
| Auth       | PyJWT, pwdlib (Argon2), HttpOnly cookies            |
| Database   | SQLite (dev), PostgreSQL (prod)                     |
| Frontend   | React 18, Vite, React Router 6, TanStack Query, Axios |
| Testing    | pytest (backend), Vitest + RTL (frontend)           |

---

## Database Relationships

```
User (instructor) ──< Course ──< Lesson
User (student)    ──< Enrollment ──< LessonProgress
                         │                │
                         └── Course       └── Lesson
AuthSession >── User
```

---

## Repository Structure

```
LMSDemoFSL/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # config, security, logging
│   │   ├── db/            # base, session, dependencies
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── api/v1/        # routers + endpoints
│   │   └── services/      # business logic
│   ├── migrations/        # Alembic migrations
│   ├── scripts/seed_data.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/           # App.jsx, RootRedirect
│   │   ├── components/    # Header, ProtectedRoute, UI
│   │   ├── context/       # AuthContext
│   │   ├── layouts/       # AppLayout
│   │   ├── pages/         # auth, instructor, student, catalog
│   │   ├── services/      # api.js (Axios client)
│   │   └── styles/        # global.css
│   ├── tests/
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Role & Permission Matrix

| Action                        | Instructor | Student |
|-------------------------------|:----------:|:-------:|
| Register (public)             | ✗          | ✓       |
| Create / edit own courses     | ✓          | ✗       |
| Publish / archive own courses | ✓          | ✗       |
| View all published courses    | ✓          | ✓       |
| Enroll in published course    | ✗          | ✓       |
| Access enrolled lessons       | ✗          | ✓       |
| Mark lessons complete         | ✗          | ✓       |
| View own progress             | ✗          | ✓       |
| View student progress (own)   | ✓          | ✗       |

---

## Prerequisites

- macOS with Homebrew
- Python 3.12: `brew install python@3.12`
- Node.js 20+: `brew install node`
- (Optional) Docker Desktop for PostgreSQL

---

## Running the Project

### 1. Backend Setup & Start

```bash
cd backend

# Copy env file and set your SECRET_KEY
cp .env.example .env
# Generate a real secret key:
#   openssl rand -hex 32
# Paste the output as SECRET_KEY in .env

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed demo data (tables are auto-created on first startup)
python scripts/seed_data.py

# Start the backend server (port 9000)
uvicorn app.main:app --reload --port 9000
```

API docs: http://127.0.0.1:9000/docs

---

### 2. Frontend Setup & Start

```bash
cd frontend

# Copy env file (points to backend at port 9000)
cp .env.example .env

# Install dependencies
npm install

# Start the frontend dev server (port 3000)
npm run dev
```

App: http://localhost:3000

---

## Demo Accounts (dev only)

| Role       | Email                          | Password         |
|------------|--------------------------------|------------------|
| Instructor | rahul.umak@test.com          | InstructorPass1! |
| Student 1  | rutwij.bawaskar@test.com     | StudentPass1!    |
| Student 2  | srividhya.suri@test.com      | StudentPass1!    |
| Student 3  | rushikesh.cheke@test.com     | StudentPass1!    |

> These credentials are only created when `APP_ENV != production`.

---

## Database Migrations

```bash
cd backend
source .venv/bin/activate

# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description"
```

---

## Test Commands

```bash
# Backend tests
cd backend
source .venv/bin/activate
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Frontend production build
npm run build
```

---

## Docker Compose

```bash
# Start everything (PostgreSQL + backend on 9000 + frontend on 3000)
docker-compose up --build

# Run migrations inside container
docker-compose exec backend alembic upgrade head

# Seed data
docker-compose exec backend python scripts/seed_data.py
```

---

## API Documentation

- Swagger UI: http://127.0.0.1:9000/docs
- ReDoc:      http://127.0.0.1:9000/redoc
- Health:     http://127.0.0.1:9000/health/live

---

## Example API Requests

```bash
# Register
curl -X POST http://localhost:9000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Alice","email":"alice@example.com","password":"Password1!"}'

# Login
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"rahul.umak@test.com","password":"InstructorPass1!"}'

# List published courses
curl http://localhost:9000/api/v1/courses

# Create course (instructor token required)
curl -X POST http://localhost:9000/api/v1/instructor/courses \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Course"}'
```

---

## Known Limitations

- No file upload (video URLs only — YouTube/Vimeo)
- No email verification
- Rate limiting uses in-memory store (not suitable for multi-process prod without Redis)
- Markdown rendered as plain text in frontend (no XSS risk, but no formatting)
- No admin panel for user management
- SQLite does not enforce foreign key constraints by default (PostgreSQL recommended for production)

---

## Production Checklist

- [ ] Set `APP_ENV=production` and `COOKIE_SECURE=true`
- [ ] Generate a strong `SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Use PostgreSQL with a strong password
- [ ] Put backend behind HTTPS (nginx/Caddy)
- [ ] Set `ALLOWED_ORIGINS` to your actual frontend domain
- [ ] Replace in-memory rate limiter with Redis-backed solution
- [ ] Set up log aggregation and monitoring
- [ ] Run `alembic upgrade head` as a deployment step (not at startup)
- [ ] Review and rotate JWT secrets periodically
