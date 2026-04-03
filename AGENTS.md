# Repository Guidelines

## Project Structure & Module Organization

`ghostlink` uses the `src/` layout. Active code lives in `src/ghostlink/`:

- `cli/`: argument parsing and command dispatch
- `domain/`: models, validation, path rules, and result types
- `services/`: create, find, check, repair, config, sync, and schedule flows
- `storage/`: registry and run-log persistence
- `output/`: human-readable renderers and prompts
- `integrations/`: macOS-specific adapters such as `launchd`

Legacy Python import compatibility is preserved through `src/symlink_cli/`. Tests live in `tests/`. User-facing docs are in `README.md` (overview) and `docs/` (reference); archived planning material is under `_archive/`.

## Build, Test, and Development Commands

Use Python 3.9+.

- `pipx install .`: install the published CLI locally
- `pipx install -e .`: editable install for development
- `python -m ghostlink.core --help`: inspect the live package entrypoint
- `python -m symlink_cli.core --help`: verify the legacy Python compatibility shim
- `pytest -q`: run the full test suite
- `python -m compileall src`: quick syntax check

For safe manual checks, prefer dry-run commands such as:

```bash
ghostlink create --bulk links.txt --dry-run
ghostlink sync run skills-sync --dry-run
```

## Coding Style & Naming Conventions

Keep changes standard-library-only unless there is a strong reason to add a dependency. Use 4-space indentation, type hints on public functions, and `Path`-first filesystem handling. Use `snake_case` for functions and variables, `UPPER_CASE` for constants, and `PascalCase` for dataclasses and enums.

CLI output should stay plain, compact, and predictable. Keep the current status style consistent: `[OK]`, `[ERR]`, `[SKIP]`, `[DRY]`, `[BROKEN]`, and similar health labels.

## Testing Guidelines

The project uses `pytest`. Add focused tests in files named `test_<feature>.py`. Cover both human and scripted flows where behavior matters, especially:

- path normalization
- bulk parsing
- conflict handling
- saved record updates
- compatibility commands and import paths
- JSON output stability
- sync and schedule status metadata

## Commit & Pull Request Guidelines

Follow Conventional Commit style, for example `feat: add schedule heartbeat metadata` or `docs: refresh publish-ready readme`. Pull requests should explain user-visible behavior changes, compatibility impact, and any storage-format implications. If a change affects CLI output or docs, update the relevant file in `docs/` (and `README.md` if the overview changes) in the same PR.

## Security & Configuration Tips

`ghostlink` creates symlinks, updates saved state, and can run sync jobs. Prefer `--dry-run` before destructive operations, avoid testing against macOS system paths unless required, and do not commit machine-specific absolute paths, private directories, or local registry artifacts.
