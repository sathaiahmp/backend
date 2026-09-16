# Graduate Support Engineer Trainee Assessment
## Complete System Design, Backend Architecture & AI-Coding Specification

> **Purpose:** This document is the implementation blueprint for the Graduate Support Engineer Trainee assessment. It is intentionally scoped to the requirements in the supplied assessment and is designed for fast, reliable implementation with an AI coding agent such as **Antigravity using Claude Sonnet**.

---

# 1. Assessment Requirements

The assessment requires a simple task-management application.

## Functional requirements

The application must allow an authenticated user to:

1. Sign in using Google Authentication.
2. Create tasks.
3. View the list of tasks.
4. Update the status of a task.

Each task must support exactly three states:

- `PLANNED`
- `IN_PROGRESS`
- `COMPLETE`

The assessment explicitly says the listed use cases are sufficient and that unnecessary scope expansion should be avoided.

## Evaluation areas

The solution is evaluated on:

- Requirement understanding
- AI tool usage
- Application functionality
- Problem solving
- Documentation
- User experience
- Deployment

## Submission

The final submission should contain:

- Source-code repository
- Live application URL, if deployed
- Documentation
- AI usage summary

The AI usage summary should explain:

- Which AI tools were used
- How they were used
- Example prompts, if useful
- Which AI-generated code was manually modified or corrected

---

# 2. Recommended Technology Stack

## Frontend

- React
- TypeScript
- Vite
- React Router only if multiple routes become necessary
- CSS / Tailwind CSS
- Google Identity Services

## Backend

- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- PostgreSQL driver: `psycopg`
- `google-auth` for Google ID-token verification
- Uvicorn

## Database

- PostgreSQL
- PostgreSQL runs inside Docker for local development.
- For the user's preferred Render deployment architecture, PostgreSQL can run as a separate Dockerized private service backed by a Render persistent disk.

## Infrastructure

- Docker
- Docker Compose for local development
- GitHub
- Render
- Environment variables for secrets/configuration

---

# 3. High-Level System Architecture

```text
                         INTERNET
                            |
                            v
                 +----------------------+
                 |   React Frontend     |
                 |   Render Static Site |
                 +----------+-----------+
                            |
                            | HTTPS / JSON
                            | Authorization
                            v
                 +----------------------+
                 |    FastAPI Backend   |
                 |    Render Web Svc    |
                 +----------+-----------+
                            |
             +--------------+---------------+
             |                              |
             | Verify Google ID Token       |
             |                              |
             v                              v
      +-------------+              +------------------+
      | Google      |              | PostgreSQL       |
      | Identity    |              | Docker Container |
      | Services    |              | Render Private  |
      +-------------+              | Service          |
                                   +------------------+
                                           |
                                   Persistent Disk
                                           |
                                           v
                                      PostgreSQL Data
```

---

# 4. Important Deployment Decision: PostgreSQL in Docker on Render

The preference is to run PostgreSQL in Docker.

This is technically possible on Render, but there is an important deployment constraint:

- Render services have an ephemeral filesystem by default.
- A database container needs persistent storage.
- A Render persistent disk preserves data across deploys/restarts.
- Render's documentation states that persistent disks are available for paid web services, private services, and background workers.
- Render recommends its managed PostgreSQL service when it is suitable.

Therefore, for this assessment there are two architectures:

## Option A — User-preferred architecture

```text
Render
|
+-- Frontend: Static Site
|
+-- Backend: Web Service
|
+-- PostgreSQL: Private Service
       |
       +-- Docker PostgreSQL
       |
       +-- Persistent Disk
```

Use this if the assessment environment/account supports the required Render persistent disk.

## Option B — Simpler production architecture

```text
Render
|
+-- Frontend: Static Site
|
+-- Backend: Web Service
|
+-- Render Managed PostgreSQL
```

Use this if the goal is minimum deployment complexity.

### Recommendation for this assessment

Develop with Docker PostgreSQL locally.

Keep the backend database layer configured through `DATABASE_URL`, so the database implementation can be switched without changing application code.

This gives:

