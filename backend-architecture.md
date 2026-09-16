# Task Management App — Backend System Design & Architecture

## 1. Overview

A lightweight task management backend supporting Google Sign-In, task CRUD, and status tracking (`Planned` → `In Progress` → `Complete`). Scoped strictly to the assessment's four functional requirements, with a few documented usability improvements.

**Build tool**: Antigravity (Claude Sonnet model)
**Backend**: FastAPI (Python)
**Database**: PostgreSQL, containerized via Docker
**Deployment**: Render (frontend + backend), Postgres running in a Docker container (either on Render as a Docker-based web service, or via Render's own managed Postgres if you decide to switch later)

---

## 2. High-Level Architecture

```
┌─────────────────┐        HTTPS         ┌──────────────────┐        SQL         ┌──────────────────┐
│   React Frontend │ ───────────────────▶ │   FastAPI Backend │ ─────────────────▶ │  PostgreSQL (Docker) │
│   (Render Static/│ ◀─────────────────── │   (Render Web Svc) │ ◀───────────────── │  (Render Docker Svc) │
│   Web Service)    │      JSON/REST       └──────────────────┘                     └──────────────────┘
└─────────────────┘
        │
        │ OAuth popup
        ▼
┌─────────────────┐
│ Google Identity  │
│ Services (OAuth) │
└─────────────────┘
```

**Flow summary:**
1. Frontend triggers Google Sign-In → receives a Google ID token directly from Google (no backend involvement at this step).
2. Frontend sends the ID token to the backend (`POST /auth/google`).
3. Backend verifies the token against Google's public keys, upserts the user, and issues its own short-lived JWT.
4. Frontend stores the JWT and attaches it as a Bearer token on every subsequent API call.
5. Backend validates the JWT on protected routes and scopes all task queries to `user_id`.

---

## 3. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend framework | FastAPI | Fast to build, async-native, auto-generated OpenAPI docs (doubles as API documentation deliverable) |
| ORM | SQLAlchemy 2.0 | Standard, works cleanly with Alembic migrations |
| Migrations | Alembic | Version-controlled schema changes |
| Database | PostgreSQL 16 | Relational, free-tier friendly, industry standard |
| Auth verification | `google-auth` (Python lib) | Verifies Google ID tokens without needing a full OAuth server flow |
| Session tokens | JWT (`python-jose` or `PyJWT`) | Stateless, no server-side session store needed |
| Containerization | Docker + Docker Compose (local) | Postgres runs in Docker; backend can also be containerized for Render's Docker deploy option |
| Deployment | Render (Web Service for backend, Static Site or Web Service for frontend, Docker service for Postgres) | Free-tier viable, straightforward CI from GitHub |

---

## 4. Data Model

### `users`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| google_id | VARCHAR | UNIQUE, NOT NULL (Google's `sub` claim) |
| email | VARCHAR | UNIQUE, NOT NULL |
| name | VARCHAR | NOT NULL |
| picture_url | VARCHAR | NULLABLE |
| created_at | TIMESTAMP | default `now()` |

### `tasks`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| user_id | UUID | FK → `users.id`, NOT NULL, ON DELETE CASCADE |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NULLABLE |
| status | ENUM(`planned`, `in_progress`, `complete`) | NOT NULL, default `planned` |
| created_at | TIMESTAMP | default `now()` |
| updated_at | TIMESTAMP | auto-updated on modification |

---

## 5. API Specification

| Method | Route | Description | Auth |
|---|---|---|---|
| POST | `/auth/google` | Verify Google ID token, upsert user, return app JWT | Public |
| GET | `/auth/me` | Return current authenticated user's profile | Bearer JWT |
| POST | `/tasks` | Create a new task (default status `planned`) | Bearer JWT |
| GET | `/tasks` | List all tasks belonging to the current user | Bearer JWT |
| GET | `/tasks/{id}` | Fetch a single task (ownership-checked) | Bearer JWT |
| PATCH | `/tasks/{id}` | Update task fields (title, description, or status) | Bearer JWT |
| DELETE | `/tasks/{id}` | Delete a task (documented usability addition) | Bearer JWT |

**Request/response bodies (illustrative):**

```
POST /auth/google
Request:  { "id_token": "<google-id-token>" }
Response: { "access_token": "<jwt>", "user": { "id", "email", "name", "picture_url" } }

POST /tasks
Request:  { "title": "Finish report", "description": "Optional" }
Response: { "id", "title", "description", "status": "planned", "created_at" }

PATCH /tasks/{id}
Request:  { "status": "in_progress" }
Response: { "id", "title", "status": "in_progress", "updated_at" }
```

---

## 6. Authentication & Authorization Design

- **No custom OAuth server** — the frontend uses Google Identity Services JS SDK to get an ID token directly; the backend's only job is **verification**, not orchestration. This is simpler, more secure (no client secret exposure), and standard practice for SPA + API architectures.
- **JWT for session**: after verification, backend issues its own JWT (HS256, short expiry — e.g., 24h) containing `user_id` and `email`.
- **Authorization**: every task query is filtered by `user_id` extracted from the JWT — no task is ever accessible cross-user.
- **Token storage on frontend**: recommend `httpOnly` cookie if backend and frontend share a domain/subdomain on Render; otherwise `localStorage` with clear documentation of the XSS trade-off.

---

## 7. Docker & Local Development Setup

### `docker-compose.yml` (local dev — Postgres in Docker, backend runs natively or containerized)

```yaml
version: "3.9"
services:
  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_USER: taskapp
      POSTGRES_PASSWORD: taskapp_pw
      POSTGRES_DB: taskapp_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://taskapp:taskapp_pw@db:5432/taskapp_db
      JWT_SECRET: ${JWT_SECRET}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
    ports:
      - "8000:8000"

volumes:
  pgdata:
```

### Backend `Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. Folder Structure

```
backend/
├── app/
│   ├── main.py                # FastAPI app entrypoint, CORS config
│   ├── database.py            # SQLAlchemy engine/session setup
│   ├── models.py              # User, Task ORM models
│   ├── schemas.py             # Pydantic request/response schemas
│   ├── auth.py                # Google token verification + JWT issuing/decoding
│   ├── dependencies.py        # get_current_user() dependency for protected routes
│   └── routers/
│       ├── auth.py            # /auth/google, /auth/me
│       └── tasks.py           # /tasks CRUD
├── alembic/
│   ├── versions/
│   └── env.py
├── requirements.txt
├── Dockerfile
├── .env.example
└── alembic.ini
```

---

## 9. Environment Variables

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string (points to Docker container in dev, Render Postgres/Docker service in prod) |
| `GOOGLE_CLIENT_ID` | Used to verify Google ID tokens' `aud` claim |
| `JWT_SECRET` | Signing key for app-issued JWTs |
| `JWT_EXPIRY_MINUTES` | Token lifetime (e.g., `1440` for 24h) |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins (Render frontend URL) |

---

## 10. Deployment Plan on Render

1. **Database**: deploy Postgres as a Render **Docker-based private service** (using the official `postgres:16` image) with a persistent disk attached — this satisfies the "Postgres runs in Docker" requirement while staying on Render's infra.
2. **Backend**: deploy as a Render **Web Service**, built from the `backend/Dockerfile`. Set environment variables in Render's dashboard. Point `DATABASE_URL` at the internal Render hostname of the Postgres Docker service.
3. **Frontend**: deploy as a Render **Static Site** (if pure React build) or **Web Service** (if it needs SSR). Set the backend API base URL as a build-time environment variable.
4. **CORS**: backend must explicitly allow the deployed frontend's Render URL as an origin.
5. **Migrations**: run `alembic upgrade head` as a Render **pre-deploy/release command**, or manually via Render's shell on first deploy.

---

## 11. Assumptions & Design Decisions (for documentation deliverable)

- Tasks are private per user; no sharing/collaboration since it wasn't requested.
- No due dates, priorities, tags, or categories — out of scope per the assessment's explicit "do not expand scope" note.
- `DELETE /tasks/{id}` added as a minimal usability affordance (correcting mistaken entries), not a scope expansion.
- Status transitions are unrestricted (any state → any state) rather than enforcing a strict linear workflow — simpler, and defensible as a deliberate design choice.
- Auth is verification-only on the backend (no backend-driven OAuth redirect flow) — reduces complexity and avoids handling client secrets server-side.
- JWT chosen over server-side sessions to avoid needing a session store for a small app.

---

## 12. AI Usage Summary (for submission)

- **Tool used**: Antigravity, powered by Claude Sonnet.
- **How used**: Architecture and API design generated collaboratively, then implementation scaffolding (models, routers, auth logic, Docker configuration) generated and reviewed before integration.
- **Manual review focus areas**: JWT secret handling and environment variable hygiene, CORS configuration correctness, Alembic migration review before applying to the database, and verifying Google token validation logic against Google's official library documentation rather than trusting generated code blindly.
