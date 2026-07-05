from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from ghostlink.domain.paths import expand_path
from ghostlink.services.history_service import history_cleanup_candidates, prune_history, query_history
from ghostlink.services.lifecycle_service import (
    adopt_index_candidate,
    plan_index,
    save_index_candidate,
    unhealthy_registry_candidates,
)
from ghostlink.services.registry_service import RegistryService
from ghostlink.storage.run_log import RunLogFormatError, append_run_log_entry


def run_history(args, run_log_path: Path) -> int:
    try:
        entries = query_history(
            run_log_path,
            limit=args.limit,
            action=args.action,
            record_type=args.record_type,
            name=args.name,
            since=args.since,
        )
    except (ValueError, RunLogFormatError) as error:
        print(error)
        return 2
    if getattr(args, "json", False):
        emit_json({"events": entries})
        return 0
    if not entries:
        print("No lifecycle events found.")
        return 0
    for entry in entries:
        identity = entry.name or entry.destination or "-"
        print(f"{entry.timestamp}\t{entry.action}\t{entry.status}\t{entry.record_type or '-'}\t{identity}")
    return 0


def run_index(args, registry: RegistryService, run_log_path: Path) -> int:
    root = expand_path(args.path)
    if not root.exists() or not root.is_dir():
        print(f"Not a directory: {root}")
        return 1
    candidates = plan_index(root, registry, max_depth=args.depth)
    new_items = [item for item in candidates if item.state == "new"]
    conflicts = [item for item in candidates if item.state == "conflict"]
    if args.yes and args.on_conflict == "ask" and conflicts:
        print("--yes requires --on-conflict keep or adopt when conflicts exist.")
        return 2
    decisions: list[tuple[object, str]] = [(item, "save") for item in new_items]
    for item in conflicts:
        decision = args.on_conflict
        if decision == "ask" and not args.dry_run:
            answer = input(
                f"Conflict {item.destination}: registry expects {item.expected_target}, filesystem points to {item.actual_target}. "
                "Keep registry intent or adopt filesystem? [K/a]: "
            ).strip().lower()
            decision = "adopt" if answer == "a" else "keep"
        decisions.append((item, decision))
    payload = {
        "root": root,
        "candidates": candidates,
        "summary": {
            "found": len(candidates),
            "new": len(new_items),
            "managed": sum(item.state == "managed" for item in candidates),
            "conflicts": len(conflicts),
        },
        "dry_run": bool(args.dry_run),
    }
    if args.dry_run:
        if getattr(args, "json", False):
            emit_json(payload)
        else:
            for item in candidates:
                print(f"[DRY] {item.state}\t{item.destination} -> {item.actual_target}")
        return 0
    if new_items and not args.yes:
        answer = input(f"Save {len(new_items)} newly discovered link(s)? [y/N]: ").strip().lower()
        if answer != "y":
            decisions = [(item, action) for item, action in decisions if action != "save"]
    saved: list[str] = []
    adopted: list[str] = []
    kept: list[str] = []
    for item, decision in decisions:
        if decision == "save":
            record = save_index_candidate(item, registry)
            saved.append(record.name)
            append_event(
                {
                    "action": "index",
                    "status": item.status,
                    "name": record.name,
                    "record_type": "link",
                    "source": str(item.actual_target),
                    "destination": str(item.destination),
                },
                run_log_path,
            )
        elif decision == "adopt":
            record = adopt_index_candidate(item, registry)
            adopted.append(str(record["name"]))
            append_event(
                {
                    "action": "adopt",
                    "status": str(record.get("last_status", "ok")),
                    "name": str(record["name"]),
                    "record_type": "link",
                    "source": str(item.actual_target),
                    "destination": str(item.destination),
                },
                run_log_path,
            )
        else:
            kept.append(str(item.managed_name or item.proposed_name))
    result = payload | {"saved": saved, "adopted": adopted, "kept": kept}
    if getattr(args, "json", False):
        emit_json(result)
    else:
        print(f"Indexed: {len(saved)}  Adopted: {len(adopted)}  Kept: {len(kept)}")
    return 0


def run_cleanup(args, registry: RegistryService, run_log_path: Path) -> int:
    if args.cleanup_command == "history":
        return run_cleanup_history(args, run_log_path)
    return run_cleanup_registry(args, registry, run_log_path)


def run_cleanup_registry(args, registry: RegistryService, run_log_path: Path) -> int:
    candidates = unhealthy_registry_candidates(registry)
    by_name = {str(record["name"]): (record, result) for record, result in candidates}
    if args.names:
        unknown = [name for name in args.names if name not in by_name]
        if unknown:
            print(f"Not an unhealthy saved link: {', '.join(unknown)}")
            return 2
        selected = list(args.names)
    elif args.yes:
        print("--yes requires at least one --name for registry cleanup.")
        return 2
    elif args.dry_run:
        selected = list(by_name)
    else:
        selected = []
        for name, (_record, result) in by_name.items():
            answer = input(f"Remove {name} ({result.status}: {result.message})? [y/N]: ").strip().lower()
            if answer == "y":
                selected.append(name)
    if args.dry_run:
        payload = {"candidates": [result for _record, result in candidates], "selected": selected, "dry_run": True}
        if getattr(args, "json", False):
            emit_json(payload)
        else:
            for name in selected:
                print(f"[DRY] remove registry record: {name}")
        return 0
    for name in selected:
        record, result = by_name[name]
        registry.remove_from_group(name, "links")
        append_event(
            {
                "action": "cleanup-remove",
                "status": result.status,
                "name": name,
                "record_type": "link",
                "source": str(record.get("source", "")),
                "destination": str(record.get("destination", "")),
            },
            run_log_path,
        )
    if getattr(args, "json", False):
        emit_json({"removed": selected})
    else:
        print(f"Removed {len(selected)} registry record(s).")
    return 0


def run_cleanup_history(args, run_log_path: Path) -> int:
    try:
        removed, retained = history_cleanup_candidates(
            run_log_path,
            older_than=args.older_than,
            before=args.before,
        )
    except (ValueError, RunLogFormatError) as error:
        print(error)
        return 2
    if args.dry_run:
        if getattr(args, "json", False):
            emit_json({"remove": removed, "retain": len(retained), "dry_run": True})
        else:
            print(f"[DRY] remove {len(removed)} event(s); retain {len(retained)}.")
        return 0
    if not args.yes:
        answer = input(f"Remove {len(removed)} history event(s)? [y/N]: ").strip().lower()
        if answer != "y":
            print("Cancelled.")
            return 1
    prune_history(run_log_path, retained)
    append_event(
        {
            "action": "cleanup-history",
            "status": "ok",
            "record_type": "history",
            "details": {"removed": len(removed), "retained": len(retained)},
        },
        run_log_path,
    )
    if getattr(args, "json", False):
        emit_json({"removed": len(removed), "retained": len(retained)})
    else:
        print(f"Removed {len(removed)} event(s); retained {len(retained)}.")
    return 0


def append_event(payload: dict[str, object], path: Path) -> None:
    try:
        append_run_log_entry(payload, path=path)
    except OSError:
        pass


def emit_json(payload: object) -> None:
    print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))


def to_jsonable(value: object) -> object:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value
