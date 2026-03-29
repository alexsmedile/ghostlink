# symlink-cli

A macOS CLI tool to create symbolic links interactively or in bulk.

Install once, use as `symlink-cli` or the short alias `slink`.

---

## Installation

```bash
pipx install symlink-cli
```

Or in editable/dev mode from this repo:

```bash
pipx install -e .
```

---

## Usage

### Interactive mode (default)

```bash
slink
```

Prompts for source path, destination, and confirms before creating.

### Bulk mode

```bash
slink --bulk links.txt
```

### Dry run (preview without changes)

```bash
slink --bulk links.txt --dry-run
```

### Auto-confirm

```bash
slink --bulk links.txt -y
```

### Conflict handling

```bash
slink --bulk links.txt --conflict overwrite
```

Options: `ask` (default) · `skip` · `overwrite` · `backup`

### Custom separator

```bash
slink --bulk links.txt --separator ","
```

---

## Bulk file format

Each line defines a `source -> destination` mapping:

```
# comment — ignored
~/Documents/project -> ~/Desktop/project-link
~/Music -> ~/Desktop/MusicLink
"/Users/you/My Files/report.pdf" -> "~/Desktop/report-link.pdf"
```

Rules:
- `#` starts a comment
- empty lines are ignored
- paths with spaces can use quotes
- default separator is `->`, configurable with `--separator`

---

## Output

```
[OK]   /Users/me/Desktop/project-link -> /Users/me/Documents/project
[SKIP] destination exists: /Users/me/Desktop/old-link
[ERR]  source does not exist: /Users/me/missing

Summary
  created : 2
  dry-run : 0
  skipped : 1
  errors  : 1
```

---

## Safety notes

- Does **not** remove directories automatically — use `backup`, `skip`, or remove manually
- `overwrite` only removes files or symlinks
- `backup` renames existing: `file → file.backup-1`
- Always test with `--dry-run` first

---

## Find mode

Search for symlinks in a folder or system-wide:

```bash
# Search current directory
slink --find

# Search a specific folder
slink --find ~/Desktop

# System-wide search
slink --find /

# Only broken symlinks
slink --find ~ --broken

# Limit recursion depth
slink --find ~ --depth 2

# Save results to file (also prints to terminal)
slink --find ~/Desktop --output results.txt

# Combine filters
slink --find ~ --broken --output broken-links.txt
```

Output format:
```
[LINK]   /path/to/link -> /path/to/target
[BROKEN] /path/to/link -> /path/to/target  (target missing)

Summary
  found  : 42
  broken : 3
```

---

## Roadmap

- Bulk-sync workflows (e.g. AI skills/agents folders)

---

## License

MIT
