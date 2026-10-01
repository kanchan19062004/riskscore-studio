import numpy as np
import pandas as pd

from app.ml.dataset import TARGET, generate_transactions
from app.ml.features import RAW_FEATURES
from app.ml.train import train_risk_model


def test_dataset_is_reproducible_and_realistic():
    first = generate_transactions(n_samples=5_000, seed=1)
    second = generate_transactions(n_samples=5_000, seed=1)

    pd.testing.assert_frame_equal(first, second)
    assert 0.015 < first[TARGET].mean() < 0.05
    assert first["account_age_days"].isna().any()


def test_trained_pipeline_beats_chance_and_scores_raw_rows():
    result = train_risk_model(n_samples=4_000, seed=7)

    assert result.algorithm in {c["algorithm"] for c in result.candidates}
    assert result.metrics["roc_auc"] > 0.7
    assert result.metrics["pr_auc"] > result.dataset["fraud_rate"]

    # Raw fields only, with a missing account age and a category never seen in training.
    row = pd.DataFrame(
        [
            {
                "amount": 25_000.0,
                "merchant_category": "lottery",
                "channel": "online",
                "hour": 3,
                "account_age_days": np.nan,
                "avg_amount_30d": 900.0,
                "txn_count_24h": 9,
                "failed_attempts_24h": 2,
                "is_new_device": 1,
                "country_mismatch": 1,
            }
        ]
    )[RAW_FEATURES]
    proba = result.pipeline.predict_proba(row)[0, 1]
    assert 0.0 <= proba <= 1.0
