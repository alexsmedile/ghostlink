# Inspect and Repair Links

Use these workflows to discover links, check managed state, preserve intent, and repair broken or mismatched destinations.

## Find links

```bash
ghostlink find ~/Desktop
ghostlink find ~/Desktop --broken --depth 2
ghostlink find ~/Desktop --broken --output broken.txt
```

## Check health

Check one path or all saved links:

```bash
ghostlink check ~/spectacular
ghostlink check --saved
ghostlink check --issues
```

Bare `ghostlink check` is equivalent to `check --saved`. Use `--issues` for every non-OK state, `--broken` for broken links only, and `--depth` for directory scans. Use `--json` when a script will consume the successful result.

## Save and inspect records

```bash
ghostlink save --name docs-link --source ~/Docs --dest ~/Desktop/Docs
ghostlink list
ghostlink show docs-link
ghostlink status
```

`list` reports the live observed target for saved links without updating saved health timestamps. Use `check` when registry health metadata should be refreshed.

Manage record names without changing the underlying link:

```bash
ghostlink rename docs-link docs-shortcut
ghostlink remove docs-shortcut
```

## Repair

Preview repairs first:

```bash
ghostlink repair docs-link --dry-run -y
ghostlink repair --saved --dry-run -y
ghostlink repair --bulk links.txt --dry-run -y
```

Then remove `--dry-run` from the verified command. Repair defaults to overwrite behavior for managed link destinations, but it still refuses automatic directory removal.
