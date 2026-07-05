# Repository Guidelines

## Project Structure & Module Organization

Active code uses the `src/` layout under `src/ghostlink/`:

- `cli/`: argument parsing and command dispatch
- `domain/`: models, validation, paths, and result types
- `services/`: link, lifecycle, config, sync, and schedule flows
- `storage/`: registry and run-log persistence
- `output/`: human-readable renderers and prompts
- `integrations/`: macOS-specific adapters such as `launchd`

Legacy imports remain in `src/symlink_cli/`. Tests live in `tests/`; user docs
live in `README.md` and `docs/`.

## Build, Test, and Development Commands

Use Python 3.9+.

- `pipx install .`: install an isolated snapshot of the local package
- `pipx install --force .`: refresh that snapshot after source changes
- `pipx install --force --editable .`: link a development install to this checkout
- `ghostlink --version`: verify which CLI release is active
- `python -m ghostlink.core --help`: inspect the live package entrypoint
- `python -m symlink_cli.core --help`: verify the legacy Python compatibility shim
- `pytest -q`: run the full test suite
- `python -m compileall src`: quick syntax check

Tests also guard package, CLI, README, changelog, and active-skill versions.

`pipx` exposes `ghostlink`, `symlink-cli`, and `slink` as command symlinks under
`~/.local/bin/`. Prefer the editable install during development; use a normal
install when testing packaged behavior.

Prefer safe manual previews such as:

```bash
ghostlink create --bulk links.txt --dry-run
ghostlink sync run skills-sync --dry-run
```

## Coding Style & Naming Conventions

Prefer the standard library. Use four spaces, public-function type hints, and
`Path`-first filesystem handling. Use `snake_case` for functions, `UPPER_CASE`
for constants, and `PascalCase` for classes and enums.

Keep CLI output compact and consistent with `[OK]`, `[ERR]`, `[SKIP]`,
`[DRY]`, `[BROKEN]`, and related health labels.

## Testing Guidelines

Add focused `pytest` files named `test_<feature>.py`. Cover:

- path normalization
- bulk parsing
- conflict handling
- saved record updates
- compatibility commands, imports, and JSON stability
- sync, schedule, history, index, and cleanup metadata
- lifecycle history, indexing, cleanup, and live registry/filesystem discrepancies

## Commit & Pull Request Guidelines

Use Conventional Commits, for example `feat: add lifecycle filters`. Pull
requests must describe user-visible behavior, compatibility, and storage-format
effects. Update relevant `docs/` files—and `README.md` for overview changes—in
the same PR.

## Security & Configuration Tips

Prefer `--dry-run` before mutations. Avoid macOS system paths and never commit
machine-specific paths, private directories, or local registry data.
