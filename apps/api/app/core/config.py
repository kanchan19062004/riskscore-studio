from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The shared .env lives at the repo root; in Docker this resolves to a missing
# file and pydantic-settings falls back to real environment variables.
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"

_DEV_JWT_SECRET = "change-me-in-production-use-long-random-string"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(_REPO_ROOT_ENV, ".env"), extra="ignore")

    APP_NAME: str = "RiskScore Studio API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Comma-separated origins, e.g. http://localhost:3000
    CORS_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = "postgresql+psycopg2://riskscore:riskscore@localhost:5432/riskscore"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = _DEV_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Trained model files (.joblib). apps/api/artifacts locally, /app/artifacts in Docker.
    MODEL_DIR: Path = Path(__file__).resolve().parent.parent.parent / "artifacts"

    # Identical (model version + payload) scores are reused for this many seconds.
    SCORE_CACHE_TTL_SECONDS: int = 3600

    # Fixed-window limits. Auth is fail-closed; scoring is fail-open.
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_LOGIN_IP: int = 10
    RATE_LIMIT_LOGIN_EMAIL: int = 5
    RATE_LIMIT_REGISTER_IP: int = 5
    RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = 3600
    RATE_LIMIT_SCORE_USER: int = 30
    RATE_LIMIT_SCORE_IP: int = 60

    MAX_REQUEST_BODY_BYTES: int = 64 * 1024

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _require_strong_secret_in_production(self) -> "Settings":
        if self.ENVIRONMENT == "production" and (
            self.JWT_SECRET == _DEV_JWT_SECRET or len(self.JWT_SECRET) < 32
        ):
            raise ValueError("JWT_SECRET must be a random string of 32+ characters in production")
        return self


settings = Settings()
