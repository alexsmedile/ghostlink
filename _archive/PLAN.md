# ghostlink Plan

## Goal

Build `ghostlink` into a safe, guided terminal tool for managing folder relationships on macOS:
- create symlinks
- find and check them
- save managed links and sync jobs
- repair drift
- preview and automate repeatable workflows

Primary command: `ghostlink`

Compatibility commands that must keep working:
- `symlink-cli`
- `slink`

## Planning Rule

If a feature already exists, the first job is to verify that it works and that it exposes the settings the product needs.

Only after that do we extend or replace it.

## Current Baseline

Already shipped:
- guided CLI entry
- `create`, `find`, `check`, `save`, `list`, `show`, `remove`, `rename`
- one-way `sync diff|run|save`
- `schedule add|list|remove`
- saved registry and run log
- legacy `--find` and `--bulk` compatibility
- modular package structure and tests

Still missing from the product direction:
- fast path: `ghostlink <source> <destination>`
- first-class `ghostlink bulk <file>` command
- repair workflow
- richer `status` and audit output
- export/import of managed definitions
- profile/config-driven relation sets
- relative-link mode
- better automation visibility and heartbeat tracking

## Product Shape

The command experience should stay simple:
- no args: guided human flow
- two args: fast single-link path
- subcommands: explicit advanced work

The tool should feel safe by default:
- preview before mutation
- clear conflict handling
- plain wording
- durable saved state

The tool should grow without breaking users:
- preserve old commands during migration
- keep storage upgradeable
- add tests before changing behavior

## Workstream 1: Verify Core Link Creation

Goal:
Prove the existing create flows match the intended `ghostlink` behavior.

Check:
- guided `ghostlink`
- `ghostlink create --source --dest`
- bulk creation via `create --bulk`
- `--dry-run`
- `--conflict ask|skip|overwrite|backup`
- `-y`
- `--separator`
- save-to-registry flow
- exit codes and safety prompts

Build only if missing:
- `ghostlink <source> <destination>`
- `ghostlink bulk <file>`

Done when:
- the current create and bulk behavior is verified with tests
- fast-path gaps are implemented or explicitly deferred
- help text makes the simple path obvious

## Workstream 2: Verify Discovery And Health

Goal:
Make sure users can reliably find problems in both unmanaged and managed links.

Check:
- `ghostlink find <path>`
- `--broken`
- `--depth`
- `--output`
- `ghostlink check <path>`
- `ghostlink check --saved`
- current status updates on saved records
- non-zero exits for broken, missing, or mismatched links

Build only if missing:
- filtered check modes such as missing-only or managed-only
- richer `status` summary across saved jobs

Done when:
- users can see broken links, missing managed links, and mismatches clearly
- scripted checks behave predictably through exit codes

## Workstream 3: Verify Managed Records

Goal:
Confirm the saved backlog works as the source of truth for later checks and automation.

Check:
- `save`, `list`, `show`, `remove`, `rename`
- link vs sync record handling
- registry schema stability
- run-log writes where already supported

Build only if missing:
- better metadata on records
- stronger status history
- import/export foundations

Done when:
- a created link or sync job can be saved, inspected, renamed, removed, and checked later
- registry changes have tests and a migration path

## Workstream 4: Add Repair And Audit

Goal:
Close the main maintenance gap after detection.

Build:
- `repair` for saved links
- repair support for bulk definitions or config sets
- richer `status` output that summarizes:
  - healthy
  - broken
  - missing
  - mismatched
- run-log entries for check and repair flows

Done when:
- a user can detect and repair a managed link without manual recreation
- `status` is useful as a high-level health view

## Workstream 5: Verify And Extend Sync

Goal:
Treat sync as a separate, explicit workflow without confusing it with symlink creation.

Check:
- `sync diff`
- `sync run`
- `sync save`
- dry-run behavior
- ignore rules
- exit codes
- schedule preview and plist generation
- `schedule add|list|remove`

Build only if missing:
- clearer diff output
- config-backed sync profiles
- explicit deletion-policy handling
- relation-set sync from saved configs

Done when:
- sync plans are readable
- saved sync jobs can be rerun safely
- scheduling is inspectable and not hidden

## Workstream 6: Add Portable Configs

Goal:
Move from ad hoc commands to reusable definitions.

Build:
- export of discovered or managed links
- import/apply of relation sets
- named profiles such as `work`, `personal`, or `dev`
- relative-link mode for repo-friendly setups

Done when:
- users can save their setup as data and replay it on another machine or repo

## Workstream 7: Add Automation Visibility

Goal:
Support recurring checks and sync jobs without turning the tool into a silent daemon.

Build:
- better schedule inspection
- heartbeat metadata for scheduled jobs
- last-run and health reporting
- decision on whether watch mode belongs in core

Done when:
- recurring jobs are visible, explainable, and easy to disable

## Execution Order

1. Verify shipped create, bulk, find, check, save, sync, and schedule behavior against the desired settings.
2. Implement the missing simple CLI paths: `ghostlink <source> <destination>` and `ghostlink bulk <file>`.
3. Add repair and richer status.
4. Add export/import, profiles, and relative-link mode.
5. Extend sync and scheduling visibility.
6. Add heartbeat or watch work only if the earlier layers are stable.

## Delivery Rule

For every milestone:
- add or extend tests first
- keep `README.md` aligned
- preserve compatibility for `symlink-cli` and `slink`
- do not change storage formats without a migration path
- prefer plain, guided UX over terse but risky behavior

## Definition Of Done

A workstream is done when:
- the behavior is covered by tests
- the CLI matches the documented product shape
- saved data remains readable across upgrades
- safety prompts and exit codes are predictable
- the human terminal flow stays clear and low-risk
