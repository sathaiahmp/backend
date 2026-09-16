"""
app/db/base.py

SQLAlchemy 2.x declarative base.
All ORM models must inherit from this Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass
