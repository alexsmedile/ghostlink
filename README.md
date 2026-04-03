# ghostlink

**invisible links between your files**

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

`ghostlink` is a guided macOS terminal tool for working with symbolic links, saved link sets, sync jobs, and schedulable file workflows.

It is built around a simple idea:

**symlinks, simplified**

Create, inspect, repair, and automate links with less risk, less guesswork, and less terminal friction.

`ghostlink` helps you **connect files without moving them**.

## Why ghostlink

Symlinks are powerful, but raw `ln -s` workflows are easy to get wrong.

`ghostlink` adds:

- guided creation for one-off links
- bulk linking from mapping files
- checks for broken and missing links
- saved records for important relationships
- repair flows for managed links
- one-way sync jobs for folder workflows
- schedule support with visible heartbeat metadata
- portable relation-set files for repeatable setups

## Use Cases

Use `ghostlink` when you want to:

- keep project folders reachable from multiple places without duplicating files
- manage shortcuts to docs, assets, agent folders, or working directories
- track important symlinks and check them later
- rebuild the same link setup on a new machine
- compare and sync folders without mixing sync logic into raw symlink commands
- automate repeated checks or sync jobs while keeping the status visible

## Features

- Guided interactive mode with no arguments
- Fast-path create: `ghostlink <source> <destination>`
- Bulk create from a file
- Relative-link mode for repo-friendly setups
- Find symlinks in a tree
- Check one path, one folder, or saved links
- Repair saved links or bulk-defined links
- Save, list, show, rename, and remove managed records
- One-way sync diff, run, and save
- Schedule add, list, show, run, and remove
- Export and apply relation sets with profiles
- Machine-readable `--json` output for scripting
- Compatibility commands: `symlink-cli` and `slink`

## Installation

Requirements:

- macOS
- Python 3.9+
- `pipx`

Install with `pipx`:

```bash
pipx install ghostlink
```

Local development install:

```bash
pipx install -e .
PYTHONPATH=src python -m ghostlink.core --help
```

Compatibility entry points still work:

```bash
symlink-cli --help
slink --help
```

## Quick Start

Guided mode:

```bash
ghostlink
```

Create one link:

```bash
ghostlink ~/Projects/site ~/Desktop/site
```

Preview a change without writing:

```bash
ghostlink ~/Projects/site ~/Desktop/site --dry-run
```

Create a relative symlink:

```bash
ghostlink create --source ~/Projects/site --dest ~/Desktop/site-link --relative
```

## Core Commands

### Create links

Create one link:

```bash
ghostlink create --source ~/Docs --dest ~/Desktop/Docs
```

Create many links from a file:

```bash
ghostlink bulk links.txt
ghostlink create --bulk links.txt --separator ","
ghostlink create --bulk links.txt --dry-run
```

Conflict handling:

```bash
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --conflict backup
ghostlink create --bulk links.txt --conflict overwrite -y
```

### Find, check, and repair

Find links:

```bash
ghostlink find ~/Desktop
ghostlink find ~/Desktop --broken --depth 2
ghostlink find ~/Desktop --broken --output broken.txt
```

Check links:

```bash
ghostlink check ~/Desktop
ghostlink check --saved
```

Repair managed links:

```bash
ghostlink repair docs-link -y
ghostlink repair --saved -y
ghostlink repair --bulk links.txt -y
```

### Save and manage records

Save a link:

```bash
ghostlink save --name docs-link --source ~/Docs --dest ~/Desktop/Docs
```

Inspect saved records:

```bash
ghostlink list
ghostlink show docs-link
ghostlink rename docs-link docs-shortcut
ghostlink remove docs-shortcut
ghostlink status
```

### Sync workflows

Save a one-way sync job:

```bash
ghostlink sync save --name skills-sync --source ~/skills --dest ~/backup/skills
```

Preview and run:

```bash
ghostlink sync diff skills-sync
ghostlink sync run skills-sync --dry-run
ghostlink sync run skills-sync
```

