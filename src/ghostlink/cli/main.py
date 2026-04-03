from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

from ghostlink.cli.parser import build_parser
from ghostlink.compat.legacy_flags import translate_legacy_args
from ghostlink.domain.models import LinkOperationResult, SavedLinkRecord, SavedSyncRecord, ScheduleSpec, SyncSpec
from ghostlink.domain.models import LinkSpec
from ghostlink.domain.paths import expand_path, normalize_destination
from ghostlink.domain.validation import validate_output_path
from ghostlink.output.prompts import ask_conflict_choice, choose_action, interactive_collect
from ghostlink.output.renderers import (
    render_check_result,
    render_check_summary,
    render_find_result,
    render_find_summary,
    render_link_result,
    render_operation_summary,
    render_saved_record,
    render_status_report,
    render_sync_plan,
    write_lines,
)
from ghostlink.services.check_service import inspect_link, inspect_tree
from ghostlink.services.config_service import (
    export_relation_set,
    load_profile_specs,
    load_profile_syncs,
    saved_link_record_to_export,
    saved_sync_record_to_export,
)
from ghostlink.services.find_service import walk_symlinks
from ghostlink.services.link_service import create_symlink, load_bulk_specs
from ghostlink.services.registry_service import RegistryService
from ghostlink.services.schedule_service import ScheduleService
from ghostlink.services.sync_service import build_sync_plan, run_sync_plan
from ghostlink.storage.run_log import append_run_log, append_run_log_entry, default_run_log_path


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    raw_args, json_requested = extract_json_flag(translate_legacy_args(raw_args))
    raw_args, registry_override = extract_registry_override(raw_args)
    raw_args = normalize_command_shape(raw_args)
    args = build_parser().parse_args(raw_args)
    if json_requested:
        setattr(args, "json", True)
    registry_path = registry_override or getattr(args, "registry_path", None)
    registry = RegistryService(expand_path(registry_path) if registry_path else None)
    if not args.command:
        return run_guided_home(registry)
    if args.command == "create":
        return run_create(args, registry)
    if args.command == "find":
        return run_find(args)
    if args.command == "check":
        return run_check(args, registry)
    if args.command == "repair":
        return run_repair(args, registry)
    if args.command == "export":
        return run_export(args, registry)
    if args.command in {"apply", "import"}:
        return run_apply(args, registry)
    if args.command == "save":
        return run_save(args, registry)
    if args.command == "list":
        return run_list(registry, getattr(args, "json", False))
    if args.command == "show":
        return run_show(args, registry)
    if args.command == "remove":
        return run_remove(args, registry)
    if args.command == "rename":
        return run_rename(args, registry)
    if args.command == "sync":
        return run_sync(args, registry)
    if args.command == "schedule":
        return run_schedule(args, registry)
    if args.command == "status":
        return run_status(registry, getattr(args, "json", False))
    return 1


def run_guided_home(registry: RegistryService) -> int:
    choice = choose_action()
    if choice == "2":
        class FindArgs:
            path = "."
            broken = False
            depth = None
            output = None
        return run_find(FindArgs())
    if choice == "3":
        class CheckArgs:
            path = None
            saved = True
            broken = False
        return run_check(CheckArgs(), registry)
    if choice == "4":
        return run_list(registry)
    class CreateArgs:
        source = None
        dest = None
        bulk = None
        separator = "->"
        conflict = "ask"
        dry_run = False
        yes = False
        save_name = None
    return run_create(CreateArgs(), registry)


