from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ghostlink.domain.models import CheckResult, FindResult, LinkOperationResult, SyncPlan
from ghostlink.domain.results import OperationSummary


def render_link_result(result: LinkOperationResult) -> str:
    prefix = {
        "created": "[OK]",
        "dry-run": "[DRY]",
        "skipped": "[SKIP]",
        "error": "[ERR]",
    }.get(result.status, "[INFO]")
    line = f"{prefix} {result.message}"
    if result.spec.line_no is not None:
        line = f"line {result.spec.line_no}: {line}"
    return line


def render_create_preview(source: str, destination: str, conflict: str, dry_run: bool) -> str:
    mode = "dry-run" if dry_run else "live"
    return (
        "Review\n"
        f"  source      {source}\n"
        f"  symlink at  {destination}\n"
        f"  conflict    {conflict}\n"
        f"  mode        {mode}"
    )


def render_operation_summary(results: Iterable[LinkOperationResult]) -> str:
    summary = OperationSummary.from_statuses(result.status for result in results)
    return (
        "Summary\n"
        f"  created : {summary.count('created')}\n"
        f"  dry-run : {summary.count('dry-run')}\n"
        f"  skipped : {summary.count('skipped')}\n"
        f"  errors  : {summary.count('error')}"
    )


def render_find_result(result: FindResult) -> str:
    prefix = "[BROKEN]" if result.broken else "[LINK]"
    suffix = "  (target missing)" if result.broken else ""
    managed = f" [{result.managed_name}]" if result.managed_name else ""
    return f"{prefix} {result.link_path} -> {result.target}{managed}{suffix}"


def render_find_summary(results: Iterable[FindResult]) -> str:
    items = list(results)
    broken = sum(item.broken for item in items)
    return f"Summary\n  found  : {len(items)}\n  broken : {broken}"


def render_find_results(results: Iterable[FindResult]) -> str:
    items = list(results)
    lines = [render_find_result(item) for item in items]
    lines.extend(["", render_find_summary(items)])
    return "\n".join(lines)


def render_check_result(result: CheckResult) -> str:
    prefix = {
        "ok": "[OK]",
        "missing": "[MISSING]",
        "broken": "[BROKEN]",
        "mismatch": "[MISMATCH]",
        "not-link": "[NOT-LINK]",
    }.get(result.status, "[INFO]")
    return f"{prefix} {result.label}: {result.message}"


def render_check_summary(results: Iterable[CheckResult]) -> str:
    items = list(results)
    counts = OperationSummary.from_statuses(item.status for item in items)
    return (
        "Summary\n"
        f"  ok       : {counts.count('ok')}\n"
        f"  missing  : {counts.count('missing')}\n"
        f"  broken   : {counts.count('broken')}\n"
        f"  mismatch : {counts.count('mismatch')}\n"
        f"  not-link : {counts.count('not-link')}"
    )


def render_check_results(results: Iterable[CheckResult]) -> str:
    items = list(results)
    lines = [render_check_result(item) for item in items]
    lines.extend(["", render_check_summary(items)])
    return "\n".join(lines)


def render_sync_plan(plan: SyncPlan) -> str:
    lines = [f"Sync plan: {plan.spec.source} -> {plan.spec.destination}"]
    for entry in plan.entries:
        lines.append(f"[{entry.action.upper()}] {entry.relative_path}  {entry.reason}")
    return "\n".join(lines)


def render_sync_diff_summary(plan: SyncPlan) -> str:
    return render_sync_plan(plan)


def render_saved_record(record: dict[str, object]) -> str:
    lines = [f"name: {record['name']}", f"type: {record.get('type', 'unknown')}"]
    for key in ("source", "destination", "mode", "every", "backend", "last_status", "last_checked_at", "last_run_at", "last_exit_code", "last_message"):
        if key in record and record[key] is not None and record[key] != "":
            lines.append(f"{key}: {record[key]}")
    return "\n".join(lines)


def render_status_report(records: Iterable[dict[str, object]]) -> str:
    items = list(records)
    counts = OperationSummary.from_statuses((item.get("last_status") or "unknown") for item in items)
    lines = [
        "Summary",
        f"  ok       : {counts.count('ok')}",
        f"  missing  : {counts.count('missing')}",
        f"  broken   : {counts.count('broken')}",
        f"  mismatch : {counts.count('mismatch')}",
        f"  unknown  : {counts.count('unknown')}",
        "",
        "Items",
    ]
    for record in items:
        name = str(record["name"])
        record_type = str(record.get("type", "unknown"))
        status = str(record.get("last_status") or "unknown")
        checked = str(record.get("last_checked_at") or "never")
        lines.append(f"{name}\t{record_type}\t{status}\t{checked}")
    return "\n".join(lines)


def write_lines(path: Path, lines: Iterable[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
