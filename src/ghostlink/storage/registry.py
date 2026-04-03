from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ghostlink.domain.models import SavedLinkRecord, SavedSyncRecord


REGISTRY_SCHEMA_VERSION = 1
SCHEMA_VERSION = REGISTRY_SCHEMA_VERSION


class RegistryError(Exception):
    pass


class RegistryFormatError(RegistryError):
    pass


class RegistryNotFoundError(RegistryError):
    pass


class RegistryConflictError(RegistryError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RegistryDocument:
    def __init__(self, records: list[dict[str, Any]] | None = None, schema_version: int = REGISTRY_SCHEMA_VERSION):
        self.records = records or []
        self.schema_version = schema_version


class RegistryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_registry_path()

    def list_records(self) -> list[dict[str, Any]]:
        return list_registry_records(self.path)

    def get_record(self, name: str, record_type: str | None = None) -> dict[str, Any] | None:
        for record in self.list_records():
            if record["name"] == name and (record_type is None or record.get("type") == record_type):
                return record
        return None


def default_registry_path() -> Path:
    return Path.home() / ".config" / "ghostlink" / "registry.json"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_parent(path)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp_path = Path(handle.name)
    tmp_path.replace(path)


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "links": {}, "syncs": {}, "schedules": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if "schema_version" not in data:
        data["schema_version"] = 1
    data.setdefault("links", {})
    data.setdefault("syncs", {})
    data.setdefault("schedules", {})
    return data


def save_registry(path: Path, data: dict[str, Any]) -> None:
    data["schema_version"] = SCHEMA_VERSION
    atomic_write_json(path, data)


def record_to_dict(record: SavedLinkRecord | SavedSyncRecord) -> dict[str, Any]:
    return asdict(record)


def _flatten(data: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for group in ("links", "syncs", "schedules"):
        for name, record in data.get(group, {}).items():
            records.append({"name": name, **record})
    return records


def _group(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped = {"schema_version": REGISTRY_SCHEMA_VERSION, "links": {}, "syncs": {}, "schedules": {}}
    for record in records:
        record = dict(record)
        name = record.pop("name")
        record_type = record.get("type")
        if record_type == "sync":
            grouped["syncs"][name] = record
        elif record_type == "schedule":
            grouped["schedules"][name] = record
        else:
            grouped["links"][name] = record
    return grouped


def load_registry_document(path: Path | None = None) -> RegistryDocument:
    store_path = path or default_registry_path()
    data = load_registry(store_path)
    return RegistryDocument(records=_flatten(data), schema_version=data.get("schema_version", REGISTRY_SCHEMA_VERSION))


def save_registry_document(document: RegistryDocument, path: Path | None = None) -> RegistryDocument:
    store_path = path or default_registry_path()
    save_registry(store_path, _group(document.records))
    return load_registry_document(store_path)


def list_registry_records(path: Path | None = None) -> list[dict[str, Any]]:
    return load_registry_document(path).records


def upsert_registry_record(record: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    records = list_registry_records(path)
    remaining = [item for item in records if not (item["name"] == record["name"] and item.get("type") == record.get("type"))]
    remaining.append(record)
    save_registry_document(RegistryDocument(records=remaining), path)
    return record


def update_registry_record(
    name: str,
    changes: dict[str, Any],
    path: Path | None = None,
    record_type: str | None = None,
) -> dict[str, Any]:
    records = list_registry_records(path)
    for record in records:
        if record["name"] == name and (record_type is None or record.get("type") == record_type):
            record.update(changes)
            save_registry_document(RegistryDocument(records=records), path)
            return record
    raise RegistryNotFoundError(name)


def remove_registry_record(name: str, path: Path | None = None, record_type: str | None = None) -> bool:
    records = list_registry_records(path)
    filtered = [record for record in records if not (record["name"] == name and (record_type is None or record.get("type") == record_type))]
    if len(filtered) == len(records):
        return False
    save_registry_document(RegistryDocument(records=filtered), path)
    return True
