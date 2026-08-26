---
schema: make-a-change/decisions/v1
---

# Decisions

Architectural decision log and design choices for this repository.
Format adheres to [make-a-change](https://github.com/alexsmedile/make-a-change).

## Accepted

### 2026-08-26: Build the TUI on Textual <!-- ref: adr-001 -->

- **Context**: ghostlink has no interactive surface. The registry, lifecycle
  history and live link health are all queryable but only as one-shot CLI output,
  so inspecting a broken setup means running `list`, `check` and `history`
  separately and correlating by eye. Candidate libraries were Textual, Rich,
  prompt_toolkit, urwid and stdlib `curses`. The binding constraint is that the
  package currently has **zero runtime dependencies** — every import is stdlib and
  `output/renderers.py` returns plain strings.
- **Decision**: Use **Textual** for the TUI, shipped as an optional extra
  (`pip install ghostlink[tui]`) so the core CLI remains dependency-free. Adopt
  **Rich** first inside `output/renderers.py` behind a capability check, as it is
  Textual's own render layer — Rich renderables pass straight into Textual
  widgets, making this one dependency direction rather than two.
- **Consequences**:
  - *Positive*: `DataTable` maps onto registry records without hand-rolled paging;
    `Tree` fits link graphs; filtering and key bindings come from the framework.
    `services/lifecycle_service.py` already computes `observed` state and
    `unhealthy_registry_candidates()`, so the TUI consumes existing structured
    data instead of new queries. Prior in-house experience with Textual for
    navigating database-backed link records lowers the delivery risk.
  - *Negative*: First runtime dependency in the project's history, and Textual
    pulls `rich` plus `typing-extensions` transitively. The optional-extra split
    means two supported install shapes to test. Textual's API has moved fast
    across releases — pin a floor version and watch upgrades.
  - *Neutral*: `curses` was the only zero-dependency option and was rejected —
    everything would be hand-rolled, with no mouse support and a poor Windows
    story, for a tool whose value is inspection ergonomics.
- **Spawns**: [TODO] Build a TUI for browsing saved links, health status and
  history <!-- ref: tui -->

## Proposed

## Superseded
