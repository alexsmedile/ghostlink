# Commands Reference

## Create

```bash
# fast-path (positional)
ghostlink <source> <destination>

# explicit
ghostlink create --source ~/Docs --dest ~/Desktop/Docs

# relative symlink
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --relative

# dry-run preview
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --dry-run
```

Conflict handling:

```bash
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --conflict backup
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --conflict overwrite -y
# options: ask | skip | overwrite | backup
```

## Bulk Create

```bash
ghostlink bulk links.txt
ghostlink create --bulk links.txt --separator ","
ghostlink create --bulk links.txt --dry-run
ghostlink create --bulk links.txt --conflict overwrite -y
```

See [bulk-format.md](bulk-format.md) for the file format.

## Find

```bash
ghostlink find ~/Desktop
ghostlink find ~/Desktop --broken
ghostlink find ~/Desktop --broken --depth 2
ghostlink find ~/Desktop --broken --output broken.txt
```

## Check

```bash
ghostlink check ~/Desktop
ghostlink check
ghostlink check --saved
ghostlink check --issues
ghostlink check ~/Projects --issues --depth 2
ghostlink check ~/Projects --broken --depth 2
```

With no path, `check` inspects saved links. `--issues` shows every non-OK state; `--broken` limits output to broken symlinks. A path and `--saved` cannot be combined.

## Repair

```bash
ghostlink repair docs-link -y
ghostlink repair --saved -y
ghostlink repair --bulk links.txt -y
```

## Save and Manage Records

```bash
ghostlink save --name docs-link --source ~/Docs --dest ~/Desktop/Docs

ghostlink list
ghostlink show docs-link
ghostlink rename docs-link docs-shortcut
ghostlink remove docs-shortcut
ghostlink status
```

`list` live-checks saved link destinations without updating registry metadata. It shows the filesystem’s observed target and warns when that differs from saved intent. Use `check` when the stored health timestamp should be refreshed.

## Index Existing Filesystem Links

`find` remains read-only. Use `index` when discovered links should also become managed records:

```bash
ghostlink index ~/Projects --depth 2 --dry-run -y
ghostlink index ~/Projects --depth 2 --on-conflict keep -y
ghostlink index ~/Projects --depth 2 --on-conflict adopt -y
```

Repeated scans are idempotent by normalized destination. New record names use the destination basename and receive numeric suffixes on collisions. On a discrepancy:

- `keep` preserves registry intent so `repair` can restore it
- `adopt` updates registry intent to the filesystem’s current target
- `ask` prompts for each conflict and is the default

## Lifecycle History

```bash
ghostlink history
ghostlink history --type link --limit 20
ghostlink history --action repair --name docs-link --since 30d
```

History is newest-first and includes lifecycle activity across links, syncs, and schedules. Dry runs are not recorded.

## Cleanup

Preview registry cleanup before explicitly selecting records:

```bash
ghostlink cleanup registry --dry-run
ghostlink cleanup registry --name missing-link --dry-run
ghostlink cleanup registry --name missing-link -y
```

Unhealthy records default to keep because they may be needed by `repair`. Non-interactive registry cleanup requires at least one `--name`.

History cleanup requires a retention boundary:

```bash
ghostlink cleanup history --older-than 90d --dry-run
ghostlink cleanup history --before 2026-01-01 --dry-run
ghostlink cleanup history --older-than 90d -y
```

Malformed history aborts cleanup; valid retained events are rewritten atomically.
