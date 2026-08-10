"""Structured JSON logger for the Parrot Trips backend."""

from __future__ import annotations

import json
import logging
import sys


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict = {"nivel": record.levelname, "mensagem": record.getMessage()}
        if hasattr(record, "extra"):
            data.update(record.extra)
        return json.dumps(data, ensure_ascii=False, default=str)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_JSONFormatter())

_logger = logging.getLogger("parrot")
_logger.setLevel(logging.INFO)
_logger.addHandler(_handler)
_logger.propagate = False


def log(evento: str, **kwargs: object) -> None:
    _logger.info("", extra={"evento": evento, **kwargs})


def log_erro(evento: str, **kwargs: object) -> None:
    _logger.error("", extra={"evento": evento, **kwargs})
