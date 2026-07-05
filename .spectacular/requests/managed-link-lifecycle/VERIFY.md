---
updated: 2026-07-05
related:
  - PLAN.md
---

# Verify — managed-link-lifecycle

## Automated {run}

- [x] pytest -q
- [x] python -m compileall -q src
- [x] python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/ghostlink-skill

## Contracts {assert}

- [x] bare `ghostlink check` routes to saved-link health checks
- [x] `find` remains read-only and relation-set `import` remains unchanged
- [x] registry schema remains version 1 and run-log legacy entries remain readable
- [x] `articles/` has no staged or committed changes

## CLI behavior {judge}

- [x] list output makes observed filesystem truth and registry intent discrepancies unambiguous
- [x] destructive cleanup and adoption flows communicate their consequences before mutation
