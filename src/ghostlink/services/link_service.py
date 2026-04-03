from __future__ import annotations

import csv
import os
import shlex
from pathlib import Path
from typing import Optional

from ghostlink.domain.models import ConflictPolicy, LinkOperationResult, LinkSpec
from ghostlink.domain.paths import expand_path
from ghostlink.domain.validation import validate_link_spec


def backup_path(path: Path) -> Path:
    index = 1
    while True:
        candidate = path.with_name(f"{path.name}.backup-{index}")
        if not candidate.exists():
            return candidate
        index += 1


def remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        raise IsADirectoryError(
            f"refusing to remove existing directory automatically: {path}. "
            "Use backup mode, skip mode, or remove it manually."
        )
    path.unlink(missing_ok=True)


def create_symlink(
    spec: LinkSpec,
    on_conflict: str = ConflictPolicy.ASK.value,
    dry_run: bool = False,
    assume_yes: bool = False,
    conflict_choice: Optional[str] = None,
) -> LinkOperationResult:
    ok, reason = validate_link_spec(spec)
    if not ok:
        return LinkOperationResult(spec, "error", reason)

    destination = spec.destination
    if destination.exists() or destination.is_symlink():
        if on_conflict == ConflictPolicy.SKIP.value:
            return LinkOperationResult(spec, "skipped", f"destination exists: {destination}")
        if on_conflict == ConflictPolicy.OVERWRITE.value or (
            on_conflict == ConflictPolicy.ASK.value and assume_yes
        ):
            if dry_run:
                return LinkOperationResult(spec, "dry-run", f"would remove existing destination and create symlink: {destination} -> {spec.source}")
            try:
                remove_existing(destination)
            except OSError as error:
                return LinkOperationResult(spec, "error", str(error))
        elif on_conflict == ConflictPolicy.BACKUP.value:
            backup = backup_path(destination)
            if dry_run:
                return LinkOperationResult(spec, "dry-run", f"would move existing destination to {backup} and create symlink: {destination} -> {spec.source}")
            destination.rename(backup)
        elif conflict_choice == "s":
            return LinkOperationResult(spec, "skipped", f"destination exists: {destination}")
        elif conflict_choice == "o":
            if dry_run:
                return LinkOperationResult(spec, "dry-run", f"would remove existing destination and create symlink: {destination} -> {spec.source}")
            try:
                remove_existing(destination)
            except OSError as error:
                return LinkOperationResult(spec, "error", str(error))
        elif conflict_choice == "b":
            backup = backup_path(destination)
            if dry_run:
                return LinkOperationResult(spec, "dry-run", f"would move existing destination to {backup} and create symlink: {destination} -> {spec.source}")
            destination.rename(backup)
        else:
            return LinkOperationResult(spec, "error", f"destination exists: {destination}")

    if dry_run:
        return LinkOperationResult(spec, "dry-run", f"would create symlink: {destination} -> {spec.source}")

    try:
        os.symlink(spec.source, destination)
    except OSError as error:
        return LinkOperationResult(spec, "error", f"failed to create symlink: {error}")
    return LinkOperationResult(spec, "created", f"{destination} -> {spec.source}")


def strip_outer_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def parse_bulk_line(line: str, separator: str) -> tuple[str, str] | None:
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    if separator in text:
        left, right = text.split(separator, 1)
        return strip_outer_quotes(left), strip_outer_quotes(right)
    try:
        parts = next(csv.reader([text], skipinitialspace=True))
        if len(parts) == 2:
            return strip_outer_quotes(parts[0]), strip_outer_quotes(parts[1])
    except Exception:
        pass
    try:
        parts = shlex.split(text)
        if len(parts) == 2:
            return parts[0], parts[1]
    except Exception:
        pass
    raise ValueError(
        f"could not parse line. Use '{separator}' or two CSV columns or two shell-like paths."
    )


def load_bulk_specs(file_path: Path, separator: str = "->") -> list[LinkSpec]:
    specs: list[LinkSpec] = []
    base_dir = file_path.parent.resolve()
    with file_path.open("r", encoding="utf-8") as handle:
        for index, raw_line in enumerate(handle, start=1):
            parsed = parse_bulk_line(raw_line, separator)
            if parsed is None:
                continue
            source_raw, destination_raw = parsed
            specs.append(
                LinkSpec(
                    source=expand_path(source_raw, base_dir=base_dir),
                    destination=expand_path(destination_raw, base_dir=base_dir),
                    line_no=index,
                )
            )
    return specs
