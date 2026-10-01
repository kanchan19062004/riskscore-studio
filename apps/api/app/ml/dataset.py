"""Synthetic card-transaction dataset with realistic fraud signals.

No real customer data is used anywhere in this project. The generator is
seeded, so the same seed always produces the same dataset.
"""

import numpy as np
import pandas as pd

# category -> (share of transactions, added fraud log-odds)
MERCHANT_CATEGORIES: dict[str, tuple[float, float]] = {
    "grocery": (0.22, -0.6),
    "restaurants": (0.15, -0.4),
    "fuel": (0.12, -0.2),
    "fashion": (0.12, 0.2),
    "electronics": (0.11, 0.9),
    "travel": (0.09, 0.8),
    "gaming": (0.08, 1.1),
    "crypto": (0.04, 1.7),
    "cash_withdrawal": (0.07, 0.5),
}

# channel -> (share, added fraud log-odds)
CHANNELS: dict[str, tuple[float, float]] = {
    "pos": (0.55, -0.5),
    "online": (0.38, 0.7),
    "atm": (0.07, 0.3),
}

TARGET = "is_fraud"


def _hours(rng: np.random.Generator, n: int) -> np.ndarray:
    weights = np.array(
        [1, 0.6, 0.4, 0.3, 0.3, 0.5, 1.5, 3, 4, 5, 5, 5, 6, 6, 5, 5, 5, 6, 7, 7, 6, 5, 3, 2],
        dtype=float,
    )
    return rng.choice(24, size=n, p=weights / weights.sum())


def generate_transactions(n_samples: int = 20_000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    categories = list(MERCHANT_CATEGORIES)
    category = rng.choice(
        categories, size=n_samples, p=[MERCHANT_CATEGORIES[c][0] for c in categories]
    )
    channels = list(CHANNELS)
    channel = rng.choice(channels, size=n_samples, p=[CHANNELS[c][0] for c in channels])

    avg_amount_30d = np.round(rng.lognormal(mean=7.0, sigma=0.8, size=n_samples), 2)
    amount = np.round(avg_amount_30d * rng.lognormal(mean=0.0, sigma=0.6, size=n_samples), 2)
    hour = _hours(rng, n_samples)
    account_age_days = np.clip(rng.gamma(shape=2.0, scale=400, size=n_samples), 1, 4000).round()
    txn_count_24h = rng.poisson(3, size=n_samples)
    failed_attempts_24h = rng.poisson(0.2, size=n_samples)
    is_new_device = (rng.random(n_samples) < 0.08).astype(int)
    country_mismatch = (rng.random(n_samples) < 0.05).astype(int)

    log_odds = (
        -4.2
        + np.array([MERCHANT_CATEGORIES[c][1] for c in category])
        + np.array([CHANNELS[c][1] for c in channel])
        + 1.1 * np.clip(np.log(amount / avg_amount_30d), -2, 4)
        + 1.4 * is_new_device
        + 1.7 * country_mismatch
        + 0.9 * (hour <= 5)
        + 0.45 * failed_attempts_24h
        + 0.08 * (txn_count_24h - 3)
        - 0.6 * np.log1p(account_age_days / 365)
        + rng.normal(0, 0.5, size=n_samples)
    )
    is_fraud = (rng.random(n_samples) < 1 / (1 + np.exp(-log_odds))).astype(int)

    df = pd.DataFrame(
        {
            "transaction_id": [f"txn_{i:06d}" for i in range(n_samples)],
            "amount": amount,
            "merchant_category": category,
            "channel": channel,
            "hour": hour,
            "account_age_days": account_age_days,
            "avg_amount_30d": avg_amount_30d,
            "txn_count_24h": txn_count_24h,
            "failed_attempts_24h": failed_attempts_24h,
            "is_new_device": is_new_device,
            "country_mismatch": country_mismatch,
            TARGET: is_fraud,
        }
    )

    # Real data is messy: ~2% of accounts are missing their age. The model
    # pipeline must handle this the same way at training and scoring time.
    df.loc[rng.random(n_samples) < 0.02, "account_age_days"] = np.nan
    return df
