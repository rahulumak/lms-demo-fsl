"""
Seed script — safe to run repeatedly.
Refuses to run with predictable passwords in production.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone
from app.core.config import settings
from app.db.base import SessionLocal, create_tables
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.course import Course, CourseStatus
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.lesson_progress import LessonProgress, ProgressStatus


def _get_or_create_user(db, email, full_name, role, password):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        db.flush()
        print(f"  Created user: {email}")
    return user


def _get_or_create_course(db, instructor_id, title, slug, short_desc, desc, status, thumbnail_url=None):
    course = db.query(Course).filter(Course.slug == slug).first()
    if not course:
        course = Course(
            instructor_id=instructor_id,
            title=title,
            slug=slug,
            short_description=short_desc,
            description=desc,
            thumbnail_url=thumbnail_url,
            status=status,
            published_at=datetime.now(timezone.utc) if status == CourseStatus.published else None,
        )
        db.add(course)
        db.flush()
        print(f"  Created course: {title}")
    return course


def _get_or_create_lesson(db, course_id, title, position, content, video_url, duration_minutes, is_published):
    lesson = db.query(Lesson).filter(Lesson.course_id == course_id, Lesson.position == position).first()
    if not lesson:
        lesson = Lesson(
            course_id=course_id,
            title=title,
            position=position,
            content=content,
            video_url=video_url,
            duration_minutes=duration_minutes,
            is_published=is_published,
        )
        db.add(lesson)
        db.flush()
    return lesson


def _get_or_create_enrollment(db, student_id, course_id):
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id,
    ).first()
    if not enrollment:
        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        db.add(enrollment)
        db.flush()
    return enrollment


def _set_progress(db, enrollment, lesson, status: ProgressStatus):
    lp = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enrollment.id,
        LessonProgress.lesson_id == lesson.id,
    ).first()
    if not lp:
        now = datetime.now(timezone.utc)
        lp = LessonProgress(
            enrollment_id=enrollment.id,
            lesson_id=lesson.id,
            status=status,
            started_at=now if status != ProgressStatus.not_started else None,
            completed_at=now if status == ProgressStatus.completed else None,
        )
        db.add(lp)
        db.flush()
    return lp


def seed():
    if settings.is_production:
        print("ERROR: Refusing to seed predictable demo accounts in production.")
        sys.exit(1)

    # Ensure tables exist (safe if already created)
    create_tables()

    db = SessionLocal()
    try:
        # ── Users ──────────────────────────────────────────────────────────────
        print("Seeding users...")
        instructor = _get_or_create_user(
            db, settings.SEED_INSTRUCTOR_EMAIL, "Rahul Umak", UserRole.instructor,
            settings.SEED_INSTRUCTOR_PASSWORD,
        )
        s1 = _get_or_create_user(db, settings.SEED_STUDENT1_EMAIL, "Rutwij Bawaskar", UserRole.student, settings.SEED_STUDENT1_PASSWORD)
        s2 = _get_or_create_user(db, settings.SEED_STUDENT2_EMAIL, "Srividhya Suri",  UserRole.student, settings.SEED_STUDENT2_PASSWORD)
        s3 = _get_or_create_user(db, settings.SEED_STUDENT3_EMAIL, "Rushikesh Cheke", UserRole.student, settings.SEED_STUDENT3_PASSWORD)

        # ── Courses ────────────────────────────────────────────────────────────
        print("Seeding courses...")

        py_course = _get_or_create_course(
            db, instructor.id,
            "Python for Beginners", "python-for-beginners",
            "Learn Python from scratch with hands-on examples.",
            "A comprehensive introduction to Python programming covering variables, control flow, functions, and OOP. Perfect for absolute beginners.",
            CourseStatus.published,
            "https://picsum.photos/seed/python/800/450",
        )

        web_course = _get_or_create_course(
            db, instructor.id,
            "Web Development Fundamentals", "web-dev-fundamentals",
            "Build your first website with HTML, CSS, and JavaScript.",
            "Start from zero and learn how the web works. You will build real pages using HTML structure, CSS styling, and JavaScript interactivity.",
            CourseStatus.published,
            "https://picsum.photos/seed/webdev/800/450",
        )

        react_course = _get_or_create_course(
            db, instructor.id,
            "React for Frontend Developers", "react-frontend",
            "Master React 18 — components, hooks, state, and routing.",
            "A practical React course covering JSX, useState, useEffect, React Router, and fetching data from APIs. Build a real project by the end.",
            CourseStatus.published,
            "https://picsum.photos/seed/react/800/450",
        )

        fastapi_course = _get_or_create_course(
            db, instructor.id,
            "FastAPI & REST APIs", "fastapi-rest-apis",
            "Build production-ready REST APIs with FastAPI and Python.",
            "Learn FastAPI from the ground up — routing, Pydantic models, dependency injection, JWT auth, and SQLAlchemy. Deploy a full API by the end.",
            CourseStatus.draft,
            "https://picsum.photos/seed/fastapi/800/450",
        )

        # ── Lessons ────────────────────────────────────────────────────────────
        print("Seeding lessons...")

        # Python for Beginners — 5 lessons
        py_lessons = [
            _get_or_create_lesson(db, py_course.id,
                "Introduction to Python & Setup", 1,
                "## What is Python?\nPython is a high-level, interpreted language known for its clean syntax.\n\n## Installing Python\n1. Download from python.org\n2. Verify: `python --version`\n3. Use VS Code or PyCharm as your editor.",
                "https://www.youtube.com/watch?v=kqtD5dpn9C8", 12, True),

            _get_or_create_lesson(db, py_course.id,
                "Variables, Data Types & Operators", 2,
                "## Variables\nVariables store data. Python is dynamically typed.\n\n```python\nname = 'Alice'\nage = 30\nprice = 9.99\nis_active = True\n```\n\n## Operators\nArithmetic: `+ - * / // % **`\nComparison: `== != > < >= <=`",
                "https://www.youtube.com/watch?v=cQT33yu9pY8", 14, True),

            _get_or_create_lesson(db, py_course.id,
                "Control Flow — if, for, while", 3,
                "## if / elif / else\n```python\nif score >= 90:\n    print('A')\nelif score >= 75:\n    print('B')\nelse:\n    print('C')\n```\n\n## Loops\n```python\nfor i in range(5):\n    print(i)\n\nwhile count > 0:\n    count -= 1\n```",
                "https://www.youtube.com/watch?v=PqFKRqpHrjw", 16, True),

            _get_or_create_lesson(db, py_course.id,
                "Functions & Scope", 4,
                "## Defining Functions\n```python\ndef greet(name, greeting='Hello'):\n    return f'{greeting}, {name}!'\n\nprint(greet('Bob'))          # Hello, Bob!\nprint(greet('Bob', 'Hi'))    # Hi, Bob!\n```\n\n## Scope\nVariables inside a function are local unless declared `global`.",
                "https://www.youtube.com/watch?v=9Os0o3wzS_I", 18, True),

            _get_or_create_lesson(db, py_course.id,
                "Lists, Dicts & Basic OOP", 5,
                "## Lists\n```python\nfruits = ['apple', 'banana', 'cherry']\nfruits.append('date')\n```\n\n## Dictionaries\n```python\nuser = {'name': 'Alice', 'age': 30}\nprint(user['name'])\n```\n\n## Classes\n```python\nclass Dog:\n    def __init__(self, name):\n        self.name = name\n    def bark(self):\n        return f'{self.name} says Woof!'\n```",
                "https://www.youtube.com/watch?v=JJmcL1N2KQs", 20, True),
        ]

        # Web Development Fundamentals — 5 lessons
        web_lessons = [
            _get_or_create_lesson(db, web_course.id,
                "How the Web Works & HTML Basics", 1,
                "## How the Web Works\nBrowser → DNS → Server → HTML/CSS/JS response.\n\n## HTML Structure\n```html\n<!DOCTYPE html>\n<html>\n  <head><title>My Page</title></head>\n  <body>\n    <h1>Hello World</h1>\n    <p>My first paragraph.</p>\n  </body>\n</html>\n```",
                "https://www.youtube.com/watch?v=qz0aGYrrlhU", 15, True),

            _get_or_create_lesson(db, web_course.id,
                "HTML Forms, Tables & Semantic Tags", 2,
                "## Semantic HTML\nUse `<header>`, `<nav>`, `<main>`, `<footer>` for structure.\n\n## Forms\n```html\n<form action='/submit' method='POST'>\n  <input type='text' name='username' placeholder='Username'>\n  <button type='submit'>Submit</button>\n</form>\n```",
                "https://www.youtube.com/watch?v=YwbIeMlxZAU", 14, True),

            _get_or_create_lesson(db, web_course.id,
                "CSS Styling & Box Model", 3,
                "## Selectors\n```css\nh1 { color: navy; }\n.card { background: white; }\n#header { font-size: 2rem; }\n```\n\n## Box Model\nEvery element = content + padding + border + margin.\n\n## Flexbox\n```css\n.container { display: flex; gap: 1rem; justify-content: center; }\n```",
                "https://www.youtube.com/watch?v=1Rs2ND1ryYc", 18, True),

            _get_or_create_lesson(db, web_course.id,
                "JavaScript Basics & DOM", 4,
                "## Variables & Functions\n```js\nconst name = 'Alice'\nfunction greet(n) { return `Hello, ${n}!` }\n```\n\n## DOM Manipulation\n```js\nconst btn = document.getElementById('myBtn')\nbtn.addEventListener('click', () => {\n  document.querySelector('h1').textContent = 'Clicked!'\n})\n```",
                "https://www.youtube.com/watch?v=W6NZfCO5SIk", 20, True),

            _get_or_create_lesson(db, web_course.id,
                "Fetch API & Putting It All Together", 5,
                "## Fetch API\n```js\nasync function loadData() {\n  const res = await fetch('https://api.example.com/data')\n  const data = await res.json()\n  console.log(data)\n}\n```\n\n## Project\nBuild a simple weather app that fetches data from a public API and displays it on the page.",
                "https://www.youtube.com/watch?v=cuEtnrL9-H0", 22, True),
        ]

        # React for Frontend Developers — 5 lessons
        react_lessons = [
            _get_or_create_lesson(db, react_course.id,
                "React Setup & JSX", 1,
                "## Create a React App\n```bash\nnpm create vite@latest my-app -- --template react\ncd my-app && npm install && npm run dev\n```\n\n## JSX\n```jsx\nfunction App() {\n  return <h1>Hello, React!</h1>\n}\n```\nJSX looks like HTML but compiles to `React.createElement()` calls.",
                "https://www.youtube.com/watch?v=SqcY0GlETPk", 16, True),

            _get_or_create_lesson(db, react_course.id,
                "Components, Props & State", 2,
                "## Components\n```jsx\nfunction Card({ title, body }) {\n  return (\n    <div className='card'>\n      <h2>{title}</h2>\n      <p>{body}</p>\n    </div>\n  )\n}\n```\n\n## useState\n```jsx\nconst [count, setCount] = useState(0)\n<button onClick={() => setCount(c => c + 1)}>{count}</button>\n```",
                "https://www.youtube.com/watch?v=35lXWvCuM8o", 18, True),

            _get_or_create_lesson(db, react_course.id,
                "useEffect & Data Fetching", 3,
                "## useEffect\n```jsx\nuseEffect(() => {\n  fetch('/api/users')\n    .then(r => r.json())\n    .then(data => setUsers(data))\n}, []) // empty array = run once on mount\n```\n\n## Cleanup\nReturn a function from useEffect to clean up subscriptions or timers.",
                "https://www.youtube.com/watch?v=0ZJgIjIuY7U", 20, True),

            _get_or_create_lesson(db, react_course.id,
                "React Router & Navigation", 4,
                "## Setup\n```bash\nnpm install react-router-dom\n```\n\n## Routes\n```jsx\n<BrowserRouter>\n  <Routes>\n    <Route path='/' element={<Home />} />\n    <Route path='/about' element={<About />} />\n    <Route path='/users/:id' element={<UserDetail />} />\n  </Routes>\n</BrowserRouter>\n```",
                "https://www.youtube.com/watch?v=Ul3y1LXxzdU", 17, True),

            _get_or_create_lesson(db, react_course.id,
                "Forms, Validation & API Integration", 5,
                "## Controlled Form\n```jsx\nconst [email, setEmail] = useState('')\n<input value={email} onChange={e => setEmail(e.target.value)} />\n```\n\n## Submitting to an API\n```jsx\nasync function handleSubmit(e) {\n  e.preventDefault()\n  const res = await fetch('/api/login', {\n    method: 'POST',\n    headers: { 'Content-Type': 'application/json' },\n    body: JSON.stringify({ email, password }),\n  })\n}\n```",
                "https://www.youtube.com/watch?v=SdzMBWT2CDQ", 22, True),
        ]

        # FastAPI & REST APIs — 5 lessons (draft)
        fastapi_lessons = [
            _get_or_create_lesson(db, fastapi_course.id,
                "FastAPI Introduction & First Route", 1,
                "## Install\n```bash\npip install fastapi uvicorn\n```\n\n## Hello World\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/')\ndef root():\n    return {'message': 'Hello World'}\n```\n\nRun: `uvicorn main:app --reload`",
                "https://www.youtube.com/watch?v=0sOvCWFmrtA", 14, True),

            _get_or_create_lesson(db, fastapi_course.id,
                "Pydantic Models & Request Validation", 2,
                "## Pydantic\n```python\nfrom pydantic import BaseModel\n\nclass UserCreate(BaseModel):\n    name: str\n    email: str\n    age: int\n\n@app.post('/users')\ndef create_user(data: UserCreate):\n    return data\n```\nFastAPI validates the request body automatically.",
                "https://www.youtube.com/watch?v=pkdgBell2Ims", 16, True),

            _get_or_create_lesson(db, fastapi_course.id,
                "Path, Query & Header Parameters", 3,
                "## Path Parameters\n```python\n@app.get('/items/{item_id}')\ndef get_item(item_id: int):\n    return {'id': item_id}\n```\n\n## Query Parameters\n```python\n@app.get('/search')\ndef search(q: str, limit: int = 10):\n    return {'query': q, 'limit': limit}\n```",
                "https://www.youtube.com/watch?v=GN6ICac3OXY", 15, True),

            _get_or_create_lesson(db, fastapi_course.id,
                "SQLAlchemy & Database Integration", 4,
                "## Setup\n```bash\npip install sqlalchemy\n```\n\n## Session Dependency\n```python\ndef get_db():\n    db = SessionLocal()\n    try:\n        yield db\n    finally:\n        db.close()\n```\n\nUse `Depends(get_db)` in your route functions.",
                "https://www.youtube.com/watch?v=2g1ZjA6zHRo", 20, False),

            _get_or_create_lesson(db, fastapi_course.id,
                "JWT Authentication", 5,
                "## JWT Flow\n1. User logs in → server returns access token\n2. Client sends token in `Authorization: Bearer <token>` header\n3. Server validates token on each request\n\n## PyJWT\n```python\nimport jwt\ntoken = jwt.encode({'sub': str(user_id)}, SECRET_KEY, algorithm='HS256')\n```",
                "https://www.youtube.com/watch?v=0A_GCXRO8OA", 22, False),
        ]

        # ── Enrollments & Progress ─────────────────────────────────────────────
        print("Seeding enrollments and progress...")

        # Rutwij: Python — completed all 5 lessons
        s1_py = _get_or_create_enrollment(db, s1.id, py_course.id)
        for lesson in py_lessons:
            _set_progress(db, s1_py, lesson, ProgressStatus.completed)
        s1_py.status = EnrollmentStatus.completed
        s1_py.completed_at = datetime.now(timezone.utc)

        # Rutwij: Web — in progress (3 done, 1 in progress)
        s1_web = _get_or_create_enrollment(db, s1.id, web_course.id)
        for lesson in web_lessons[:3]:
            _set_progress(db, s1_web, lesson, ProgressStatus.completed)
        _set_progress(db, s1_web, web_lessons[3], ProgressStatus.in_progress)

        # Srividhya: Python — just started
        s2_py = _get_or_create_enrollment(db, s2.id, py_course.id)
        _set_progress(db, s2_py, py_lessons[0], ProgressStatus.completed)
        _set_progress(db, s2_py, py_lessons[1], ProgressStatus.in_progress)

        # Srividhya: React — enrolled, not started
        _get_or_create_enrollment(db, s2.id, react_course.id)

        # Rushikesh: Web — completed all
        s3_web = _get_or_create_enrollment(db, s3.id, web_course.id)
        for lesson in web_lessons:
            _set_progress(db, s3_web, lesson, ProgressStatus.completed)
        s3_web.status = EnrollmentStatus.completed
        s3_web.completed_at = datetime.now(timezone.utc)

        # Rushikesh: React — in progress (2 done)
        s3_react = _get_or_create_enrollment(db, s3.id, react_course.id)
        for lesson in react_lessons[:2]:
            _set_progress(db, s3_react, lesson, ProgressStatus.completed)
        _set_progress(db, s3_react, react_lessons[2], ProgressStatus.in_progress)

        db.commit()
        print("\nSeed complete!")
        print(f"  Instructor : {settings.SEED_INSTRUCTOR_EMAIL} / {settings.SEED_INSTRUCTOR_PASSWORD}")
        print(f"  Student 1  : {settings.SEED_STUDENT1_EMAIL} / {settings.SEED_STUDENT1_PASSWORD}")
        print(f"  Student 2  : {settings.SEED_STUDENT2_EMAIL} / {settings.SEED_STUDENT2_PASSWORD}")
        print(f"  Student 3  : {settings.SEED_STUDENT3_EMAIL} / {settings.SEED_STUDENT3_PASSWORD}")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
