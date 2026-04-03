# Safety & Compatibility

## Safety

`ghostlink` is cautious by default:

- `--dry-run` previews create, repair, apply, and sync work before writing
- `--conflict ask|skip|overwrite|backup` controls what happens to existing destinations
- `-y` suppresses interactive confirmations
- directory removal is refused automatically
- broad `find` scans skip some macOS system paths
- saved checks, repairs, sync runs, and schedules update status metadata

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
