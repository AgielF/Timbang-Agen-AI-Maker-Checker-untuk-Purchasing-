"""Middleware registration (CORS, security headers, rate limiting hook).

Security headers applied (docs/SECURITY.md / OWASP API8):
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: no-referrer
"""

from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from timbang.shared.core.config import get_settings

_settings = get_settings()

# Rate limiter — storage_uri from config ("memory://" for dev, "redis://..." for prod).
# When rate_limit_enabled=False we use a very high limit rather than a no-op decorator,
# so the same @limiter.limit decorators on endpoints stay valid and don't need to change.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_settings.rate_limit_default],
    storage_uri=_settings.rate_limit_storage_uri,
    enabled=_settings.rate_limit_enabled,
)


def get_rate_limit_key(request: Request) -> str:
    """Composite rate-limit key: remote address + authenticated user ID (if available).

    The user_id comes from request.state (populated by auth middleware when ready).
    Falls back to remote address for anonymous requests.
    """
    remote_addr = get_remote_address(request)
    user_id: str | None = getattr(request.state, "user_id", None)
    return f"{remote_addr}:{user_id or 'anon'}"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach security headers to every response."""

    async def dispatch(self, request: Request, call_next: object) -> Response:
        response: Response = await call_next(request)  # type: ignore[arg-type]
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


def register_middleware(app: FastAPI) -> None:
    """Attach all middleware to the FastAPI application."""
    settings = get_settings()

    # CORS — explicit allowlist from config (docs/SECURITY.md: CORS ketat)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # slowapi rate-limit middleware — must come after SecurityHeadersMiddleware
    app.add_middleware(SlowAPIMiddleware)