```text
Local:
Docker PostgreSQL

Production:
Docker PostgreSQL + persistent disk
OR
Render PostgreSQL
```

The application code remains the same.

---

# 5. Backend Architecture

Use a clean layered FastAPI architecture.

```text
HTTP Request
     |
     v
+------------------+
| API Router       |
| routes/          |
+--------+---------+
         |
         v
+------------------+
| Authentication   |
| / Dependencies   |
+--------+---------+
         |
         v
+------------------+
| Pydantic Schema  |
| Validation       |
+--------+---------+
         |
         v
+------------------+
| Service Layer    |
| Business Logic   |
+--------+---------+
         |
         v
+------------------+
| SQLAlchemy ORM   |
| Data Access      |
+--------+---------+
         |
         v
+------------------+
| PostgreSQL       |
+------------------+
```

## Layer responsibilities

### Router layer

Responsible for:

- HTTP endpoints
- HTTP status codes
- Request/response models
- Dependency injection
- Authentication dependencies

Do not put complex business logic inside route functions.

### Authentication layer

Responsible for:

- Receiving Google authentication credentials
- Verifying Google ID tokens
- Extracting Google user identity
- Creating/finding local user
- Providing the current authenticated user to protected routes

### Schema layer

Responsible for:

- Request validation
- Response serialization
- Enum validation
- Preventing invalid task states

### Service layer

Responsible for:

- Create task
- List user's tasks
- Update task status
- Ownership checks
- Business rules

### Database layer

Responsible for:

- SQLAlchemy engine
- Session management
- Models
- Queries
- Transactions

---

# 6. Backend Project Structure

Recommended structure:

```text
backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── base.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── task.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   └── task.py
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── task_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   └── task_service.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── tasks.py
│   │       └── health.py
│   │
│   └── exceptions/
│       └── handlers.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_tasks.py
│   └── test_health.py
│
├── alembic/
│   └── ...
│
├── Dockerfile
├── requirements.txt
├── alembic.ini
├── .env.example
└── README.md
```

For a very short assessment, repositories can be omitted and the service layer can access SQLAlchemy directly. The above structure is preferable if there is enough time.

---

# 7. Database Design

## Entity Relationship

```text
+----------------------+
|        users         |
+----------------------+
| id PK                |
| google_id UNIQUE     |
| email UNIQUE         |
| name                 |
| profile_picture      |
| created_at           |
| updated_at           |
+----------+-----------+
           |
           | 1
           |
           | N
           v
+----------------------+
|        tasks         |
+----------------------+
| id PK                |
| user_id FK           |
| title                |
| description          |
| status               |
| created_at           |
| updated_at           |
+----------------------+
```

## Users table

```text
users
-------------------------
id                UUID / integer PK
google_id         VARCHAR UNIQUE NOT NULL
email             VARCHAR UNIQUE NOT NULL
name              VARCHAR NOT NULL
profile_picture   TEXT NULL
created_at        TIMESTAMP
updated_at        TIMESTAMP
```

## Tasks table

```text
tasks
-------------------------
id                UUID / integer PK
user_id           FK -> users.id
title             VARCHAR NOT NULL
description       TEXT NULL
status            ENUM / VARCHAR NOT NULL
created_at        TIMESTAMP
updated_at        TIMESTAMP
```

## Task status constraint

Only these values are valid:

```text
PLANNED
IN_PROGRESS
COMPLETE
```

Do not allow arbitrary status strings.

---

# 8. Authentication Architecture

Use Google Identity Services on the frontend.

## Flow

```text
User
 |
 | Click "Sign in with Google"
 v
Google
 |
 | Google ID Token
 v
React
 |
 | POST /api/v1/auth/google
 | Authorization: Bearer <Google-ID-Token>
 v
FastAPI
 |
 | Verify ID Token with Google
 v
Google Token Verification
 |
 | Valid
 v
Extract:
- google_id
- email
- name
- picture
 |
 v
Find user in PostgreSQL
 |
 +---- Existing ----> return authenticated user
 |
 +---- New ---------> create user
 |
 v
React receives authenticated user/session state
```

