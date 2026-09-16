"""
tests/test_tasks.py

Tests for task endpoints:
  POST  /api/v1/tasks
  GET   /api/v1/tasks
  PATCH /api/v1/tasks/{task_id}/status

Covers:
  - Create task
  - List tasks (only own tasks)
  - Update status (PLANNED / IN_PROGRESS / COMPLETE)
  - Invalid status rejected
  - Missing title rejected
  - Empty title rejected
  - Unauthenticated access blocked
  - User cannot update another user's task
"""

import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User
from tests.conftest import FAKE_GOOGLE_TOKEN, make_auth_headers, mock_verify_token

TASKS_URL = "/api/v1/tasks"


# ── Helper: authenticated client via patched Google verification ──────────────

def authenticated_client_for(client: TestClient, user: User):
    """
    Returns a context that patches verify_google_token to return the given user's payload.
    Use with `with` to perform authenticated requests.
    """
    payload = mock_verify_token(user.google_id, user.email, user.name)
    return patch("app.core.security.id_token.verify_oauth2_token", return_value=payload)


# ── POST /api/v1/tasks ────────────────────────────────────────────────────────

def test_create_task_returns_201(client: TestClient, sample_user: User) -> None:
    """Creating a valid task must return 201 with full task data."""
    with authenticated_client_for(client, sample_user):
        response = client.post(
            TASKS_URL,
            json={"title": "My first task", "description": "Some description", "status": "PLANNED"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My first task"
    assert data["description"] == "Some description"
    assert data["status"] == "PLANNED"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_task_default_status_is_planned(client: TestClient, sample_user: User) -> None:
    """Omitting status must default to PLANNED."""
    with authenticated_client_for(client, sample_user):
        response = client.post(
            TASKS_URL,
            json={"title": "No status provided"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 201
    assert response.json()["status"] == "PLANNED"


def test_create_task_without_description(client: TestClient, sample_user: User) -> None:
    """Description is optional — must succeed without it."""
    with authenticated_client_for(client, sample_user):
        response = client.post(
            TASKS_URL,
            json={"title": "Task without description"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_task_missing_title_returns_422(client: TestClient, sample_user: User) -> None:
    """Omitting title must return 422."""
    with authenticated_client_for(client, sample_user):
        response = client.post(
            TASKS_URL,
            json={"description": "No title"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 422


def test_create_task_empty_title_returns_422(client: TestClient, sample_user: User) -> None:
    """An empty title must return 422."""
    with authenticated_client_for(client, sample_user):
        response = client.post(
            TASKS_URL,
            json={"title": ""},
            headers=make_auth_headers(),
        )

    assert response.status_code == 422


def test_create_task_whitespace_only_title_returns_422(client: TestClient, sample_user: User) -> None:
    """A whitespace-only title must be rejected."""
    with authenticated_client_for(client, sample_user):
        response = client.post(
            TASKS_URL,
            json={"title": "   "},
            headers=make_auth_headers(),
        )

    assert response.status_code == 422


def test_create_task_invalid_status_returns_422(client: TestClient, sample_user: User) -> None:
    """An invalid status string must return 422."""
    with authenticated_client_for(client, sample_user):
        response = client.post(
            TASKS_URL,
            json={"title": "Valid title", "status": "DONE"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 422


def test_create_task_unauthenticated_returns_401(client: TestClient) -> None:
    """Creating a task without a token must return 401."""
    response = client.post(TASKS_URL, json={"title": "Should fail"})
    assert response.status_code == 401


# ── GET /api/v1/tasks ─────────────────────────────────────────────────────────

def test_list_tasks_returns_only_own_tasks(
    client: TestClient, db: Session, sample_user: User, another_user: User
) -> None:
    """User must only see their own tasks — never another user's tasks."""
    # Create a task for sample_user
    own_task = Task(
        user_id=sample_user.id,
        title="My Task",
        status=TaskStatus.PLANNED,
    )
    # Create a task for another_user
    other_task = Task(
        user_id=another_user.id,
        title="Other User's Task",
        status=TaskStatus.PLANNED,
    )
    db.add_all([own_task, other_task])
    db.commit()

    with authenticated_client_for(client, sample_user):
        response = client.get(TASKS_URL, headers=make_auth_headers())

    assert response.status_code == 200
    tasks = response.json()
    titles = [t["title"] for t in tasks]
    assert "My Task" in titles
    assert "Other User's Task" not in titles


def test_list_tasks_empty_for_new_user(client: TestClient, sample_user: User) -> None:
    """A user with no tasks must receive an empty list, not an error."""
    with authenticated_client_for(client, sample_user):
        response = client.get(TASKS_URL, headers=make_auth_headers())

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_unauthenticated_returns_401(client: TestClient) -> None:
    """GET /tasks without a token must return 401."""
    response = client.get(TASKS_URL)
    assert response.status_code == 401


# ── PATCH /api/v1/tasks/{task_id}/status ─────────────────────────────────────

def test_update_status_to_in_progress(
    client: TestClient, db: Session, sample_user: User
) -> None:
    """Status can be updated from PLANNED to IN_PROGRESS."""
    task = Task(user_id=sample_user.id, title="Task", status=TaskStatus.PLANNED)
    db.add(task)
    db.commit()

    with authenticated_client_for(client, sample_user):
        response = client.patch(
            f"{TASKS_URL}/{task.id}/status",
            json={"status": "IN_PROGRESS"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert "updated_at" in data


def test_update_status_to_complete(
    client: TestClient, db: Session, sample_user: User
) -> None:
    """Status can be updated to COMPLETE."""
    task = Task(user_id=sample_user.id, title="Task", status=TaskStatus.IN_PROGRESS)
    db.add(task)
    db.commit()

    with authenticated_client_for(client, sample_user):
        response = client.patch(
            f"{TASKS_URL}/{task.id}/status",
            json={"status": "COMPLETE"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETE"


def test_update_status_invalid_value_returns_422(
    client: TestClient, db: Session, sample_user: User
) -> None:
    """An invalid status string must return 422."""
    task = Task(user_id=sample_user.id, title="Task", status=TaskStatus.PLANNED)
    db.add(task)
    db.commit()

    with authenticated_client_for(client, sample_user):
        response = client.patch(
            f"{TASKS_URL}/{task.id}/status",
            json={"status": "INVALID_STATUS"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 422


def test_update_status_nonexistent_task_returns_404(
    client: TestClient, sample_user: User
) -> None:
    """Updating a task that does not exist must return 404."""
    random_id = uuid.uuid4()

    with authenticated_client_for(client, sample_user):
        response = client.patch(
            f"{TASKS_URL}/{random_id}/status",
            json={"status": "COMPLETE"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 404


def test_user_cannot_update_another_users_task(
    client: TestClient, db: Session, sample_user: User, another_user: User
) -> None:
    """
    Critical security test: a user must NOT be able to update a task
    belonging to another user, even if they supply a valid task_id.
    The response must be 404 (not 403) to avoid leaking task existence.
    """
    # Create a task owned by another_user
    other_task = Task(
        user_id=another_user.id,
        title="Other user's private task",
        status=TaskStatus.PLANNED,
    )
    db.add(other_task)
    db.commit()

    # Attempt to update it as sample_user
    with authenticated_client_for(client, sample_user):
        response = client.patch(
            f"{TASKS_URL}/{other_task.id}/status",
            json={"status": "COMPLETE"},
            headers=make_auth_headers(),
        )

    assert response.status_code == 404


def test_update_status_unauthenticated_returns_401(
    client: TestClient, db: Session, sample_user: User
) -> None:
    """PATCH /status without a token must return 401."""
    task = Task(user_id=sample_user.id, title="Task", status=TaskStatus.PLANNED)
    db.add(task)
    db.commit()

    response = client.patch(f"{TASKS_URL}/{task.id}/status", json={"status": "COMPLETE"})
    assert response.status_code == 401
