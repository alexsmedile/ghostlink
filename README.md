# ghostlink

**invisible links between your files**

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![License](https://img.shields.io/badge/license-MIT-green)

`ghostlink` is a guided macOS CLI for working with symbolic links — create, inspect, repair, sync, and schedule them without the raw `ln -s` guesswork.

## Install

```bash
pipx install ghostlink
```

## Quick Start

```bash
# guided mode — no arguments needed
ghostlink

# create a link
ghostlink ~/Projects/site ~/Desktop/site

# preview without writing
ghostlink ~/Projects/site ~/Desktop/site --dry-run
```

## Core Commands

```bash
ghostlink create --source ~/Docs --dest ~/Desktop/Docs
ghostlink find ~/Desktop --broken
ghostlink check --saved
ghostlink repair --saved -y
ghostlink sync run skills-sync
ghostlink schedule add skills-sync --every 30m --write
```

## Docs

- [Commands reference](docs/commands.md)
- [Sync & schedules](docs/sync-and-schedules.md)
- [Relation sets (export/import)](docs/relation-sets.md)
- [Bulk file format](docs/bulk-format.md)
- [JSON output & exit codes](docs/json-and-exit-codes.md)
- [Safety & compatibility](docs/safety-and-compatibility.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)

## License

MIT
