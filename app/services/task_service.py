"""
app/services/task_service.py

Task business logic layer.

Responsibilities:
  - Create tasks (user_id always from the authenticated user)
  - List the current user's tasks
  - Update task status with ownership verification

This layer has no knowledge of HTTP — it receives plain Python objects
and raises application exceptions (not HTTPExceptions).
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.exceptions.handlers import NotFoundError
from app.models.task import Task, TaskStatus
from app.repositories import task_repository
from app.schemas.task import TaskCreate

logger = logging.getLogger(__name__)


def create_task(db: Session, *, user_id: uuid.UUID, data: TaskCreate) -> Task:
    """
    Create a new task for the authenticated user.

    Args:
        db:      Active database session.
        user_id: Authenticated user's UUID — never from request body.
        data:    Validated TaskCreate schema.

    Returns:
        The newly created Task.
    """
    return task_repository.create(
        db,
        user_id=user_id,
        title=data.title,
        description=data.description,
        status=data.status,
    )


def list_tasks(db: Session, *, user_id: uuid.UUID) -> list[Task]:
    """
    Return all tasks belonging to the authenticated user.

    Security: user_id comes from the auth dependency, not the request.
    """
    return task_repository.get_all_for_user(db, user_id)


def update_task_status(
    db: Session,
    *,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    new_status: TaskStatus,
) -> Task:
    """
    Update the status of a task, enforcing ownership.

    Args:
        db:         Active database session.
        task_id:    UUID of the task to update (from URL path).
        user_id:    Authenticated user's UUID (from auth dependency).
        new_status: The new TaskStatus value.

    Returns:
        The updated Task.

    Raises:
        NotFoundError: If the task does not exist or belongs to another user.
                       (The response is intentionally the same — 404 — to avoid
                        leaking information about tasks owned by other users.)
    """
    task = task_repository.update_status(
        db,
        task_id=task_id,
        user_id=user_id,
        new_status=new_status,
    )
    if task is None:
        raise NotFoundError("Task not found")
    return task


def delete_task(db: Session, *, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """
    Delete a task, enforcing ownership.

    Raises:
        NotFoundError: If the task does not exist or belongs to another user.
    """
    deleted = task_repository.delete(db, task_id=task_id, user_id=user_id)
    if not deleted:
        raise NotFoundError("Task not found")
