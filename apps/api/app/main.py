"""RiskScore Studio API — fintech transaction risk scoring."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.cache import get_cache
from app.core.config import settings
from app.core.middleware import BodySizeLimitMiddleware, SecurityHeadersMiddleware

_public_docs = None if settings.ENVIRONMENT == "production" else "/docs"

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Fintech risk scoring API (Project 1 — IIT Mandi DSAI portfolio)",
    docs_url=_public_docs,
    redoc_url=None if _public_docs is None else "/redoc",
    openapi_url=None if _public_docs is None else "/openapi.json",
)

# Last added runs first. CORS outermost so 413/429 still get Allow-Origin.
app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health():
    """Liveness probe for Docker / K8s later. Redis being down does not fail this."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "redis": "up" if get_cache().ping() else "down",
    }
