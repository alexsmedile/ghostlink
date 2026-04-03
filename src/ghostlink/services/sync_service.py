from __future__ import annotations

import filecmp
import shutil
from pathlib import Path

from ghostlink.domain.models import SyncDiffEntry, SyncPlan, SyncRunResult, SyncSpec
from ghostlink.domain.validation import validate_sync_spec


def _iter_paths(root: Path, ignore_names: tuple[str, ...]) -> dict[Path, Path]:
    items: dict[Path, Path] = {}
    for path in root.rglob("*"):
        if _should_ignore(path, ignore_names):
            continue
        if path.is_dir():
            continue
        items[path.relative_to(root)] = path
    return items


def _should_ignore(path: Path, ignore_names: tuple[str, ...]) -> bool:
    if any(part in ignore_names for part in path.parts):
        return True
    if any(part.endswith(".egg-info") for part in path.parts):
        return True
    if path.suffix == ".pyc":
        return True
    return False


def build_sync_plan(spec: SyncSpec) -> SyncPlan:
    ok, reason = validate_sync_spec(spec)
    if not ok:
        raise ValueError(reason)
    source_files = _iter_paths(spec.source, spec.ignore_names)
    destination_files = _iter_paths(spec.destination, spec.ignore_names) if spec.destination.exists() else {}
    entries: list[SyncDiffEntry] = []
    for relative_path, source_path in sorted(source_files.items()):
        destination_path = spec.destination / relative_path
        if relative_path not in destination_files:
            entries.append(
                SyncDiffEntry(relative_path, "copy", source_path, destination_path, "missing on destination")
            )
        elif not filecmp.cmp(source_path, destination_files[relative_path], shallow=False):
            entries.append(
                SyncDiffEntry(relative_path, "update", source_path, destination_path, "content changed")
            )
        else:
            entries.append(
                SyncDiffEntry(relative_path, "skip", source_path, destination_path, "already in sync")
            )
    for relative_path, destination_path in sorted(destination_files.items()):
        if relative_path not in source_files:
            entries.append(
                SyncDiffEntry(relative_path, "extra", None, destination_path, "exists only on destination")
            )
    return SyncPlan(spec=spec, entries=entries)


def run_sync_plan(plan: SyncPlan, dry_run: bool = False) -> SyncRunResult:
    applied = 0
    skipped = 0
    errors: list[str] = []
    if not plan.spec.destination.exists() and not dry_run:
        plan.spec.destination.mkdir(parents=True, exist_ok=True)
    for entry in plan.entries:
        if entry.action not in {"copy", "update"}:
            skipped += 1
            continue
        assert entry.source is not None
        assert entry.destination is not None
        if dry_run:
            skipped += 1
            continue
        try:
            entry.destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry.source, entry.destination)
            applied += 1
        except OSError as error:
            errors.append(f"{entry.relative_path}: {error}")
    return SyncRunResult(plan=plan, applied=applied, skipped=skipped, errors=errors)
