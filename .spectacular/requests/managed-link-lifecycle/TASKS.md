---
status: verified
updated: 2026-07-05
related:
  - PLAN.md
---

# Tasks — managed-link-lifecycle

## v1

### M1 — Lifecycle history
- [x] Normalize run-log reads while preserving legacy entries.
- [x] Log link and job lifecycle mutations consistently.
- [x] Add filtered human and JSON history output.

### M2 — Live inventory and checks
- [x] Compare saved links with filesystem state during list.
- [x] Make bare check inspect saved links and validate scope combinations.
- [x] Add consistent issue, broken, and depth filters.

### M3 — Optional indexing
- [x] Add idempotent filesystem-to-registry indexing.
- [x] Derive stable names and handle registry conflicts with keep/adopt policy.
- [x] Cover broken, repeated, dry-run, interactive, and JSON cases.

### M4 — Cleanup
- [x] Add explicit-selection registry cleanup.
- [x] Add threshold-required, atomic history pruning.
- [x] Refuse unsafe non-interactive and malformed-log cleanup.

### M5 — Release and verification
- [x] Update docs, changelog, roadmap, version metadata, and skill references.
- [x] Run all automated and structural verification.
- [x] Record final request state and evidence.
