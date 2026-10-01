# Project 1 — ML Studio (Fintech Risk)

**Status:** Security hardening complete → Next: CI polish  
**Domain (context):** Fintech — transaction / credit risk scoring  
**Product name (working):** RiskScore Studio  
**Type:** Full-stack ML product (Frontend + Backend)  
**Goal:** Ship a production-style app that uses your **ML201 + AI101** skills, then wraps them with auth, caching, Docker, security, and CI — so it looks industry-standard, not like a notebook.

---

## Decision log

| Decision | Choice | Date |
|---|---|---|
| Domain | **Fintech** (credit / transaction risk) | 2026-09-26 |
| Stack | **Next.js + FastAPI + Postgres + Redis + Docker** | 2026-09-26 |
| Scaffold | **Done** — `apps/web`, `apps/api`, `infra/docker`, CI | 2026-09-26 |
| Auth | **Done** — Argon2 + JWT in FastAPI, httpOnly cookie via Next.js BFF, Alembic migrations ([details](PHASE_2_AUTH.md)) | 2026-10-02 |
| Risk model | **Done** — synthetic data, sklearn Pipeline, PR-AUC selection, versioned models with champion/challenger ([details](PHASE_3_MODEL.md)) | 2026-10-02 |
| Scoring | **Done** — POST /scores, LOW/MEDIUM/HIGH, Redis cache, audit rows ([details](PHASE_4_SCORING.md)) | 2026-10-02 |
| History | **Done** — paginated filters, 404-not-403 privacy, CSV export ([details](PHASE_5_HISTORY.md)) | 2026-10-02 |
| Security | **Done** — rate limits (auth fail-closed, scoring fail-open), headers, 64 KiB body cap ([details](PHASE_6_SECURITY.md)) | 2026-10-02 |

---

## 1. What is “domain”? (your question)

**Yes — domain = the context / subject of the project.**

It answers: *What real-world problem does this app solve?*

| Domain (context) | Example problem the app solves |
|---|---|
| E-commerce | Predict if a customer will churn / buy again |
| Fintech | Score a transaction as risky or safe |
| Education | Predict student risk of dropping a course |
| Healthcare (demo) | Classify risk level from tabular clinical-style features (demo data only) |
| Real estate | Predict house price from features |

**Same engineering in every case** (API, UI, Redis, Docker, auth).  
**Only the dataset + model story changes.**

You pick one domain so the portfolio tells a clear story:  
*“I built an ML product for X.”*  
not  
*“I built a generic random forest demo.”*

---

## 2. What this project is (in one paragraph)

**RiskScore Studio** is a fintech-style web app where a logged-in analyst can:

1. Use a sample (or uploaded) **transaction / credit** dataset  
2. Train a classical ML risk model (classification + probability score)  
3. Score new transactions from a dashboard (**LOW / MEDIUM / HIGH** risk + probability)  
4. See model metrics and a searchable scoring history  

Behind the scenes: a secured FastAPI backend serves the model, Redis caches repeated scores, Postgres stores users and history, everything runs in Docker, and GitHub Actions runs tests on every push.

**Portfolio story:** *“I built a full-stack fintech risk-scoring product with JWT auth, Redis caching, Docker, and CI — applying my IIT Mandi ML minor.”*

This is **Project 1 of 3**. Later projects (Data Hub, Agent Console) will reuse the same auth style, Docker patterns, and eventually call this scoring API.

---

## 3. What it is NOT

- Not a Jupyter notebook with screenshots  
- Not Streamlit-only (we want a real frontend + API split)  
- Not full Kubernetes yet (that deepens in Project 2)  
- Not deep learning / MCP yet (that is Project 3)

---

## 4. Who it’s for (imagine the user)

A **risk / ops analyst** at a small fintech who wants to:

- Log in securely  
- Score transactions without opening a notebook  
- See risk probability + history in a dashboard  
- Trust that the API is rate-limited and cached under load  

You are building the **product**, not only the model.

**Important:** We use **public or synthetic** transaction data only (e.g. Kaggle-style credit/fraud datasets). No real customer PII. That itself is part of the security story.

---

## 5. Domain locked — Fintech risk scoring

### Chosen: Credit / Transaction Risk Scorer
- **Context:** Fintech  
- **ML task:** Binary classification (risky vs not) + **probability score** (0–1)  
- **UI labels:** Map probability → LOW / MEDIUM / HIGH (thresholds we define)  
- **Typical features (examples):** amount, merchant category, time, country, device type, prior failures — depending on dataset  
- **Certificate link:** ML201 (classification, metrics) + AI101 (cleaning, EDA, evaluation)  
- **Data rule:** Public/synthetic only — never real bank data  

### Other options (not chosen — kept for reference)
- A: Customer churn · C: House price · D: Student at-risk

---

## 6. Features (MVP → stretch)

