import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Score(Base):
    """One scoring request (audit trail). Cache hits are still stored."""

    __tablename__ = "scores"
    __table_args__ = (Index("ix_scores_scored_by_created", "scored_by_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    scored_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    model_version_id: Mapped[int] = mapped_column(ForeignKey("model_versions.id"))
    payload: Mapped[dict] = mapped_column(JSON)
    probability: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(10))
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
