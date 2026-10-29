# LMS Demo — Architecture & Security Audit Report

**Project:** `/Users/rahulumak/Desktop/GSLabWorkspace/Python/LMSDemoFSL`
**Audit Date:** 2025-07-10
**Auditor:** Amazon Q (Prompt 1 — Architecture Audit)
**Scope:** Full repository inspection — backend, frontend, models, services, tests, deployment config

---

## Test Execution Results (Pre-Audit Baseline)

| Suite | Command | Result |
|-------|---------|--------|
| Backend (pytest) | `pytest tests/ -v` | **41 passed, 0 failed, 2 warnings** |
| Frontend (Vitest) | `npm test` | **34 passed, 0 failed** |
| Frontend build | `npm run build` | **PASS — 313 kB bundle, 475ms** |

Warnings: `@app.on_event("startup")` is deprecated in FastAPI 0.111 — lifespan handlers should be used instead.

---

## A. Executive Summary

The LMS is a well-structured full-stack prototype with a clean layered architecture (FastAPI → service layer → SQLAlchemy ORM → SQLite/PostgreSQL). Authentication uses HttpOnly refresh-token cookies with rotation, CSRF origin validation, and Argon2 password hashing. All 75 automated tests pass and the production build succeeds.

**Overall readiness: CONDITIONAL GO — suitable for internal development demonstration only.**

The application is not ready for staging or production due to the following confirmed blockers:

- **P0:** `SECRET_KEY` has no startup validation — a weak or default key will silently be accepted in production.
- **P0:** `create_tables()` runs on every startup with no environment gate — it will attempt DDL against a production PostgreSQL database on every deploy.
- **P0:** Dockerfile exposes port 8000 but `docker-compose.yml` maps port 9000 — the container will not serve traffic.
- **P1:** `_optional_user` in `catalog.py` uses a `__import__` hack and is defined but never used — dead code with a fragile import pattern.
- **P1:** `student.py` `my_courses` endpoint uses `response_model=list[dict]` — no schema validation or field filtering on the response.
- **P1:** `my_course_lessons` calls `get_enrollment_or_404` twice — double DB query on every lesson page load.
- **P1:** `AuthContext.jsx` calls `/auth/refresh` on mount without an `Origin` header — will receive `403 CSRF check failed` in any browser that does not automatically set `Origin` on same-site requests (e.g. initial page load from a file or non-standard client).
- **P1:** In-memory rate limiter is not safe for multi-process or multi-worker deployments.
- **P2:** No `SECRET_KEY` minimum-length enforcement — a 1-character key is accepted.
- **P2:** `CourseCreate` / `CourseUpdate` do not validate `thumbnail_url` format or length beyond the model column limit.
- **P2:** `LessonProgress` has no DB-level constraint preventing a progress record from linking an enrollment to a lesson from a different course.
- **P2:** `on_event("startup")` deprecation warning — should migrate to lifespan context manager.
- **P3:** No security response headers (CSP, X-Frame-Options, X-Content-Type-Options).
- **P3:** `LearnPage.jsx` iframe `src` transforms YouTube watch URLs to embed URLs client-side with a simple string replace — does not handle `youtu.be` short URLs or Vimeo.
- **P3:** `renderContent` in `LearnPage.jsx` is a hand-rolled Markdown parser — incomplete and inconsistent with lesson content authored in the seed data.

---

## B. Findings

---

### CRITICAL

---

#### FIND-001
**Severity:** Critical
**File:** `backend/Dockerfile` line 6 / `docker-compose.yml` line 20
**Problem:** The Dockerfile `EXPOSE`s and `CMD` binds to port **8000**, but `docker-compose.yml` maps host port **9000** to container port **9000** (`"9000:9000"`). The container starts uvicorn on 8000, but Compose expects it on 9000. Traffic will not reach the backend.
**Failure scenario:** `docker-compose up --build` starts the backend container, but all API requests from the frontend container time out because nothing is listening on container port 9000.
**Impact:** Complete service outage in Docker deployment.
**Reproduction:** `docker-compose up --build` → `curl http://localhost:9000/health/live` → connection refused.
**Remediation:** Change `Dockerfile` CMD to `--port 9000` and `EXPOSE 9000`, or change `docker-compose.yml` port mapping to `"9000:8000"`.
**Regression test:** Add a Docker Compose smoke test that curls `/health/live` after startup.

