# Phase 3 — The risk model (how it works and why)

**Status:** Done · 19 API tests · trained live and browser-verified
**Certificate link:** AI101 (data cleaning, EDA, evaluation) + ML201 (classification, model comparison)

## The pipeline in one picture

```text
generate_transactions(seed)          ← synthetic, reproducible, ~3% fraud, 2% missing values
        │
        ▼
train/test split (80/20, stratified) ← fraud rate identical in both halves
        │
        ▼
sklearn Pipeline ─────────────────────────────────────────────────────────────┐
│ 1. engineer   log_amount, amount_to_avg_ratio, is_night                     │
│ 2. preprocess numeric: median-impute → scale   categorical: one-hot encode  │
│ 3. model      Logistic Regression  vs  Gradient Boosting                    │
└─────────────────────────────────────────────────────────────────────────────┘
        │  best PR-AUC on the test set wins
        ▼
risk_model_v{N}.joblib  +  row in model_versions (metrics, dataset summary)
        │
        ▼
champion/challenger: old active model is scored on the NEW test set;
the new model is promoted only if it's at least as good on the same data
```

## Why each decision (interview talking points)

| Decision | Why |
|---|---|
| **Synthetic data with a seed** | No real customer data anywhere (privacy), and the same seed always rebuilds the same dataset, so results are reproducible |
| **Feature engineering inside the Pipeline** | The saved `.joblib` takes *raw* transaction fields. Phase 4's scoring API can't compute features differently from training, which is a classic production bug called *training/serving skew* |
| **Imputation inside the Pipeline** | The median learned from training data is reused at scoring time, never recomputed on a single new row |
| **`handle_unknown="ignore"`** | A merchant category never seen in training doesn't crash scoring (tested with `"lottery"`) |
| **Stratified split** | With 3% fraud, a random split could leave the test set with too few fraud cases |
| **PR-AUC to pick the model, not accuracy** | Calling everything legitimate scores 97% accuracy and catches zero fraud. PR-AUC focuses on how well the model finds the rare class |
| **Two candidate algorithms** | The fancier model doesn't always win. Here Logistic Regression beats Gradient Boosting, because the data's real pattern is close to linear in log-odds |
| **Review threshold 10%, high-risk 40%** | Thresholds are business decisions: lower means more fraud caught but more manual reviews. The confusion matrix on the dashboard shows that trade-off |
| **Versioned models + champion/challenger** | Every model is kept. A new one goes live only if it wins **on the same test data** as the current one. Admins can roll back with one click |
| **Admin-only training (`require_admin`)** | Changing the production model is privileged; analysts can view but not train |

## Reading the numbers (from a real run)

| Metric | Value | Meaning |
|---|---|---|
| ROC-AUC | ~0.80–0.82 | Pick a random fraud and a random legit transaction: the model ranks the fraud higher ~81% of the time |
| PR-AUC | ~0.18–0.21 | ~6–7× better than random guessing (0.03) |
| Recall @ 10% | ~35% | About a third of fraud gets flagged for review |
| Precision @ 10% | ~19% | About 1 in 5 flagged transactions is really fraud |
| Accuracy | ~93.5% | **Lower** than the 97% "do nothing" baseline, which is exactly why we don't use it |

**Why do scores jump around between versions?** Each test set has only ~120 fraud cases, so a handful of cases going one way or the other moves PR-AUC by 0.02–0.04. That's why the challenger is compared to the champion on identical data instead of comparing numbers from different runs.

## Bug found during testing (and the fix)

The first version compared the new model's PR-AUC with the number *stored* for the active model. But each training run uses a different random seed, so those two numbers came from **different test sets**. That's not a fair comparison. The fix: load the active model from disk and score it on the challenger's test set (`_champion_pr_auc` in `app/services/model_registry.py`). Same data, fair fight.

## What each file does

| File | Job |
|---|---|
| `apps/api/app/ml/dataset.py` | Synthetic transaction generator with documented fraud signals |
| `apps/api/app/ml/features.py` | Raw and engineered feature lists, `add_engineered_features` |
| `apps/api/app/ml/train.py` | Pipeline, candidates, evaluation, `python -m app.ml.train` CLI |
| `apps/api/app/services/model_registry.py` | Save artifacts, champion/challenger, activation |
| `apps/api/app/api/v1/models.py` | `GET /models`, `GET /models/active`, `POST /models/train`, `POST /models/{id}/activate` |
| `apps/api/app/cli.py` | `python -m app.cli make-admin <email>` |
| `apps/web/src/components/models/` | Metric tiles, confusion matrix, category bars, versions table, train button |

## Known trade-offs (on purpose, for later)

- Training runs inside the HTTP request (~5 s). Fine at 20k rows; Project 2 moves it to a background worker/pipeline.
- Model files live on local disk (a Docker volume). In the cloud they'd go to object storage like S3.
- Only one active model at a time is enforced in code, not by a database constraint.
- The model isn't serving predictions yet. That's Phase 4.

## Try it yourself

1. Run an experiment without the database: `.\.venv\Scripts\python.exe -m app.ml.train --rows 50000 --seed 7` (from `apps/api`). Does more data change the winner or the PR-AUC?
2. In `dataset.py`, make `country_mismatch` a much stronger signal (change `1.7` to `3.0`) and rerun. Watch PR-AUC rise.
3. In `train.py`, change `REVIEW_THRESHOLD` to `0.05`, then `0.30`. How do recall and precision move? Which would a bank prefer, and why?
4. Make yourself an admin: `.\.venv\Scripts\python.exe -m app.cli make-admin you@example.com`, then train from the dashboard.
