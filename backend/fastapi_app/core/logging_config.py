

# backend/fastapi_app/core/logging_config.py
import logging
import structlog
import sys

import os

def configure_logging():
    """Configure structlog for JSON structured logging."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    environment = os.getenv("APP_ENV", "development")

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            timestamper,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    log = structlog.get_logger("ReSimHub").bind(env=environment)
    log.info("Structured logging configured", environment=environment)
    return log


# Initialise structured logger once at import
logger = configure_logging()
