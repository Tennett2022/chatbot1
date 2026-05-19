import logging
import sys
import time
from contextlib import contextmanager
from typing import Optional

from app.config import settings


def get_logger(name: str) -> logging.Logger:
    """Return a structured JSON logger for the given module name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s",'
            ' "module": "%(name)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        logger.propagate = False  # avoid duplicate logs from root logger
    return logger


@contextmanager
def log_duration(logger: logging.Logger, label: str, **extra):
    """Context manager that logs the wall-clock duration of a block."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        parts = " ".join(f"{k}={v}" for k, v in extra.items())
        logger.info(f"{label} elapsed={elapsed_ms}ms {parts}".strip())
