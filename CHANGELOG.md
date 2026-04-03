# Changelog

All notable changes to `ghostlink` are documented here.

## 1.0.0

Initial public `ghostlink` release.

### Brand And Packaging

- Renamed the project to `ghostlink`
- Kept command compatibility for `ghostlink`, `symlink-cli`, and `slink`
- Renamed the internal Python package to `ghostlink`
- Preserved legacy Python import compatibility through `symlink_cli`

### Symlink Workflows

- Added guided interactive mode
- Added fast-path single-link creation
- Added bulk create from mapping files
- Added conflict handling with `ask`, `skip`, `overwrite`, and `backup`
- Added relative-link creation mode
- Added saved link records and managed link checks
- Added repair flows for saved links and bulk-defined links

### Discovery And Health

- Added `find` with broken-link filtering
- Added recursion depth control and output export
- Added `check` for paths, trees, and saved links
- Added richer `status` summaries for managed records
- Added audit logging for saved checks and repairs

### Sync And Scheduling

- Added one-way sync save, diff, and run workflows
- Added saved sync metadata such as `last_status` and `last_run_at`
- Added schedule add, list, show, run, and remove
- Added schedule heartbeat metadata including last run, exit code, and message

### Portable Configs And Automation

- Added relation-set export, apply, and import workflows
- Added profile-based relation sets
- Added relation-set support for both links and sync jobs
- Added config-backed sync resolution with `--config` and `--profile`
- Added machine-readable `--json` output for key command flows

### Documentation

- Rewrote the README as a publish-ready branded GitHub document
- Added `ROADMAP.md` for future work
- Archived the completed planning documents under `_archive/`
