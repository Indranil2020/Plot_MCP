"""Application logging setup."""

from __future__ import annotations

import logging
import os


def setup_app_logger(name: str = "plot_mcp") -> logging.Logger:
    """Create a file logger for backend requests."""
    log_dir = os.path.join("backend", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
