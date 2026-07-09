"""Centralized logging configuration."""

import logging
import sys
from pathlib import Path


def setup_logging(log_path: str, level: int = logging.INFO) -> None:
    """Configure application-wide logging."""
    log_dir = Path(log_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if not root_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
