import hashlib
import json
import uuid

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.cache import get_cache
from app.core.config import settings
from app.ml.features import RAW_FEATURES
from app.ml.score import risk_level
from app.ml.train import HIGH_RISK_THRESHOLD, REVIEW_THRESHOLD
from app.models import Score, User
from app.schemas.scores import TransactionIn
from app.services.model_registry import get_active_version

_pipelines: dict[int, object] = {}


def cache_key(version_id: int, payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return f"score:v{version_id}:{digest}"


def load_pipeline(version) -> object:
    cached = _pipelines.get(version.id)
    if cached is not None:
        return cached
    path = settings.MODEL_DIR / version.artifact_path
    try:
        pipeline = joblib.load(path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The active model file is missing. An admin needs to retrain.",
        ) from exc
    _pipelines[version.id] = pipeline
    return pipeline


def payload_to_frame(payload: TransactionIn) -> pd.DataFrame:
    row = payload.model_dump()
    row["is_new_device"] = int(row["is_new_device"])
    row["country_mismatch"] = int(row["country_mismatch"])
    if row["account_age_days"] is None:
        row["account_age_days"] = np.nan
    return pd.DataFrame([row])[RAW_FEATURES]


def _persist(
    db: Session,
    *,
    user_id: uuid.UUID,
    version_id: int,
    payload: dict,
    probability: float,
    level: str,
    cache_hit: bool,
) -> Score:
    score = Score(
        scored_by_id=user_id,
        model_version_id=version_id,
        payload=payload,
        probability=probability,
        risk_level=level,
        cache_hit=cache_hit,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def score_transaction(db: Session, user: User, payload: TransactionIn) -> Score:
    version = get_active_version(db)
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No model has been trained yet",
        )

    body = payload.model_dump(mode="json")
    key = cache_key(version.id, body)
    cache = get_cache()
    cached = cache.get(key)
    if cached:
        stored = json.loads(cached)
        return _persist(
            db,
            user_id=user.id,
            version_id=version.id,
            payload=body,
            probability=stored["probability"],
            level=stored["risk_level"],
            cache_hit=True,
        )

    pipeline = load_pipeline(version)
    proba = round(float(pipeline.predict_proba(payload_to_frame(payload))[0, 1]), 4)
    level = risk_level(proba)
    cache.setex(
        key,
        settings.SCORE_CACHE_TTL_SECONDS,
        json.dumps({"probability": proba, "risk_level": level}),
    )
    return _persist(
        db,
        user_id=user.id,
        version_id=version.id,
        payload=body,
        probability=proba,
        level=level,
        cache_hit=False,
    )


def score_thresholds() -> dict[str, float]:
    return {
        "review_threshold": REVIEW_THRESHOLD,
        "high_risk_threshold": HIGH_RISK_THRESHOLD,
    }
