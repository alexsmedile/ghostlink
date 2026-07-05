from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from ghostlink.storage.run_log import RunLogEntry, read_run_log_entries, write_run_log_entries


def parse_duration(value: str) -> timedelta:
    if len(value) < 2 or not value[:-1].isdigit():
        raise ValueError("duration must look like 30d, 12h, or 4w")
    amount = int(value[:-1])
    unit = value[-1].lower()
    if amount <= 0:
        raise ValueError("duration must be greater than zero")
    factors = {"h": timedelta(hours=amount), "d": timedelta(days=amount), "w": timedelta(weeks=amount)}
    if unit not in factors:
        raise ValueError("duration unit must be h, d, or w")
    return factors[unit]


def parse_before(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("before must be an ISO date or datetime") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def entry_time(entry: RunLogEntry) -> datetime:
    parsed = datetime.fromisoformat(entry.timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def query_history(
    path: Path,
    *,
    limit: int = 50,
    action: str | None = None,
    record_type: str | None = None,
    name: str | None = None,
    since: str | None = None,
) -> list[RunLogEntry]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero")
    entries = read_run_log_entries(path)
    cutoff = datetime.now(timezone.utc) - parse_duration(since) if since else None
    filtered = [
        entry
        for entry in entries
        if (action is None or entry.action == action)
        and (record_type is None or entry.record_type == record_type)
        and (name is None or entry.name == name)
        and (cutoff is None or entry_time(entry) >= cutoff)
    ]
    return sorted(filtered, key=entry_time, reverse=True)[:limit]


def history_cleanup_candidates(
    path: Path,
    *,
    older_than: str | None = None,
    before: str | None = None,
) -> tuple[list[RunLogEntry], list[RunLogEntry]]:
    if bool(older_than) == bool(before):
        raise ValueError("provide exactly one of --older-than or --before")
    cutoff = (
        datetime.now(timezone.utc) - parse_duration(str(older_than))
        if older_than
        else parse_before(str(before))
    )
    entries = read_run_log_entries(path)
    removed = [entry for entry in entries if entry_time(entry) < cutoff]
    retained = [entry for entry in entries if entry_time(entry) >= cutoff]
    return removed, retained


def prune_history(path: Path, retained: list[RunLogEntry]) -> None:
    write_run_log_entries(retained, path)
