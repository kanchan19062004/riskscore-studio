import uuid

import joblib
from sklearn.metrics import average_precision_score
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ml.train import TrainingResult, train_risk_model
from app.models import ModelVersion


def get_active_version(db: Session) -> ModelVersion | None:
    return db.scalar(select(ModelVersion).where(ModelVersion.is_active))


def activate_version(db: Session, version: ModelVersion) -> None:
    """Make `version` the only active model. The caller commits."""
    db.execute(
        update(ModelVersion)
        .where(ModelVersion.is_active, ModelVersion.id != version.id)
        .values(is_active=False)
    )
    version.is_active = True


def _champion_pr_auc(champion: ModelVersion, result: TrainingResult) -> float | None:
    """Score the champion on the challenger's test set, so both are judged on the same data.

    Returns None if the champion's file is gone, since it can't serve predictions anyway.
    """
    try:
        pipeline = joblib.load(settings.MODEL_DIR / champion.artifact_path)
    except FileNotFoundError:
        return None
    proba = pipeline.predict_proba(result.X_test)[:, 1]
    return round(float(average_precision_score(result.y_test, proba)), 4)


def train_and_register(
    db: Session, *, n_samples: int, seed: int, trained_by: uuid.UUID | None
) -> tuple[ModelVersion, bool, float | None]:
    """Train a challenger, save it, and promote it only if it beats the champion.

    Returns the new version, whether it was promoted, and the champion's PR-AUC on
    the challenger's test set (None when there was no usable champion).
    """
    result = train_risk_model(n_samples=n_samples, seed=seed)

    version = ModelVersion(
        algorithm=result.algorithm,
        metrics=result.metrics,
        candidates=result.candidates,
        dataset=result.dataset,
        artifact_path="",
        is_active=False,
        trained_by_id=trained_by,
    )
    db.add(version)
    db.flush()  # assigns version.id, which names the artifact file

    settings.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    file_name = f"risk_model_v{version.id}.joblib"
    joblib.dump(result.pipeline, settings.MODEL_DIR / file_name)
    version.artifact_path = file_name

    champion = get_active_version(db)
    champion_score = _champion_pr_auc(champion, result) if champion else None
    promoted = champion_score is None or result.metrics["pr_auc"] >= champion_score
    if promoted:
        activate_version(db, version)

    db.commit()
    db.refresh(version)
    return version, promoted, champion_score