## Important security rule

Never trust the Google profile information supplied by the browser without verifying the Google ID token on the backend.

The backend must verify:

- Token signature
- Token issuer
- Audience/client ID
- Expiration
- Google user identity

---

# 9. Authentication Strategy for the Assessment

Keep authentication simple.

Recommended:

```text
Google Identity Services
        |
        v
Google ID Token
        |
        v
FastAPI verifies token
        |
        v
Local user lookup/create
```

For the task assessment, avoid implementing a complicated custom OAuth server.

If persistent backend sessions are needed, use a secure server-side session or a short-lived application token.

Do not store Google client secrets in the frontend.

---

# 10. API Design

Use versioned REST APIs.

Base URL:

```text
/api/v1
```

---

## Health

### GET /api/v1/health

Response:

```json
{
  "status": "ok"
}
```

Purpose:

- Render health checks
- Debugging
- Deployment verification

---

# 11. Authentication APIs

## POST /api/v1/auth/google

Purpose:

Authenticate a Google user.

Request:

```json
{
  "credential": "<google-id-token>"
}
```

Response:

```json
{
  "user": {
    "id": "user-id",
    "email": "user@example.com",
    "name": "Example User",
    "profile_picture": "https://..."
  }
}
```

Possible responses:

```text
200 OK
400 Bad Request
401 Unauthorized
```

---

# 12. Task APIs

## POST /api/v1/tasks

Create a task.

Request:

```json
{
  "title": "Build FastAPI backend",
  "description": "Implement task APIs",
  "status": "PLANNED"
}
```

Response:

```json
{
  "id": "task-id",
  "title": "Build FastAPI backend",
  "description": "Implement task APIs",
  "status": "PLANNED",
  "created_at": "2026-09-16T10:00:00Z",
  "updated_at": "2026-09-16T10:00:00Z"
}
```

---

## GET /api/v1/tasks

Return tasks belonging to the authenticated user.

Response:

```json
[
  {
    "id": "task-1",
    "title": "Build API",
    "description": "Create FastAPI endpoints",
    "status": "IN_PROGRESS",
    "created_at": "2026-09-16T10:00:00Z",
    "updated_at": "2026-09-16T10:15:00Z"
  }
]
```

Important:

```text
GET /tasks
```

must never return another user's tasks.

---

## PATCH /api/v1/tasks/{task_id}/status

Update only the status.

Request:

```json
{
  "status": "COMPLETE"
}
```

Response:

```json
{
  "id": "task-1",
  "status": "COMPLETE",
  "updated_at": "2026-09-16T10:30:00Z"
}
```

Possible responses:

```text
200 OK
400 Bad Request
401 Unauthorized
404 Not Found
```

---

# 13. API Summary

```text
GET    /api/v1/health
POST   /api/v1/auth/google

POST   /api/v1/tasks
GET    /api/v1/tasks
PATCH  /api/v1/tasks/{task_id}/status
```

This is intentionally small.

Do NOT create unnecessary APIs such as:

```text
DELETE /tasks
PUT /profile
POST /comments
GET /analytics
POST /notifications
```

unless the requirements later change.

---

# 14. Request Validation

## Create task schema

```python
class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.PLANNED
```

Validation:

- Title required
- Trim whitespace
- Title cannot be empty
- Reasonable maximum title length
- Description optional
- Status must be a valid enum

## Status schema

```python
class TaskStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
```

---

# 15. Authorization

Authentication answers:

> Who is the user?

Authorization answers:

> Is this user allowed to access this task?

Every task query must be scoped by the authenticated user.

Example conceptual query:

```sql
SELECT *
FROM tasks
WHERE id = :task_id
AND user_id = :current_user_id;
```

Do not do this:

```sql
SELECT *
FROM tasks
WHERE id = :task_id;
```

and then trust the frontend.

The backend must enforce ownership.

---

# 16. Error Handling

Use consistent FastAPI errors.

Example:

```json
{
  "detail": "Task not found"
}
```

Recommended mapping:

