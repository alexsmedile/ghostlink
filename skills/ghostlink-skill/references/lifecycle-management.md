# Manage the Link Lifecycle

Use this workflow to bridge read-only filesystem discovery with optional registry management. Keep the distinction explicit:

- filesystem state is what currently exists
- registry state is what a managed link is intended to be
- `repair` makes filesystem state match registry intent
- `index --on-conflict adopt` makes registry intent match filesystem state

## Discover before indexing

```bash
ghostlink find ~/Projects --depth 2
ghostlink index ~/Projects --depth 2 --dry-run -y
```

`find` never writes registry data. `index` is the explicit opt-in mutation. Repeating `index` on the same path is idempotent by destination, so no separate reindex command is needed.

## Index links

Preserve registry intent on conflicts:

```bash
ghostlink index ~/Projects --depth 2 --on-conflict keep -y
```

Adopt the filesystem’s observed target only when the user explicitly chooses filesystem-wins behavior:

```bash
ghostlink index ~/Projects --depth 2 --on-conflict adopt -y
```

Without `--on-conflict`, prompt for each discrepancy. New records use the destination basename and numeric suffixes when names collide.

## Compare current and intended state

```bash
ghostlink list
ghostlink check
ghostlink check --issues
```

`list` performs a live, read-only comparison. `check` persists health status and timestamps. Never describe stale registry status as current filesystem truth.

## Inspect history

```bash
ghostlink history
ghostlink history --type link --limit 20
ghostlink history --action repair --name docs-link --since 30d
```

History is newest-first and contains committed lifecycle events. Dry runs are not recorded.

## Clean stored data

Preview registry cleanup, then name every record to remove in non-interactive execution:

```bash
ghostlink cleanup registry --dry-run
ghostlink cleanup registry --name missing-link --dry-run
ghostlink cleanup registry --name missing-link -y
```

Keep unhealthy records by default because they may be required by `repair`.

Require an explicit history boundary:

```bash
ghostlink cleanup history --older-than 90d --dry-run
ghostlink cleanup history --older-than 90d -y
```

Do not clean malformed history; report the error and leave the file untouched.
