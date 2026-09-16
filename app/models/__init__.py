"""
app/models/__init__.py

Re-export all models so Alembic's env.py can import them
through a single import statement:

    from app.models import *   # noqa: F401 — ensures all metadata is registered
"""

from app.models.task import Task, TaskStatus  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = ["User", "Task", "TaskStatus"]
