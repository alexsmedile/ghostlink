# Sync and Schedule

Use sync jobs for explicit one-way folder copies. Do not describe sync as symlink creation: it copies or updates files according to the computed plan.

## Save a sync job

```bash
ghostlink sync save \
  --name skills-sync \
  --source ~/skills \
  --dest ~/backup/skills
```

## Preview and run

Inspect the diff, then dry-run before applying:

```bash
ghostlink sync diff skills-sync
ghostlink sync run skills-sync --dry-run -y
ghostlink sync run skills-sync -y
```

A non-zero `sync diff` exit code can mean work is pending rather than an execution failure.

Use a portable config when appropriate:

```bash
ghostlink sync diff docs-sync --config links.json --profile dev
ghostlink sync run docs-sync --config links.json --profile dev --dry-run -y
```

## Schedule with launchd

Preview schedule content before writing it:

```bash
ghostlink schedule add skills-sync --every 30m
ghostlink schedule add skills-sync --every 30m --write
```

Inspect and manage schedules:

```bash
ghostlink schedule list
ghostlink schedule show skills-sync
ghostlink schedule run skills-sync
ghostlink schedule remove skills-sync
```

Scheduling is supported for saved link checks and saved sync jobs. Report whether a command only previewed the launchd file or wrote it.
