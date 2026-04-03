from __future__ import annotations

import os
from pathlib import Path

from ghostlink.domain.models import CheckResult
from ghostlink.services.find_service import walk_symlinks


def inspect_link(path: Path, expected_target: Path | None = None, label: str | None = None) -> CheckResult:
    if not path.exists() and not path.is_symlink():
        return CheckResult(
            label=label or path.name,
            path=path,
            expected_target=expected_target,
            actual_target=None,
            status="missing",
            message=f"missing link path: {path}",
        )
    if not path.is_symlink():
        return CheckResult(
            label=label or path.name,
            path=path,
            expected_target=expected_target,
            actual_target=None,
            status="not-link",
            message=f"path is not a symlink: {path}",
        )
    target = Path(os.readlink(path))
    resolved_target = (path.parent / target).resolve() if not target.is_absolute() else target
    if not resolved_target.exists():
        return CheckResult(
            label=label or path.name,
            path=path,
            expected_target=expected_target,
            actual_target=target,
            status="broken",
            message=f"broken symlink: {path} -> {target}",
        )
    if expected_target is not None and resolved_target != expected_target.resolve():
        return CheckResult(
            label=label or path.name,
            path=path,
            expected_target=expected_target,
            actual_target=resolved_target,
            status="mismatch",
            message=f"link points to {resolved_target}, expected {expected_target}",
        )
    return CheckResult(
        label=label or path.name,
        path=path,
        expected_target=expected_target,
        actual_target=resolved_target,
        status="ok",
        message=f"ok: {path} -> {resolved_target}",
    )


def inspect_tree(root: Path, broken_only: bool = False, max_depth: int | None = None) -> list[CheckResult]:
    results: list[CheckResult] = []
    for item in walk_symlinks(root, max_depth=max_depth):
        status = inspect_link(item.link_path)
        if broken_only and status.status != "broken":
            continue
        results.append(status)
    return results
