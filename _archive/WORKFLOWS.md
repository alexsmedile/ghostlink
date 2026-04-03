# Workflows, Questions, and Edge Cases

## Purpose

This document captures the expected human workflows for `slink`, plus the open usability questions and edge cases we should answer before or during implementation.

It includes:
- how the core flows should work
- what users may expect
- where product decisions are still needed
- failure cases that should be handled safely

## Core Workflow: Create One Link

Expected flow:
1. User runs `slink` or `slink create`
2. Tool asks for source path
3. Tool asks for destination path or destination folder + link name
4. Tool validates both paths
5. Tool shows a preview
6. Tool asks for confirmation
7. Tool creates the symlink
8. Tool offers to save the link in the registry

Direct command example:

```bash
slink create --source ~/Projects/site --dest ~/Desktop/site
```

Questions:
- Should `slink` with no args always open the guided menu, or jump directly into create if that is still the most common action?
- Should the tool auto-suggest the default link name from the source folder?
- Should the destination prompt ask first for "folder or exact path" every time, or infer it from a trailing slash?
- After success, should save-to-registry be opt-in or the default?

Edge cases:
- Source does not exist
- Destination parent does not exist
- Destination already exists as a file
- Destination already exists as a symlink
- Destination already exists as a directory
- Source and destination resolve to the same path
- Source path contains spaces or quotes
- User pastes a relative path

## Core Workflow: Bulk Creation

Expected flow:
1. User runs `slink create --bulk links.txt`
2. Tool reads all entries
3. Tool validates entries before making changes
4. Tool shows a summary:
   - valid entries
   - invalid entries
   - warnings
5. Tool asks whether to continue
6. Tool applies the operation entry by entry
7. Tool prints a summary

Examples:

```bash
slink create --bulk links.txt
slink create --bulk links.csv --separator ","
```

Questions:
- If 2 out of 50 lines are invalid, should the tool stop the whole run or continue with valid entries?
- Should there be a `--strict` mode that fails the whole batch on any invalid row?
- Should the tool support previewing the parsed rows before execution?
- Should duplicate destinations in the same bulk file be rejected?
- Should comments and blank lines be preserved if the user later imports the file into a saved set?

Edge cases:
- Empty bulk file
- File contains only comments
- Invalid separator usage
- Same destination appears twice
- Same source appears many times
- One bad line among many good ones
- Relative paths in a bulk file
- Paths with commas when separator is comma

## Core Workflow: Check Links

Expected flow:
1. User runs `slink check [PATH]` or `slink check --saved`
2. Tool decides the scope:
   - one link
   - one folder
   - all saved jobs
3. Tool validates actual state against expected state
4. Tool reports health and next steps

Examples:

```bash
slink check ~/Desktop/project
slink check ~/Desktop
slink check --saved
```

Questions:
- When checking a folder, should the tool inspect only symlinks or also compare them against saved records?
- What counts as "missing":
  - saved link record exists but symlink is gone
  - symlink exists but target is missing
  - symlink exists but points somewhere different than expected
- Should `check` optionally offer repair right away?
- Should `check` return non-zero on warnings, or only on true errors/broken states?

Edge cases:
- Saved record exists but destination file is gone
- Saved record exists but source moved
- Symlink exists but target changed intentionally
- Folder contains many unmanaged symlinks
- Broken symlink inside a directory with permission issues

## Core Workflow: Find Links

Expected flow:
1. User runs `slink find [DIR]`
2. Tool scans the directory tree
3. Tool prints link results as it finds them
4. Tool prints a summary
5. Tool optionally writes the same results to a file

Examples:

```bash
slink find ~/Desktop
slink find ~/Desktop --broken
slink find ~/Desktop --depth 2
slink find ~/Desktop --output results.txt
```

Questions:
- Should `find` show unmanaged symlinks the same way as saved symlinks?
- Should saved links be marked specially in `find` results?
- Should `find` hide system folders automatically even when the user starts at `/`?
- Should `find` allow include/exclude path filters later?

Edge cases:
- Permission denied during traversal
- Very large directory trees
- Broken symlinks with relative targets
- Symlink loops in scanned folders
- Output file path is invalid or not writable

## Core Workflow: Save Links to Backlog

Expected behavior:
- Every important created link can be saved to a registry for future checks, reuse, and status tracking.

