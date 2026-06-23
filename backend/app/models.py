from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AIEvent(Base):
    """One canonical AI interaction.

    The id is a deterministic dedup key (``source:message_id``) so re-running a
    collector upserts rather than duplicates. Token/cost fields are nullable on
    purpose — the platform represents uncertainty rather than inventing data.
    """

    __tablename__ = "ai_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    application: Mapped[str] = mapped_column(String, index=True)
    provider: Mapped[str] = mapped_column(String, index=True)
    model: Mapped[str | None] = mapped_column(String, index=True, nullable=True)

    event_type: Mapped[str] = mapped_column(String, index=True)
    capability: Mapped[str] = mapped_column(String, index=True)

    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_read_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_creation_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    estimated_cost: Mapped[float | None] = mapped_column(Numeric(14, 6), nullable=True)
    project: Mapped[str | None] = mapped_column(String, index=True, nullable=True)

    # high | medium | low
    confidence: Mapped[str] = mapped_column(String, index=True)

    # tools[], session_id, git_branch, version, raw_hash — never raw prompt text.
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
