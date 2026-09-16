# Task Management API — Backend

FastAPI backend for the Graduate Support Engineer Trainee Assessment.

## Architecture

- **Local Development**:
  ```
  React/Vite (Host) → FastAPI (Host/Docker) → PostgreSQL (Docker Compose)
  ```
- **Production (Render)**:
  ```
  React/Vite (Render Static Site) → FastAPI (Render Web Service) → Render Managed PostgreSQL
  ```

---

## Local Development Workflow

### 1. Start PostgreSQL with Docker Compose
From the project root:
```bash
docker compose up -d postgres
```
This launches a PostgreSQL 16 container exposed on `localhost:5432` with persistent data in a Docker volume.

### 2. Configure Local Environment Variables
In the `Backend/` directory:
```bash
cp .env.example .env
```
Set your local environment variables in `.env`:
```ini
APP_ENV=development
DATABASE_URL=postgresql://taskflow:taskflow_dev_password@localhost:5432/taskflow
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
FRONTEND_URL=http://localhost:5173
LOG_LEVEL=INFO
```
*(If running FastAPI inside Docker Compose, set `DATABASE_URL=postgresql://taskflow:taskflow_dev_password@postgres:5432/taskflow`)*.

### 3. Run Database Migrations
Apply Alembic migrations to create the `users` and `tasks` tables and the `task_status` enum:
```bash
alembic upgrade head
```

### 4. Start FastAPI
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API root: `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

---

## Production Deployment on Render

Production uses **Render Managed PostgreSQL** instead of running PostgreSQL as a container.

### Step 1: Create Render PostgreSQL Database
1. In the Render Dashboard, click **New +** → **PostgreSQL**.
2. Configure:
   - **Name**: `taskflow-db`
   - **Database**: `taskflow`
   - **User**: `taskflow`
   - **Region**: Choose the same region as your web service (e.g., Oregon or Frankfurt).
   - **Plan**: Free
3. Click **Create Database**.
4. Once provisioned, copy the **Internal Database URL** (e.g., `postgres://taskflow:...@dpg-xxx-a:5432/taskflow`).

### Step 2: Create Render FastAPI Web Service
1. Click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `taskflow-backend`
   - **Root Directory**: `Backend`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && alembic upgrade head
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Health Check Path**: `/api/v1/health`

### Step 3: Configure Render Environment Variables
Under the **Environment** tab of the Web Service, add:

| Key | Value | Description |
|---|---|---|
| `APP_ENV` | `production` | Enables production mode |
| `DATABASE_URL` | `<Render Internal Database URL>` | Connection string from Step 1 |
| `GOOGLE_CLIENT_ID` | `<Google OAuth Client ID>` | Web Client ID from Google Cloud Console |
| `FRONTEND_URL` | `https://<your-frontend>.onrender.com` | Allowed CORS origin |
| `LOG_LEVEL` | `INFO` | Standard logging |

> **Note**: Render provides URLs starting with `postgres://` or `postgresql://`. The application's `normalize_database_url` automatically adapts this to SQLAlchemy's psycopg3 dialect (`postgresql+psycopg://`).

### Step 4: Deploy and Verify
1. Click **Manual Deploy** → **Deploy latest commit** (or trigger automatically via Git push).
2. The build command automatically runs `alembic upgrade head`, ensuring tables (`users`, `tasks`) and ENUM types are created.
3. Test the health endpoint:
   ```bash
   curl https://taskflow-backend.onrender.com/api/v1/health
   # Expected response: {"status": "ok"} (HTTP 200)
   ```
4. If the database is unreachable, the endpoint safely responds with `{"status": "unhealthy"}` (HTTP 503) without leaking credentials or stack traces.

---

## API Endpoints Reference

| Method | Path | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/v1/health` | No | Health check & DB connectivity probe |
| `POST` | `/api/v1/auth/google` | No | Verifies Google ID token, returns user profile |
| `GET` | `/api/v1/tasks` | Bearer Token | Lists all tasks for authenticated user |
| `POST` | `/api/v1/tasks` | Bearer Token | Creates a new task |
| `PATCH` | `/api/v1/tasks/{task_id}/status` | Bearer Token | Updates task status (`PLANNED`, `IN_PROGRESS`, `COMPLETE`) |
| `DELETE` | `/api/v1/tasks/{task_id}` | Bearer Token | Deletes a task owned by authenticated user |

---

## Running Automated Tests

Tests use an in-memory SQLite database and mock authentication:
```bash
python -m pytest tests/ -v
```
All 26 tests cover authentication, task lifecycle, data validation, status transitions, and health check failure recovery.
