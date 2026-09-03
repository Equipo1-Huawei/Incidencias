"""structlog setup — one log line per node, legible in terminal and UI."""

from __future__ import annotations

import logging

import structlog

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
    _configured = True


def get_logger(name: str = "harness"):
    _configure()
    return structlog.get_logger(name)
