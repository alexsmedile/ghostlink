# Create One Link

Use this workflow for the most common request: expose an existing project, folder, or file at a convenient symlink path, often directly under `~`.

## Determine direction

Map the request into:

- `source`: the existing real path
- `destination`: the new symlink path

For “link the Spectacular project in my home directory,” use:

```text
source      = /Users/you/path/to/spectacular
destination = ~/spectacular
```

If direction is unclear, inspect both candidates. Infer the existing path as the source and the absent path as the destination when that matches the request. Ask one concise question if both exist or neither exists.

## Preflight

Confirm that the CLI is available and inspect the paths:

```bash
ghostlink --version
ls -ld "/absolute/source" "$HOME" "$HOME/link-name" 2>/dev/null || true
```

Stop if the source does not exist. If the destination exists, identify whether it is a symlink, file, or directory before choosing a conflict policy.

## Preview

Use the explicit command form so source and destination remain obvious:

```bash
ghostlink create \
  --source "/absolute/source" \
  --dest "$HOME/link-name" \
  --dry-run -y
```

Verify that the preview names the intended mapping. `--dry-run` does not suppress confirmation by itself; include `-y` for non-interactive execution.

## Create

Remove only `--dry-run` from the verified command:

```bash
ghostlink create \
  --source "/absolute/source" \
  --dest "$HOME/link-name" \
  -y
```

Use `--relative` only when the user explicitly wants a relative symlink target.

## Handle conflicts

Default to `ask`. Choose another policy only with clear user intent:

- `skip`: preserve the existing destination
- `backup`: rename an existing file or symlink, then create the link
- `overwrite`: replace an existing file or symlink

Never use `overwrite` to remove a directory; ghostlink refuses automatic directory removal.

## Verify and report

```bash
ghostlink check "$HOME/link-name"
readlink "$HOME/link-name"
```

Report one unambiguous mapping:

```text
~/link-name -> /absolute/source
```

If the user wants repeatable health checks, add `--save-name <name>` during creation or save the link afterward.
