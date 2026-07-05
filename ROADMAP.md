# Roadmap

## Near Term

- Finish structured JSON error coverage and stabilize schemas for scripting.
- Add richer filtering for `list` and `status` after observing the 1.1 lifecycle workflows.
- Improve import/export validation with clearer errors for malformed relation-set files.
- Add packaged release workflows and publish/update guidance for `ghostlink`.
- Evaluate persisted index roots only if repeated explicit `index PATH` scans prove cumbersome.

## Dashboard Idea

Keep the dashboard terminal-first.

Planned direction:
- a focused TUI screen, not a separate GUI
- one view for saved links, sync jobs, and schedules
- health sections for:
  - broken links
  - missing managed links
  - pending sync changes
  - schedule heartbeat status
- keyboard-first navigation
- drill-down from summary to one record

Not planned yet:
- background daemon behavior by default
- real-time filesystem watching as a required dependency

## Later

- sync profile editing from the CLI
- richer schedule inspection, including next-run estimation where possible
- optional machine-readable logs or export snapshots for automation
