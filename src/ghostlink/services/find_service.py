from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from ghostlink.domain.models import FindResult
from ghostlink.domain.paths import MACOS_SKIP_PREFIXES


def walk_symlinks(
    root: Path,
    max_depth: int | None = None,
    skip_prefixes: tuple[str, ...] = MACOS_SKIP_PREFIXES,
) -> Generator[FindResult, None, None]:
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        try:
            entries = list(os.scandir(current))
        except PermissionError:
            continue
        for entry in entries:
            if entry.is_symlink():
                target = Path(os.readlink(entry.path))
                broken = not os.path.exists(entry.path)
                yield FindResult(link_path=Path(entry.path), target=target, broken=broken)
            elif entry.is_dir(follow_symlinks=False):
                absolute = os.path.abspath(entry.path)
                if any(absolute.startswith(prefix) for prefix in skip_prefixes):
                    continue
                if max_depth is not None and depth + 1 > max_depth:
                    continue
                stack.append((Path(entry.path), depth + 1))
