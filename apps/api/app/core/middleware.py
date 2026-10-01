"""Security headers and a request-size cap.

The browser talks to Next.js, not to FastAPI, but headers still matter for
/docs, health probes, and anyone who hits the API directly.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings

_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cache-Control": "no-store",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for name, value in _HEADERS.items():
            response.headers.setdefault(name, value)
        if settings.ENVIRONMENT == "production":
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
            )
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        raw = request.headers.get("content-length")
        if raw:
            try:
                size = int(raw)
            except ValueError:
                return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
            if size > settings.MAX_REQUEST_BODY_BYTES:
                return JSONResponse(
                    {"detail": "Request body too large"},
                    status_code=413,
                )
        return await call_next(request)
