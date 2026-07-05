---
status: verified
priority: high
owner: alex
updated: 2026-07-05
build: b1
summary: "Close managed symlink lifecycle gaps across discovery, indexing, history, health checks, and cleanup"
related:
  - ../../PRD.md
  - ../../SPEC.md
---

# Plan — managed-link-lifecycle

## 1. Goal

Make Ghostlink’s managed-link lifecycle complete: discover filesystem links, optionally index them, compare live state with saved intent, inspect history, repair drift, and clean stored data safely.

## 2. Constraints

- Keep the registry schema at version 1 and preserve existing saved data.
- Treat filesystem state as current reality and registry state as managed intent.
- Keep discovery read-only; indexing, adoption, repair, and cleanup remain explicit mutations.
- Stay standard-library-only and preserve existing CLI aliases and JSON fields.
- Leave `articles/` untouched.

## Understanding

### How it works now

`find` scans the filesystem, while `list` and `status` read saved registry metadata. Creation is not consistently logged, discovered links cannot be indexed, the run log contains two legacy shapes, and cleanup has no supported workflow.

### What changes

Add live inventory comparison, lifecycle history, idempotent indexing, consistent check scopes and filters, conservative registry cleanup, explicit history retention, and normalized event logging.

### What stays the same

Relation-set `import` remains an alias for `apply`; `repair` continues to make filesystem state match registry intent; no daemon, notification service, indexed-root persistence, or automatic deletion is added.

## 3. Milestones

- M1 — Normalized lifecycle events and backward-compatible history are queryable.
- M2 — Saved inventory shows live filesystem discrepancies and checks use consistent scopes.
- M3 — Filesystem links can be indexed idempotently with explicit conflict adoption.
- M4 — Registry and history cleanup are previewable, explicit, and atomic.
- M5 — Public docs, skill routing, versions, and verification reflect the shipped lifecycle.

## 4. Tasks

See `TASKS.md`.

## 5. Dependencies

- Current `chore/repository-hygiene` commits are the base of this stacked branch.
- Existing registry and run-log compatibility tests remain authoritative.

## 6. Validation

- M1 — History tests cover ordering, filters, legacy normalization, and lifecycle event logging.
- M2 — CLI tests cover every link health state, bare check, filters, JSON observed state, and non-mutating list behavior.
- M3 — Index tests cover new, repeated, broken, collision, keep, adopt, dry-run, and JSON flows.
- M4 — Cleanup tests cover explicit selection, threshold requirements, malformed logs, previews, confirmation, and atomic retention.
- M5 — Full pytest, compile, manifest, CLI help, skill validation, and Spectacular verification checks pass.

## 7. Deliverables

- New `history`, `index`, and `cleanup` command surfaces.
- Focused lifecycle services and normalized event storage.
- Updated tests, docs, changelog, roadmap, version metadata, and Ghostlink skill.
- Verified Spectacular request artifacts.