| Situation | HTTP |
|---|---:|
| Invalid input | 400 / 422 |
| Missing authentication | 401 |
| User not authorized | 403 |
| Task doesn't exist for user | 404 |
| Unexpected server failure | 500 |

Do not expose:

- Database passwords
- Stack traces
- Internal filesystem paths
- Google secrets
- Environment variables

---

# 17. CORS

Because the React frontend and FastAPI backend will be separate Render services, configure CORS.

Development:

```text
http://localhost:5173
```

Production:

```text
https://<your-frontend>.onrender.com
```

Use an environment variable:

```text
FRONTEND_URL=https://your-frontend.onrender.com
```

Configure:

```python
CORSMiddleware(
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Avoid:

```python
allow_origins=["*"]
```

for the final deployment.

---

# 18. Docker Architecture — Local Development

Use Docker Compose locally.

```text
project/
│
├── frontend/
│
├── backend/
│   └── Dockerfile
│
├── docker-compose.yml
│
└── README.md
```

Architecture:

```text
Docker Compose
|
+----------------------+
| frontend             |
| React / Vite         |
+----------+-----------+
           |
           |
+----------v-----------+
| backend              |
| FastAPI              |
+----------+-----------+
           |
           |
+----------v-----------+
| postgres             |
| PostgreSQL           |
+----------------------+
```

---

# 19. Docker Compose Requirements

Conceptual configuration:

```yaml
services:

  postgres:
    image: postgres:16
    container_name: taskflow-postgres
    environment:
      POSTGRES_DB: taskflow
      POSTGRES_USER: taskflow
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    container_name: taskflow-backend
    environment:
      DATABASE_URL: postgresql+psycopg://taskflow:${POSTGRES_PASSWORD}@postgres:5432/taskflow
    depends_on:
      - postgres
    ports:
      - "8000:8000"

volumes:
  postgres_data:
```

The exact configuration should be generated and tested by the coding agent rather than copied blindly.

---

# 20. Database Connection

Use:

```text
DATABASE_URL
```

Example local value:

```text
postgresql+psycopg://taskflow:password@localhost:5432/taskflow
```

Inside Docker Compose, the hostname should be the service name:

```text
postgres
```

Therefore:

```text
postgresql+psycopg://taskflow:password@postgres:5432/taskflow
```

Production should use a Render environment variable.

Never hard-code credentials.

---

# 21. Database Migrations

Use Alembic.

Development:

```text
Create migration
      |
      v
alembic revision --autogenerate
      |
      v
Review migration
      |
      v
alembic upgrade head
```

Production:

```text
Deploy
 |
 v
Run migration
 |
 v
Start FastAPI
```

For a very small assessment, `Base.metadata.create_all()` can be used during initial prototyping, but Alembic is preferable for the final repository.

---

# 22. Environment Variables

Create:

```text
.env.example
```

Example:

```text
APP_ENV=development

DATABASE_URL=postgresql+psycopg://taskflow:password@localhost:5432/taskflow

GOOGLE_CLIENT_ID=your-google-client-id

FRONTEND_URL=http://localhost:5173

LOG_LEVEL=INFO
```

Production:

```text
APP_ENV=production

DATABASE_URL=<render-database-url>

GOOGLE_CLIENT_ID=<production-google-client-id>

FRONTEND_URL=https://your-frontend.onrender.com

LOG_LEVEL=INFO
```

Never commit:

```text
.env
```

to GitHub.

---

# 23. Logging

Use Python's standard logging system.

Log useful events:

```text
Application started
Database connection established
Google authentication success/failure
Task created
Task status updated
Unexpected exception
```

Do not log:

```text
Google ID tokens
Passwords
Database passwords
Authorization headers
Sensitive user information
```

Example:

```text
INFO - Task created - user_id=123 task_id=456
INFO - Task status updated - task_id=456 status=COMPLETE
ERROR - Database operation failed
```

---

# 24. Frontend-to-Backend Flow

## Login

```text
React
  |
  | Google Sign-In
  v
Google
  |
  | ID Token
  v
