"""Structured logging configuration."""

from __future__ import annotations

import json
import logging


class JsonFormatter(logging.Formatter):
    """Very small JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "run_id"):
            payload["run_id"] = record.run_id
        if hasattr(record, "part_number"):
            payload["part_number"] = record.part_number
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once for CLI/API/dashboard use."""

    logger = logging.getLogger()
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level.upper())

