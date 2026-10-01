from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Score, User

PAGE_SIZE_MAX = 100
EXPORT_ROW_CAP = 10_000


def filtered_scores(
    user: User,
    *,
    risk_level: str | None = None,
    merchant_category: str | None = None,
    cache_hit: bool | None = None,
    model_version_id: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    scope: str = "mine",
) -> Select[tuple[Score]]:
    if scope not in {"mine", "all"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="scope must be mine or all")
    if scope == "all" and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    stmt = select(Score)
    if scope == "mine":
        stmt = stmt.where(Score.scored_by_id == user.id)
    if risk_level:
        stmt = stmt.where(Score.risk_level == risk_level)
    if cache_hit is not None:
        stmt = stmt.where(Score.cache_hit.is_(cache_hit))
    if model_version_id is not None:
        stmt = stmt.where(Score.model_version_id == model_version_id)
    if created_from is not None:
        stmt = stmt.where(Score.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(Score.created_at < created_to)
    if merchant_category:
        stmt = stmt.where(Score.payload["merchant_category"].as_string() == merchant_category)
    return stmt


def paginate_scores(db: Session, stmt: Select[tuple[Score]], page: int, page_size: int):
    page_size = min(max(page_size, 1), PAGE_SIZE_MAX)
    page = max(page, 1)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Score.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return items, total, page, page_size


def get_visible_score(db: Session, user: User, score_id) -> Score:
    score = db.get(Score, score_id)
    if score is None or (user.role != "admin" and score.scored_by_id != user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")
    return score
