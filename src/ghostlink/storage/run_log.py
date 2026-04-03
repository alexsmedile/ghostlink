from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ghostlink.domain.models import utc_now


RUN_LOG_SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return utc_now()


@dataclass(slots=True)
class RunLogEntry:
    action: str
    status: str
    name: str | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)
    schema_version: int = RUN_LOG_SCHEMA_VERSION


def default_run_log_path() -> Path:
    return Path.home() / ".local" / "state" / "ghostlink" / "runs.jsonl"


def append_run_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    item = {"timestamp": utc_now(), **payload}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, sort_keys=True))
        handle.write("\n")


def append_run_log_entry(payload: dict[str, Any], path: Path | None = None) -> RunLogEntry:
    store_path = path or default_run_log_path()
    entry = RunLogEntry(
        action=str(payload.get("action", payload.get("job_type", "unknown"))),
        status=str(payload.get("status", "ok")),
        name=payload.get("name"),
        message=payload.get("message"),
        details=dict(payload.get("details", {})),
    )
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True))
        handle.write("\n")
    return entry


def read_run_log_entries(path: Path | None = None) -> list[RunLogEntry]:
    store_path = path or default_run_log_path()
    if not store_path.exists():
        return []
    entries: list[RunLogEntry] = []
    for line in store_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        entries.append(RunLogEntry(**payload))
    return entries
