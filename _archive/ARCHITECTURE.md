# Architecture Plan

## Purpose

This document describes the target architecture needed to grow `symlink-cli` from a small single-file helper into a guided terminal product for creating, checking, finding, saving, and syncing symlink-related workflows.

The current implementation lives mostly in `src/symlink_cli/core.py`. That is acceptable for the first release, but it will not scale cleanly to saved jobs, sync execution, or scheduling. The target architecture should separate CLI parsing, domain logic, storage, and system integrations.

## Architecture Goals

- Keep the CLI simple for users and stable for scripts.
- Keep filesystem logic testable without going through prompts.
- Make risky operations pass through one safety layer.
- Support saved link jobs and saved sync jobs without duplicating logic.
- Allow sync and scheduling to be added without rewriting core link behavior.
- Keep modules loosely coupled so features can be replaced or extended independently.
- Make storage, command parsing, and system integrations upgradeable without breaking user data.

## Modularity Principles

- Define small modules with one main responsibility.
- Depend on interfaces between layers, not concrete implementations.
- Keep domain logic free from terminal UI and OS-specific code.
- Keep storage format upgrades explicit and reversible.
- Add new commands by composing services, not by extending one large file.
- Prefer adapters for external concerns such as `launchd`, filesystem traversal details, and persistence.

## Upgrade Strategy

- Version persisted data with `schema_version`.
- Add migration functions for registry and run-log format changes.
- Keep a compatibility layer for old flags and old command shapes.
- Treat output rendering as replaceable so human output and machine output can evolve independently.
- Isolate platform-specific scheduling so macOS behavior can change without touching core services.
- Keep sync planning separate from sync execution so diff logic can improve without changing the CLI contract.

## Proposed Package Structure

```text
src/symlink_cli/
  __init__.py
  cli/
    main.py
    parser.py
    commands/
      create.py
      find.py
      check.py
      save.py
      list.py
      show.py
      remove.py
      sync.py
      schedule.py
      status.py
  domain/
    models.py
    paths.py
    validation.py
    results.py
  services/
    link_service.py
    find_service.py
    check_service.py
    registry_service.py
    sync_service.py
    schedule_service.py
  storage/
    registry.py
    run_log.py
  integrations/
    launchd.py
  output/
    renderers.py
    prompts.py
  compat/
    legacy_flags.py
```

## Layer Responsibilities

### CLI layer

Responsible for:
- parsing subcommands and flags
- guiding interactive flows
- translating user input into service requests
- mapping service results to exit codes

The CLI layer should not perform filesystem mutations directly.
It should depend on service interfaces so command parsing can evolve without rewriting core behavior.

### Domain layer

Responsible for:
- shared models
- path normalization rules
- validation rules
- operation result types
- enums and policies such as conflict behavior

This layer should contain the core business rules and be mostly pure.
It should be the most stable layer in the project.

### Services layer

Responsible for:
- orchestrating create, find, check, sync, and save flows
- calling validation before mutation
- applying dry-run behavior
- reusing shared safety rules
- returning structured results to the CLI

This will be the main application layer.
Each service should expose a narrow API so future command variants can reuse the same logic.

### Storage layer

Responsible for:
- reading and writing saved jobs
- schema versioning for registry files
- writing run history and last-status metadata
- applying storage migrations when formats change

Recommended files:
- `~/.config/symlink-cli/registry.json`
- `~/.local/state/symlink-cli/runs.jsonl`

If macOS paths are preferred, this can later map to Application Support and Logs, but the service API should hide that detail.
The rest of the system should not care whether storage is JSON, split files, or a future SQLite backend.

### Integrations layer

Responsible for:
- system-specific scheduling support
- generating and installing `launchd` definitions
- optional cron support if ever added

This layer should be isolated because it is platform-specific and harder to test.
It should be designed as an adapter boundary.

### Output layer

Responsible for:
- human-readable rendering
- prompt wording
- summaries and diff views
- consistent status prefixes and messages

This keeps text decisions separate from core logic.

## Core Domain Models

Link-related:
- `LinkSpec`
- `LinkStatus`
- `LinkCheckResult`
- `LinkOperationResult`

Saved records:
- `SavedLinkRecord`
- `SavedSyncRecord`
- `RegistryRecord`

Sync-related:
- `SyncSpec`
- `SyncDiffEntry`
- `SyncPlan`
- `SyncRunResult`

Scheduling:
- `ScheduleSpec`
- `ScheduleStatus`

Shared model rules:
- all paths stored as expanded absolute strings
- all records include timestamps
- all persisted records include a `schema_version`
- models should avoid embedding CLI-only fields

## Command Architecture

### `create`

