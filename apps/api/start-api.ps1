# Start RiskScore Studio API (works even if Activate.ps1 is blocked)
# Postgres must be running first: docker compose up -d postgres redis (from infra\docker)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venv = Join-Path $PSScriptRoot ".venv\Scripts"
if (-not (Test-Path "$venv\uvicorn.exe")) {
    Write-Host "venv missing. Run: python -m venv .venv && .\.venv\Scripts\pip.exe install -r requirements.txt"
    exit 1
}

& "$venv\alembic.exe" upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$venv\uvicorn.exe" app.main:app --reload --reload-dir app --port 8000