def run_create(args, registry: RegistryService) -> int:
    if getattr(args, "bulk", None):
        return run_bulk_create(args, registry)
    if getattr(args, "source", None) and getattr(args, "dest", None):
        source = expand_path(args.source)
        destination = normalize_destination(
            source,
            args.dest,
            None,
        )
        spec = LinkSpec(
            source=relative_source_for_destination(source, destination) if getattr(args, "relative", False) else source,
            destination=destination,
        )
    else:
        spec = interactive_collect()
        if spec is None:
            return 1
    if not args.yes:
        confirm = input("Create this symlink? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return 1
    choice = None
    if args.conflict == "ask" and spec.destination.exists() and not args.yes:
        choice = ask_conflict_choice(spec.destination)
    result = create_symlink(
        spec,
        on_conflict=args.conflict,
        dry_run=args.dry_run,
        assume_yes=args.yes,
        conflict_choice=choice,
    )
    if getattr(args, "json", False):
        emit_json({"result": result, "saved_name": args.save_name})
    else:
        print(render_link_result(result))
    if result.status == "created":
        maybe_save_created_link(spec.source, spec.destination, args.conflict, args.save_name, registry, args.yes)
    return 1 if result.status == "error" else 0


def run_bulk_create(args, registry: RegistryService) -> int:
    file_path = expand_path(args.bulk)
    if not file_path.exists():
        print(f"Bulk file not found: {file_path}")
        return 1
    try:
        specs = load_bulk_specs(file_path, separator=args.separator)
    except Exception as error:
        print(f"Failed to load bulk file: {error}")
        return 1
    if not specs:
        print("No link entries found.")
        return 1
    print(f"Loaded {len(specs)} link entries from {file_path}")
    if not args.yes:
        confirm = input("Continue? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return 1
    results = []
    for spec in specs:
        if getattr(args, "relative", False):
            spec = LinkSpec(
                source=relative_source_for_destination(spec.source, spec.destination),
                destination=spec.destination,
                conflict_policy=spec.conflict_policy,
                line_no=spec.line_no,
            )
        choice = None
        if args.conflict == "ask" and spec.destination.exists() and not args.yes:
            choice = ask_conflict_choice(spec.destination)
        result = create_symlink(
            spec,
            on_conflict=args.conflict,
            dry_run=args.dry_run,
            assume_yes=args.yes,
            conflict_choice=choice,
        )
        results.append(result)
        if not getattr(args, "json", False):
            print(render_link_result(result))
    if getattr(args, "json", False):
        emit_json({"results": results, "summary": summarize_link_results(results), "bulk_file": str(file_path)})
    else:
        print()
        print(render_operation_summary(results))
    for result in results:
        if result.status == "created":
            maybe_save_created_link(
                result.spec.source,
                result.spec.destination,
                args.conflict,
                None,
                registry,
                auto_yes=True,
            )
    return 1 if any(result.status == "error" for result in results) else 0


def maybe_save_created_link(
    source: Path,
    destination: Path,
    conflict_policy: str,
    save_name: str | None,
    registry: RegistryService,
    auto_yes: bool,
) -> None:
    should_save = bool(save_name)
    if not should_save and not auto_yes:
        answer = input("Save this link for later checks? [y/N]: ").strip().lower()
        should_save = answer == "y"
    if not should_save:
        return
    name = save_name or input(f"Saved name (default: {destination.name}): ").strip() or destination.name
    try:
        registry.save_link(
            SavedLinkRecord(
                name=name,
                source=str(source),
                destination=str(destination),
                conflict_policy=conflict_policy,
            )
        )
    except ValueError as error:
        print(f"[WARN] Could not save link: {error}")
    else:
        print(f"[SAVED] {name}")


def run_find(args) -> int:
    root = expand_path(args.path)
    if not root.exists() or not root.is_dir():
        print(f"Not a directory: {root}")
        return 1
    results = []
    header = f"Searching for symlinks under: {root}"
    if args.broken:
        header += "  (broken only)"
    if args.depth is not None:
        header += f"  (depth limit: {args.depth})"
    if not getattr(args, "json", False):
        print(header)
    for result in walk_symlinks(root, max_depth=args.depth):
        if args.broken and not result.broken:
            continue
        if not getattr(args, "json", False):
            print(render_find_result(result))
        results.append(result)
    if getattr(args, "json", False):
        emit_json(
            {
                "root": root,
                "broken_only": bool(args.broken),
                "depth": args.depth,
                "results": results,
                "summary": {
                    "found": len(results),
                    "broken": sum(item.broken for item in results),
                },
            }
        )
    else:
        print()
        print(render_find_summary(results))
    if args.output:
        output_path = expand_path(args.output)
        ok, reason = validate_output_path(output_path)
        if not ok:
            print(reason)
            return 1
        lines = [render_find_result(item) for item in results]
        lines.extend(["", render_find_summary(results)])
        write_lines(output_path, lines)
        print(f"-> saved to {output_path}")
    return 1 if any(item.broken for item in results) else 0


def run_check(args, registry: RegistryService) -> int:
    if getattr(args, "saved", False):
        records = [item for item in registry.list_records("links") if item.get("type") == "link"]
        if not records:
            print("No saved links.")
            return 0
        results = []
        for record in records:
            result = inspect_link(
                expand_path(str(record["destination"])),
                expected_target=expand_path(str(record["source"])),
                label=str(record["name"]),
            )
            results.append(result)
            registry.update_link_status(str(record["name"]), result.status)
            append_audit_log(
                {
                    "action": "check",
                    "status": result.status,
                    "name": str(record["name"]),
                    "message": result.message,
                    "details": {
                        "path": str(record["destination"]),
                        "expected_target": str(record["source"]),
                    },
                },
            )
            if not getattr(args, "json", False):
                print(render_check_result(result))
        if getattr(args, "json", False):
            emit_json({"scope": "saved", "results": results, "summary": summarize_check_results(results)})
        else:
            print()
            print(render_check_summary(results))
        return 1 if any(result.status != "ok" for result in results) else 0
    if not getattr(args, "path", None):
        print("Provide a path or use --saved.")
        return 1
    target = expand_path(args.path)
    if target.is_dir():
        results = inspect_tree(target, broken_only=args.broken)
    else:
        results = [inspect_link(target)]
        if args.broken:
            results = [item for item in results if item.status == "broken"]
    if getattr(args, "json", False):
        emit_json({"scope": str(target), "results": results, "summary": summarize_check_results(results)})
    else:
        for result in results:
            print(render_check_result(result))
        print()
        print(render_check_summary(results))
    return 1 if any(result.status in {"broken", "missing", "mismatch", "not-link"} for result in results) else 0


def run_repair(args, registry: RegistryService) -> int:
    specs = resolve_repair_specs(args, registry)
    if specs is None:
        return 1
    if not specs:
        print("No repair targets found.")
        return 1
    if not args.yes:
        confirm = input(f"Repair {len(specs)} link(s)? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return 1
    results: list[LinkOperationResult] = []
    for name, spec in specs:
        result = repair_link_spec(spec, args.conflict, args.dry_run)
        results.append(result)
        if name:
            if result.status in {"created", "skipped"}:
                registry.update_link_status(name, "ok")
            append_audit_log(
                {
                    "action": "repair",
                    "status": result.status,
                    "name": name,
                    "message": result.message,
                    "details": {
                        "source": str(spec.source),
                        "destination": str(spec.destination),
                        "dry_run": args.dry_run,
                    },
                },
            )
        if not getattr(args, "json", False):
            print(render_link_result(result))
    if getattr(args, "json", False):
        emit_json({"results": results, "summary": summarize_link_results(results)})
    else:
        print()
        print(render_operation_summary(results))
    return 1 if any(result.status == "error" for result in results) else 0


def resolve_repair_specs(args, registry: RegistryService) -> list[tuple[str | None, LinkSpec]] | None:
    if getattr(args, "bulk", None):
        file_path = expand_path(args.bulk)
        if not file_path.exists():
            print(f"Bulk file not found: {file_path}")
            return None
        try:
            return [(None, spec) for spec in load_bulk_specs(file_path, separator=args.separator)]
        except Exception as error:
            print(f"Failed to load bulk file: {error}")
            return None
    if getattr(args, "saved", False):
        records = [item for item in registry.list_records("links") if item.get("type") == "link"]
        if not records:
            print("No saved links.")
            return []
        return [
            (
                str(record["name"]),
                LinkSpec(
                    source=expand_path(str(record["source"])),
                    destination=expand_path(str(record["destination"])),
                    conflict_policy=args.conflict,
                ),
            )
            for record in records
        ]
    if getattr(args, "name", None):
        record = registry.get_record(args.name)
        if not record or record.get("type") != "link":
            print(f"Saved link not found: {args.name}")
            return None
        return [
            (
                str(record["name"]),
                LinkSpec(
                    source=expand_path(str(record["source"])),
                    destination=expand_path(str(record["destination"])),
                    conflict_policy=args.conflict,
                ),
            )
        ]
    print("Provide a saved link name, use --saved, or use --bulk.")
    return None


def repair_link_spec(spec: LinkSpec, conflict_policy: str, dry_run: bool) -> LinkOperationResult:
    current = inspect_link(spec.destination, expected_target=spec.source)
    if current.status == "ok":
        return LinkOperationResult(spec, "skipped", f"already healthy: {spec.destination} -> {spec.source}")
    return create_symlink(
        spec,
        on_conflict=conflict_policy,
        dry_run=dry_run,
        assume_yes=True,
    )


def run_save(args, registry: RegistryService) -> int:
    try:
        if args.type == "sync":
            registry.save_sync(
                SavedSyncRecord(
                    name=args.name,
                    source=str(expand_path(args.source)),
                    destination=str(expand_path(args.dest)),
                )
            )
        else:
            registry.save_link(
                SavedLinkRecord(
                    name=args.name,
                    source=str(expand_path(args.source)),
                    destination=str(expand_path(args.dest)),
                    conflict_policy=args.conflict,
                )
            )
    except ValueError as error:
        print(error)
        return 1
    if getattr(args, "json", False):
        emit_json({"saved": {"name": args.name, "type": args.type, "source": expand_path(args.source), "destination": expand_path(args.dest)}})
    else:
        print(f"Saved {args.type}: {args.name}")
    return 0


def run_export(args, registry: RegistryService) -> int:
    records = [item for item in registry.list_records("links") if item.get("type") == "link"]
    sync_records = [item for item in registry.list_records("syncs") if item.get("type") == "sync"]
    if getattr(args, "names", None):
        wanted = set(args.names)
        records = [item for item in records if str(item["name"]) in wanted]
        sync_records = [item for item in sync_records if str(item["name"]) in wanted]
    if not records and not sync_records:
        print("No saved links or syncs to export.")
        return 1
    output_path = expand_path(args.file)
    payload = export_relation_set(
        [saved_link_record_to_export(record) for record in records],
        output_path=output_path,
        profile_name=args.profile,
        relative=args.relative,
        sync_records=[saved_sync_record_to_export(record) for record in sync_records],
    )
    link_count = len(payload["profiles"][args.profile]["links"])
    sync_count = len(payload["profiles"][args.profile].get("syncs", []))
    if getattr(args, "json", False):
        emit_json(
            {
                "file": output_path,
                "profile": args.profile,
                "links": link_count,
                "syncs": sync_count,
                "payload": payload,
            }
        )
    else:
        print(f"Exported {link_count} link(s) and {sync_count} sync(s) to {output_path} [{args.profile}]")
    return 0


def run_apply(args, registry: RegistryService) -> int:
    file_path = expand_path(args.file)
    if not file_path.exists():
        print(f"Relation set not found: {file_path}")
        return 1
    try:
        specs = load_profile_specs(file_path, profile_name=args.profile, relative_links=args.relative)
        sync_specs = load_profile_syncs(file_path, profile_name=args.profile)
    except ValueError as error:
        print(error)
        return 1
    if not specs and not sync_specs:
        print("No link or sync entries found.")
        return 1
    if not args.yes:
        confirm = input(f"Apply {len(specs)} link(s) and import {len(sync_specs)} sync profile(s) from {file_path}? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return 1
    results: list[LinkOperationResult] = []
    for name, spec in specs:
        result = create_symlink(
            LinkSpec(
                source=spec.source,
                destination=spec.destination,
                conflict_policy=args.conflict,
                line_no=spec.line_no,
            ),
            on_conflict=args.conflict,
            dry_run=args.dry_run,
            assume_yes=args.yes,
        )
        results.append(result)
        if not getattr(args, "json", False):
            print(render_link_result(result))
        if args.save and result.status == "created":
            save_name = str(name) if name else spec.destination.name
            try:
                registry.save_link(
                    SavedLinkRecord(
                        name=save_name,
                        source=str(absolute_source_for_spec(spec)),
                        destination=str(spec.destination),
                        conflict_policy=args.conflict,
                    )
                )
            except ValueError as error:
                if not getattr(args, "json", False):
                    print(f"[WARN] Could not save link: {error}")
    imported_syncs: list[str] = []
    if args.save:
        for sync_name, sync_spec in sync_specs:
            try:
                registry.save_sync(
                    SavedSyncRecord(
                        name=sync_name,
                        source=str(sync_spec.source),
                        destination=str(sync_spec.destination),
                        mode=sync_spec.mode,
                    )
                )
                imported_syncs.append(sync_name)
            except ValueError as error:
                if not getattr(args, "json", False):
                    print(f"[WARN] Could not save sync: {error}")
    if getattr(args, "json", False):
        emit_json(
            {
                "results": results,
                "summary": summarize_link_results(results),
                "imported_syncs": imported_syncs,
                "available_syncs": [name for name, _sync in sync_specs],
                "profile": args.profile,
                "file": file_path,
            }
        )
    else:
        print()
        print(render_operation_summary(results))
        if sync_specs and not args.save:
            print(f"[INFO] {len(sync_specs)} sync profile(s) available; use --save to import them.")
        elif imported_syncs:
            print(f"[IMPORTED] syncs: {', '.join(imported_syncs)}")
    return 1 if any(result.status == "error" for result in results) else 0


def run_list(registry: RegistryService, json_output: bool = False) -> int:
    records = registry.list_records()
    if not records:
        if not json_output:
            print("No saved items.")
        else:
            emit_json({"items": []})
        return 0
    if json_output:
        emit_json({"items": records})
    else:
        for record in records:
            print(f"{record['name']}\t{record.get('type', 'unknown')}\t{record.get('source', '')}\t{record.get('destination', '')}")
    return 0


def run_show(args, registry: RegistryService) -> int:
    record = registry.get_record(args.name)
    if not record:
        print(f"Not found: {args.name}")
        return 1
    if getattr(args, "json", False):
        emit_json({"item": record})
    else:
        print(render_saved_record(record))
    return 0


def run_remove(args, registry: RegistryService) -> int:
    if not registry.remove(args.name):
        print(f"Not found: {args.name}")
        return 1
    print(f"Removed: {args.name}")
    return 0


def run_rename(args, registry: RegistryService) -> int:
    try:
        ok = registry.rename(args.old_name, args.new_name)
    except ValueError as error:
        print(error)
        return 1
    if not ok:
        print(f"Not found: {args.old_name}")
        return 1
    print(f"Renamed: {args.old_name} -> {args.new_name}")
    return 0


def resolve_sync_spec(args, registry: RegistryService) -> SyncSpec:
    if getattr(args, "config", None):
        file_path = expand_path(args.config)
        sync_specs = load_profile_syncs(file_path, profile_name=getattr(args, "profile", "default"))
        if getattr(args, "name", None):
            for sync_name, sync_spec in sync_specs:
                if sync_name == args.name:
                    return sync_spec
            raise ValueError(f"sync profile not found: {args.name}")
        if len(sync_specs) == 1:
            return sync_specs[0][1]
        if not sync_specs:
            raise ValueError("no sync profiles found in config")
        raise ValueError("multiple sync profiles found; provide the sync name")
    if getattr(args, "name", None) and not getattr(args, "source", None) and not getattr(args, "dest", None):
        record = registry.get_record(args.name)
        if not record or record.get("type") != "sync":
            raise ValueError(f"saved sync not found: {args.name}")
        return SyncSpec(
            source=expand_path(str(record["source"])),
            destination=expand_path(str(record["destination"])),
        )
    if getattr(args, "source", None) and getattr(args, "dest", None):
        return SyncSpec(source=expand_path(args.source), destination=expand_path(args.dest))
    raise ValueError("provide --source and --dest, or a saved sync name")


def run_sync(args, registry: RegistryService) -> int:
    if args.sync_command == "save":
        try:
            registry.save_sync(
                SavedSyncRecord(
                    name=args.name,
                    source=str(expand_path(args.source)),
                    destination=str(expand_path(args.dest)),
                )
            )
        except ValueError as error:
            print(error)
            return 1
        if getattr(args, "json", False):
            emit_json({"saved": {"name": args.name, "type": "sync", "source": expand_path(args.source), "destination": expand_path(args.dest)}})
        else:
            print(f"Saved sync: {args.name}")
        return 0
    try:
        spec = resolve_sync_spec(args, registry)
        plan = build_sync_plan(spec)
    except ValueError as error:
        print(error)
        return 1
    if getattr(args, "json", False):
        sync_name = getattr(args, "name", None) if getattr(args, "name", None) else None
        sync_payload = {"plan": plan, "name": sync_name}
    else:
        print(render_sync_plan(plan))
    if args.sync_command == "diff":
        if getattr(args, "json", False):
            emit_json(sync_payload | {"summary": summarize_sync_plan(plan)})
        return 1 if any(item.action in {"copy", "update", "extra"} for item in plan.entries) else 0
    dry_run = getattr(args, "dry_run", False)
    if not dry_run and not getattr(args, "yes", False):
        confirm = input("Run this one-way sync? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return 1
    result = run_sync_plan(plan, dry_run=dry_run)
    if getattr(args, "name", None) and not getattr(args, "source", None) and not getattr(args, "dest", None) and not getattr(args, "config", None):
        registry.update_sync_status(args.name, "ok" if not result.errors else "error", mark_ran=True)
    append_audit_log(
        {
            "job_type": "sync",
            "source": str(spec.source),
            "destination": str(spec.destination),
            "applied": result.applied,
            "skipped": result.skipped,
            "errors": result.errors,
            "dry_run": dry_run,
        },
        structured=False,
    )
    if getattr(args, "json", False):
        emit_json({"plan": plan, "result": result, "summary": summarize_sync_plan(plan)})
    else:
        print(f"Applied: {result.applied}")
        print(f"Skipped: {result.skipped}")
    if result.errors:
        if not getattr(args, "json", False):
            for error in result.errors:
                print(f"[ERR] {error}")
        return 1
    return 0


def run_schedule(args, registry: RegistryService) -> int:
    if args.schedule_command == "list":
        schedules = [item for item in registry.list_records("schedules") if item.get("job_name")]
        if not schedules:
            if getattr(args, "json", False):
                emit_json({"schedules": []})
            else:
                print("No saved schedules.")
            return 0
        if getattr(args, "json", False):
            emit_json({"schedules": schedules})
        else:
            for schedule in schedules:
                print(
                    f"{schedule['job_name']}\t{schedule.get('every', '')}\t{schedule.get('backend', '')}\t"
                    f"{schedule.get('last_status') or 'unknown'}\t{schedule.get('last_run_at') or 'never'}"
                )
        return 0
    if args.schedule_command == "show":
        schedules = [item for item in registry.list_records("schedules") if item.get("job_name") and item["name"] == args.name]
        if not schedules:
            print(f"Not found: {args.name}")
            return 1
        if getattr(args, "json", False):
            emit_json({"schedule": schedules[0]})
        else:
            print(render_saved_record(schedules[0]))
        return 0
    if args.schedule_command == "run":
        return run_scheduled_job(args.name, registry)
    if args.schedule_command == "remove":
        if not registry.remove_from_group(args.name, "schedules"):
            print(f"Not found: {args.name}")
            return 1
        print(f"Removed schedule: {args.name}")
        return 0
    record = registry.get_record(args.name)
    if not record:
        print(f"Saved job not found: {args.name}")
        return 1
    if record.get("type") in {"sync", "link"}:
        command = ["ghostlink", "schedule", "run", args.name]
    else:
        print("Scheduling is only supported for saved link and sync jobs.")
        return 1
    service = ScheduleService()
    spec = ScheduleSpec(
        name=args.name,
        interval_seconds=service_parse_interval(args.every),
        program_arguments=tuple(command),
    )
    path, content = service.preview(spec, command)
    if not getattr(args, "json", False):
        print(f"Schedule file: {path}")
        print(content)
    if getattr(args, "write", False):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        registry.save_schedule(spec, job_type=str(record.get("type", "schedule")))
        if not getattr(args, "json", False):
            print(f"Wrote schedule preview: {path}")
    if getattr(args, "json", False):
        emit_json({"schedule_file": path, "plist": content, "written": bool(getattr(args, "write", False)), "name": args.name})
    return 0


def run_scheduled_job(name: str, registry: RegistryService) -> int:
    target = registry.get_record(name)
    if not target:
        print(f"Saved job not found: {name}")
        registry.update_schedule_status(name, "error", exit_code=1, message="saved job not found", mark_ran=True)
        return 1
    result_code = 1
    message = "unsupported scheduled job"
    if target.get("type") == "sync":
        result_code = run_sync(
            type(
                "Args",
                (),
                {"sync_command": "run", "name": name, "source": None, "dest": None, "dry_run": False, "yes": True},
            )(),
            registry,
        )
        message = "sync run completed" if result_code == 0 else "sync run failed"
    elif target.get("type") == "link":
        result_code, message = run_scheduled_link_check(name, registry)
    else:
        print("Scheduling is only supported for saved link and sync jobs.")
        registry.update_schedule_status(name, "error", exit_code=1, message=message, mark_ran=True)
        return 1
    registry.update_schedule_status(
        name,
        "ok" if result_code == 0 else "error",
        exit_code=result_code,
        message=message,
        mark_ran=True,
    )
    return result_code


def run_scheduled_link_check(name: str, registry: RegistryService) -> tuple[int, str]:
    record = registry.get_record(name)
    if not record or record.get("type") != "link":
        print(f"Saved link not found: {name}")
        return 1, "saved link not found"
    result = inspect_link(
        expand_path(str(record["destination"])),
        expected_target=expand_path(str(record["source"])),
        label=str(record["name"]),
    )
    registry.update_link_status(str(record["name"]), result.status)
    append_audit_log(
        {
            "action": "check",
            "status": result.status,
            "name": str(record["name"]),
            "message": result.message,
            "details": {
                "path": str(record["destination"]),
                "expected_target": str(record["source"]),
                "scheduled": True,
            },
        }
    )
    print(render_check_result(result))
    print()
    print(render_check_summary([result]))
    if result.status == "ok":
        return 0, result.message
    return 1, result.message


def run_status(registry: RegistryService, json_output: bool = False) -> int:
    records = registry.list_records()
    if not records:
        if json_output:
            emit_json({"summary": {}, "items": []})
        else:
            print("No saved items.")
        return 0
    if json_output:
        emit_json({"summary": summarize_status_records(records), "items": records})
    else:
        print(render_status_report(records))
    return 0


def relative_source_for_destination(source: Path, destination: Path) -> Path:
    return Path(os.path.relpath(source, start=destination.parent))


def absolute_source_for_spec(spec: LinkSpec) -> Path:
    if spec.source.is_absolute():
        return spec.source
    return (spec.destination.parent / spec.source).resolve()


def extract_registry_override(argv: list[str]) -> tuple[list[str], str | None]:
    output: list[str] = []
    override: str | None = None
    index = 0
    while index < len(argv):
        item = argv[index]
        if item == "--registry-path":
            if index + 1 >= len(argv):
                raise SystemExit("--registry-path requires a value")
            override = argv[index + 1]
            index += 2
            continue
        output.append(item)
        index += 1
    return output, override


def extract_json_flag(argv: list[str]) -> tuple[list[str], bool]:
    output: list[str] = []
    requested = False
    for item in argv:
        if item == "--json":
            requested = True
            continue
        output.append(item)
    return output, requested


def normalize_command_shape(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    known_commands = {
        "create",
        "find",
        "check",
        "repair",
        "export",
        "apply",
        "import",
        "save",
        "list",
        "show",
        "remove",
        "rename",
        "sync",
        "schedule",
        "status",
    }
    first = argv[0]
    if first == "bulk":
        if len(argv) >= 2:
            return ["create", "--bulk", argv[1], *argv[2:]]
        return ["create", "--bulk"]
    if first.startswith("-") or first in known_commands:
        return argv
    if len(argv) >= 2 and not argv[1].startswith("-"):
        return ["create", "--source", argv[0], "--dest", argv[1], *argv[2:]]
    return argv


def append_audit_log(payload: dict[str, object], structured: bool = True) -> None:
    try:
        if structured:
            append_run_log_entry(payload, path=default_run_log_path())
        else:
            append_run_log(default_run_log_path(), payload)
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


def summarize_link_results(results: list[LinkOperationResult]) -> dict[str, int]:
    return {
        "created": sum(result.status == "created" for result in results),
        "dry_run": sum(result.status == "dry-run" for result in results),
        "skipped": sum(result.status == "skipped" for result in results),
        "errors": sum(result.status == "error" for result in results),
    }


def summarize_check_results(results: list[object]) -> dict[str, int]:
    statuses = [getattr(result, "status", "unknown") for result in results]
    return {
        "ok": statuses.count("ok"),
        "missing": statuses.count("missing"),
        "broken": statuses.count("broken"),
        "mismatch": statuses.count("mismatch"),
        "not_link": statuses.count("not-link"),
    }


def summarize_sync_plan(plan: SyncSpec | object) -> dict[str, int]:
    entries = getattr(plan, "entries", [])
    actions = [getattr(entry, "action", "unknown") for entry in entries]
    return {
        "copy": actions.count("copy"),
        "update": actions.count("update"),
        "skip": actions.count("skip"),
        "extra": actions.count("extra"),
    }


def summarize_status_records(records: list[dict[str, object]]) -> dict[str, int]:
    statuses = [str(record.get("last_status") or "unknown") for record in records]
    return {
        "ok": statuses.count("ok"),
        "missing": statuses.count("missing"),
        "broken": statuses.count("broken"),
        "mismatch": statuses.count("mismatch"),
        "unknown": statuses.count("unknown"),
    }


def service_parse_interval(value: str) -> int:
    from ghostlink.services.schedule_service import parse_interval

    return parse_interval(value)
