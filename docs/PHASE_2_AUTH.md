# Phase 2 — Authentication (how it works and why)

**Status:** Done · 10 API tests · browser flow verified

## The flow in one picture

```text
Browser                     Next.js server (BFF)                 FastAPI                 Postgres
───────                     ───────────────────                  ───────                 ────────
submit login form  ──────►  Server Action login()
                            POST /api/v1/auth/login  ─────────►  find user by email ───► users
                                                                 verify Argon2 hash
                            ◄───────── { access_token (JWT) }    sign JWT (sub=user id)
                            set httpOnly cookie rs_session
◄──── redirect /dashboard

open /dashboard    ──────►  proxy.ts: cookie present? (fast)
                            requireUser(): GET /auth/me  ─────►  verify JWT signature
                              with Authorization: Bearer          + expiry, load user ──► users
                            ◄───────── { user }
◄──── rendered dashboard
```

The browser only ever holds an **httpOnly cookie**. JavaScript in the page can't read it, so an XSS bug can't steal the token. The browser never calls FastAPI directly; the Next.js server does. This pattern is called **Backend-for-Frontend (BFF)**.

## What each file does

| File | Job |
|---|---|
| `apps/api/app/models/user.py` | `users` table: UUID id, unique email, Argon2 hash, role |
| `apps/api/migrations/versions/0001_create_users.py` | Creates that table (Alembic migration) |
| `apps/api/app/core/security.py` | Hash/verify passwords, create/decode JWTs |
| `apps/api/app/api/deps.py` | `get_current_user`: turns a Bearer token into a `User`, or 401 |
| `apps/api/app/api/v1/auth.py` | `POST /register`, `POST /login`, `GET /me` |
| `apps/web/src/app/actions/auth.ts` | Server Actions: call FastAPI, set/delete the cookie |
| `apps/web/src/lib/dal.ts` | `requireUser()`: the real auth check for pages |
| `apps/web/src/proxy.ts` | Fast redirect to `/login` when there's no cookie at all |

## Security decisions (interview talking points)

| Decision | Why |
|---|---|
| **Argon2id** password hashing | OWASP's first recommendation; slow and memory-hard, so stolen hashes are expensive to crack |
| Same error for unknown email and wrong password | Attackers can't use login to discover which emails have accounts |
| Dummy hash check when the email doesn't exist | Both failure paths take the same time, so timing doesn't leak it either |
| JWT holds only user id + role, no email | Tokens are readable by anyone who has them; keep PII out |
| JWT expires in 60 min | A leaked token stops working on its own |
| UUID user ids | Ids can't be guessed by counting 1, 2, 3… |
| httpOnly + SameSite=Lax cookie, `secure` in production | Blocks token theft by page scripts and most cross-site request forgery |
| API refuses to start in production with a weak `JWT_SECRET` | Prevents shipping the dev secret by accident |
| Validation lives in FastAPI (Pydantic) | One source of truth; the HTML `required`/`minLength` are only UX hints |
| Proxy check is "optimistic", `requireUser()` is the real check | Next.js docs: proxy runs on every request, so it must stay cheap; security belongs next to the data |

## Known trade-offs (on purpose, for later phases)

- `POST /register` returns 409 for an existing email, which does reveal that the email is registered. Most products accept this for usability.
- No login rate limiting yet. Phase 6 adds it with Redis.
- No refresh tokens. After 60 minutes the user logs in again.

## Try it yourself

1. Swagger: http://localhost:8000/docs. Register with `POST /auth/register`, click **Authorize**, enter your email as `username`, then call `GET /auth/me`.
2. Look at the stored hash:
   `docker exec riskscore-postgres psql -U riskscore -d riskscore -c "SELECT email, hashed_password FROM users;"`
3. Paste your access token into [jwt.io](https://jwt.io) and see what's inside (and what isn't).
4. In the browser DevTools console on the dashboard, run `document.cookie`. `rs_session` won't appear, because it's httpOnly.
