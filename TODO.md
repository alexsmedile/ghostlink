---
schema: make-a-change/todo/v1
---

# Todo

Actionable tasks and development roadmap.
Format adheres to [make-a-change](https://github.com/alexsmedile/make-a-change).

> **🔴 The bundled agent skill is withdrawn.** `skills/ghostlink-skill` is not
> working as intended and has been uninstalled from local agent harnesses. It
> stays in this repo as the source of truth, work-in-progress. Do not re-install
> it into any harness until every task under **Now** is resolved.
> The CLI is unaffected — `ghostlink`, `slink` and `symlink-cli` still work, and
> the registry and run log are untouched.

## Now

- [ ] [skill] Narrow the `SKILL.md` `description` trigger surface — the skill
      activates on requests it should not handle. It currently claims a broad set
      of phrases ("link this project…", "create a symlink", "find or repair broken
      symlinks"). Scope it to what the tool handles well <!-- ref: skill-firing -->
- [ ] [skill] Resolve the nested skill path — a harness must link to
      `skills/ghostlink-skill`, not the repository root. This is a plugin repo
      wrapping a skill, which is not the flat layout most installers assume.
      Either flatten the layout or document the nesting <!-- ref: skill-nesting -->
- [ ] [core] Fix `check` false-positives — a link that resolves reports `ok` even
      when it points at a structurally wrong path. `check` validates reachability,
      not intent <!-- ref: check-fp -->
- [ ] [storage] Guarantee registry coverage — links created by ghostlink are not
      reliably registered. Observed: `create` runs present in `runs.jsonl` with no
      corresponding registry entry. The creation path must write both, or neither.
      Blocks the audit-trail claim in the positioning task
      <!-- ref: registry-coverage -->
- [ ] [release] Reconcile version drift — three sources disagree and must collapse
      to one: the CLI reports `1.1.0` (`ghostlink --version`), `CHANGELOG.md` tops
      out at `1.1.0`, but `skills/ghostlink-skill/SKILL.md` declares
      `metadata.version: "1.2.1"` (with `versions/SKILL@1.2.1.md` present).
      Suspected contributor to the mis-firing — a harness loads a skill contract
      the CLI never shipped. Pick the source of truth, derive the other two
      <!-- ref: version-drift, from: skill-firing -->

## Next

- [ ] [docs] Explain what ghostlink is actually for — the README, `SKILL.md` and
      `--help` never state the value proposition, so the tool reads as a wrapper
      around `ln -s` with extra typing. It does not compete with `ls` (which only
      reads) or with a one-off `ln -s`. The pitch is managed, reproducible,
      portable link setups <!-- ref: positioning, from: skill-firing -->

  | | `ln -s` | ghostlink |
  |---|---|---|
  | Preview before writing | none | `--dry-run -y` |
  | Existing destination | silent clobber risk | explicit conflict policy |
  | Record of what was made | none | registry + run log |
  | Verify after | manual | `check` |
  | Many links at once | shell loop | links file / relation set |
  | Move a setup to a new machine | rewrite by hand | `export` → `apply` |
  | Repair after a move | manual | `repair` |

  State the boundary honestly: for a single symlink you will never touch again,
  `ln -s` is the right tool. ghostlink pays off on setups you rebuild, migrate or
  audit. Overclaiming is what makes the current description fire on trivial
  one-off requests. ⚠️ Do not ship this positioning until the registry reliably
  records every created link — until then the audit-trail claim is aspiration,
  not behaviour.

- [ ] [core] Retain variables in link definitions — let relation sets and links
      files carry named variables instead of hardcoded absolute paths, e.g.
      `${HOME}`, `${PROJECTS}`, `${TARGET}`. `domain/paths.py` already calls
      `os.path.expandvars` and `expanduser` in `expand_path()` and
      `normalize_path()`, so environment variables expand on input — but the fully
      resolved absolute path is what reaches the registry and `export`. The
      variable is lost at that boundary, which is why exported setups are not
      portable. Retain the unexpanded form alongside the resolved one and have
      `export` emit the symbolic form <!-- ref: vars-retain -->
- [ ] [config] Support a `vars` block in relation-set files so a set is
      self-describing and a new machine only overrides the roots
      <!-- ref: vars-block, from: vars-retain -->

  ```json
  {
    "vars": { "PROJECTS": "~/projects", "TARGET": "~/.config" },
    "profiles": { "default": { "links": [] } }
  }
  ```

  Precedence to implement and document: CLI `--var K=V` > environment > the
  file's `vars` block > built-in defaults. Fail loudly on an undefined variable
  rather than silently writing a literal `${VAR}` path.

- [ ] [core] Make setup migration between machines actually work — the headline
      use case, currently half-built. `export --relative` and `apply --relative`
      exist, but neither survives a different home directory, username or volume
      layout. With variables in place, `export` on machine A → `apply
      --var PROJECTS=…` on machine B reproduces the setup. Add a `--remap OLD=NEW`
      escape hatch for sets exported before variables existed
      <!-- ref: migrate, from: vars-retain -->
- [ ] [core] Record individual symlinks portably — `create` should optionally
      store a link symbolically (`${PROJECTS}/app/…`) rather than fully resolved,
      so a moved source directory becomes a one-line variable change instead of a
      rebuild. Pairs with `repair` <!-- ref: portable-links, from: vars-retain -->
- [ ] [config] Add a user config layer — there is none today. Introduce
      `config.toml` in the user config dir: default conflict policy, default
      `--json`, preferred install targets. Convention: `.toml` for human-edited
      config, `.json` for machine data <!-- ref: user-config -->
- [ ] [storage] Reconcile schema versions — the registry is `schema_version: 1`
      while newer run-log records write `schema_version: 2`. The registry can also
      accumulate stale records with `last_status: null` that nothing clears.
      Files: `src/ghostlink/storage/registry.py`,
      `src/ghostlink/storage/run_log.py` <!-- ref: schema-versions -->

## Later

- [ ] [cli] Add a `gl` shorthand with a `-s` symlink flag
      <!-- ref: gl-shorthand -->

  ```
  gl -s <source> <destination>     # == ghostlink create <source> <destination>
  ```

  - [ ] [cli] Register `gl` in `pyproject.toml` under `[project.scripts]`
        alongside `ghostlink` / `symlink-cli` / `slink`, all pointing at
        `ghostlink.core:main`. A commented alias-candidate block already exists
        there to extend
  - [ ] [cli] Document the `gl` collision — it is a common shell alias for
        `git log` and ships with the oh-my-zsh git plugin. Keep `gl` opt-in
        rather than installing it by default
  - [ ] [cli] Route `-s` through the same code path as `create`, not a parallel
        implementation, so the dry-run preview, conflict policy and post-create
        `check` apply identically
  - [ ] [cli] Ensure `-s` never implies `-y` — it is a typing shortcut, not a
        `--force`

- [ ] [cli] Support multi-target install — `ghostlink install` should understand a
      configurable set of install targets and install/uninstall across all of them
      in one command, rather than one invocation per target
      <!-- ref: multi-install -->
- [ ] [ui] Build a TUI for browsing saved links, health status and history —
      there is no interactive surface today <!-- ref: tui -->

  **Constraint that drives the choice**: ghostlink currently has **zero runtime
  dependencies** — every import is stdlib, and `output/renderers.py` returns plain
  strings. A TUI is the first thing that would break that. Decide deliberately
  whether the TUI ships as an **optional extra** (`pip install ghostlink[tui]`,
  declared under `[project.optional-dependencies]`) so the core CLI stays
  dependency-free. Recommended: yes, optional.

  **Library options (Python):**

  | Library | Model | Deps | Fit |
  |---|---|---|---|
  | **Textual** | async widget app, CSS-like styling | rich + typing-ext | Best fit — `DataTable` for the registry, `Tree` for link graphs, built-in filtering |
  | **Rich** | render-only, no event loop | none beyond itself | Cheapest upgrade: colored tables and health badges without a full app |
  | **prompt_toolkit** | full-screen + line editing | wcwidth | Good if the priority is interactive prompts, weaker for dashboards |
  | **urwid** | classic widget toolkit | none | Mature but dated API, more boilerplate |
  | **curses** (stdlib) | raw terminal control | none | Keeps zero-dep promise; everything hand-rolled, no mouse, poor Windows story |

  **Recommendation**: `Rich` for the immediate win (colorize existing renderers,
  no architectural change), then `Textual` for the actual TUI — same author and
  ecosystem, so Rich renderables drop straight into Textual widgets. That makes
  it one dependency direction, not two.

  - [ ] [ui] Adopt Rich in `output/renderers.py` behind a capability check —
        fall back to the current plain strings when Rich is absent or the output
        is not a TTY. Keeps `--json` and piped output byte-identical
  - [ ] [ui] Design the screen layout before writing widgets: a links list
        (source → destination, health badge, profile), a detail pane
        (registry record + last check + run history), and a filter bar
        (by status, by profile, broken-only)
  - [ ] [ui] Map read-only views first — `list`, `check`, `history`, `status`
        all already return structured data. Ship browsing before any mutation
  - [ ] [ui] Only then add actions — `repair`, `remove`, `rename` from the TUI.
        Every mutating action must route through the same service layer as the
        CLI, keeping the dry-run preview and conflict policy intact
  - [ ] [ui] Decide the entry point: `ghostlink tui`, or a bare `ghostlink` with
        no subcommand launching the TUI. The latter changes existing behaviour —
        today a bare invocation prints help
  - [ ] [ui] Handle the no-TTY case explicitly — the TUI must refuse to start
        under a pipe or in CI with a clear message, not hang or emit escape codes

## Done (Unreleased)
