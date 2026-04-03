from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


MACOS_SKIP_PREFIXES: tuple[str, ...] = (
    "/System/Volumes/VM",
    "/System/Volumes/Preboot",
    "/System/Volumes/Recovery",
    "/private/var/vm",
    "/private/var/db/dslocal",
    "/dev",
    "/net",
    "/home",
)


def expand_path(raw: str, base_dir: Optional[Path] = None) -> Path:
    value = os.path.expandvars(os.path.expanduser(raw.strip()))
    path = Path(value)
    if path.is_absolute():
        return path
    root = base_dir or Path.cwd()
    return (root / path).resolve()


def normalize_path(raw: str | Path, cwd: str | Path | None = None) -> Path:
    value = os.path.expandvars(os.path.expanduser(str(raw).strip()))
    path = Path(value)
    if path.is_absolute():
        return path
    root = Path(cwd) if cwd else Path.cwd()
    return (root / path).absolute()


def normalize_path_text(raw: str, cwd: str | Path | None = None) -> str:
    return str(normalize_path(raw, cwd=cwd))


def normalize_destination(
    source: Path,
    dest_input: str,
    link_name: Optional[str],
    base_dir: Optional[Path] = None,
) -> Path:
    destination = expand_path(dest_input, base_dir=base_dir)
    if destination.exists() and destination.is_dir():
        final_name = link_name.strip() if link_name and link_name.strip() else source.name
        return destination / final_name
    if dest_input.endswith("/"):
        final_name = link_name.strip() if link_name and link_name.strip() else source.name
        return destination / final_name
    return destination


def same_path(a: Path, b: Path) -> bool:
    a = Path(a)
    b = Path(b)
    try:
        return a.resolve() == b.resolve()
    except FileNotFoundError:
        return a.absolute() == b.absolute()


def is_within_directory(path: str | Path, directory: str | Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(directory).resolve())
        return True
    except ValueError:
        return False
