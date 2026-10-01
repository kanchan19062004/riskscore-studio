"""Feature definitions shared by training and (Phase 4) scoring.

Feature engineering lives inside the saved sklearn Pipeline, so the scoring
API sends raw transaction fields and can never compute features differently
from training ("training/serving skew").
"""

import numpy as np
import pandas as pd

RAW_FEATURES = [
    "amount",
    "merchant_category",
    "channel",
    "hour",
    "account_age_days",
    "avg_amount_30d",
    "txn_count_24h",
    "failed_attempts_24h",
    "is_new_device",
    "country_mismatch",
]

CATEGORICAL_FEATURES = ["merchant_category", "channel"]

NUMERIC_FEATURES = [
    "log_amount",
    "amount_to_avg_ratio",
    "hour",
    "is_night",
    "account_age_days",
    "txn_count_24h",
    "failed_attempts_24h",
    "is_new_device",
    "country_mismatch",
]


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["log_amount"] = np.log1p(out["amount"])
    out["amount_to_avg_ratio"] = out["amount"] / out["avg_amount_30d"].clip(lower=1)
    out["is_night"] = (out["hour"] <= 5).astype(int)
    return out
