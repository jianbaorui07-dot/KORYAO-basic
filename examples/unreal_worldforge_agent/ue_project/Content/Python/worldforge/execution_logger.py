"""Structured logging for WorldForge runs."""

from __future__ import annotations

import json
import time
import traceback
from pathlib import Path


class ExecutionLogger:
    def __init__(self, ledger_dir: str | Path):
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.text_path = self.ledger_dir / "execution_log.txt"
        self.jsonl_path = self.ledger_dir / "execution_log.jsonl"

    def event(self, level: str, message: str, **fields) -> dict:
        record = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "level": level,
            "message": message,
        }
        record.update(fields)
        with self.text_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{record['time']}] {level}: {message} {fields}\n")
        with self.jsonl_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def exception(self, message: str, exc: BaseException) -> dict:
        return self.event("error", message, error=str(exc), traceback=traceback.format_exc())
