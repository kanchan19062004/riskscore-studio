import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.ml.dataset import CHANNELS, MERCHANT_CATEGORIES
from app.ml.train import HIGH_RISK_THRESHOLD, REVIEW_THRESHOLD


class TransactionIn(BaseModel):
    amount: float = Field(gt=0, le=1_000_000)
    merchant_category: str = Field(min_length=1, max_length=50)
    channel: str = Field(min_length=1, max_length=20)
    hour: int = Field(ge=0, le=23)
    account_age_days: float | None = Field(default=None, ge=0, le=20_000)
    avg_amount_30d: float = Field(gt=0, le=1_000_000)
    txn_count_24h: int = Field(ge=0, le=10_000)
    failed_attempts_24h: int = Field(ge=0, le=100)
    is_new_device: bool
    country_mismatch: bool

    @field_validator("merchant_category")
    @classmethod
    def known_merchant_category(cls, value: str) -> str:
        if value not in MERCHANT_CATEGORIES:
            raise ValueError("Unknown merchant category")
        return value

    @field_validator("channel")
    @classmethod
    def known_channel(cls, value: str) -> str:
        if value not in CHANNELS:
            raise ValueError("Unknown channel")
        return value


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scored_by_id: uuid.UUID
    probability: float
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    model_version_id: int
    cache_hit: bool
    payload: dict
    created_at: datetime
    review_threshold: float = REVIEW_THRESHOLD
    high_risk_threshold: float = HIGH_RISK_THRESHOLD


class ScoreListOut(BaseModel):
    items: list[ScoreOut]
    total: int
    page: int
    page_size: int


class ScoreOptions(BaseModel):
    merchant_categories: list[str] = list(MERCHANT_CATEGORIES)
    channels: list[str] = list(CHANNELS)
    review_threshold: float = REVIEW_THRESHOLD
    high_risk_threshold: float = HIGH_RISK_THRESHOLD
