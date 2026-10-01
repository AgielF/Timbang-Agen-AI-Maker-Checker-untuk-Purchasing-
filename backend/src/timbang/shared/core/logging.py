"""Structured logging setup via structlog.

Rules (docs/SECURITY.md):
- NEVER log PII, tokens, or API keys.
- Audit trail for maker & checker actions is logged at INFO level
  with explicit structured fields — no raw user data.
"""

from __future__ import annotations

import logging
import sys

import structlog

from timbang.shared.core.config import get_settings


def setup_logging() -> None:
    """Configure structlog based on the current app environment."""
    settings = get_settings()
    is_prod = settings.app_env == "prod"

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_prod:
        # JSON output — machine-readable, safe for log aggregators
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        # Human-friendly console output for development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
