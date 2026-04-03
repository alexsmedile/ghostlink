# Bulk File Format

Each line defines one link:

```text
source -> destination
```

Example:

```text
# comment
~/Documents/project -> ~/Desktop/project-link
"/Users/you/My Files/report.pdf" -> "~/Desktop/report-link.pdf"
```

Rules:

- `#` starts a comment
- empty lines are ignored
- quotes are allowed for paths with spaces
- default separator is `->` (override with `--separator`)
- relative paths are resolved from the bulk file's folder
