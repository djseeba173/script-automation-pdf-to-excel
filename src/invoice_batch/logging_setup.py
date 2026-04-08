from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from invoice_batch.config import AppConfig


def configure_logging(config: AppConfig) -> logging.Logger:
    config.paths.log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("invoice_batch")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        config.paths.log_dir / "batch.log",
        maxBytes=2_000_000,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger
