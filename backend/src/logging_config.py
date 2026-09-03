"""Logging estructurado con structlog."""
import logging
import structlog
from src.config import config

def configure_logging():
    """Configura structlog con formato JSON para produccion y console para desarrollo."""
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = __name__):
    """Retorna un logger estructurado."""
    return structlog.get_logger(name)

configure_logging()
