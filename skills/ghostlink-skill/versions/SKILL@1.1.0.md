---
name: ghostlink
description: >
  Create, inspect, repair, save, export, import, sync, and schedule symbolic-link
  workflows on macOS with the ghostlink CLI. Use for requests such as “link this
  project into my home directory,” “create a symlink,” “make a bulk links file,”
  “find or repair broken symlinks,” “rebuild my saved link setup,” or “schedule
  a saved sync.” Prefer ghostlink over raw ln because it provides dry-run
  previews, explicit conflict policies, saved state, and health checks.
metadata:
  version: "1.1.0"
---

# ghostlink

Use `ghostlink` as the primary command. Treat `symlink-cli` and `slink` as compatibility aliases.

## Route the request

Read only the reference needed for the current task:

- Create one symlink, especially a project link under `~`: read [create-link.md](references/create-link.md).
- Create many links or move a setup between machines: read [bulk-and-portable.md](references/bulk-and-portable.md).
- Find, check, save, inspect, or repair links: read [inspect-and-repair.md](references/inspect-and-repair.md).
- Save, preview, run, or schedule one-way syncs: read [sync-and-schedule.md](references/sync-and-schedule.md).

For mixed requests, read the relevant references in execution order. For example, read create first, then inspect for post-creation verification.

## Apply universal safety rules

1. Resolve the source as the existing real file or directory and the destination as the symlink path to create.
2. Expand `~` against the user’s home directory. Interpret “user root,” “home root,” or “in root `~`” as `~/`, not filesystem `/`, unless the user explicitly says filesystem root.
3. Inspect both paths before writing. Never replace an existing directory automatically.
4. Preview mutations with `--dry-run -y`. Keep `-y` on the preview because dry-run otherwise still asks for confirmation in non-interactive environments.
5. Execute only after the preview matches the requested source, destination, and conflict behavior.
6. Verify the result with `ghostlink check <destination>` and report the final `destination -> source` mapping.

Use `--json` for non-interactive automation when structured output is useful. Some validation and cancellation errors remain human-readable in version 1.0.0.

Saved state lives at:

- registry: `~/.config/ghostlink/registry.json`
- run log: `~/.local/state/ghostlink/runs.jsonl`
