@echo off
REM Start RiskScore Studio API without needing Activate.ps1
REM Postgres must be running first: docker compose up -d postgres redis (from infra\docker)
cd /d "%~dp0"
".venv\Scripts\alembic.exe" upgrade head || exit /b 1
".venv\Scripts\uvicorn.exe" app.main:app --reload --reload-dir app --port 8000
