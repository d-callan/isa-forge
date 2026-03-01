"""Structured logging wrapper for ISA-Forge."""

import logging
import sys
from typing import Any

import structlog
from structlog.typing import Processor

from isaforge.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for ISA-Forge."""
    # Set up standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Shared processors for all outputs
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set up formatter for stdlib handler
    if settings.log_level == "DEBUG":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Apply formatter to root handler
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A bound structlog logger.
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """Bind context variables to all subsequent log calls in this context.

    Args:
        **kwargs: Key-value pairs to bind to the logging context.
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """Unbind specific context variables.

    Args:
        *keys: Keys to unbind from the logging context.
    """
    structlog.contextvars.unbind_contextvars(*keys)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


class LogContext:
    """Context manager for temporary logging context."""

    def __init__(self, **kwargs: Any):
        """Initialize with context to bind.

        Args:
            **kwargs: Key-value pairs to bind to the logging context.
        """
        self.kwargs = kwargs
        self.token = None

    def __enter__(self) -> "LogContext":
        """Bind context on entry."""
        self.token = structlog.contextvars.bind_contextvars(**self.kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Unbind context on exit."""
        structlog.contextvars.unbind_contextvars(*self.kwargs.keys())
