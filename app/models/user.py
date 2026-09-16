"""
app/models/user.py

User ORM model.

Columns (from architecture §7):
  id               UUID PK
  google_id        VARCHAR UNIQUE NOT NULL  (Google's 'sub' claim)
  email            VARCHAR UNIQUE NOT NULL
  name             VARCHAR NOT NULL
  profile_picture  TEXT NULLABLE
  created_at       TIMESTAMP WITH TIME ZONE NOT NULL
  updated_at       TIMESTAMP WITH TIME ZONE NOT NULL
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    google_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Google's 'sub' claim — unique identifier per Google account",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    profile_picture: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
