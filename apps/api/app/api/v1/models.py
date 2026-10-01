import secrets

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models import ModelVersion
from app.schemas.models import ModelVersionOut, TrainRequest, TrainResponse
from app.services.model_registry import activate_version, get_active_version, train_and_register

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelVersionOut])
def list_models(_: CurrentUser, db: DbSession):
    return db.scalars(select(ModelVersion).order_by(ModelVersion.id.desc()).limit(20)).all()


@router.get("/active", response_model=ModelVersionOut)
def active_model(_: CurrentUser, db: DbSession):
    version = get_active_version(db)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No model has been trained yet")
    return version


@router.post("/train", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
def train_model(payload: TrainRequest, admin: AdminUser, db: DbSession):
    """Train a new version synchronously (a few seconds). It becomes active only if its
    PR-AUC is at least as good as the current active model's, measured on the same test set."""
    seed = payload.seed if payload.seed is not None else secrets.randbelow(2**31)
    version, promoted, champion_pr_auc = train_and_register(
        db, n_samples=payload.n_samples, seed=seed, trained_by=admin.id
    )
    return TrainResponse(
        version=ModelVersionOut.model_validate(version),
        promoted=promoted,
        champion_pr_auc=champion_pr_auc,
    )


@router.post("/{version_id}/activate", response_model=ModelVersionOut)
def activate_model(version_id: int, _: AdminUser, db: DbSession):
    """Manually switch the active model, e.g. to roll back a bad release."""
    version = db.get(ModelVersion, version_id)
    if version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found")
    activate_version(db, version)
    db.commit()
    db.refresh(version)
    return version
