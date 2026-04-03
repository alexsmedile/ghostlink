# Agent Execution Plan

## Purpose

This document defines the parallel agent setup to build `symlink-cli` across the full planned scope while we act as:
- orchestrators
- integrators
- reviewers

The goal is to maximize parallel work, minimize merge conflicts, and keep each agent focused on a bounded area.

## Operating Model

- We keep product decisions, sequencing, final integration, and quality review.
- Each agent owns a clear module or vertical slice.
- Agents should avoid editing files outside their assigned ownership unless explicitly reassigned.
- Shared contracts must be defined first, then implementation agents build against them.
- Integration happens in waves, not continuously.

## Agent Set

### Agent 1: CLI and Compatibility Agent

Role:
- Own command parsing and migration from legacy flags to subcommands.

Primary tasks:
- Create `cli/` package structure
- Implement `parser.py` and `cli/main.py`
- Add subcommands: `create`, `find`, `check`, `save`, `list`, `show`, `remove`, `sync`, `schedule`, `status`
- Maintain old flags through `compat/legacy_flags.py`
- Preserve current `--bulk`, `--find`, `--separator`, `--depth`, and `--output`

Owned files:
- `src/symlink_cli/cli/**`
- `src/symlink_cli/compat/**`

Key constraints:
- No filesystem mutations in parser code
- Stable exit codes
- Guided no-args entry remains available

### Agent 2: Domain and Safety Agent

Role:
- Define the core models, validation, and shared safety rules.

Primary tasks:
- Build `domain/models.py`, `paths.py`, `validation.py`, `results.py`
- Define request/result objects for create, find, check, sync, and schedule
- Implement shared safety gate for dry-run, confirmation, overwrite, backup, and circular checks

Owned files:
- `src/symlink_cli/domain/**`
- shared safety code under `src/symlink_cli/services/` if needed

Key constraints:
- Keep logic pure where possible
- No terminal prompting
- No storage assumptions inside models

### Agent 3: Link Operations Agent

Role:
- Own create, bulk import, find, and check services.

Primary tasks:
- Build `link_service.py`
- Build `find_service.py`
- Build `check_service.py`
- Port existing create/find behavior from `core.py`
- Support bulk parsing with custom separators
- Support `find` depth filtering and output export hooks

Owned files:
- `src/symlink_cli/services/link_service.py`
- `src/symlink_cli/services/find_service.py`
- `src/symlink_cli/services/check_service.py`

Key constraints:
- Reuse domain validation
- Keep check logic separate from rendering
- Preserve current behavior during migration

### Agent 4: Registry and Persistence Agent

Role:
- Own saved-job storage, schema versioning, and run history.

Primary tasks:
- Build `storage/registry.py`
- Build `storage/run_log.py`
- Build `services/registry_service.py`
- Implement atomic writes
- Add schema versioning and migration helpers
- Support saved links and saved sync jobs

Owned files:
- `src/symlink_cli/storage/**`
- `src/symlink_cli/services/registry_service.py`

Key constraints:
- File format must be forward-upgradable
- Reads must tolerate older records
- Storage backend hidden behind service API

### Agent 5: Sync Engine Agent

Role:
- Own one-way sync planning and execution.

Primary tasks:
- Build `services/sync_service.py`
- Define sync models and diff entries
- Implement source vs destination comparison
- Produce dry-run plans
- Execute approved one-way sync plans
- Add ignore/include rule handling

Owned files:
- `src/symlink_cli/services/sync_service.py`
- related sync models in `src/symlink_cli/domain/**`

Key constraints:
- One-way sync only
- Keep sync planning separate from sync execution
- Do not entangle sync with symlink creation logic

### Agent 6: Output and Guided UX Agent

Role:
- Own prompts, summaries, diff rendering, and plain-language messaging.

Primary tasks:
- Build `output/renderers.py`
- Build `output/prompts.py`
- Design guided create/check/save flows
- Standardize status lines, summaries, and warnings
- Prepare reusable renderers for human output and future JSON output

Owned files:
- `src/symlink_cli/output/**`

Key constraints:
- No direct business logic
- All wording should stay plain and low-jargon
- Risky actions must be explained clearly

### Agent 7: Scheduling and System Integration Agent

Role:
- Own macOS scheduling and status integration.

Primary tasks:
- Build `integrations/launchd.py`
- Build `services/schedule_service.py`
- Implement schedule create/list/remove
- Generate launchd plists for saved jobs
- Track next run, last run, and job status hooks

Owned files:
- `src/symlink_cli/integrations/**`
- `src/symlink_cli/services/schedule_service.py`

Key constraints:
- macOS-first
- Prefer launchd over cron
- Keep platform-specific code isolated

### Agent 8: Test and Quality Agent

Role:
- Own the test harness and regression coverage.

Primary tasks:
- Create `tests/` structure
- Add unit tests for domain, services, storage, and sync planning
- Add integration tests for CLI flows
- Add compatibility tests for legacy flags
- Verify migration safety for storage schema changes

Owned files:
- `tests/**`
- minimal test config if introduced

Key constraints:
- Do not rewrite production behavior to fit tests without review
- Focus on safety-critical and migration-critical paths first

## Parallel Work Plan

### Wave 1: Contracts

Run first:
- Agent 2 defines domain models and service contracts
- Agent 1 sets CLI structure and command skeletons
- Agent 4 defines registry schema and storage interfaces

Reason:
- These agents define interfaces that other agents can build against.

### Wave 2: Core behavior

Run in parallel after Wave 1 contracts stabilize:
- Agent 3 implements create/find/check
- Agent 6 implements prompts/renderers
- Agent 8 starts unit tests for domain and core services

Reason:
- These areas are tightly related but can proceed in parallel with stable interfaces.

### Wave 3: Managed workflows

Run next:
- Agent 4 completes saved record flows
- Agent 1 wires `save`, `list`, `show`, `remove`
- Agent 8 adds saved-job integration tests

### Wave 4: Sync

Run next:
- Agent 5 implements sync diff and run
- Agent 6 adds sync summaries and risk prompts
- Agent 8 adds sync dry-run and execution tests

### Wave 5: Scheduling

Run last:
- Agent 7 implements `launchd` integration
- Agent 1 wires schedule/status commands
- Agent 8 adds schedule generation tests

## Integration Rules

- Agents are not alone in the codebase and must not revert other changes.
- Shared interfaces must be reviewed before downstream implementation starts.
- Cross-module edits require orchestrator approval.
- Integration happens through small merge windows after each wave.
- Breaking contract changes must be announced before merge.

## Review Checklist Per Agent

- Does the work stay inside ownership boundaries?
- Are interfaces small and reusable?
- Is behavior testable without terminal input?
- Are dry-run and safety rules preserved?
- Does the change keep backward compatibility where required?
- Does storage remain upgradeable?

## Deliverables By Agent

- Agent 1: subcommand CLI and compatibility layer
- Agent 2: domain contracts and safety framework
- Agent 3: create/find/check services
- Agent 4: registry and run-log persistence
- Agent 5: one-way sync engine
- Agent 6: prompts and renderers
- Agent 7: launchd scheduling integration
- Agent 8: unit and integration test suite

## Orchestrator Responsibilities

We keep ownership of:
- PRD and architecture changes
- contract approval
- merge conflict resolution
- acceptance review
- release sequencing
- final documentation updates

## Recommended Execution Order

1. Approve service and storage contracts.
2. Land CLI skeleton and domain layer.
3. Land create/find/check services with tests.
4. Land saved-job registry features.
5. Land sync diff and sync run.
6. Land scheduling and status.
7. Run final hardening, compatibility testing, and doc updates.
