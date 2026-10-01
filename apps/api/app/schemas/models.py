from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConfusionMatrix(BaseModel):
    tn: int
    fp: int
    fn: int
    tp: int


class ModelMetrics(BaseModel):
    roc_auc: float
    pr_auc: float
    precision: float
    recall: float
    f1: float
    accuracy: float
    baseline_accuracy: float
    review_threshold: float
    confusion_matrix: ConfusionMatrix


class CandidateScore(BaseModel):
    algorithm: str
    roc_auc: float
    pr_auc: float


class DatasetSummary(BaseModel):
    n_samples: int
    n_train: int
    n_test: int
    fraud_rate: float
    seed: int
    fraud_rate_by_category: dict[str, float]


class ModelVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    algorithm: str
    is_active: bool
    created_at: datetime
    metrics: ModelMetrics
    candidates: list[CandidateScore]
    dataset: DatasetSummary


class TrainRequest(BaseModel):
    n_samples: int = Field(20_000, ge=1_000, le=200_000)
    seed: int | None = Field(None, ge=0, le=2**31 - 1, description="Random if omitted")


class TrainResponse(BaseModel):
    version: ModelVersionOut
    promoted: bool
    champion_pr_auc: float | None = Field(
        description="Previous active model's PR-AUC on this version's test set; null if there was none"
    )
