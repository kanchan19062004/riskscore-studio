# Phase 4 — Scoring + Redis cache

**Status:** Done · 28 API tests · scored against Docker Redis
**Certificate link:** ML201 (using a trained classifier in production)

## The flow

```text
POST /api/v1/scores  { amount, merchant_category, channel, ... raw fields ... }
        │
        ├─ load active model version from Postgres
        ├─ cache key = sha256(version_id + canonical JSON payload)
        │
        ├─ Redis GET ── hit ──► reuse probability/risk_level, still write an audit row
        │
        └─ miss ──► sklearn Pipeline.predict_proba (raw fields in, probability out)
                    Redis SETEX 1 hour
                    write scores row (cache_hit = false)
        │
        ▼
LOW < 10%   ·   MEDIUM 10–40%   ·   HIGH ≥ 40%
```

The browser never calls FastAPI. Next.js (BFF) posts the form, the API scores it, the page shows the band.

## Why these decisions

| Decision | Why |
|---|---|
| **Raw fields only** | Feature engineering lives inside the saved Pipeline, so scoring cannot drift from training |
| **Cache key includes model version** | Activating v3 does not reuse v2's cached scores |
| **Canonical JSON + SHA-256** | `{"a":1,"b":2}` and `{"b":2,"a":1}` hit the same key |
| **Fail open** | If Redis is down, scoring still works; a cache outage must not take down payments |
| **Audit row on cache hits** | Fintech: every decision is a record, even when the number was reused |
| **In-memory Pipeline** | `joblib.load` on every request would dominate latency; the file is loaded once per version per process |
| **Thresholds are not the model's job** | The model outputs a probability. LOW/MEDIUM/HIGH is a business rule layered on top |

## What each file does

| File | Job |
|---|---|
| `apps/api/app/core/cache.py` | Redis backend + in-memory backend for tests; fail-open |
| `apps/api/app/ml/score.py` | Probability → LOW / MEDIUM / HIGH |
| `apps/api/app/services/scorer.py` | Cache, load pipeline, persist |
| `apps/api/app/api/v1/scores.py` | `POST /scores`, `GET /scores`, `GET /scores/options` |
| `apps/api/app/models/score.py` | `scores` table (audit trail) |
| `apps/web/src/app/score/page.tsx` | Scoring UI with grocery vs crypto presets |

## Try it yourself

1. Score **Typical grocery**, then submit the same form again. The second result should say **Served from Redis cache**. In Redis: `docker exec riskscore-redis redis-cli KEYS "score:*"`
2. Change the amount by ₹1 and score again — cache miss, because the payload changed.
3. In DevTools, the cookie is still `rs_session`; the JSON body never includes a password or token.

## Known trade-offs

- Cache TTL is a flat 1 hour. No per-user invalidation besides version id.
- History on `/score` is "latest 20 for me", not a searchable log. That's Phase 5.
- Rate limiting on `/scores` is done in Phase 6.
