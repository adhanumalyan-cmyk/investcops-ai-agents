"""
Logging configuration for the backend.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root application logging once."""
    logger = logging.getLogger("investcops")
    if logger.handlers:
        return
    logger.setLevel(level.upper())
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    logger.addHandler(handler)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"investcops.{name}")