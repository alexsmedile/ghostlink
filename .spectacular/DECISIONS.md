---
version: 1.0
updated: 2026-07-05
summary: "Architectural and product decisions log"
---

# Decisions

## 2026-07-05

**Context:**
**Decision:**
**Consequences:**

## 2026-07-05 — Treat filesystem state as current reality and registry state as managed intent

**Context:**
Ghostlink must surface drift without silently choosing one source over the other.

**Decision:**
Treat filesystem state as current reality and registry state as managed intent

**Consequences:**
list observes without mutation; check persists health; repair applies registry intent; index adoption explicitly applies filesystem state.

## 2026-07-05 — Use repeatable index scans instead of a separate reindex command

**Context:**
Indexed roots are not persisted and health refresh already belongs to check.

**Decision:**
Use repeatable index scans instead of a separate reindex command

**Consequences:**
index PATH is idempotent by destination; cleanup stays explicit; indexed-root persistence remains deferred.
