from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ghostlink.domain.models import CheckResult, SavedLinkRecord, utc_now
from ghostlink.services.check_service import inspect_link
from ghostlink.services.find_service import walk_symlinks
from ghostlink.services.registry_service import RegistryService


@dataclass(slots=True)
class IndexCandidate:
    destination: Path
    actual_target: Path
    status: str
    proposed_name: str
    state: str
    managed_name: str | None = None
    expected_target: Path | None = None


def normalized_path(path: Path) -> Path:
    return path.expanduser().absolute()


def resolved_link_target(destination: Path) -> Path:
    raw = Path(os.readlink(destination))
    return (destination.parent / raw).resolve(strict=False) if not raw.is_absolute() else raw.expanduser().absolute()


def expected_source(record: dict[str, Any]) -> Path:
    value = Path(str(record.get("source", ""))).expanduser()
    if value.is_absolute():
        return value
    destination = normalized_path(Path(str(record.get("destination", ""))))
    return (destination.parent / value).resolve(strict=False)


def observe_saved_link(record: dict[str, Any]) -> dict[str, Any]:
    destination = normalized_path(Path(str(record["destination"])))
    expected = expected_source(record)
    result = inspect_link(destination, expected_target=expected, label=str(record["name"]))
    return {
        **record,
        "observed": {
            "status": result.status,
            "actual_target": str(result.actual_target) if result.actual_target is not None else None,
            "expected_target": str(result.expected_target) if result.expected_target is not None else None,
            "message": result.message,
        },
    }


def observe_saved_links(registry: RegistryService) -> list[dict[str, Any]]:
    return [observe_saved_link(record) for record in registry.list_records("links")]


def derive_name(destination: Path, used_names: set[str]) -> str:
    base = destination.name or "link"
    candidate = base
    suffix = 2
    while candidate in used_names:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used_names.add(candidate)
    return candidate


def plan_index(root: Path, registry: RegistryService, max_depth: int | None = None) -> list[IndexCandidate]:
    records = registry.list_records("links")
    used_names = {str(record["name"]) for record in registry.list_records()}
    by_destination = {
        normalized_path(Path(str(record["destination"]))): record
        for record in records
    }
    candidates: list[IndexCandidate] = []
    discovered = sorted(walk_symlinks(root, max_depth=max_depth), key=lambda item: str(item.link_path))
    for found in discovered:
        destination = normalized_path(found.link_path)
        actual = resolved_link_target(destination)
        status = "broken" if found.broken else "ok"
        existing = by_destination.get(destination)
        if existing is None:
            candidates.append(
                IndexCandidate(
                    destination=destination,
                    actual_target=actual,
                    status=status,
                    proposed_name=derive_name(destination, used_names),
                    state="new",
                )
            )
            continue
        expected = expected_source(existing)
        state = "managed" if actual.resolve(strict=False) == expected.resolve(strict=False) else "conflict"
        candidates.append(
            IndexCandidate(
                destination=destination,
                actual_target=actual,
                status=status if state == "managed" else "mismatch",
                proposed_name=str(existing["name"]),
                state=state,
                managed_name=str(existing["name"]),
                expected_target=expected,
            )
        )
    return sorted(candidates, key=lambda item: str(item.destination))


def save_index_candidate(candidate: IndexCandidate, registry: RegistryService) -> SavedLinkRecord:
    now = utc_now()
    record = SavedLinkRecord(
        name=candidate.proposed_name,
        source=str(candidate.actual_target),
        destination=str(candidate.destination),
        last_checked_at=now,
        last_status=candidate.status,
    )
    return registry.save_link(record)


def adopt_index_candidate(candidate: IndexCandidate, registry: RegistryService) -> dict[str, Any]:
    if not candidate.managed_name:
        raise ValueError("cannot adopt an unmanaged candidate")
    status = "broken" if not candidate.actual_target.exists() else "ok"
    return registry.adopt_link_source(candidate.managed_name, candidate.actual_target, status)


def unhealthy_registry_candidates(registry: RegistryService) -> list[tuple[dict[str, Any], CheckResult]]:
    candidates: list[tuple[dict[str, Any], CheckResult]] = []
    for record in registry.list_records("links"):
        result = inspect_link(
            normalized_path(Path(str(record["destination"]))),
            expected_target=expected_source(record),
            label=str(record["name"]),
        )
        if result.status != "ok":
            candidates.append((record, result))
    return candidates
