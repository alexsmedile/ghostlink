---
version: 1.1
updated: 2026-07-05
summary: "Index of Ghostlink's implemented CLI and managed-link lifecycle"
related:
  - PRD.md
  - requests/managed-link-lifecycle/PLAN.md
---

# ghostlink — System Spec

## What this system is

Ghostlink is a standard-library Python CLI for creating, discovering, managing, checking, repairing, exporting, syncing, and scheduling symbolic-link workflows on macOS. It stores managed intent in a local JSON registry and committed lifecycle events in a JSONL run log while treating the filesystem as current operational reality.

## Capabilities

- Create one or many absolute or relative symlinks with dry-run and conflict policies.
- Discover filesystem symlinks without mutation and optionally index them as managed records.
- Compare saved intent with live filesystem targets through `list` and `check`.
- Resolve discrepancies explicitly: `repair` applies registry intent; index adoption applies filesystem state.
- Query normalized lifecycle history and safely prune old history.
- Clean explicitly selected unhealthy registry records without automatic deletion.
- Export, apply, and import portable relation sets with profiles.
- Save, diff, run, and schedule one-way sync jobs with status metadata.
- Preserve `ghostlink`, `symlink-cli`, `slink`, and legacy Python import compatibility.