Flow:
1. Parse direct flags or enter guided prompts.
2. Build `LinkSpec`.
3. Validate source, destination parent, same-path rules, and conflict policy.
4. Produce preview if `--dry-run`.
5. Execute through `link_service`.
6. Optionally offer to save the created link as a named record.

### `find`

Flow:
1. Build a `FindRequest` with root, broken filter, depth, and output path.
2. Traverse through `find_service`.
3. Render results incrementally or in batch.
4. Write optional export file.
5. Return non-zero when configured conditions are met, such as broken links found.

### `check`

Flow:
1. Resolve target scope: one path, a folder, or saved jobs.
2. Validate whether links still point to expected targets.
3. Return health summary and detailed findings.
4. Later allow optional repair mode without changing the base check API.

### `save`, `list`, `show`, `remove`

Flow:
1. Use `registry_service`.
2. Validate unique names and record type.
3. Keep storage operations atomic.
4. Return stable structured output for human display and future automation.

### `sync`

Flow:
1. Build `SyncSpec`.
2. Compare source and destination through `sync_service`.
3. Produce `SyncPlan` with actions: copy, update, skip, conflict.
4. Render diff summary.
5. If not dry-run, execute the approved plan.
6. Save run result and timestamps.

Important rule:
- sync is a separate service from symlink creation, even if both deal with folders.

### `schedule`

Flow:
1. Resolve saved job.
2. Build schedule definition.
3. Generate `launchd` plist through `schedule_service` and `integrations/launchd.py`.
4. Install, remove, or inspect schedules.
5. Write status metadata.

## Safety Architecture

All mutating commands should pass through a shared safety gate before execution.

The safety gate should enforce:
- dry-run handling
- confirmation policy
- overwrite and backup rules
- directory deletion refusal
- self-target and circular-path checks
- plain-language risk messages

This should be implemented once and reused by `create`, `repair`, and `sync run`.

## Compatibility Strategy

The project already ships flag-based entry points like:
- `slink`
- `slink --bulk`
- `slink --find`

During migration:
- keep `slink` with no args as the guided entry point
- keep legacy flags working through `compat/legacy_flags.py`
- internally translate old flags to the new subcommand model
- keep service request objects stable even if CLI syntax changes

Example:
- `slink --bulk links.txt` maps to `slink create --bulk links.txt`
- `slink --find ~/Desktop --depth 2` maps to `slink find ~/Desktop --depth 2`

## Storage Design

Registry file requirements:
- JSON for readability and simple backups
- top-level schema version
- separate sections for `links` and `syncs`
- unique names per record
- atomic write strategy using temp file + replace
- migration path for adding fields without breaking old registries

Run log requirements:
- append-only JSON Lines
- timestamp
- job name
- job type
- command
- result summary
- exit code
- tolerant reader behavior for older log entries with missing fields

## Extension Points

The architecture should leave clear places for future upgrades:
- new output modes such as JSON or compact summaries in `output/renderers.py`
- new storage backends behind `storage/`
- new schedulers behind `integrations/`
- new sync strategies behind `sync_service.py`
- optional richer terminal UI behind `output/prompts.py`

These extensions should not require changing domain models unless the product behavior itself changes.

## Sync Design Constraints

To keep scope controlled:
- support one-way sync only in v1
- require explicit source and destination
- default to preview before execution
- define ignore rules centrally
- do not add file watching or background daemons in v1

Recommended implementation approach:
- start with metadata comparison by path, size, and mtime
- only add content hashing where needed later

## Scheduling Design Constraints

For macOS:
- prefer `launchd`
- generate explicit job labels
- store generated plist files in a predictable location
- do not hide installation details from the user

Recommended UX:
- generate the schedule definition
- show the exact command and interval
- confirm before installing

## Testing Strategy

Unit tests should focus on:
- path normalization
- conflict policy behavior
- bulk parsing with custom separators
- broken-link detection
- check result classification
- sync diff planning
- registry read/write behavior

Integration tests should cover:
- create command end to end in temp directories
- find with depth and output file
- saved link lifecycle
- sync dry-run and sync apply
- schedule file generation

## Recommended Refactor Plan

1. Extract domain models and path helpers from `core.py`.
2. Introduce subcommand parser while keeping legacy flags.
3. Move create, bulk, and find logic into services.
4. Add `check` on top of shared domain models.
5. Add registry storage and saved record commands.
6. Add sync diff and sync run.
7. Add scheduling integration last.

## Open Decisions

- Whether `save` should be automatic after guided create
- Whether `check --fix` is better than a separate `repair` command
- Whether registry lives in one file or multiple files
- Whether run logs should be always on or optional
- Whether prompt rendering stays plain `input()` based or moves to a richer terminal UI later
