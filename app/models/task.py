"""
app/models/task.py

Task ORM model and TaskStatus enum.

Task status is restricted to exactly three values (architecture §5):
  PLANNED
  IN_PROGRESS
  COMPLETE

Columns (from architecture §7):
  id           UUID PK
  user_id      UUID FK → users.id  NOT NULL  ON DELETE CASCADE
  title        VARCHAR(255) NOT NULL
  description  TEXT NULLABLE
  status       ENUM NOT NULL  DEFAULT 'PLANNED'
  created_at   TIMESTAMP WITH TIME ZONE NOT NULL
  updated_at   TIMESTAMP WITH TIME ZONE NOT NULL
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, enum.Enum):
    """
    Valid task status values.

    Using str + enum.Enum so the value serialises cleanly in Pydantic schemas
    and FastAPI responses (e.g., "PLANNED" not "TaskStatus.PLANNED").
    """

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,   # speed up user-scoped queries
        comment="Owner of this task — every task belongs to exactly one user",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",       # PostgreSQL ENUM type name
            create_type=True,         # Alembic will create the type in PostgreSQL
            native_enum=False,        # Renders as VARCHAR on SQLite (test compatibility)
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=TaskStatus.PLANNED,
        server_default="PLANNED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=_utcnow,
        default=_utcnow,
    )

    # ── Relationship (not used in queries directly, but useful for ORM context)
    owner = relationship("User", backref="tasks", lazy="select")

    def __repr__(self) -> str:
        return f"<Task id={self.id} status={self.status.value!r}>"
