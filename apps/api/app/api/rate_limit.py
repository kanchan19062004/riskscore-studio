from fastapi import HTTPException, Request, Response, status

from app.core.rate_limit import hit_limit


def client_ip(request: Request) -> str:
    # Do not trust X-Forwarded-For here. Anyone can send that header; we only
    # know the TCP peer. A reverse proxy we control would be the place to
    # replace this with the forwarded client address.
    if request.client is None:
        return "unknown"
    return request.client.host


def enforce_rate_limit(
    request: Request,
    response: Response,
    *,
    key: str,
    limit: int,
    window_seconds: int,
    fail_closed: bool,
    detail: str,
) -> None:
    result = hit_limit(
        key, limit=limit, window_seconds=window_seconds, fail_closed=fail_closed
    )
    response.headers["X-RateLimit-Limit"] = str(result.limit)
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    if result.allowed:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=detail.format(retry_after=result.retry_after),
        headers={
            "Retry-After": str(max(1, result.retry_after)),
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": "0",
        },
    )