Likely flow:
1. User creates a link
2. Tool asks whether to save it
3. User gives it a short name
4. Tool stores the record in a registry file

Examples:

```bash
slink save --name docs-link --source ~/Docs --dest ~/Desktop/Docs
slink list
slink show docs-link
```

Questions:
- Should save happen automatically after every successful guided create?
- Should users be able to tag or group saved links?
- Should names be unique globally, or only unique within type (`link` vs `sync`)?
- Should there be a quick-save default name suggested from the destination?
- Should `list` show all records or separate `links` and `syncs` by default?

Edge cases:
- Duplicate saved name
- Saved name with spaces
- Saved record points to a path that later disappears
- Registry file becomes corrupted
- Registry schema changes between versions

## Core Workflow: See Missing Links

There are two different meanings of "missing links", and the product should make this clear.

### Meaning 1: Broken existing symlinks

The symlink exists, but its target does not.

Example:

```bash
slink find ~/Desktop --broken
```

### Meaning 2: Missing expected links from the saved backlog

The tool expected a link to exist because it was saved earlier, but now:
- the link path is gone
- or it points to the wrong place
- or the source target is gone

Example:

```bash
slink check --saved
```

Questions:
- Should missing expected links get their own status label, such as `[MISSING]`?
- Should the summary distinguish:
  - broken target
  - missing link path
  - target mismatch
- Should users be able to ask only for missing saved links?

Edge cases:
- Link path deleted manually
- Link replaced by a regular folder
- Link still exists but points somewhere else
- Source moved to a new place intentionally

## Core Workflow: Sync Folders

Expected behavior:
- Sync is separate from symlink creation.
- It compares two real folders and optionally copies changes one way.

Examples:

```bash
slink sync diff --source ~/skills --dest ~/backup/skills
slink sync run --source ~/skills --dest ~/backup/skills --dry-run
slink sync save --name skills-sync --source ~/skills --dest ~/backup/skills
```

Questions:
- Should sync create the destination folder if it does not exist?
- Should sync ignore junk files like `.DS_Store` by default?
- How should deletions be handled in one-way sync?
- Should missing files on destination be copied automatically, or first shown and confirmed?
- Should sync be file-level only, or preserve symlink objects inside synced folders too?

Edge cases:
- Destination disk is offline
- Source has unreadable files
- Destination has newer files than source
- Very large sync set
- Sync interrupted halfway through

## Core Workflow: Scheduling and Heartbeats

Expected behavior:
- A saved sync or saved check can run later on a schedule.

Examples:

```bash
slink schedule add skills-sync --every 30m
slink schedule list
slink status
```

Questions:
- Should scheduling install directly, or first generate a reviewable config?
- Should the tool use `launchd` only, or offer cron as an advanced fallback?
- What should `status` show:
  - next run
  - last run
  - last success
  - last failure
- Should heartbeat mean "job still scheduled" or "job ran recently"?

Edge cases:
- Scheduled job refers to a deleted saved record
- Scheduled job fails repeatedly
- User edits the registry outside the tool
- Launchd job exists but the registry entry was removed

## Usability Questions

These questions matter for the overall feel of the product:

- Should there be a quiet mode for experienced users?
- Should there be a `--json` output mode early, or only after the human flow is stable?
- Should all guided screens allow `b` for back?
- Should paths be auto-expanded and echoed back before confirmation?
- Should the tool suggest fixes when it detects common mistakes?
- Should the tool remember recent paths for faster repeated use?
- Should the main menu show recent saved jobs?
- Should "save this link" happen before or after the success message?
- Should success screens propose a next action automatically?

## Safety Questions

- Should `--yes` still stop on directory replacement cases?
- Should the tool require extra confirmation for risky operations outside the home folder?
- Should the tool warn before scanning `/` because it may be slow?
- Should overwrite of existing symlinks be considered low risk or medium risk?
- Should saved sync runs require explicit confirmation the first time only?

## Recommended Decisions To Make Early

Before building too much, we should settle:

1. Whether guided mode defaults to main menu or direct create flow
2. Whether successful creates are auto-saved or opt-in
3. What `check --saved` should classify as missing vs broken vs mismatched
4. Whether bulk mode is strict by default or partial-success by default
5. Whether sync should ignore macOS junk files by default
6. Whether scheduling installs directly or generates a reviewable setup first
