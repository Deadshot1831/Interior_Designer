"""Design model."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Design(Base):
    __tablename__ = "designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), index=True, nullable=False)
    style: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)

    # JSON columns (portable: maps to JSONB on Postgres, JSON-as-text on SQLite).
    detected_objects: Mapped[list | None] = mapped_column(JSON, nullable=True)
    palette: Mapped[list | None] = mapped_column(JSON, nullable=True)
    furniture_suggestions: Mapped[list | None] = mapped_column(JSON, nullable=True)

    layout_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_model_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    room: Mapped["Room"] = relationship(back_populates="designs")
