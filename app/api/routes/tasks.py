"""
app/api/routes/tasks.py

Task API routes:

  POST  /api/v1/tasks               — Create a task
  GET   /api/v1/tasks               — List authenticated user's tasks
  PATCH /api/v1/tasks/{task_id}/status — Update task status

All routes require authentication.
The authenticated user is resolved by get_current_user() — the frontend
cannot supply or override the user identity.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_session
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskStatusResponse, TaskStatusUpdate
from app.services import task_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
    description=(
        "Create a new task for the authenticated user. "
        "The user_id is always taken from the authenticated session — "
        "it cannot be supplied in the request body."
    ),
)
def create_task(
    body: TaskCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """POST /api/v1/tasks"""
    task = task_service.create_task(db, user_id=current_user.id, data=body)
    return TaskResponse.model_validate(task)


@router.get(
    "/tasks",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="List tasks",
    description=(
        "Return all tasks belonging to the authenticated user. "
        "Tasks from other users are never returned."
    ),
)
def list_tasks(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    """GET /api/v1/tasks"""
    tasks = task_service.list_tasks(db, user_id=current_user.id)
    return [TaskResponse.model_validate(t) for t in tasks]


@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task status",
    description=(
        "Update the status of a task. "
        "The task must belong to the authenticated user — "
        "ownership is enforced at the database query level."
    ),
)
def update_task_status(
    task_id: uuid.UUID,
    body: TaskStatusUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskStatusResponse:
    """PATCH /api/v1/tasks/{task_id}/status"""
    # NotFoundError raised by service → caught by registered exception handler → 404
    task = task_service.update_task_status(
        db,
        task_id=task_id,
        user_id=current_user.id,
        new_status=body.status,
    )
    return TaskStatusResponse.model_validate(task)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description=(
        "Delete a task belonging to the authenticated user. "
        "Ownership is enforced — users can only delete their own tasks."
    ),
)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """DELETE /api/v1/tasks/{task_id}"""
    task_service.delete_task(db, task_id=task_id, user_id=current_user.id)