React
  |
  | POST /auth/google
  v
FastAPI
  |
  | verify
  v
PostgreSQL
```

## Create task

```text
User
 |
 | Create Task
 v
React
 |
 | POST /tasks
 | Authorization
 v
FastAPI
 |
 | validate
 v
Task Service
 |
 v
PostgreSQL
 |
 v
Created Task
 |
 v
React
```

## View tasks

```text
React
 |
 | GET /tasks
 v
FastAPI
 |
 | current user
 v
PostgreSQL
 |
 | WHERE user_id = current_user
 v
Tasks
 |
 v
React
```

## Update status

```text
User
 |
 | Select Complete
 v
React
 |
 | PATCH /tasks/{id}/status
 v
FastAPI
 |
 | authenticate
 | authorize ownership
 | validate status
 v
PostgreSQL
 |
 v
Updated task
 |
 v
React
```

---

# 25. API Documentation

FastAPI automatically provides:

```text
/docs
```

and:

```text
/redoc
```

Use Swagger UI during development to test:

- Authentication
- Create task
- Get tasks
- Update status
- Error responses

Do not expose sensitive development credentials through the API docs.

---

# 26. Testing Requirements

At minimum test:

## Authentication

- Valid Google credential
- Invalid Google credential
- New user creation
- Existing user login

## Tasks

- Create task
- Get user's tasks
- Update status
- Invalid status
- Missing title
- Empty title
- Unauthenticated task request
- User cannot update another user's task

## Health

```text
GET /api/v1/health
```

should return:

```json
{
  "status": "ok"
}
```

---

# 27. Deployment Architecture on Render

## Recommended service separation

```text
                    Render
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
  Frontend        Backend         Database
 Static Site     Web Service    Private Service
 React/Vite       FastAPI       PostgreSQL
                                   Docker
                                     |
                              Persistent Disk
```

## Frontend

Render service:

```text
Type: Static Site
```

Build:

```text
npm install
npm run build
```

Publish directory:

```text
dist
```

Environment variable:

```text
VITE_API_URL=https://your-backend.onrender.com
```

---

# 28. Backend Render Configuration

Render service:

```text
Type: Web Service
Runtime: Docker
```

Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
```

The backend must listen on:

```text
0.0.0.0
```

and use Render's `PORT` environment variable.

Health check:

```text
/api/v1/health
```

---

# 29. Dockerized PostgreSQL on Render

If using the preferred Docker database architecture:

```text
Render Private Service
        |
        v
PostgreSQL Docker Container
        |
        v
/var/lib/postgresql/data
        |
        v
Render Persistent Disk
```

The PostgreSQL container should not be exposed publicly.

Backend connects through Render's private network.

Conceptually:

```text
DATABASE_URL=
postgresql://taskflow:<password>@<private-db-host>:5432/taskflow
```

The exact internal hostname should come from the Render service configuration.

## Important

Do not use:

```text
localhost
```

for the production backend-to-database connection.

`localhost` inside the FastAPI container refers to the FastAPI container itself.

---

# 30. Render Production Network

```text
Internet
   |
   v
React Static Site
   |
   | HTTPS
   v
FastAPI Web Service
   |
   | Private Network
   v
PostgreSQL Private Service
```

Google authentication traffic:

```text
React
 |
 v
Google
```

Google ID-token verification:

```text
FastAPI
 |
 v
Google token verification
```

---

# 31. Render Environment Variables

## Frontend

```text
VITE_API_URL
VITE_GOOGLE_CLIENT_ID
```

## Backend

```text
DATABASE_URL
GOOGLE_CLIENT_ID
FRONTEND_URL
APP_ENV
LOG_LEVEL
```