---

#### FIND-002
**Severity:** Critical
**File:** `backend/app/core/config.py` line 11 / `backend/app/db/base.py` `create_tables()`
**Problem:** `SECRET_KEY` is declared as `str` with no default, which means Pydantic will raise a `ValidationError` at startup if it is missing — good. However, there is no minimum-length check. A key of `"x"` is accepted silently. Additionally, `create_tables()` is called unconditionally on every startup (`main.py` line 23) with no `APP_ENV != production` guard. In production with PostgreSQL, this will attempt `CREATE TABLE IF NOT EXISTS` on every deploy, which is unsafe when Alembic is the intended migration tool.
**Failure scenario:** A developer sets `SECRET_KEY=dev` in a production `.env`. All JWTs are signed with a trivially brute-forceable key. Separately, a production deploy runs `create_tables()` which may conflict with Alembic-managed schema state.
**Impact:** Token forgery risk; schema management conflict in production.
**Remediation:**
1. Add a `@field_validator("SECRET_KEY")` that enforces `len(v) >= 32`.
2. Gate `create_tables()` behind `if not settings.is_production`.
**Regression test:** Test that startup fails with a short `SECRET_KEY`; test that `create_tables()` is not called when `APP_ENV=production`.

---

### HIGH

---

#### FIND-003
**Severity:** High
**File:** `backend/app/api/v1/endpoints/catalog.py` lines 16–32
**Problem:** `_optional_user` is defined using `__import__("fastapi.security", fromlist=["HTTPBearer"])` — a dynamic import hack that bypasses normal module resolution. The function is imported but **never called by any route** in the file. It is dead code.
**Failure scenario:** If a future developer wires this function into a route, the dynamic import may fail in certain deployment environments or when the module path changes. The dead code also adds confusion during security reviews.
**Impact:** Code quality, potential runtime failure if used.
**Remediation:** Delete `_optional_user` entirely. If optional auth is needed on catalog routes, use a proper `Optional[User]` dependency with a standard import.
**Regression test:** Confirm catalog endpoints return correct data for both authenticated and unauthenticated requests.

---

#### FIND-004
**Severity:** High
**File:** `backend/app/api/v1/endpoints/student.py` line 16
**Problem:** `my_courses` endpoint declares `response_model=list[dict]`. This disables Pydantic response validation and field filtering entirely. Any field added to the dict — including internal fields — will be serialized and returned to the client without validation.
**Failure scenario:** A developer adds a sensitive field (e.g. `password_hash`, internal IDs) to the result dict. It is returned to the browser with no schema enforcement.
**Impact:** Potential data leakage; no contract enforcement on the student dashboard API.
**Remediation:** Define a `StudentCourseItem` Pydantic schema with explicit fields and use it as `response_model=list[StudentCourseItem]`.
**Regression test:** Assert that the response contains only expected fields and does not include `password_hash` or other internal fields.

---

#### FIND-005
**Severity:** High
**File:** `backend/app/api/v1/endpoints/student.py` lines 51–55
**Problem:** `my_course_lessons` calls `get_enrollment_or_404(db, student.id, course_id)` **twice** — once to verify enrollment and once to pass to `touch_last_accessed`. This issues two identical SQL SELECT queries per request.
**Failure scenario:** Under load, every lesson page load issues a redundant DB query. With 100 concurrent students this doubles enrollment lookup queries.
**Impact:** Performance degradation; unnecessary DB load.
**Remediation:**
```python
enrollment = enrollment_service.get_enrollment_or_404(db, student.id, course_id)
enrollment_service.touch_last_accessed(db, enrollment)
```
**Regression test:** Existing `test_student_can_enroll_published` covers the happy path; add a query-count assertion.

---

