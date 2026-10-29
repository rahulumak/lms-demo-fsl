# LMS Demo — Full-Stack Learning Management System

A production-oriented LMS prototype with FastAPI backend, React frontend, JWT authentication, and role-based access control.

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
- Refresh tokens in HttpOnly cookies (`SameSite=Strict`), hashed on server
- CSRF protection via `Origin`/`Referer` header validation on all cookie-consuming endpoints
- All authorization enforced on the backend

---

## Technology Stack

| Layer      | Technology                                                        |
|------------|-------------------------------------------------------------------|
| Backend    | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0, Alembic 1.13         |
| Auth       | PyJWT 2.8, pwdlib/Argon2, HttpOnly cookies, CSRF origin check    |
| Database   | SQLite (dev), PostgreSQL 16 (prod/Docker)                        |
| Frontend   | React 18, Vite 5, React Router 6, TanStack Query 5, Axios 1.7   |
| Testing    | pytest 8 + httpx (backend), Vitest 2 + RTL (frontend)            |
| Container  | Docker + Docker Compose (PostgreSQL + backend + frontend)         |

---

## Database Relationships

```
User (instructor) ──< Course ──< Lesson
User (student)    ──< Enrollment ──< LessonProgress
                         │                │
                         └── Course       └── Lesson
AuthSession >── User
```

Cascade rules:
- Deleting a `Course` cascades to `Lesson`, `Enrollment`, and `LessonProgress`
- Deleting a `User` (student) cascades to `Enrollment` and `LessonProgress`

---

## Repository Structure

```
LMSDemoFSL/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, middleware, startup
│   │   ├── core/                 # config, security, logging, limiter
│   │   ├── db/                   # base, session, dependencies
│   │   ├── models/               # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── course.py
│   │   │   ├── lesson.py
│   │   │   ├── enrollment.py
│   │   │   ├── lesson_progress.py
│   │   │   └── auth_session.py
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── api/v1/               # routers + endpoints
│   │   │   └── endpoints/
│   │   │       ├── auth.py
│   │   │       ├── catalog.py
│   │   │       ├── instructor.py
│   │   │       └── student.py
│   │   └── services/             # business logic
│   │       ├── auth_service.py
│   │       ├── course_service.py
│   │       ├── lesson_service.py
│   │       ├── enrollment_service.py
│   │       └── progress_service.py
│   ├── migrations/               # Alembic (PostgreSQL prod)
│   ├── scripts/seed_data.py
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                  # App.jsx, RootRedirect.jsx
│   │   ├── components/           # Header, ProtectedRoute, UI, ErrorBoundary
│   │   ├── context/              # AuthContext.jsx
│   │   ├── layouts/              # AppLayout.jsx
│   │   ├── pages/
│   │   │   ├── auth/             # LoginPage, RegisterPage
│   │   │   ├── catalog/          # CatalogPage
│   │   │   ├── instructor/       # Dashboard, CourseForm, Lessons, Progress, StudentDetail
│   │   │   └── student/          # StudentDashboard, LearnPage
│   │   ├── services/             # api.js (Axios client + interceptors)
│   │   └── styles/               # global.css
│   ├── tests/
│   └── package.json
├── docker-compose.yml
├── LMS_API.postman_collection.json
└── README.md
```

---

## Role & Permission Matrix

| Action                        | Instructor | Student |
|-------------------------------|:----------:|:-------:|
| Register (public)             | ✗          | ✓       |
| Create / edit own courses     | ✓          | ✗       |
| Publish / archive own courses | ✓          | ✗       |
| Delete own courses            | ✓          | ✗       |
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
# Generate a strong secret key:
#   openssl rand -hex 32
# Paste the output as SECRET_KEY in .env

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed demo data (tables are auto-created on first startup via create_tables())
python scripts/seed_data.py