## PostgreSQL

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
```

Use Render secrets/environment variables rather than committing credentials.

---

# 32. Security Checklist

Before submission:

- [ ] Google ID token verified on backend
- [ ] No secrets in GitHub
- [ ] `.env` in `.gitignore`
- [ ] CORS restricted to frontend origin
- [ ] Every task query scoped to current user
- [ ] Invalid statuses rejected
- [ ] Authentication required for task endpoints
- [ ] Database not publicly exposed
- [ ] Database password stored as secret
- [ ] No tokens printed in logs
- [ ] HTTPS used in production
- [ ] Production Google OAuth configuration verified

---

# 33. Scope Control

Do NOT implement these unless explicitly requested:

```text
Teams
Roles
Admin dashboard
Task comments
Attachments
Notifications
Email notifications
Task priorities
Tags
Calendar
Search
Analytics
Dark mode
Chat
Real-time WebSockets
Redis
Celery
Microservices
GraphQL
Kubernetes
AI task generation
```

The assessment specifically warns against unnecessary scope expansion.

---

# 34. Requirement-to-Implementation Mapping

| Assessment requirement | Implementation |
|---|---|
| Google Authentication | Google Identity Services + FastAPI token verification |
| Create tasks | `POST /api/v1/tasks` |
| View task list | `GET /api/v1/tasks` |
| Update task status | `PATCH /api/v1/tasks/{id}/status` |
| Planned | `TaskStatus.PLANNED` |
| In Progress | `TaskStatus.IN_PROGRESS` |
| Complete | `TaskStatus.COMPLETE` |
| User isolation | `tasks.user_id` |
| Documentation | README + user documentation |
| AI Usage Summary | `docs/AI_USAGE.md` |
| Deployment | Render |
| Database | PostgreSQL |
| Local database | Docker |
| Production database | Docker PostgreSQL + persistent disk, or Render PostgreSQL |

---

# 35. Documentation Deliverables

Create:

```text
docs/
├── USER_GUIDE.md
├── ARCHITECTURE.md
└── AI_USAGE.md
```

## USER_GUIDE.md

Include:

- Application URL
- How to sign in
- How to create a task
- How to update task status
- Meaning of each status
- Known limitations
- Important warnings
- Setup instructions

## ARCHITECTURE.md

Include:

- System architecture
- Database architecture
- API endpoints
- Authentication flow
- Deployment architecture
- Environment variables

## AI_USAGE.md

Include:

- AI tool: Antigravity
- Model: Claude Sonnet
- What AI generated
- What prompts were used
- What was manually reviewed
- What was manually corrected
- Debugging/troubleshooting performed by the developer
- Tests performed after AI generation

---

# 36. AI Usage Philosophy

Do not tell the AI coding agent:

```text
"Build the entire application."
```

and blindly accept the result.

Instead use staged prompts:

```text
Requirements
    ↓
Architecture
    ↓
Database
    ↓
Backend skeleton
    ↓
Authentication
    ↓
Task APIs
    ↓
Tests
    ↓
Frontend integration
    ↓
Docker
    ↓
Deployment
    ↓
Debugging
    ↓
Documentation
```

This makes it easier to understand and defend the implementation during evaluation.

---

# 37. Master Prompt for Antigravity + Claude Sonnet

Use the following as the initial project prompt:

```text
You are a senior full-stack engineer helping me implement a Graduate Support Engineer Trainee assessment.

IMPORTANT:
Do not expand the scope beyond the stated requirements.

ASSESSMENT REQUIREMENTS:
1. Google Authentication
2. Create tasks
3. View task list
4. Update task status
5. Status values:
   - PLANNED
   - IN_PROGRESS
   - COMPLETE

STACK:
Frontend:
- React
- TypeScript
- Vite

Backend:
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Google ID token verification

Infrastructure:
- Docker
- Docker Compose for local development
- Render for deployment

DATABASE:
- PostgreSQL
- Local PostgreSQL must run in Docker.
- Production architecture should support Dockerized PostgreSQL as a Render private service with persistent storage.
- Keep database configuration controlled through DATABASE_URL so the database can be switched to Render Managed PostgreSQL if necessary.

BACKEND ARCHITECTURE:
Use:
- routes
- schemas
- services
- models
- database layer
- authentication dependencies
- configuration

REQUIRED API:
GET /api/v1/health
POST /api/v1/auth/google
POST /api/v1/tasks
GET /api/v1/tasks
PATCH /api/v1/tasks/{task_id}/status