### Must have (MVP)
- [x] User signup / login (JWT)  
- [x] Protected risk dashboard  
- [x] Built-in sample **credit/transaction** dataset  
- [x] Train classical risk model (e.g. Logistic Regression / Random Forest)  
- [x] Show metrics: accuracy, precision, recall, F1, ROC-AUC  
- [x] Score a transaction from UI → risk label + probability  
- [x] Save scoring history in Postgres  
- [x] Redis cache for identical scoring requests  
- [x] Docker Compose: `web` + `api` + `postgres` + `redis`  
- [x] Basic CI: lint + tests on GitHub Actions  
- [ ] README + architecture diagram (fintech risk story)  

### Should have (makes it “solid”)
- [x] Role-based access (user / admin)  
- [x] Rate limiting on predict API  
- [x] Input validation & file size limits  
- [x] API docs (OpenAPI / Swagger)  
- [x] Health check endpoints  
- [ ] Simple charts (metrics, prediction volume)  

### Nice to have (if time)
- [x] Model version list (v1, v2)  
- [x] Export predictions as CSV  
- [ ] Dark/light UI polish  
- [ ] Deploy to a free/cheap cloud host  

---

## 7. Architecture (high level)

```text
┌─────────────────┐         HTTPS / JWT          ┌─────────────────┐
│  Next.js Web    │  ─────────────────────────►  │  FastAPI API    │
│  (Frontend)     │                              │  (Backend)      │
└─────────────────┘                              └────────┬────────┘
                                                          │
                                        ┌─────────────────┼─────────────────┐
                                        ▼                 ▼                 ▼
                                   ┌─────────┐      ┌─────────┐      ┌──────────┐
                                   │ Postgres│      │  Redis  │      │  Model   │
                                   │ users,  │      │  cache  │      │  files   │
                                   │ history │      │         │      │ (.joblib)│
                                   └─────────┘      └─────────┘      └──────────┘
```

All four services start with **Docker Compose**.

---

## 8. Tech stack (locked for Project 1)

| Layer | Technology |
|---|---|
| Frontend | Next.js + TypeScript |
| Backend | FastAPI + Python |
| ML | scikit-learn (+ pandas) |
| Database | PostgreSQL |
| Cache | Redis |
| Auth | JWT (access tokens) |
| Containers | Docker + Docker Compose |
| CI | GitHub Actions |
| K8s | Intro only (optional Minikube later) — full focus in Project 2 |

---

## 9. How this uses your certificate

| Course | How ML Studio uses it |
|---|---|
| **AI101 – Data Science** | Load CSV, clean columns, EDA summary, train/test split, metric interpretation, charts |
| **ML201 – Machine Learning** | Train classical models, evaluate, avoid leakage, serve predictions |
| **AI301 – Deep Learning** | Not the focus here (saved for Project 3) |

You are **applying** the minor inside a real product shell.

---

## 10. Security & scale (even in Project 1)

| Concern | What we implement |
|---|---|
| Auth | Password hashing (bcrypt), JWT, protected routes |
| Validation | Pydantic schemas; reject bad/oversized uploads |
| Secrets | `.env` locally; never commit secrets |
| Abuse | Rate limit `/predict` |
| Cache | Redis TTL for repeated prediction payloads |
| Data volume | Pagination for history; async-friendly API design |

This is enough to say “security + caching considered,” without overbuilding.

---

## 11. Folder structure (planned)

```text
masai_iit_project1/
├── docs/
│   └── PROJECT_1_ML_STUDIO.md      ← this file
├── apps/
│   ├── web/                        ← Next.js frontend
│   └── api/                        ← FastAPI backend + ML
├── infra/
│   └── docker/
│       └── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
```

(We create this when you confirm the domain and we start scaffolding.)

---

## 12. Build phases (how we will learn)

| Phase | What we build | What you learn |
|---|---|---|
| 0 | Domain + this doc (now) | Product thinking |
| 1 | Repo scaffold + Compose | Project structure, Docker basics |
| 2 | Auth API + login UI | Full-stack auth |
| 3 | Dataset + train endpoint | ML in a service (not notebook) |
| 4 | Predict + Redis cache | Caching strategy |
| 5 | Dashboard + history | Frontend product UX |
| 6 | Security hardening | Rate limits, validation |
| 7 | CI pipeline | Professional delivery |
| 8 | Polish + README for LinkedIn | How to present the work |

I teach each phase before/while we code — like a mentor, not a code dump.

---

## 13. Definition of done (Project 1 complete when…)

1. Another person can `docker compose up` and use the app  
2. They can sign up, train (or load model), predict, see history  
3. Repeated predictions hit Redis (you can show this in logs/metrics)  
4. CI passes on GitHub  
5. README explains architecture + how it links to your IIT Mandi minor  
6. You can explain every major folder in an interview  

---

## 14. What you decide next

Domain, stack, scaffold, auth, the risk model, scoring, history and security hardening are done.

**Next phase:** CI polish (Phase 7).
