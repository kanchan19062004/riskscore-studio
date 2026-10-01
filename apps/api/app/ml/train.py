"""Train and evaluate the transaction risk model.

Run an experiment without touching the database:
    python -m app.ml.train --rows 20000 --seed 42
"""

import argparse
import json
from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from app.ml.dataset import TARGET, generate_transactions
from app.ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    RAW_FEATURES,
    add_engineered_features,
)

# Probability at or above which a transaction is sent for manual review
# (MEDIUM risk); HIGH risk starts at HIGH_RISK_THRESHOLD. These are business
# decisions: lower thresholds catch more fraud but create more review work.
REVIEW_THRESHOLD = 0.10
HIGH_RISK_THRESHOLD = 0.40


@dataclass
class TrainingResult:
    pipeline: Pipeline
    algorithm: str
    metrics: dict
    candidates: list[dict]
    dataset: dict
    X_test: pd.DataFrame
    y_test: pd.Series


def build_pipeline(model) -> Pipeline:
    preprocess = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline(
                    [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    return Pipeline(
        [
            ("engineer", FunctionTransformer(add_engineered_features)),
            ("preprocess", preprocess),
            ("model", model),
        ]
    )


def candidate_models(seed: int) -> dict:
    return {
        "logistic_regression": LogisticRegression(max_iter=1000),
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.08, random_state=seed
        ),
    }


def evaluate(y_true: pd.Series, proba) -> dict:
    flagged = (proba >= REVIEW_THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, flagged, labels=[0, 1]).ravel()
    return {
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4),
        "pr_auc": round(float(average_precision_score(y_true, proba)), 4),
        "precision": round(float(precision_score(y_true, flagged, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, flagged, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, flagged, zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y_true, flagged)), 4),
        # What you'd score by calling every transaction legitimate.
        "baseline_accuracy": round(float(1 - y_true.mean()), 4),
        "review_threshold": REVIEW_THRESHOLD,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def train_risk_model(n_samples: int = 20_000, seed: int = 42) -> TrainingResult:
    df = generate_transactions(n_samples=n_samples, seed=seed)
    X, y = df[RAW_FEATURES], df[TARGET]
    # stratify keeps the ~3% fraud rate identical in the train and test splits.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed
    )

    candidates: list[dict] = []
    best: tuple[str, Pipeline, dict] | None = None
    for name, model in candidate_models(seed).items():
        pipeline = build_pipeline(model).fit(X_train, y_train)
        metrics = evaluate(y_test, pipeline.predict_proba(X_test)[:, 1])
        candidates.append({"algorithm": name, "roc_auc": metrics["roc_auc"], "pr_auc": metrics["pr_auc"]})
        # PR-AUC, not accuracy: with 3% fraud, accuracy rewards ignoring fraud.
        if best is None or metrics["pr_auc"] > best[2]["pr_auc"]:
            best = (name, pipeline, metrics)

    algorithm, pipeline, metrics = best
    fraud_by_category = (
        df.groupby("merchant_category")[TARGET].mean().round(4).sort_values(ascending=False)
    )
    dataset = {
        "n_samples": n_samples,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "fraud_rate": round(float(y.mean()), 4),
        "seed": seed,
        "fraud_rate_by_category": {str(k): float(v) for k, v in fraud_by_category.items()},
    }
    return TrainingResult(pipeline, algorithm, metrics, candidates, dataset, X_test, y_test)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the risk model and print its metrics")
    parser.add_argument("--rows", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    result = train_risk_model(n_samples=args.rows, seed=args.seed)
    print(json.dumps(
        {
            "selected": result.algorithm,
            "candidates": result.candidates,
            "metrics": result.metrics,
            "dataset": result.dataset,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
