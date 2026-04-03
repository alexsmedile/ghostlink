# Terminal UX and TUI Specification

## Purpose

This document defines how `symlink-cli` should look and feel when used by humans in a terminal. The product should feel guided, calm, and safe. It is still a CLI, but when used interactively it should behave like a lightweight TUI.

The experience should help users avoid mistakes without making simple tasks feel heavy.

## Design Principles

- Plain language over technical jargon
- Clear next step at every moment
- Safe defaults and visible risk warnings
- Short screens with strong hierarchy
- Keyboard-first interaction
- Good experience both for quick actions and repeated workflows

## Tone

The tool should sound:
- direct
- helpful
- calm
- non-alarmist

It should not sound:
- robotic
- overly verbose
- overly clever
- full of internal terms like "mutation", "policy", or "artifact"

Examples:
- Good: `This destination already exists. What do you want to do?`
- Good: `Nothing will be changed. This is a preview.`
- Bad: `Conflict policy unresolved.`
- Bad: `Filesystem mutation queued.`

## Interaction Modes

The CLI should support two human-facing modes:

### 1. Command mode

The user already knows what they want:

```bash
slink create --source ~/Docs --dest ~/Desktop/Docs
```

This should print a short summary, validate, warn if needed, and ask for confirmation unless `--yes` is used.

### 2. Guided mode

The user runs:

```bash
slink
```

This should open a guided menu with the most common actions.

Recommended first screen:

```text
Symlink CLI

What do you want to do?

1. Create a symlink
2. Check a symlink
3. Find symlinks
4. Run a saved job
5. Save or manage jobs
6. Sync folders
7. Schedule a saved job
q. Quit
```

## Visual Style

The terminal UI should feel clean and structured.

Recommended conventions:
- One short title at the top of each guided screen
- Blank lines between sections
- Labels aligned when useful
- Status prefixes kept short and consistent
- Important warnings separated visually

Suggested status markers:
- `[OK]`
- `[WARN]`
- `[ERR]`
- `[SKIP]`
- `[DRY]`
- `[INFO]`

Color can help, but the UI must remain fully understandable without color.

If color is added:
- green for success
- yellow for warnings and previews
- red for blocking errors
- cyan or blue for headings and informational labels

Avoid flashy styling, spinners by default, or dense box drawing.

## Human Journey

### Journey 1: Quick create

User intent:
- create one symlink safely

Flow:
1. User starts `slink`
2. Picks `Create a symlink`
3. Tool asks for source path
4. Tool asks for destination style:
   - folder + link name
   - full destination path
5. Tool validates inputs
6. Tool shows preview
7. Tool asks for confirmation
8. Tool shows result and optional save prompt

Preview example:

```text
Ready to create

Source      /Users/alex/Documents/project
Link path   /Users/alex/Desktop/project
Mode        create symlink
Safety      confirm before change

Proceed? [y/N]
```

Post-success example:

```text
[OK] /Users/alex/Desktop/project -> /Users/alex/Documents/project

Do you want to save this link for later checks? [y/N]
```

### Journey 2: Conflict during create

User intent:
- create a link, but destination already exists

Flow:
1. Tool explains the exact problem
2. Tool shows the destination path
3. Tool offers a short action menu
4. Tool explains the consequence of each choice

Recommended conflict screen:

```text
This destination already exists:
/Users/alex/Desktop/project

Choose what to do:
1. Skip it
2. Replace the existing file or symlink
3. Keep the old item and rename it to a backup
q. Cancel
```

If the destination is a directory and replacement is unsafe, the tool should say so clearly and remove that option from the menu.

### Journey 3: Find and inspect

User intent:
- inspect symlinks in a folder

Flow:
1. User runs `slink find ~/Desktop`
2. Tool prints a short header
3. Results stream line by line
4. Summary appears at the end
5. User may save output to file

Example:

```text
Searching under: /Users/alex/Desktop
Depth limit: 2

[LINK]   /Users/alex/Desktop/project -> /Users/alex/Documents/project
[BROKEN] /Users/alex/Desktop/old-link -> /Users/alex/Old/project  (target missing)

Summary
  found  : 2
  broken : 1
```

### Journey 4: Check and repair mindset

User intent:
- know whether a link or saved set is still healthy

Flow:
1. User selects `Check a symlink` or runs `slink check`
2. Tool asks for one path, one folder, or saved jobs
3. Tool classifies results:
   - healthy
   - broken
   - target changed
   - missing expected link
