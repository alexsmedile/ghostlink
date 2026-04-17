---
name: ghostlink
description: >
  Use this skill when the user wants to create, inspect, repair, save, export,
  import, sync, or schedule symbolic link workflows on macOS with the
  `ghostlink` CLI. Trigger for requests like "create a symlink", "make a bulk
  links file", "find broken symlinks", "repair saved links", "export my link
  setup", or "set up a saved sync job". Use it for both one-off and repeatable
  symlink work because `ghostlink` handles path expansion, dry-run previews,
  conflict policies, and saved state safely.
---

# ghostlink

Use `ghostlink` for symlink work on macOS. The primary command is `ghostlink`; compatibility aliases `symlink-cli` and `slink` also work.

## Quick Start

```bash
ghostlink
ghostlink ~/Projects/site ~/Desktop/site
ghostlink ~/Projects/site ~/Desktop/site --dry-run
ghostlink create --source ~/Projects/site --dest ~/Desktop/site --save-name site-link -y
```

## Core Workflows

Create one link:

```bash
ghostlink create --source ~/Docs --dest ~/Desktop/Docs
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --relative
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --conflict backup
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --dry-run
```

Create many links from a file:

```bash
ghostlink bulk links.txt
ghostlink bulk links.txt --dry-run
ghostlink bulk links.txt --conflict overwrite -y
```

Find or check links:

```bash
ghostlink find ~/Desktop
ghostlink find ~/Desktop --broken --depth 2
ghostlink check ~/Desktop
ghostlink check --saved
```

Repair saved or bulk-managed links:

```bash
ghostlink repair site-link -y
ghostlink repair --saved -y
ghostlink repair --bulk links.txt -y
```

Save and manage records:

```bash
ghostlink save --name docs-link --source ~/Docs --dest ~/Desktop/Docs
ghostlink list
ghostlink show docs-link
ghostlink rename docs-link docs-shortcut
ghostlink remove docs-shortcut
ghostlink status
```

Export or apply a portable setup:

```bash
ghostlink export links.json --profile dev
ghostlink apply links.json --profile dev --save -y
ghostlink import links.json --profile work --relative --save -y
```

Run one-way syncs and schedules:

```bash
ghostlink sync save --name skills-sync --source ~/skills --dest ~/backup/skills
ghostlink sync diff skills-sync
ghostlink sync run skills-sync --dry-run
ghostlink schedule add skills-sync --every 30m --write
ghostlink schedule list
ghostlink schedule run skills-sync
```

## Bulk File Format

```text
# comments and blank lines are ignored
~/source/path -> ~/destination/link-name
"/path/with spaces/file.pdf" -> "~/Desktop/file-link.pdf"
```

- Default separator is `->`
- Override it with `--separator ","`
- Relative paths are resolved from the bulk file location

## Conflict Policies

- `ask`: prompt interactively
- `skip`: leave the destination untouched
- `overwrite`: replace an existing file or symlink
- `backup`: rename the existing file or symlink, then create the new link

`ghostlink` will not remove directories automatically.

## Saved State

Saved data lives in plain local files:

- registry: `~/.config/ghostlink/registry.json`
- run log: `~/.local/state/ghostlink/runs.jsonl`

Use saved records when the user wants repeatable checks, repairs, exports, sync jobs, or schedules instead of one-off links.
