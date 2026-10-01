import csv
import io
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, DbSession
from app.api.rate_limit import client_ip, enforce_rate_limit
from app.core.config import settings
from app.models import Score
from app.schemas.scores import ScoreListOut, ScoreOptions, ScoreOut, TransactionIn
from app.services.score_query import EXPORT_ROW_CAP, filtered_scores, get_visible_score, paginate_scores
from app.services.scorer import score_thresholds, score_transaction

router = APIRouter(prefix="/scores", tags=["scores"])


def _to_out(score: Score) -> ScoreOut:
    return ScoreOut.model_validate(score, from_attributes=True).model_copy(update=score_thresholds())


def _filters(
    user: CurrentUser,
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] | None,
    merchant_category: str | None,
    cache_hit: bool | None,
    model_version_id: int | None,
    created_from: datetime | None,
    created_to: datetime | None,
    scope: Literal["mine", "all"],
):
    return filtered_scores(
        user,
        risk_level=risk_level,
        merchant_category=merchant_category,
        cache_hit=cache_hit,
        model_version_id=model_version_id,
        created_from=created_from,
        created_to=created_to,
        scope=scope,
    )


@router.get("/options", response_model=ScoreOptions)
def options(_: CurrentUser):
    return ScoreOptions()


@router.get("/export")
def export_scores(
    user: CurrentUser,
    db: DbSession,
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] | None = None,
    merchant_category: str | None = None,
    cache_hit: bool | None = None,
    model_version_id: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    scope: Literal["mine", "all"] = "mine",
):
    stmt = _filters(
        user, risk_level, merchant_category, cache_hit, model_version_id, created_from, created_to, scope
    ).order_by(Score.created_at.desc()).limit(EXPORT_ROW_CAP)
    rows = db.scalars(stmt).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["created_at", "risk_level", "probability", "merchant_category", "channel", "amount", "cache_hit", "model_version_id", "id"]
    )
    for row in rows:
        payload = row.payload or {}
        writer.writerow(
            [
                row.created_at.isoformat() if row.created_at else "",
                row.risk_level,
                row.probability,
                payload.get("merchant_category", ""),
                payload.get("channel", ""),
                payload.get("amount", ""),
                row.cache_hit,
                row.model_version_id,
                row.id,
            ]
        )
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="riskscore-history.csv"'},
    )


@router.get("/{score_id}", response_model=ScoreOut)
def get_score(score_id: uuid.UUID, user: CurrentUser, db: DbSession):
    return _to_out(get_visible_score(db, user, score_id))


@router.post("", response_model=ScoreOut, status_code=201)
def create_score(
    payload: TransactionIn,
    user: CurrentUser,
    db: DbSession,
    request: Request,
    response: Response,
):
    # Fail open: a Redis outage must not freeze scoring. Cache hits still count —
    # this is an API-request budget, not a "compute was expensive" budget.
    enforce_rate_limit(
        request,
        response,
        key=f"rl:score:user:{user.id}",
        limit=settings.RATE_LIMIT_SCORE_USER,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        fail_closed=False,
        detail="Scoring rate limit reached. Try again in {retry_after} seconds.",
    )
    enforce_rate_limit(
        request,
        response,
        key=f"rl:score:ip:{client_ip(request)}",
        limit=settings.RATE_LIMIT_SCORE_IP,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        fail_closed=False,
        detail="Scoring rate limit reached. Try again in {retry_after} seconds.",
    )
    return _to_out(score_transaction(db, user, payload))


@router.get("", response_model=ScoreListOut)
def list_scores(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] | None = None,
    merchant_category: str | None = None,
    cache_hit: bool | None = None,
    model_version_id: int | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    scope: Literal["mine", "all"] = "mine",
):
    stmt = _filters(
        user, risk_level, merchant_category, cache_hit, model_version_id, created_from, created_to, scope
    )
    items, total, page, page_size = paginate_scores(db, stmt, page, page_size)
    return ScoreListOut(items=[_to_out(row) for row in items], total=total, page=page, page_size=page_size)