You can also resolve sync jobs from a config file:

```bash
ghostlink sync diff docs-sync --config links.json --profile dev
ghostlink sync run docs-sync --config links.json --profile dev --dry-run
```

### Schedule workflows

Create and inspect schedules:

```bash
ghostlink schedule add skills-sync --every 30m --write
ghostlink schedule list
ghostlink schedule show skills-sync
```

Run a scheduled job manually and update heartbeat metadata:

```bash
ghostlink schedule run skills-sync
```

Remove a schedule:

```bash
ghostlink schedule remove skills-sync
```

## Relation Sets

`ghostlink` can export and apply portable JSON relation sets.

Export a profile:

```bash
ghostlink export links.json --profile dev
```

Apply a profile:

```bash
ghostlink apply links.json --profile dev -y
```

Import a profile, create relative links, and save imported records:

```bash
ghostlink import links.json --profile work --relative --save -y
```

Example format:

```json
{
  "schema_version": 1,
  "profiles": {
    "dev": {
      "links": [
        {
          "name": "docs-link",
          "source": "~/Docs",
          "destination": "~/Desktop/Docs",
          "conflict_policy": "ask"
        }
      ],
      "syncs": [
        {
          "name": "docs-sync",
          "source": "~/Docs",
          "destination": "~/Backup/Docs",
          "mode": "one-way"
        }
      ]
    }
  }
}
```

Rules:

- `apply` and `import` read one profile at a time
- relation sets can include both `links` and `syncs`
- relative paths are resolved from the relation-set file location
- `--relative` creates relative symlink targets
- destination parent folders must already exist before apply

## Bulk File Format

Each line defines:

```text
source -> destination
```

Example:

```text
# comment
~/Documents/project -> ~/Desktop/project-link
"/Users/you/My Files/report.pdf" -> "~/Desktop/report-link.pdf"
```

Rules:

- `#` starts a comment
- empty lines are ignored
- quotes are allowed for paths with spaces
- default separator is `->`
- relative paths in a bulk file are resolved from that file's folder

## JSON Output

For scripting and automation, use `--json`:

```bash
ghostlink find ~/Desktop --json
ghostlink check --saved --json
ghostlink status --json
ghostlink sync diff docs-sync --config links.json --profile dev --json
```

## Safety

`ghostlink` is designed to be cautious by default.

- `--dry-run` previews create, repair, apply, and sync work
- `--conflict ask|skip|overwrite|backup` controls existing destinations
- `-y` suppresses confirmations
- directory removal is refused automatically
- broad `find` scans skip some macOS system paths
- saved checks, repairs, sync runs, and schedules update status metadata

## Exit Codes

- `create` and bulk runs return non-zero if any operation fails
- `find` returns non-zero when broken links are found
- `check --saved` returns non-zero when a saved link is missing, broken, or mismatched
- `sync diff` returns non-zero when there is work to do
- `sync run` returns non-zero on execution errors
- `schedule run` updates heartbeat metadata and returns the job result code

## Compatibility

`ghostlink` is the primary name.

Legacy commands remain available:

- `symlink-cli`
- `slink`

Legacy Python module compatibility is also preserved:

```bash
python -m ghostlink.core --help
python -m symlink_cli.core --help
```

## Documentation

- [ROADMAP.md](ROADMAP.md)
- [CHANGELOG.md](CHANGELOG.md)
- [_archive/PLAN.md](_archive/PLAN.md)
- [_archive/IDEA.md](_archive/IDEA.md)
- [_archive/PRD.md](_archive/PRD.md)
- [_archive/ARCHITECTURE.md](_archive/ARCHITECTURE.md)
- [_archive/TUI.md](_archive/TUI.md)
- [_archive/WORKFLOWS.md](_archive/WORKFLOWS.md)
- [_archive/AGENT-PLAN.md](_archive/AGENT-PLAN.md)

## License

MIT