#### FIND-006
**Severity:** High
**File:** `frontend/src/context/AuthContext.jsx` lines 29–32
**Problem:** On mount, `AuthContext` calls `api.post('/auth/refresh')` to restore the session. This request goes through the Axios instance which sets the `Origin` header correctly in a browser. However, the CSRF guard in `_verify_origin` checks `Origin` or `Referer`. On the very first page load from a cold start (no prior navigation), some browser configurations and non-browser clients (Postman, curl, mobile webviews) may not send `Origin` on a same-origin POST, causing a `403 CSRF check failed` and forcing the user to log in again on every page refresh.
**Failure scenario:** User opens the app in a fresh tab. The mount refresh call returns 403. `setUser(null)` is called. User is redirected to login despite having a valid refresh cookie.
**Impact:** Session restoration broken for some clients; poor UX; potential support burden.
**Remediation:** The Axios instance already sends `Origin` in browsers. For non-browser clients, document that the CSRF check is intentional. Consider adding `localhost` and `127.0.0.1` to `ALLOWED_ORIGINS` in dev `.env.example` (already done). Verify the mount refresh works end-to-end in the actual browser.
**Regression test:** Add a frontend integration test that simulates page reload and verifies session is restored.

---

#### FIND-007
**Severity:** High
**File:** `backend/app/main.py` lines 36–38
**Problem:** The in-memory rate limiter explicitly skips rate limiting for `127.0.0.1` and `testclient`. In a production deployment behind a reverse proxy (nginx, Caddy), `request.client.host` will always be `127.0.0.1` (the proxy's loopback address), making the rate limiter completely ineffective.
**Failure scenario:** An attacker behind a reverse proxy can send unlimited login attempts. The rate limiter never triggers because every request appears to come from `127.0.0.1`.
**Impact:** Brute-force protection is bypassed in any proxied deployment.
**Remediation:** Use `X-Forwarded-For` or `X-Real-IP` headers (with trusted proxy validation) to get the real client IP. Or use a Redis-backed rate limiter (slowapi with Redis storage) that is proxy-aware.
**Regression test:** Test that rate limiting triggers when `X-Forwarded-For` is set to a non-localhost IP.

---

#### FIND-008
**Severity:** High
**File:** `backend/app/models/lesson_progress.py` / `backend/app/services/progress_service.py`
**Problem:** There is no database-level constraint preventing a `LessonProgress` record from linking an `enrollment_id` (for course A) to a `lesson_id` (from course B). The application code in `progress_service.py` checks `lesson.is_published` and `enrollment.course_id == lesson.course_id` at the service layer, but this invariant is not enforced by a DB constraint or check.
**Failure scenario:** A race condition or a direct DB manipulation could create a progress record where `enrollment.course_id != lesson.course_id`. Progress calculations would then count lessons from the wrong course.
**Impact:** Data integrity — progress percentages could be incorrect; cross-course data contamination.
**Remediation:** Add a DB-level check or enforce via a trigger. At minimum, add an explicit assertion in `_get_or_create_progress` that `enrollment.course_id == lesson.course_id` before creating the record, raising a 400 if violated.
**Regression test:** Test that completing a lesson from a different course than the enrollment raises an error.

---

### MEDIUM

---

#### FIND-009
**Severity:** Medium
**File:** `backend/app/schemas/course.py` `CourseCreate` / `CourseUpdate`
**Problem:** `thumbnail_url` accepts any string up to 2048 characters with no URL format validation. An instructor can submit `thumbnail_url: "javascript:alert(1)"` or any non-HTTP string.
**Impact:** Stored XSS risk if the frontend renders the URL in an `<img src>` or `<a href>` without sanitization. The `CourseCard` component renders it directly in `<img src={course.thumbnail_url}>`.
**Remediation:** Add a `@field_validator("thumbnail_url")` that checks the value starts with `https://` or is `None`.
**Regression test:** Test that `thumbnail_url: "javascript:alert(1)"` returns 422.

---

#### FIND-010
**Severity:** Medium
**File:** `backend/app/services/auth_service.py` `_verify_origin`
**Problem:** The CSRF guard parses `Referer` by stripping the path, but `Referer` can be suppressed by `Referrer-Policy: no-referrer` headers on the page. If both `Origin` and `Referer` are absent, `request_origin` becomes `""` which is not in `allowed`, so the request is correctly rejected. However, this means legitimate browser requests from pages with strict referrer policies will be blocked.
**Impact:** Legitimate users on privacy-hardened browsers may be unable to refresh tokens or log out.
**Remediation:** Rely primarily on `Origin` (which browsers always send on cross-origin requests and on same-origin POST in modern browsers). Document that `Referer` is a fallback only. Consider adding a CSRF double-submit cookie as a more robust alternative.
**Regression test:** Test that a request with no `Origin` and no `Referer` is rejected; test that a request with a valid `Origin` but no `Referer` is accepted.

---

#### FIND-011
**Severity:** Medium
**File:** `frontend/src/pages/student/LearnPage.jsx` lines 9–17 (`renderContent`)
**Problem:** `renderContent` is a hand-rolled line-by-line Markdown parser. It handles only `#`, `##`, `###` headings and blank lines. Code blocks (` ``` `), bold, italic, links, lists, and inline code are rendered as raw text. The seed data contains extensive Markdown with code blocks and inline code that will not render correctly.
**Impact:** Poor student experience — lesson content appears as raw Markdown syntax rather than formatted text.
**Remediation:** Replace `renderContent` with a proper Markdown library such as `react-markdown` with `remark-gfm`. Ensure HTML sanitization is enabled (use `rehype-sanitize`) to prevent XSS from instructor-authored content.
**Regression test:** Render a lesson with a code block and assert the `<pre>` / `<code>` elements are present.

---

#### FIND-012
**Severity:** Medium
**File:** `frontend/src/pages/student/LearnPage.jsx` line 93
**Problem:** The iframe `src` is constructed with `activeLesson.video_url.replace('watch?v=', 'embed/')`. This only works for `https://www.youtube.com/watch?v=...` URLs. It does not handle:
- `https://youtu.be/<id>` short URLs
- `https://vimeo.com/<id>` URLs
- YouTube URLs with additional query parameters (e.g. `&t=30`)
**Impact:** Videos from Vimeo or YouTube short URLs will not embed correctly — the iframe will show a broken or blank player.
**Remediation:** Write a proper `getEmbedUrl(url)` utility that handles all allowed URL formats from `ALLOWED_VIDEO_SCHEMES` in `lesson.py`.
**Regression test:** Unit test `getEmbedUrl` with all four allowed URL formats.

---

#### FIND-013
**Severity:** Medium
**File:** `backend/app/services/progress_service.py` `get_instructor_course_progress`
**Problem:** For each enrollment, `compute_progress` issues two separate SQL queries (one for published lessons, one for completed progress records). With N enrollments, this is **2N+1 queries** (N×2 + 1 for the enrollment list). For a course with 100 students this is 201 queries per progress page load.
**Impact:** Performance — instructor progress page will be slow for popular courses.
**Remediation:** Rewrite using a single JOIN query or use SQLAlchemy `joinedload` / subquery to fetch all progress in one query, then compute in Python.
**Regression test:** Add a query-count assertion for a course with multiple enrollments.

---

#### FIND-014
**Severity:** Medium
**File:** `backend/app/services/enrollment_service.py` `enroll_student`
**Problem:** The duplicate enrollment check uses an application-level SELECT before INSERT. Under concurrent requests, two simultaneous enrollment requests can both pass the SELECT check before either commits, resulting in a race condition. The `IntegrityError` catch on the INSERT handles this correctly for the DB constraint path, but the error message returned is `"Already enrolled"` which is correct. However, the `db.rollback()` in the `except IntegrityError` block rolls back the entire session, which could affect other pending writes in the same session if the caller had made prior unflushed changes.
**Impact:** Low probability data integrity risk under high concurrency; session state risk.
**Remediation:** Use `INSERT ... ON CONFLICT DO NOTHING` or rely solely on the unique constraint + IntegrityError catch, removing the pre-check SELECT.
**Regression test:** Existing `test_duplicate_enrollment_rejected` covers the sequential case; add a concurrent enrollment test.

---

#### FIND-015
**Severity:** Medium
**File:** `backend/.env.example` line 8
**Problem:** `.env.example` still contains `COOKIE_SAMESITE=lax` even though `COOKIE_SAMESITE` was removed from `config.py` and `auth_service.py` now hard-codes `samesite="strict"`. This stale entry will confuse developers who copy `.env.example` to `.env`.
**Impact:** Developer confusion; stale documentation.
**Remediation:** Remove `COOKIE_SAMESITE=lax` from `.env.example`.
**Regression test:** N/A — documentation fix.

---

### LOW

---

#### FIND-016
**Severity:** Low
**File:** `backend/app/main.py` line 23
**Problem:** `@app.on_event("startup")` is deprecated in FastAPI 0.111. The deprecation warning appears in every test run and server startup log.
**Remediation:** Migrate to the `lifespan` context manager pattern.
**Regression test:** Verify no deprecation warnings in test output after migration.

---

#### FIND-017
**Severity:** Low
**File:** `backend/app/schemas/auth.py` `RegisterRequest`
**Problem:** Password validation only checks length (8–128 chars). There is no complexity requirement (uppercase, digit, special character). The seed passwords use `Password1!` format but the schema does not enforce this pattern.
**Impact:** Weak passwords like `aaaaaaaa` are accepted.
**Remediation:** Add complexity validation or document that complexity is intentionally not enforced.
**Regression test:** Test that `"aaaaaaaa"` is accepted or rejected per policy decision.

---

#### FIND-018
**Severity:** Low
**File:** `backend/app/models/auth_session.py`
**Problem:** There is no cleanup mechanism for expired or revoked `AuthSession` rows. Over time the `auth_sessions` table will grow unboundedly.
**Impact:** Table bloat; slower session lookup queries over time.
**Remediation:** Add a periodic cleanup job or a DB-level TTL. At minimum, add an index on `expires_at` and document the cleanup requirement.
**Regression test:** N/A — operational concern.

---

#### FIND-019
**Severity:** Low
**File:** `frontend/src/pages/instructor/CourseFormPage.jsx` lines 13–18
**Problem:** The `initialised` guard pattern (`if (initial && !initialised) { setForm(...); setInitialised(true) }`) calls `setForm` and `setInitialised` during render (not in a `useEffect`). This is a React anti-pattern — calling `setState` during render causes an extra render cycle and can trigger React warnings in strict mode.
**Remediation:** Move the initialisation into a `useEffect(() => { if (initial) { setForm(...) } }, [initial])`.
**Regression test:** Existing edit form tests cover the functional behavior.

---

#### FIND-020
**Severity:** Low
**File:** `frontend/src/services/api.js` line 3
**Problem:** The fallback base URL is `http://127.0.0.1:8000/api/v1` (port 8000) but the project runs on port 9000. If `VITE_API_BASE_URL` is not set in `.env`, the frontend will silently point to the wrong port.
**Impact:** Silent misconfiguration — all API calls fail with connection refused if `.env` is missing.
**Remediation:** Change the fallback to port 9000, or remove the fallback and throw an error if `VITE_API_BASE_URL` is not set.
**Regression test:** N/A — configuration fix.

---

### INFORMATIONAL

---

#### FIND-021
**File:** `backend/app/schemas/course.py`
**Note:** `CourseCreate` imports `HttpUrl` from Pydantic but never uses it. Dead import.

#### FIND-022
**File:** `backend/app/models/lesson_progress.py`
**Note:** `last_position_seconds` column exists in the model and schema but is never written to by any service. It is a placeholder for video resume functionality that has not been implemented.

#### FIND-023
**File:** `frontend/src/features/`
**Note:** The `features/` directory (courses, enrollment, lessons, progress subdirectories) and `hooks/` directory are empty. They appear to be scaffolding for a future feature-based architecture that was not implemented.

#### FIND-024
**File:** `backend/app/services/progress_service.py` `get_student_lesson_progress`
**Note:** `get_student_lesson_progress` is defined but never called from any endpoint or service. Dead code.

#### FIND-025
**File:** `backend/migrations/`
**Note:** An Alembic migration exists (`2fa5b8185adc_initial_lms_schema.py`) but has not been verified to run cleanly against a fresh PostgreSQL database. The migration should be tested as part of the deployment checklist.

---

## C. Missing Requirements and Incomplete Functionality

| # | Feature | Status |
|---|---------|--------|
| 1 | Video resume position (`last_position_seconds`) | Column exists, never written |
| 2 | Email verification on registration | Not implemented (documented in README) |
| 3 | Admin panel for user management | Not implemented (documented in README) |
| 4 | Lesson reorder UI | Backend supports it; no drag-and-drop UI |
| 5 | Archived course access for enrolled students | Not specified — archived courses disappear from catalog but enrolled students lose access |
| 6 | Instructor account creation | No self-registration path; must be seeded or created directly in DB |
| 7 | File/video upload | Not implemented — YouTube/Vimeo URLs only |
| 8 | Pagination on instructor course list | No pagination — unbounded list |
| 9 | Student search/filter on progress page | No search on instructor progress report |

---

## D. Database Design and Data Integrity Assessment

**Strengths:**
- All foreign keys are defined with appropriate `ondelete` actions.
- `UniqueConstraint` on `(student_id, course_id)` prevents duplicate enrollments at DB level.
- `UniqueConstraint` on `(course_id, position)` prevents duplicate lesson positions at DB level.
- `UniqueConstraint` on `(enrollment_id, lesson_id)` prevents duplicate progress records.
- Cascade deletes are correctly configured: Course → Lesson → LessonProgress; Course → Enrollment → LessonProgress.
- `AuthSession.refresh_token_hash` has a unique constraint — prevents token hash collisions.

**Deficiencies:**
- No DB-level constraint preventing `LessonProgress` from crossing course boundaries (FIND-008).
- No index on `AuthSession.expires_at` — session cleanup queries will be slow.
- No index on `LessonProgress.status` — progress aggregation queries scan all progress rows.
- `Course.instructor_id` uses `ondelete="RESTRICT"` — deleting an instructor with courses will fail at DB level with no user-friendly error.
- SQLite does not enforce foreign key constraints by default (`PRAGMA foreign_keys = ON` is not set in `base.py`).

---

## E. Security Assessment and Authorization Matrix

| Endpoint | Unauth | Student | Instructor (own) | Instructor (other) |
|----------|--------|---------|------------------|--------------------|
| GET /courses | ✓ | ✓ | ✓ | ✓ |
| GET /courses/{id} | ✓ (published only) | ✓ | ✓ | ✓ |
| POST /courses/{id}/enroll | ✗ 401 | ✓ | ✗ 403 | ✗ 403 |
| GET /instructor/courses | ✗ 401 | ✗ 403 | ✓ | ✓ (own only) |
| POST /instructor/courses | ✗ 401 | ✗ 403 | ✓ | ✓ |
| PATCH /instructor/courses/{id} | ✗ 401 | ✗ 403 | ✓ | ✗ 403 |
| DELETE /instructor/courses/{id} | ✗ 401 | ✗ 403 | ✓ | ✗ 403 |
| POST /instructor/courses/{id}/publish | ✗ 401 | ✗ 403 | ✓ | ✗ 403 |
| GET /instructor/courses/{id}/progress | ✗ 401 | ✗ 403 | ✓ | ✗ 403 |
| GET /students/me/courses | ✗ 401 | ✓ | ✗ 403 | ✗ 403 |
| POST /students/me/lessons/{id}/complete | ✗ 401 | ✓ (enrolled) | ✗ 403 | ✗ 403 |
| POST /auth/refresh | ✗ 403 (no Origin) | ✓ | ✓ | ✓ |
| POST /auth/logout | ✗ 403 (no Origin) | ✓ | ✓ | ✓ |

**Confirmed correct:** Role enforcement is server-side on all protected endpoints. Course ownership (`assert_owns_course`) is checked before every instructor mutation. Students cannot access other students' progress (enforced by `student_id` filter in `get_course_progress`).

**Confirmed gap:** No server-side check that a lesson being completed belongs to a course the student is enrolled in via the enrollment record — the check is `enrollment.course_id == lesson.course_id` which is correct, but see FIND-008 for the missing DB constraint.

---

## F. Build and Startup Results

| Check | Result |
|-------|--------|
| Backend: `pytest tests/ -v` | 41 passed, 2 warnings |
| Frontend: `npm test` | 34 passed |
| Frontend: `npm run build` | PASS (313 kB, 475ms) |
| Backend startup (uvicorn) | Not executed in audit (safe to run locally) |
| Docker build | Not executed — port mismatch identified (FIND-001) |
| Alembic migration on fresh DB | Not executed — requires PostgreSQL |

---

## G. Prioritized Remediation Plan

### P0 — Critical Blockers

| ID | Action |
|----|--------|
| FIND-001 | Fix Dockerfile port: change `EXPOSE 8000` and `--port 8000` to `9000` |
| FIND-002a | Add `SECRET_KEY` minimum-length validator (≥32 chars) in `config.py` |
| FIND-002b | Gate `create_tables()` behind `if not settings.is_production` in `main.py` |

### P1 — High Priority

| ID | Action |
|----|--------|
| FIND-003 | Delete `_optional_user` dead code from `catalog.py` |
| FIND-004 | Replace `response_model=list[dict]` with a typed `StudentCourseItem` schema |
| FIND-005 | Fix double `get_enrollment_or_404` call in `my_course_lessons` |
| FIND-007 | Fix rate limiter to use real client IP behind reverse proxy |
| FIND-008 | Add cross-course enrollment/lesson validation in `_get_or_create_progress` |

### P2 — Medium Priority

| ID | Action |
|----|--------|
| FIND-009 | Add `https://` validation on `thumbnail_url` in course schemas |
| FIND-011 | Replace hand-rolled Markdown parser with `react-markdown` + `rehype-sanitize` |
| FIND-012 | Fix iframe embed URL generation for all allowed video URL formats |
| FIND-013 | Optimize `get_instructor_course_progress` to avoid N+1 queries |
| FIND-015 | Remove stale `COOKIE_SAMESITE` from `.env.example` |
| FIND-016 | Migrate `@app.on_event("startup")` to lifespan handler |
| FIND-019 | Fix `CourseFormPage` setState-during-render anti-pattern |
| FIND-020 | Fix fallback base URL in `api.js` from port 8000 to 9000 |

### P3 — Lower Priority

| ID | Action |
|----|--------|
| FIND-017 | Document or enforce password complexity policy |
| FIND-018 | Add `AuthSession` cleanup job or document operational requirement |
| FIND-021 | Remove unused `HttpUrl` import from `course.py` schemas |
| FIND-022 | Implement or remove `last_position_seconds` |
| FIND-023 | Remove empty `features/` and `hooks/` scaffold directories or implement them |
| FIND-024 | Remove unused `get_student_lesson_progress` function |
| FIND-025 | Verify Alembic migration runs cleanly on a fresh PostgreSQL database |

---

## H. Final Readiness Assessment

**CONDITIONAL GO — suitable for internal development demonstration only.**

The application demonstrates solid architecture, correct role-based access control, proper token rotation, and a clean service layer. All automated tests pass and the production build succeeds.

It is **not ready for staging** until the following are resolved:

1. **FIND-001** — Docker port mismatch (container will not serve traffic)
2. **FIND-002** — `SECRET_KEY` length enforcement and `create_tables()` production gate
3. **FIND-007** — Rate limiter bypass behind reverse proxy
4. **FIND-004** — Untyped student courses response
5. **FIND-011** — Markdown rendering (lesson content is unreadable in the browser)

After P0 and P1 fixes are applied and verified, the application would be **ready for staging** with the P2 items tracked as known issues.
