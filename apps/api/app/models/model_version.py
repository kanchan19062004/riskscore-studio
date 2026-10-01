import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelVersion(Base):
    """One trained risk model. The id doubles as the version number (v1, v2, ...)."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    algorithm: Mapped[str] = mapped_column(String(50))
    metrics: Mapped[dict] = mapped_column(JSON)
    candidates: Mapped[list] = mapped_column(JSON)
    dataset: Mapped[dict] = mapped_column(JSON)
    # File name inside settings.MODEL_DIR, so the same row works locally and in Docker.
    artifact_path: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    trained_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
