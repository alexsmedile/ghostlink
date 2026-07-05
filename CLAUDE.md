# CLAUDE.md

This file gives Claude Code a concise map of the active `ghostlink` codebase.

## Overview

`ghostlink` is a standard-library Python CLI for guided symlink management on macOS. The product name is `ghostlink`. Compatibility commands remain available:
- `ghostlink`
- `symlink-cli`
- `slink`

The real package now lives in `src/ghostlink/`. A small compatibility shim remains in `src/symlink_cli/` for legacy Python import paths.

## Install And Run

```bash
# isolated snapshot; rerun with --force after source changes
pipx install .

# editable development install linked to this checkout
pipx install --force --editable .

ghostlink --version
python -m ghostlink.core --help
python -m symlink_cli.core --help
```

`pipx` exposes the three command aliases as symlinks under `~/.local/bin/`.
Use `pipx install --force .` to refresh a non-editable local installation.

## Package Structure

```text
src/ghostlink/
  cli/
  compat/
  domain/
  integrations/
  output/
  services/
  storage/
  core.py
```

Key entry points:
- `src/ghostlink/cli/main.py`: command dispatch
- `src/ghostlink/cli/parser.py`: argparse structure
- `src/ghostlink/services/`: operational logic
- `src/ghostlink/storage/`: registry and run-log persistence

## Current Scope

Implemented:
- guided mode
- fast-path create
- bulk create
- find, check, repair
- saved link and sync records
- sync diff/run/save
- schedule add/list/show/run/remove
- relation-set export/apply/import
- relative-link mode
- `--json` output for machine-readable flows
- live saved-link comparison in `list`
- default saved-link checks plus `--issues`, `--broken`, and `--depth`
- existing-link indexing with explicit `keep` or `adopt` conflict behavior
- lifecycle history and conservative registry/history cleanup

## Active Docs

- `README.md`: overview and quick start
- `docs/commands.md`: complete command reference, including lifecycle management
- `docs/sync-and-schedules.md`: sync and schedule commands
- `docs/relation-sets.md`: export/apply/import + JSON schema
- `docs/bulk-format.md`: bulk file syntax
- `docs/json-and-exit-codes.md`: `--json` usage and exit code table
- `docs/safety-and-compatibility.md`: safety flags and legacy aliases
- `AGENTS.md`: contributor guide
- `ROADMAP.md`: future work
- `CHANGELOG.md`: release/build summary
- `_archive/`: completed planning docs
