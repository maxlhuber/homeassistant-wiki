"""Bounded operational events: never accept arbitrary payloads or subprocess output."""
from __future__ import annotations

import datetime as dt
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import threading


class OperationLog:
    def __init__(self, directory: Path, max_bytes: int = 256_000, backups: int = 3):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "operations.jsonl"
        self.backups = backups
        self.lock = threading.Lock()
        self.logger = logging.Logger(f"hauswiki.operations.{id(self)}", logging.INFO)
        handler = RotatingFileHandler(self.path, maxBytes=max_bytes, backupCount=backups, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(console)

    def emit(self, event: str, message: str, level: str = "info", **fields):
        # Callers use fixed messages. Exceptions, credentials, names and CLI output
        # are deliberately excluded from the structured event schema.
        allowed = {"run_id", "phase", "duration_seconds", "version", "outcome", "backup_date", "source", "reason", "error_type"}
        entry = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "level": level, "event": event, "message": message}
        entry.update({key: value for key, value in fields.items() if key in allowed})
        with self.lock:
            self.logger.info(json.dumps(entry, ensure_ascii=False))

    def read(self, limit: int = 200):
        entries = []
        with self.lock:
            for path in [self.path.with_name(self.path.name + f".{i}") for i in range(self.backups, 0, -1)] + [self.path]:
                try:
                    for line in path.read_text(encoding="utf-8").splitlines():
                        try:
                            entries.append(json.loads(line))
                        except ValueError:
                            continue
                except OSError:
                    continue
        return {"entries": entries[-max(1, min(int(limit), 1000)):]}