DATABASE:
users:
- id
- google_id
- email
- name
- profile_picture
- created_at
- updated_at

tasks:
- id
- user_id
- title
- description
- status
- created_at
- updated_at

CONSTRAINTS:
- Every task belongs to exactly one user.
- Users can only view and modify their own tasks.
- Status must be one of PLANNED, IN_PROGRESS, COMPLETE.
- Google credentials must never be trusted without backend verification.
- Secrets must be environment variables.
- Do not hard-code credentials.
- Do not use localhost for production database communication.
- Do not expose PostgreSQL publicly.

CODE QUALITY:
- Use type hints.
- Use Pydantic schemas.
- Use SQLAlchemy 2.x style.
- Use clear exception handling.
- Use structured logging where appropriate.
- Keep functions small.
- Avoid unnecessary abstractions.
- Do not add features outside the requirements.

DEVELOPMENT PROCESS:
Before writing code:
1. Inspect the repository.
2. Create a concise implementation plan.
3. Identify assumptions.
4. Identify ambiguities.
5. Propose the file structure.
6. Wait for approval before large changes.

Then implement incrementally.

After every major implementation:
1. Run the application.
2. Run tests.
3. Check API behavior.
4. Fix errors.
5. Explain what changed.

Do not silently invent requirements.
If a requirement is ambiguous, identify the ambiguity and make the smallest reasonable assumption.

DOCUMENTATION:
Create:
- README.md
- docs/USER_GUIDE.md
- docs/ARCHITECTURE.md
- docs/AI_USAGE.md

The final project must be understandable by a developer reviewing it during an interview.
```

---

# 38. Recommended AI Implementation Sequence

Use these prompts one at a time.

## Prompt 1 — Analyze repository

```text
Inspect the current repository.

Do not modify files yet.

Compare the repository with the assessment requirements.

Return:
1. Existing structure
2. Missing components
3. Architecture recommendation
4. Assumptions
5. Potential implementation risks
6. Exact next implementation step

Do not add features outside the requirements.
```

## Prompt 2 — Backend foundation

```text
Implement the FastAPI backend foundation.

Create:
- application entry point
- configuration
- database connection
- SQLAlchemy base
- health endpoint
- error handling
- CORS configuration
- environment configuration

Do not implement task features yet.

Run the backend and verify:
GET /api/v1/health
```

## Prompt 3 — Database

```text
Implement the PostgreSQL database models.

Create:
User model
Task model
TaskStatus enum

Relationship:
User 1 -> N Tasks

Add appropriate constraints and indexes.

Create Alembic migration.

Do not implement authentication or task routes yet.

Run the migration and verify the database schema.
```

## Prompt 4 — Authentication

```text
Implement Google authentication.

Requirements:
- Accept Google ID token from frontend.
- Verify it on the backend.
- Extract Google user identity.
- Create the user if they do not exist.
- Return authenticated user information.
- Provide a reusable current-user dependency.
- Protect task endpoints.

Do not implement custom password authentication.
```

## Prompt 5 — Task APIs

```text
Implement only the required task APIs:

POST /api/v1/tasks
GET /api/v1/tasks
PATCH /api/v1/tasks/{task_id}/status

Requirements:
- Authentication required.
- User can access only their own tasks.
- Validate title.
- Validate status.
- Return correct HTTP status codes.
- Do not add delete, comments, tags, priorities, or other features.
```

## Prompt 6 — Testing

```text
Create backend tests for:

1. Health endpoint
2. Authentication failure
3. Task creation
4. Task listing
5. Status update
6. Invalid status
7. Missing title
8. User isolation
9. Attempt to update another user's task

Run the tests and fix failures.
```

## Prompt 7 — Docker

```text
Create production-ready Docker configuration.

Requirements:
- FastAPI backend Dockerfile
- PostgreSQL Docker Compose service for local development
- Persistent PostgreSQL volume locally
- Environment-variable configuration
- Backend connects using DATABASE_URL
- Do not hard-code credentials
- Backend must listen on 0.0.0.0
- Use Render PORT when deployed
```

## Prompt 8 — Frontend integration

```text
Integrate the existing React UI with the FastAPI API.

