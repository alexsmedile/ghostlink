---
version: 1.1
updated: 2026-07-05
summary: "ghostlink roadmap — managed lifecycle now, optional automation later"
related:
  - PRD.md
  - SPEC.md
---

# ghostlink — Roadmap

## v1 (current)

- [x] Safe symlink creation, discovery, saved intent, checks, and repair
- [x] Portable relation sets, one-way sync, schedules, and JSON output
- [x] Live inventory comparison, optional indexing, lifecycle history, and explicit cleanup

## v2 — Automation informed by use

- [ ] Persist indexed roots only if repeated explicit scans prove cumbersome
- [ ] Add richer list/status filtering after observing 1.1 workflows
- [ ] Stabilize fully structured JSON error schemas

## v3+ — Terminal dashboard

- [ ] Present saved links, sync jobs, schedules, discrepancies, and heartbeat state in one terminal-first view
