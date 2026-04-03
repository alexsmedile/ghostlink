# Product Requirements Document

## Product Name

`symlink-cli` (`slink`)

## Goal

Build a guided terminal tool for working with symbolic links on a personal computer. It should help users create, inspect, verify, find, repair, and sync symlinks with low risk of mistakes.

The product should feel safe by default:
- show what will happen before making changes
- explain risky actions in plain language
- remember important link relationships for later checks and syncs
- support both one-off commands and repeatable managed workflows

## Problem

Working with symlinks from the terminal is powerful but easy to get wrong. Users can:
- point a link to the wrong place
- overwrite the wrong file
- forget which folders are linked
- lose track of broken links
- need repeated sync behavior without a clear workflow

The current tool covers basic creation and find flows, but it does not yet manage ongoing relationships between folders.

## Target User

A terminal user on macOS who wants a safer and easier way to manage symlinks for:
- project folders
- dotfiles
- AI skills, agents, or workspace folders
- mirrored working directories across disks or locations

## Product Principles

- Guided first: interactive mode should be the safest and most discoverable path.
- Safe by default: default to preview, confirm, skip, or backup instead of destructive actions.
- Plain language: prompts and errors should be short and easy to understand.
- Scriptable second: every guided action should also have a clear non-interactive CLI form.
- Managed workflows: users should be able to save important link/sync definitions and revisit them later.

## Primary Use Cases

1. Create one symlink from source `X` to destination `Y`.
2. Create many symlinks from a file or saved set.
3. Check whether existing symlinks are still valid.
4. Find symlinks in a directory tree and optionally only show broken ones.
5. Compare a source folder and destination folder before syncing.
6. Save a sync or link relationship and run it again later.
7. Run repeat checks or syncs manually, on demand, or through a scheduler.

## Feature Scope

### Phase 1: Core link management

Must have:
- Guided interactive create flow
- Non-interactive create command
- Bulk create from file
- Custom bulk separators for import files
- Conflict handling: ask, skip, overwrite, backup
- Dry-run mode
- Find mode with broken-link filtering
- Find mode output export to file
- Find mode recursion depth control
- Check mode for validating one link, a folder of links, or saved jobs

CLI shape:
- `slink create`
- `slink create --source ~/A --dest ~/B`
- `slink create --bulk links.txt`
- `slink create --bulk links.csv --separator ","`
- `slink find [DIR]`
- `slink check [PATH]`
- `slink check --broken`
- `slink find ~/Desktop --depth 2`
- `slink find ~/Desktop --output results.txt`

### Phase 2: Managed link sets

Must have:
- Save named link definitions in a local registry
- List saved items
- Show details for one saved item
- Remove or rename saved items
- Run checks against saved items

CLI shape:
- `slink save --name docs-link --source ~/Docs --dest ~/Desktop/Docs`
- `slink list`
- `slink show docs-link`
- `slink check --saved`
- `slink remove docs-link`

Storage:
- Use a local config/data file under the user home directory, for example `~/.config/symlink-cli/registry.json`

### Phase 3: Sync workflows

Goal:
Support folder sync workflows that may use symlinks as part of setup, but also compare source and destination contents.

Must define clearly:
- This is not the same as creating a symlink.
- Sync compares two real folders and copies changes according to rules.

Must have:
- Compare source and destination and show diff summary
- Preview sync actions before execution
- Save a named sync job
- Run one saved sync job

CLI shape:
- `slink sync diff --source ~/skills --dest ~/backup/skills`
- `slink sync run --source ~/skills --dest ~/backup/skills --dry-run`
- `slink sync save --name skills-sync --source ~/skills --dest ~/backup/skills`
- `slink sync run skills-sync`

Diff output should show:
- new files
- missing files
- changed files
- skipped files
- conflicts if relevant

Open product decision:
- Start with one-way sync only. Do not attempt two-way sync in v1.

### Phase 4: Scheduling and heartbeat

Nice to have, not core v1:
- Generate cron entries or launchd jobs for saved sync/check tasks
- Show next run time
- Show last run status
- Optional heartbeat log for monitoring

CLI shape:
- `slink schedule add skills-sync --every 30m`
- `slink schedule list`
- `slink schedule remove skills-sync`
- `slink status`

Open product decision:
- On macOS, prefer `launchd` over cron for native scheduling. Cron can be a secondary option if simpler to ship early.

## UX Requirements

- Default command with no arguments should open a guided menu.
- Every risky action should show:
  - what will change
  - where it will change
  - what safety mode is active
- Before destructive actions, ask for explicit confirmation unless `--yes` is passed.
- Prompts should avoid jargon. Example:
  - Good: `This file already exists. What do you want to do?`
  - Bad: `Destination conflict detected. Select overwrite policy.`
- Output should be readable by humans first, but stable enough for logs.

## Command Design

Recommended top-level structure:

```text
slink create ...
slink find ...
slink check ...
slink save ...
slink list
slink show ...
slink remove ...
slink sync diff ...
slink sync run ...
slink sync save ...
slink schedule ...
slink status
```

Recommendation:
- Move away from flag-only mode switching over time.
- Keep old flags like `--bulk` and `--find` as compatibility aliases during migration.
- Keep currently shipped options available during migration, including `--separator`, `--depth`, and `--output`.

## Safety Requirements

- `--dry-run` for create, repair, and sync actions
- Backup mode for overwrite scenarios
- Never delete directories silently
- Clear warnings when `--yes` suppresses prompts
- Validate source existence and destination parent existence
- Detect and warn about self-referential or circular operations
- Log saved job runs with timestamp and result

## Non-Goals For v1

- Two-way sync
- Cloud sync integrations
- Cross-platform support beyond macOS
- GUI app
- Real-time filesystem watching daemon

## Data Model

Saved link record:
- name
- type: `link`
- source
- destination
- conflict_policy
- created_at
- last_checked_at
- last_status

Saved sync record:
- name
- type: `sync`
- source
- destination
- mode: `one-way`
- include/exclude rules
- created_at
- last_run_at
- last_status

## Success Criteria

- A new user can safely create a symlink without remembering `ln -s` syntax.
- A current user of `--bulk`, `--separator`, `--find`, `--depth`, and `--output` can migrate without losing capability.
- A user can list and re-check saved link relationships.
- A user can preview sync differences before making changes.
- The tool prevents common destructive mistakes by default.
- The CLI remains simple enough to use without reading long docs.

## Recommended Delivery Order

1. Refactor current commands into subcommands: `create`, `find`, `check`.
2. Add saved registry for named link records.
3. Add `check --saved` and `list/show/remove`.
4. Add one-way sync diff and dry-run sync execution.
5. Add saved sync jobs.
6. Add scheduling/status support.

## Open Questions

- Should `save` happen automatically after a successful guided create, or only when the user opts in?
- Should sync ignore common junk files by default, such as `.DS_Store`?
- Should saved jobs live in one file or separate files per job?
- Should `repair` be its own command, or part of `check --fix`?
- Should scheduling be created by the CLI directly, or should the CLI generate setup commands for the user to review first?
