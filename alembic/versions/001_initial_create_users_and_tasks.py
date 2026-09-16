"""create_users_and_tasks

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-16 04:30:00.000000 UTC

Initial migration — creates:
  - task_status ENUM type
  - users table
  - tasks table with FK to users
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Create the task_status ENUM type ────────────────────────────────────
    task_status_enum = postgresql.ENUM(
        "PLANNED",
        "IN_PROGRESS",
        "COMPLETE",
        name="task_status",
        create_type=False,  # We create it explicitly below
    )
    task_status_enum.create(op.get_bind(), checkfirst=True)

    # ── Create users table ───────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("google_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("profile_picture", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── Create tasks table ───────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PLANNED", "IN_PROGRESS", "COMPLETE", name="task_status", create_type=False),
            nullable=False,
            server_default="PLANNED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_tasks_id", "tasks", ["id"], unique=False)
    op.create_index("ix_tasks_user_id", "tasks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("users")

    # Drop the ENUM type last (after tables that reference it are gone)
    op.execute("DROP TYPE IF EXISTS task_status")
