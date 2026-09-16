"""
app/repositories/task_repository.py

Database access layer for tasks.

Security rules (from architecture §14–15):
  - Every query is scoped to user_id — never fetch tasks without it.
  - get_by_id_and_user enforces ownership: task_id AND user_id must match.
  - No query returns tasks from other users.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


def create(db: Session, *, user_id: uuid.UUID, title: str, description: str | None, status: TaskStatus) -> Task:
    """
    Insert a new task for the given user.

    Args:
        db:          Active database session.
        user_id:     Authenticated user's UUID (from dependency — never from request body).
        title:       Validated, stripped task title.
        description: Optional task description.
        status:      Initial task status.

    Returns:
        Newly created Task ORM object.
    """
    task = Task(
        user_id=user_id,
        title=title,
        description=description,
        status=status,
    )
    db.add(task)
    db.flush()  # assigns the UUID without committing
    logger.info("Task created | user_id=%s | task_id=%s", user_id, task.id)
    return task


def get_all_for_user(db: Session, user_id: uuid.UUID) -> list[Task]:
    """
    Return all tasks belonging to the authenticated user.

    IMPORTANT: The WHERE clause always includes user_id.
    This endpoint must never return another user's tasks.
    """
    return list(
        db.execute(
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
        ).scalars().all()
    )


def get_by_id_and_user(
    db: Session, *, task_id: uuid.UUID, user_id: uuid.UUID
) -> Task | None:
    """
    Return the task only if it exists AND belongs to the given user.

    Ownership check built into the query — not a separate step.
    Conceptually:  WHERE id = :task_id AND user_id = :user_id
    """
    return db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )
    ).scalar_one_or_none()


def update_status(
    db: Session,
    *,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    new_status: TaskStatus,
) -> Task | None:
    """
    Update task status, but only if the task belongs to the authenticated user.

    Returns:
        Updated Task, or None if the task was not found for this user.
    """
    task = get_by_id_and_user(db, task_id=task_id, user_id=user_id)
    if task is None:
        return None

    task.status = new_status
    task.updated_at = datetime.now(timezone.utc)
    db.flush()

    logger.info(
        "Task status updated | user_id=%s | task_id=%s | status=%s",
        user_id,
        task_id,
        new_status.value,
    )
    return task


def delete(
    db: Session,
    *,
    task_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Delete a task if it belongs to the authenticated user.

    Returns:
        True if deleted, False if not found.
    """
    task = get_by_id_and_user(db, task_id=task_id, user_id=user_id)
    if task is None:
        return False
    db.delete(task)
    db.flush()
    logger.info("Task deleted | user_id=%s | task_id=%s", user_id, task_id)
    return True
