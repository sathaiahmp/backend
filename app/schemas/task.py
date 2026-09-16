"""
app/schemas/task.py

Pydantic schemas for task endpoints.

Validation rules (from architecture §13–14):
  - title: required, stripped of whitespace, non-empty, max 255 chars
  - description: optional
  - status: must be one of PLANNED | IN_PROGRESS | COMPLETE
  - user_id: NEVER accepted from the request body — always comes from the
             authenticated user dependency
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    """Request body for POST /api/v1/tasks."""

    title: str = Field(
        ...,
        max_length=255,
        description="Task title — required, cannot be empty or whitespace only",
    )
    description: str | None = Field(
        default=None,
        description="Optional task description",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PLANNED,
        description="Task status — defaults to PLANNED",
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or contain only whitespace.")
        return stripped


class TaskStatusUpdate(BaseModel):
    """Request body for PATCH /api/v1/tasks/{task_id}/status."""

    status: TaskStatus = Field(
        ...,
        description="New task status — must be PLANNED, IN_PROGRESS, or COMPLETE",
    )


class TaskResponse(BaseModel):
    """Full task representation returned by POST and GET endpoints."""

    id: uuid.UUID
    title: str
    description: str | None = None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskStatusResponse(BaseModel):
    """Minimal task representation returned by PATCH /status endpoint."""

    id: uuid.UUID
    status: TaskStatus
    updated_at: datetime

    model_config = {"from_attributes": True}
