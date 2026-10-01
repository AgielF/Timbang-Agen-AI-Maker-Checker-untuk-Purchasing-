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
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from timbang.shared.core.config import get_settings

# Rate limiter instance — registered in main.py via app.state.limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[get_settings().rate_limit_default])


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
