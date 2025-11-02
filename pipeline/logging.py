from __future__ import annotations

"""
Centralised logging configuration for the pipeline.
"""

import logging
from typing import Optional


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a simple formatter."""
    if logging.getLogger().handlers:
        # Preserve existing configuration (useful when invoked from tests)
        return

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Shortcut for fetching a configured logger."""
    configure_logging()
    return logging.getLogger(name if name else "pipeline")


__all__ = ["configure_logging", "get_logger"]
