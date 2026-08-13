"""
Logging configuration shared by agents and backend services.
"""

import logging
import sys
from typing import Optional

_CONFIGURED = False


def get_logger(name: str = "investcops", level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger, configuring the root 'investcops' logger on first use.
    """
    global _CONFIGURED
    if not _CONFIGURED:
        lvl = (level or "INFO").upper()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )
        root = logging.getLogger("investcops")
        root.setLevel(lvl)
        root.addHandler(handler)
        root.propagate = False
        _CONFIGURED = True
    return logging.getLogger(name)