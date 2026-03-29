# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Python CLI tool for creating symbolic links on macOS. No dependencies beyond the standard library. Installable via `pipx` — exposes two commands: `symlink-cli` (descriptive) and `slink` (short alias), both pointing to the same entrypoint.

## Installation

```bash
pipx install .
# or for development (editable)
pipx install -e .
```

## Running the tool

```bash
# Interactive mode (default)
slink
symlink-cli

# Bulk mode from a mapping file
slink --bulk links.txt
symlink-cli --bulk links.txt

# Dry run (safe preview, no changes)
slink --bulk links.txt --dry-run

# Auto-confirm, overwrite conflicts
slink --bulk links.txt -y --conflict overwrite
```

## Bulk file format

```
# comment
~/source/path -> ~/destination/path
"/path with spaces/file" -> "~/Desktop/link"
```

Default separator is `->`, configurable with `--separator`.

## Project structure

```
src/symlink_cli/
  __init__.py
  core.py          # all logic
pyproject.toml     # package definition + entry points
_archived/
  symlink_helper.py  # original standalone script, superseded by src/
```

## Architecture

Everything lives in `src/symlink_cli/core.py`, organized in clear sections:

- **Data models** — `LinkSpec` (source+destination pair) and `OperationResult` (status + message after an operation)
- **Path utilities** — `expand_path` (resolves `~`, env vars, relative paths), `normalize_destination` (handles "drop into folder" vs "exact path" semantics)
- **Validation** — `validate_spec` checks source existence, same-path identity, and destination parent
- **Create logic** — `create_symlink` orchestrates conflict handling (ask/skip/overwrite/backup) then calls `os.symlink`
- **Interactive mode** — `interactive_collect` prompts for source/destination; two sub-modes: pick folder + name, or full path
- **Bulk parsing** — `load_bulk_specs` + `parse_bulk_line`; tries separator split, then CSV, then `shlex` fallback
- **Reporting** — `print_result` / `print_summary` format output with `[OK]` / `[ERR]` / `[SKIP]` / `[DRY]` prefixes
- **Find logic** — `walk_symlinks(root, max_depth, skip_prefixes)`: stack-based DFS using `os.scandir()`; yields `FindResult`; skips `MACOS_SKIP_PREFIXES` and permission-denied dirs silently
- **CLI** — `build_parser` + `run_interactive` / `run_bulk` / `run_find` + `main`

## Planned features (FEATURES.md)

- Search all symlinks in system or a folder
- Bulk-sync workflows (e.g. syncing AI skills/agents folders)
- Search all symlinks in system or a folder
- Bulk-sync workflows (e.g. syncing AI skills/agents folders)