Implement:
- Google login
- Fetch tasks
- Create task
- Update status
- Loading state
- Empty state
- Error state

Do not redesign the UI unless required for functionality.

Use VITE_API_URL.

Handle API errors clearly.
```

## Prompt 9 — Deployment verification

```text
Prepare the application for Render deployment.

Verify:
- Frontend build
- Backend Docker build
- CORS configuration
- Environment variables
- Google OAuth configuration
- Health endpoint
- Database connection
- Production API URL
- No secrets committed
- PostgreSQL is not publicly exposed

Create a deployment checklist.

Do not deploy until local verification passes.
```

## Prompt 10 — Final audit

```text
Perform a final assessment audit.

Compare the implementation against every requirement in the assessment.

Return a table:

Requirement | Implemented | Evidence | Risk | Fix

Also inspect:
- security
- authentication
- authorization
- database ownership
- error handling
- deployment
- documentation
- AI usage documentation
- unnecessary scope

Do not add new features.
Only identify and fix issues that affect the assessment requirements.
```

---

# 39. Manual Verification Checklist

Before submission:

## Authentication

- [ ] Google login works
- [ ] Invalid authentication is rejected
- [ ] User record is created
- [ ] Existing user is recognized

## Tasks

- [ ] Create task works
- [ ] Task appears in list
- [ ] Planned works
- [ ] In Progress works
- [ ] Complete works
- [ ] Refresh preserves tasks
- [ ] User only sees own tasks

## Frontend

- [ ] Loading state
- [ ] Empty state
- [ ] Error state
- [ ] Create-task validation
- [ ] Status update UI
- [ ] Responsive layout

## Backend

- [ ] `/health` works
- [ ] Swagger works
- [ ] Authentication dependency works
- [ ] CORS works
- [ ] Validation works
- [ ] Errors are meaningful
- [ ] Logs do not contain secrets

## Database

- [ ] PostgreSQL starts
- [ ] Migrations work
- [ ] User table exists
- [ ] Task table exists
- [ ] Foreign key exists
- [ ] Status constraint works
- [ ] Data survives container restart locally

## Deployment

- [ ] Frontend deployed
- [ ] Backend deployed
- [ ] Database deployed
- [ ] Persistent database storage configured if using Docker PostgreSQL
- [ ] Production environment variables configured
- [ ] Google OAuth production origin configured
- [ ] Frontend can call backend
- [ ] Backend can reach database
- [ ] HTTPS works

## Submission

- [ ] GitHub repository
- [ ] Live URL
- [ ] README
- [ ] User documentation
- [ ] Architecture documentation
- [ ] AI usage summary

---

# 40. Final Architecture

The target architecture is:

```text
                              USER
                               |
                               v
                    +--------------------+
                    | React + TypeScript |
                    | Render Static Site |
                    +---------+----------+
                              |
                              | HTTPS
                              |
                 +------------v-------------+
                 |       FastAPI API        |
                 |      Render Web Service  |
                 |                          |
                 |  Auth Dependency         |
                 |  Pydantic Validation     |
                 |  Task Service            |
                 |  SQLAlchemy              |
                 +-----+--------------+-----+
                       |              |
                 HTTPS |              | Private Network
                       |              |
                       v              v
              +---------------+  +----------------------+
              |    Google     |  | PostgreSQL Container |
              | Identity      |  | Render Private Svc  |
              | Services      |  |                      |
              +---------------+  | /var/lib/postgresql  |
                                 +----------+-----------+
                                            |
                                            v
                                   +------------------+
                                   | Persistent Disk  |
                                   +------------------+
```

## Core principle

Keep the application:

```text
Simple
Secure
Testable
Deployable
Documented
```

rather than:

```text
Large
Over-engineered
Feature-heavy
```

The assessment itself states that the required use cases are sufficient, so the strongest implementation strategy is to make the required path work reliably and demonstrate that you understand the decisions behind it.
