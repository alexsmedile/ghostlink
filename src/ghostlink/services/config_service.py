from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ghostlink.domain.models import ConflictPolicy, LinkSpec, SavedLinkRecord, SavedSyncRecord, SyncMode, SyncSpec
from ghostlink.domain.paths import expand_path, normalize_destination


RELATION_SET_SCHEMA_VERSION = 1


def relation_set_template(
    profile_name: str,
    links: list[dict[str, Any]],
    syncs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": RELATION_SET_SCHEMA_VERSION,
        "profiles": {
            profile_name: {
                "links": links,
                "syncs": syncs or [],
            }
        },
    }


def export_relation_set(
    link_records: list[dict[str, Any]],
    output_path: Path,
    profile_name: str = "default",
    relative: bool = False,
    sync_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    base_dir = output_path.parent.resolve()
    links: list[dict[str, Any]] = []
    for record in link_records:
        source = str(record["source"])
        destination = str(record["destination"])
        if relative:
            source = os.path.relpath(source, start=base_dir)
            destination = os.path.relpath(destination, start=base_dir)
        links.append(
            {
                "name": record["name"],
                "source": source,
                "destination": destination,
                "conflict_policy": record.get("conflict_policy", ConflictPolicy.ASK.value),
            }
        )
    syncs: list[dict[str, Any]] = []
    for record in sync_records or []:
        source = str(record["source"])
        destination = str(record["destination"])
        if relative:
            source = os.path.relpath(source, start=base_dir)
            destination = os.path.relpath(destination, start=base_dir)
        syncs.append(
            {
                "name": record["name"],
                "source": source,
                "destination": destination,
                "mode": record.get("mode", SyncMode.ONE_WAY.value),
            }
        )
    payload = relation_set_template(profile_name, links, syncs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def load_relation_set(file_path: Path) -> dict[str, Any]:
    payload = json.loads(file_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != RELATION_SET_SCHEMA_VERSION:
        raise ValueError(f"unsupported relation set schema_version: {payload.get('schema_version')}")
    if "profiles" not in payload or not isinstance(payload["profiles"], dict):
        raise ValueError("relation set must include a profiles object")
    return payload


def list_profiles(payload: dict[str, Any]) -> list[str]:
    return sorted(payload.get("profiles", {}).keys())


def load_profile_specs(file_path: Path, profile_name: str = "default", relative_links: bool = False) -> list[tuple[str | None, LinkSpec]]:
    payload = load_relation_set(file_path)
    profiles = payload.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"profile not found: {profile_name}")
    links = profiles[profile_name].get("links", [])
    specs: list[tuple[str | None, LinkSpec]] = []
    for index, item in enumerate(links, start=1):
        source_path = expand_path(str(item["source"]), base_dir=file_path.parent)
        destination_path = normalize_destination(
            source_path,
            str(item["destination"]),
            None,
            base_dir=file_path.parent,
        )
        spec = LinkSpec(
            source=_relative_source(source_path, destination_path) if relative_links else source_path,
            destination=destination_path,
            conflict_policy=str(item.get("conflict_policy", ConflictPolicy.ASK.value)),
            line_no=index,
        )
        specs.append((item.get("name"), spec))
    return specs


def load_profile_syncs(file_path: Path, profile_name: str = "default") -> list[tuple[str, SyncSpec]]:
    payload = load_relation_set(file_path)
    profiles = payload.get("profiles", {})
    if profile_name not in profiles:
        raise ValueError(f"profile not found: {profile_name}")
    syncs = profiles[profile_name].get("syncs", [])
    specs: list[tuple[str, SyncSpec]] = []
    for item in syncs:
        specs.append(
            (
                str(item["name"]),
                SyncSpec(
                    source=expand_path(str(item["source"]), base_dir=file_path.parent),
                    destination=expand_path(str(item["destination"]), base_dir=file_path.parent),
                    mode=str(item.get("mode", SyncMode.ONE_WAY.value)),
                ),
            )
        )
    return specs


def saved_link_record_to_export(record: dict[str, Any]) -> dict[str, Any]:
    model = SavedLinkRecord(
        name=str(record["name"]),
        source=str(record["source"]),
        destination=str(record["destination"]),
        conflict_policy=str(record.get("conflict_policy", ConflictPolicy.ASK.value)),
    )
    return {
        "name": model.name,
        "source": model.source,
        "destination": model.destination,
        "conflict_policy": model.conflict_policy,
    }


def saved_sync_record_to_export(record: dict[str, Any]) -> dict[str, Any]:
    model = SavedSyncRecord(
        name=str(record["name"]),
        source=str(record["source"]),
        destination=str(record["destination"]),
        mode=str(record.get("mode", SyncMode.ONE_WAY.value)),
    )
    return {
        "name": model.name,
        "source": model.source,
        "destination": model.destination,
        "mode": model.mode,
    }


def _relative_source(source: Path, destination: Path) -> Path:
    return Path(os.path.relpath(source, start=destination.parent))
