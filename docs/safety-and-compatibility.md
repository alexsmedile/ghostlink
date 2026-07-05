# Safety & Compatibility

## Safety

`ghostlink` is cautious by default:

- `--dry-run` previews create, repair, apply, and sync work before writing
- `--conflict ask|skip|overwrite|backup` controls what happens to existing destinations
- `-y` suppresses interactive confirmations
- directory removal is refused automatically
- broad `find` scans skip some macOS system paths
- saved checks, repairs, sync runs, and schedules update status metadata
- `list` compares saved link intent with live filesystem state without mutating the registry
- `find` remains read-only; only explicit `index` saves discovered links
- `index` never changes conflicting registry intent unless the user chooses `adopt`
- registry cleanup removes only explicitly selected unhealthy records
- history cleanup requires an age or date boundary and rewrites retained events atomically

## Source of Truth

The filesystem is authoritative for what currently exists. The registry records what managed links are intended to be. `check` reports and stores discrepancies, `repair` makes the filesystem match registry intent, and `index --on-conflict adopt` explicitly changes registry intent to match the filesystem.

## Compatibility

`ghostlink` is the primary command. Legacy aliases still work:

```bash
symlink-cli --help
slink --help
```

Legacy Python module paths are also preserved:

```bash
python -m ghostlink.core --help
python -m symlink_cli.core --help
```
