---
version: 1.2
updated: 2026-07-05
summary: "Safe, inspectable, and repeatable symlink lifecycle management for macOS"
kit: coding
---

# ghostlink — Product Requirements Document

## 1. Vision

Make symbolic links maintainable relationships rather than invisible filesystem trivia: safe to create, easy to discover, explicit to manage, portable between machines, and repairable when reality drifts from intent.

## 2. Problem

macOS users who rely on symlinks across projects and configuration folders lose track of why links exist, discover breakage late, and cannot reliably rebuild their setup on another machine.

## 3. Target users

Technical macOS users who organize projects, tools, dotfiles, or skills with symlinks and need a terminal-first workflow without adopting a daemon or third-party runtime.

## 4. Deliverable

A standard-library Python CLI, compatibility aliases, portable relation-set format, local managed registry, lifecycle history, and reusable agent skill.

## 5. Goals & success criteria

- Preview every destructive or bulk mutation before execution.
- Distinguish live filesystem state from saved managed intent in user-visible output.
- Discover and optionally manage existing links without making discovery itself mutating.
- Detect every managed-link discrepancy as `missing`, `broken`, `mismatch`, or `not-link`.
- Preserve enough intent to repair managed links and rebuild setups on another machine.
- Keep scripted outputs and storage schemas backward-compatible within a major release.

## 6. Non-goals

- Background filesystem watching or a daemon by default.
- Automatic deletion of unhealthy registry records.
- Treating sync copies as symlinks.
- Replacing Finder or becoming a general-purpose file manager.

## 7. Constraints

- Python 3.9+ and standard library only.
- macOS-first behavior with cautious handling of system paths and launchd integration.
- Plain local files for registry and run-log persistence.
- Explicit confirmation for adoption, repair, overwrite, and cleanup decisions.

## 8. First milestone

Ship the managed-link lifecycle: live inventory, optional indexing, history, consistent checks, repair, and explicit cleanup with complete regression coverage.
