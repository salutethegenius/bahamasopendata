"""Shared logging setup for the Intelligence imprint (architecture §6).

Writes to stdout and data/intelligence/logs/capture.log.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from backend.app.services.document_ingestion import INTELLIGENCE_DATA_DIR

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a logger writing to stdout and the rotating capture log file."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_dir = INTELLIGENCE_DATA_DIR / "logs"
    capture_log_file = log_dir / "capture.log"
    log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler(
        capture_log_file,
        maxBytes=10_000_000,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger
