from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ghostlink.domain.models import utc_now


RUN_LOG_SCHEMA_VERSION = 2


class RunLogFormatError(ValueError):
    pass


def utc_now_iso() -> str:
    return utc_now()


@dataclass(slots=True)
class RunLogEntry:
    action: str
    status: str
    name: str | None = None
    record_type: str | None = None
    source: str | None = None
    destination: str | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)
    schema_version: int = RUN_LOG_SCHEMA_VERSION


def default_run_log_path() -> Path:
    return Path.home() / ".local" / "state" / "ghostlink" / "runs.jsonl"


def append_run_log(path: Path, payload: dict[str, Any]) -> None:
    append_run_log_entry(payload, path=path)


def append_run_log_entry(payload: dict[str, Any], path: Path | None = None) -> RunLogEntry:
    store_path = path or default_run_log_path()
    entry = normalize_run_log_payload(payload)
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), sort_keys=True))
        handle.write("\n")
    return entry


def normalize_run_log_payload(payload: dict[str, Any]) -> RunLogEntry:
    known = {
        "action",
        "status",
        "name",
        "record_type",
        "source",
        "destination",
        "message",
        "details",
        "timestamp",
        "schema_version",
    }
    action = str(payload.get("action") or payload.get("job_type") or "unknown")
    raw_errors = payload.get("errors")
    status = str(payload.get("status") or ("error" if raw_errors else "ok"))
    details = dict(payload.get("details") or {})
    for key, value in payload.items():
        if key not in known and key != "job_type":
            details[key] = value
    return RunLogEntry(
        action=action,
        status=status,
        name=str(payload["name"]) if payload.get("name") is not None else None,
        record_type=str(payload["record_type"]) if payload.get("record_type") is not None else None,
        source=str(payload["source"]) if payload.get("source") is not None else None,
        destination=str(payload["destination"]) if payload.get("destination") is not None else None,
        message=str(payload["message"]) if payload.get("message") is not None else None,
        details=details,
        timestamp=str(payload.get("timestamp") or utc_now_iso()),
        schema_version=RUN_LOG_SCHEMA_VERSION,
    )


def read_run_log_entries(path: Path | None = None) -> list[RunLogEntry]:
    store_path = path or default_run_log_path()
    if not store_path.exists():
        return []
    entries: list[RunLogEntry] = []
    for line_no, line in enumerate(store_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise RunLogFormatError(f"invalid run-log JSON on line {line_no}: {error.msg}") from error
        if not isinstance(payload, dict):
            raise RunLogFormatError(f"invalid run-log entry on line {line_no}: expected object")
        entries.append(normalize_run_log_payload(payload))
    return entries


def write_run_log_entries(entries: list[RunLogEntry], path: Path | None = None) -> None:
    store_path = path or default_run_log_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=store_path.parent) as handle:
        for entry in entries:
            handle.write(json.dumps(asdict(entry), sort_keys=True))
            handle.write("\n")
        tmp_path = Path(handle.name)
    tmp_path.replace(store_path)
