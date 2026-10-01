# RiskScore Studio

Full-stack **fintech transaction risk scoring** product (Project 1 of 3).

Applies an IIT Mandi Minor in AI & Data Science (**AI101 + ML201**) inside a real product shell: auth, caching, Docker, and CI.

| Layer | Stack |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | FastAPI + Python + scikit-learn |
| Data | PostgreSQL |
| Cache | Redis |
| Containers | Docker Compose |
| CI | GitHub Actions |

Docs: [`docs/PROJECT_1_ML_STUDIO.md`](docs/PROJECT_1_ML_STUDIO.md) · Auth: [`docs/PHASE_2_AUTH.md`](docs/PHASE_2_AUTH.md) · Model: [`docs/PHASE_3_MODEL.md`](docs/PHASE_3_MODEL.md) · Scoring: [`docs/PHASE_4_SCORING.md`](docs/PHASE_4_SCORING.md) · History: [`docs/PHASE_5_HISTORY.md`](docs/PHASE_5_HISTORY.md) · Security: [`docs/PHASE_6_SECURITY.md`](docs/PHASE_6_SECURITY.md)

---

## Repository layout

```text
masai_iit_project1/
├── apps/
│   ├── web/          # Next.js UI
│   └── api/          # FastAPI + ML
├── infra/docker/     # docker-compose.yml
├── docs/             # Project documentation
└── .github/workflows # CI
```

---

## Mentor note — why this layout?

- **`apps/web`** and **`apps/api`** are separate deployable services (industry monorepo style).
- **`infra/docker`** keeps Compose/K8s away from application code.
- Same pattern scales to Project 2 (K8s) and Project 3 (MCP) without rewriting structure.

---

## Prerequisites

- Node.js 20+
- Python 3.11+ (3.10 works for local scaffold)
- Docker Desktop (for Compose) — **install if missing**
- Git

---

## Quick start (local, without Docker first)

### 1. Env file

```bash
cp .env.example .env
```

### 2. Databases (Docker)

```powershell
cd infra\docker
docker compose up -d postgres redis
```

### 3. API

```bash
cd apps/api
python -m venv .venv
```

**Windows (recommended — avoids Activate.ps1 policy issues):**

```powershell
cd apps\api
.\start-api.bat
```

`start-api.bat` applies database migrations (`alembic upgrade head`) and then starts uvicorn. To do it by hand:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

If you want Activate.ps1 to work in PowerShell, set (once per user):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- Health: http://localhost:8000/health  
- Docs: http://localhost:8000/docs  

### 4. Web (new terminal)

```bash
cd apps/web
npm install
npm run dev
```

- UI: http://localhost:3000 (register at `/register`, dashboard at `/dashboard`)
- Training models needs the admin role. After registering, from `apps\api` run:
  `.\.venv\Scripts\python.exe -m app.cli make-admin you@example.com`
- The Next.js server reaches FastAPI at `API_URL` (default `http://127.0.0.1:8000`, see `apps/web/.env.example`).

---

## Docker Compose (when Docker is installed)

```bash
cp .env.example .env
cd infra/docker
docker compose up --build
```

| Service | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |

---

## Tests & CI

```bash
cd apps/api
pytest -q
```

Tests use an in-memory SQLite database, so they don't need Docker.

GitHub Actions runs on every push/PR (`.github/workflows/ci.yml`): API lint, migrations against a real Postgres plus `alembic check` (fails if a model changed without a migration), API tests, and web lint/build.

---

## Build phases (where we are)

| Phase | Status |
|---|---|
| 0 Domain + docs | Done (Fintech) |
| 1 Scaffold | Done |
| 2 Auth API + login UI | Done |
| 3 Dataset + train | Done |
| 4 Predict + Redis cache | Done |
| 5 Dashboard + history | **Done** |
| 6 Security hardening | **Done** |
| 7 CI polish | Scaffolded |
| 7 CI polish | Scaffolded |
| 8 LinkedIn-ready README | Pending |

---

## Security note

Never commit `.env`. `JWT_SECRET` in `.env.example` is for local dev only.
