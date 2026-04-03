# Sync & Schedules

## Sync

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

Using a config file and profile:

```bash
ghostlink sync diff docs-sync --config links.json --profile dev
ghostlink sync run docs-sync --config links.json --profile dev --dry-run
```

## Schedule

```bash
ghostlink schedule add skills-sync --every 30m --write
ghostlink schedule list
ghostlink schedule show skills-sync

# run manually and update heartbeat metadata
ghostlink schedule run skills-sync

ghostlink schedule remove skills-sync
```