# Start the backend server (port 9000)
uvicorn app.main:app --reload --port 9000
```

> Tables are created automatically on startup via `Base.metadata.create_all()`.
> Alembic is available for PostgreSQL production migrations but is not used in SQLite dev.

API docs: http://127.0.0.1:9000/docs
ReDoc:    http://127.0.0.1:9000/redoc
Health:   http://127.0.0.1:9000/health/live

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

| Role       | Email                        | Password         |
|------------|------------------------------|------------------|
| Instructor | rahul.umak@test.com          | InstructorPass1! |
| Student 1  | rutwij.bawaskar@test.com     | StudentPass1!    |
| Student 2  | srividhya.suri@test.com      | StudentPass1!    |
| Student 3  | rushikesh.cheke@test.com     | StudentPass1!    |

> These accounts are only created when `APP_ENV != production`.

---

## Re-seeding the Database

If you change models or seed data, delete the SQLite file and re-seed:

```bash
cd backend
rm -f lms_dev.db
source .venv/bin/activate
python scripts/seed_data.py
```

---

## Database Migrations (PostgreSQL / Production)

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
# Backend tests (49 tests)
cd backend
source .venv/bin/activate
pytest tests/ -v

# Frontend tests (34 tests)
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

## API Reference

| Method   | Endpoint                                                        | Auth         | Description                        |
|----------|-----------------------------------------------------------------|--------------|------------------------------------|
| GET      | `/health/live`                                                  | —            | Liveness check                     |
| GET      | `/health/ready`                                                 | —            | Readiness check (DB ping)          |
| POST     | `/api/v1/auth/register`                                         | —            | Register a new student             |
| POST     | `/api/v1/auth/login`                                            | —            | Login, returns access token        |
| POST     | `/api/v1/auth/refresh`                                          | Cookie       | Rotate refresh token               |
| POST     | `/api/v1/auth/logout`                                           | Cookie       | Revoke session                     |
| GET      | `/api/v1/auth/me`                                               | Bearer       | Current user info                  |
| GET      | `/api/v1/courses`                                               | —            | List published courses             |
| GET      | `/api/v1/courses/{id}`                                          | —            | Get published course               |
| GET      | `/api/v1/courses/{id}/lessons`                                  | —            | List published lessons             |
| POST     | `/api/v1/courses/{id}/enroll`                                   | Student      | Enroll in a course                 |
| GET      | `/api/v1/instructor/courses`                                    | Instructor   | List own courses                   |
| POST     | `/api/v1/instructor/courses`                                    | Instructor   | Create course                      |
| GET      | `/api/v1/instructor/courses/{id}`                               | Instructor   | Get own course                     |
| PATCH    | `/api/v1/instructor/courses/{id}`                               | Instructor   | Update course                      |
| POST     | `/api/v1/instructor/courses/{id}/publish`                       | Instructor   | Publish course                     |
| POST     | `/api/v1/instructor/courses/{id}/archive`                       | Instructor   | Archive course                     |
| DELETE   | `/api/v1/instructor/courses/{id}`                               | Instructor   | Delete course (cascades)           |
| GET      | `/api/v1/instructor/courses/{id}/lessons`                       | Instructor   | List lessons                       |
| POST     | `/api/v1/instructor/courses/{id}/lessons`                       | Instructor   | Create lesson                      |
| PATCH    | `/api/v1/instructor/courses/{id}/lessons/{lid}`                 | Instructor   | Update lesson                      |
| PATCH    | `/api/v1/instructor/courses/{id}/lessons/reorder`               | Instructor   | Reorder lessons                    |
| DELETE   | `/api/v1/instructor/courses/{id}/lessons/{lid}`                 | Instructor   | Delete lesson                      |
| GET      | `/api/v1/instructor/courses/{id}/progress`                      | Instructor   | All students' progress             |
| GET      | `/api/v1/instructor/courses/{id}/students/{sid}/progress`       | Instructor   | Single student progress            |
| GET      | `/api/v1/students/me/courses`                                   | Student      | My enrolled courses (typed `StudentCourseItem` response) |
| GET      | `/api/v1/students/me/courses/{id}/lessons`                      | Student      | Lessons for enrolled course        |
| GET      | `/api/v1/students/me/courses/{id}/progress`                     | Student      | My progress for a course           |
| POST     | `/api/v1/students/me/lessons/{lid}/start`                       | Student      | Mark lesson started                |
| POST     | `/api/v1/students/me/lessons/{lid}/complete`                    | Student      | Mark lesson complete               |

A full Postman collection is available at `LMS_API.postman_collection.json` — import via **File → Import** in Postman.

---

## Security Notes

- Refresh token cookie is `HttpOnly`, `SameSite=Strict`, scoped to `/api/v1/auth`
- `Origin`/`Referer` header validated on `/refresh` and `/logout` to prevent CSRF
- Passwords hashed with Argon2 via pwdlib
- `SECRET_KEY` must be at least 32 characters — startup will fail with a validation error if shorter
- Access tokens expire in 15 minutes; refresh tokens in 7 days with rotation
- Rate limiting on `/auth/login` (10 req/min) and `/auth/register` (20 req/min) per IP
- Rate limiter resolves real client IP via `X-Forwarded-For` → `X-Real-IP` → direct connection (proxy-aware)
- `create_tables()` is skipped when `APP_ENV=production` — Alembic is the sole migration tool in production
- `ALLOWED_ORIGINS` must be set to your actual frontend domain in production

---

## Example API Requests

```bash
# Register
curl -X POST http://localhost:9000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Alice","email":"alice@example.com","password":"Password1!"}'

# Login (saves refresh cookie to cookies.txt)
curl -X POST http://localhost:9000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"rahul.umak@test.com","password":"InstructorPass1!"}'

# List published courses
curl http://localhost:9000/api/v1/courses

# Create course (instructor token required)
curl -X POST http://localhost:9000/api/v1/instructor/courses \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Course","description":"Course description"}'
```

---

## Known Limitations

- No file upload — video URLs only (YouTube / Vimeo)
- No email verification on registration
- Rate limiter uses in-memory store — not suitable for multi-process prod without Redis
- Rate limiter reads `X-Forwarded-For` but has no trusted-proxy allowlist — header can be spoofed by clients in deployments without a hardened proxy; replace with a Redis-backed solution (e.g. `slowapi`) for production
- No admin panel for user management
- SQLite does not enforce foreign key constraints by default — PostgreSQL recommended for production

---

## Production Checklist

- [ ] Set `APP_ENV=production` and `COOKIE_SECURE=true`
- [ ] Generate a strong `SECRET_KEY` — minimum 32 characters (`openssl rand -hex 32` produces 64)
- [ ] Use PostgreSQL with a strong password
- [ ] Put backend behind HTTPS (nginx / Caddy)
- [ ] Set `ALLOWED_ORIGINS` to your actual frontend domain
- [ ] Replace in-memory rate limiter with Redis-backed solution
- [ ] Run `alembic upgrade head` as a deployment step — `create_tables()` is disabled when `APP_ENV=production`
- [ ] Configure reverse proxy to set `X-Forwarded-For` / `X-Real-IP` and restrict header spoofing
- [ ] Set up log aggregation and monitoring
- [ ] Review and rotate JWT secrets periodically
