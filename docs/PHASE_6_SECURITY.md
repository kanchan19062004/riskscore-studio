# Phase 6 — Security hardening

**Status:** Done · 41 API tests
**Certificate link:** this is the product-engineering layer around ML201 — abuse, headers, fail-open vs fail-closed

## What this phase adds

```text
POST /auth/login     IP 10/min  +  email 5/min     fail CLOSED
POST /auth/register  IP 5/hour                     fail CLOSED
POST /scores         user 30/min + IP 60/min       fail OPEN

429 + Retry-After + X-RateLimit-Limit / Remaining
X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Cache-Control: no-store
JSON bodies larger than 64 KiB → 413
Swagger UI off when ENVIRONMENT=production
Unknown merchant_category / channel → 422 (allow-list, not free text)
```

The UI already shows FastAPI's `detail` string, so a 429 on login or score is a readable "try again in N seconds" — no extra spinner logic.

## Why these decisions

| Decision | Why |
|---|---|
| **Fixed window in Redis (`INCR` + `EXPIRE NX`)** | Cheap, easy to explain, keys die on their own. Sliding windows are smoother but harder to interview about. |
| **Auth fail-closed** | If we cannot count login attempts, we must not accept them. A Redis outage must not become an open brute-force window. |
| **Scoring fail-open** | Same reason the score *cache* fails open: a cache/limiter outage must not freeze decisions. Abuse protection is important; availability of a risk decision is more important. |
| **Cache hits still count** | Rate limits budget *requests*, not CPU. Each POST still writes an audit row. |
| **IP + email (login)** | IP stops a noisy client. Email stops a distributed spray at one account. |
| **Do not trust `X-Forwarded-For`** | Anyone can send that header. Only a reverse proxy we control should overwrite the client IP. |
| **Headers on the API *and* Next.js** | The browser talks to Next.js (BFF). FastAPI headers still matter for `/docs` and anyone who hits the API directly. |
| **64 KiB body cap** | Auth and score payloads are tiny. This is not an upload API. |
| **Hide `/docs` in production** | OpenAPI is a map of the attack surface. Fine in development; off when `ENVIRONMENT=production`. |

## Contrast with Phase 4 (the interview soundbite)

> Redis down + **cache**: keep scoring (fail open).  
> Redis down + **login limiter**: reject (fail closed).  
> Redis down + **score limiter**: keep scoring (fail open).

Same Redis. Opposite policy, on purpose.

## What each file does

| File | Job |
|---|---|
| `apps/api/app/core/rate_limit.py` | Memory / Redis / broken backends; `hit_limit(..., fail_closed=)` |
| `apps/api/app/api/rate_limit.py` | Turns a miss into HTTP 429 + `Retry-After` |
| `apps/api/app/core/middleware.py` | Security headers + body-size cap |
| `apps/api/app/api/v1/auth.py` | Login/register limits |
| `apps/api/app/api/v1/scores.py` | POST /scores limits |
| `apps/web/next.config.ts` | Same class of headers on the UI |
| `apps/web/src/lib/api.ts` | Maps 429 / 413 to a form message |

Redis keys look like `rl:login:email:analyst@example.com`. Flush a lockout with:

```powershell
docker exec riskscore-redis redis-cli KEYS "rl:*"
docker exec riskscore-redis redis-cli DEL rl:login:ip:127.0.0.1
```

## Try it yourself

1. Open DevTools → Network on **Log in**. The JSON error from a wrong password is still 401. After five failures for that email you should get **429** and a wait message.
2. Score grocery twice (cache hit). That is two of your 30/min, not one.
3. `curl -I http://localhost:8000/health` — you should see `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`.
4. Stop Redis (`docker stop riskscore-redis`). Login should 429 (fail closed). Scoring should still 201 (fail open). Start Redis again when you are done.

## Known trade-offs

- Fixed windows allow a burst of `limit` at the boundary (use 10, wait, use 10). Good enough for this product; token buckets can wait for Project 2.
- Localhost shares one IP, so hammering login in tests against the *running* API will lock you out for a minute. The pytest suite uses an in-memory limiter that resets every test.
- We still do not have CSRF tokens on the BFF cookie. Same-site cookies + server actions are the current control; a dedicated CSRF story can land with public deploy.