4. Tool gives next-step suggestions

Example:

```text
Check result

[OK]   docs-link points to the expected target
[WARN] skills-link is broken
[WARN] work-link points somewhere different than expected

Next steps:
- repair the broken link
- update the saved target if the move was intentional
```

### Journey 5: Save and manage remembered jobs

User intent:
- keep important links and syncs in a known list

Flow:
1. After a successful create or sync setup, tool offers save
2. Tool asks for a short name
3. Tool confirms what was stored
4. `list`, `show`, and `remove` should feel simple and readable

Example `list` screen:

```text
Saved jobs

Links
- docs-link      /Users/alex/Docs -> /Users/alex/Desktop/Docs
- config-link    /Users/alex/.config/app -> /Users/alex/work/config

Syncs
- skills-sync    /Users/alex/skills => /Volumes/backup/skills
```

### Journey 6: Sync diff before action

User intent:
- compare folders safely before any copy or update happens

Flow:
1. User runs `slink sync diff ...` or picks Sync from the guided menu
2. Tool shows source and destination
3. Tool prints a categorized summary
4. Tool offers dry-run or apply

Example:

```text
Sync preview

Source       /Users/alex/skills
Destination  /Volumes/backup/skills
Mode         one-way sync

Planned changes
  new files      12
  changed files   3
  missing files   1
  skipped files   8

Nothing has been changed yet.
Run this sync now? [y/N]
```

Important:
- sync should never feel like "just another create"
- the tool must make clear that sync copies data, while symlink creation does not

### Journey 7: Scheduling a saved job

User intent:
- repeat a check or sync later

Flow:
1. User picks a saved job
2. Tool asks for interval
3. Tool shows exact schedule details
4. Tool asks for confirmation before installation
5. Tool explains where schedule metadata lives

Example:

```text
Schedule job

Job         skills-sync
Action      sync run
Interval    every 30 minutes
System      launchd

This will install a scheduled job on this Mac.
Proceed? [y/N]
```

## Navigation Rules

- `q` should cancel or go back when safe
- `Enter` should accept a sensible default only when the default is safe
- Dangerous defaults must never be preselected
- After each completed action, offer the next likely choices:
  - save this job
  - run a check
  - go back to main menu
  - quit

## Prompt Rules

Prompts should be:
- one question at a time
- short
- explicit about what format is expected

Good examples:
- `Source path:`
- `Target folder:`
- `Link name [default: project]:`
- `Save this job with a name? [y/N]`

Bad examples:
- `Please provide the canonical source object for the symlink operation:`

## Error Handling UX

Errors should help the user recover.

Format:
1. Say what failed
2. Show the path or item involved
3. Give the next useful action

Example:

```text
[ERR] Source does not exist
/Users/alex/missing-folder

Check the path and try again.
```

The tool should avoid stack traces in normal human mode.

## Confirmation UX

Every risky action should have a final review screen with:
- the action
- source
- destination
- conflict behavior
- whether this is a preview or a real change

Example:

```text
Review

Action       create symlink
Source       /Users/alex/Documents/project
Destination  /Users/alex/Desktop/project
Conflict     backup existing item
Mode         dry-run

Proceed? [y/N]
```

## Accessibility and Robustness

- Do not rely only on color
- Keep line widths reasonable for smaller terminals
- Avoid deep nested menus
- Keep important path lines copyable
- Handle Ctrl+C cleanly with a short cancellation message

Example:

```text
Cancelled. No changes were made.
```

## Output Modes

Human mode should be the default.

Recommended future output modes:
- normal
- compact
- json

Human mode should optimize for clarity.
JSON mode should optimize for scripting and automation.

## TUI Scope Boundary

This should remain a terminal-first guided CLI, not a full-screen terminal app.

That means:
- no complex pane layout
- no mouse requirements
- no heavy terminal framework unless clearly needed later

The right feel is:
- guided
- lightweight
- readable
- safe

Not:
- dashboard-like
- noisy
- over-animated
- visually dense

## Acceptance Standard

The TUI is successful if:
- a new user can run `slink` and understand the next step immediately
- risky actions are hard to perform by accident
- common actions are fast
- saved jobs feel easy to inspect and reuse
- sync actions feel clearly different from symlink actions
- the terminal output stays calm and readable during long sessions
