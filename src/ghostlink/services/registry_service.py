from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from ghostlink.domain.models import SavedLinkRecord, SavedSyncRecord, ScheduleSpec, utc_now
from ghostlink.domain.validation import validate_saved_name
from ghostlink.storage.registry import (
    default_registry_path,
    load_registry,
    record_to_dict,
    save_registry,
)


class RegistryService:
    def __init__(self, registry_path: Path | None = None) -> None:
        self.registry_path = registry_path or default_registry_path()

    def _load(self) -> dict[str, Any]:
        return load_registry(self.registry_path)

    def list_records(self, kind: str | None = None) -> list[dict[str, Any]]:
        data = self._load()
        groups = [kind] if kind else ["links", "syncs", "schedules"]
        results: list[dict[str, Any]] = []
        for group in groups:
            for name, record in data.get(group, {}).items():
                results.append({"name": name, **record})
        return sorted(results, key=lambda item: (item.get("type", ""), item["name"]))

    def get_record(self, name: str) -> dict[str, Any] | None:
        data = self._load()
        for group in ("links", "syncs", "schedules"):
            if name in data.get(group, {}):
                return {"name": name, **data[group][name]}
        return None

    def save_link(self, record: SavedLinkRecord) -> SavedLinkRecord:
        ok, reason = validate_saved_name(record.name)
        if not ok:
            raise ValueError(reason)
        data = self._load()
        if record.name in data["links"] or record.name in data["syncs"] or record.name in data["schedules"]:
            raise ValueError(f"record already exists: {record.name}")
        data["links"][record.name] = record_to_dict(record)
        save_registry(self.registry_path, data)
        return record

    def save_sync(self, record: SavedSyncRecord) -> SavedSyncRecord:
        ok, reason = validate_saved_name(record.name)
        if not ok:
            raise ValueError(reason)
        data = self._load()
        if record.name in data["links"] or record.name in data["syncs"] or record.name in data["schedules"]:
            raise ValueError(f"record already exists: {record.name}")
        data["syncs"][record.name] = record_to_dict(record)
        save_registry(self.registry_path, data)
        return record

    def save_schedule(self, spec: ScheduleSpec, job_type: str = "schedule") -> None:
        data = self._load()
        existing = data["schedules"].get(spec.name, {})
        data["schedules"][spec.name] = {
            "type": job_type,
            "job_name": spec.name,
            "every": spec.interval_seconds,
            "backend": spec.backend,
            "created_at": existing.get("created_at", spec.created_at),
            "updated_at": utc_now(),
            "last_status": existing.get("last_status"),
            "last_run_at": existing.get("last_run_at"),
            "last_exit_code": existing.get("last_exit_code"),
            "last_message": existing.get("last_message"),
        }
        save_registry(self.registry_path, data)

    def remove(self, name: str) -> bool:
        return self.remove_from_group(name)

    def remove_from_group(self, name: str, group: str | None = None) -> bool:
        data = self._load()
        removed = False
        groups = (group,) if group else ("links", "syncs", "schedules")
        for group_name in groups:
            if name in data[group_name]:
                del data[group_name][name]
                removed = True
        if removed:
            save_registry(self.registry_path, data)
        return removed

    def update_link_status(self, name: str, status: str) -> None:
        data = self._load()
        if name not in data["links"]:
            return
        existing = data["links"][name]
        existing["last_checked_at"] = utc_now()
        existing["last_status"] = status
        existing["updated_at"] = utc_now()
        save_registry(self.registry_path, data)

    def update_sync_status(self, name: str, status: str, mark_ran: bool = False) -> None:
        data = self._load()
        if name not in data["syncs"]:
            return
        existing = data["syncs"][name]
        now = utc_now()
        existing["last_checked_at"] = now
        existing["last_status"] = status
        if mark_ran:
            existing["last_run_at"] = now
        existing["updated_at"] = now
        save_registry(self.registry_path, data)

    def update_schedule_status(
        self,
        name: str,
        status: str,
        *,
        exit_code: int | None = None,
        message: str | None = None,
        mark_ran: bool = False,
    ) -> None:
        data = self._load()
        if name not in data["schedules"]:
            return
        existing = data["schedules"][name]
        now = utc_now()
        existing["last_status"] = status
        if mark_ran:
            existing["last_run_at"] = now
        if exit_code is not None:
            existing["last_exit_code"] = exit_code
        if message is not None:
            existing["last_message"] = message
        existing["updated_at"] = now
        save_registry(self.registry_path, data)

    def rename(self, old_name: str, new_name: str) -> bool:
        ok, reason = validate_saved_name(new_name)
        if not ok:
            raise ValueError(reason)
        data = self._load()
        for group in ("links", "syncs", "schedules"):
            if old_name in data[group]:
                if new_name in data[group]:
                    raise ValueError(f"record already exists: {new_name}")
                data[group][new_name] = replace_name(data[group].pop(old_name), new_name)
                save_registry(self.registry_path, data)
                return True
        return False


def replace_name(record: dict[str, Any], new_name: str) -> dict[str, Any]:
    record = dict(record)
    record["name"] = new_name
    record["updated_at"] = utc_now()
    return record
