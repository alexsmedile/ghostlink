# Bulk and Portable Setups

Use bulk files for several local mappings. Use relation sets when the setup must be exported, versioned, profiled, or rebuilt on another machine.

## Bulk creation

Create a mapping file:

```text
# comments and blank lines are ignored
~/source/path -> ~/destination/link-name
"/path/with spaces/file.pdf" -> "~/Desktop/file-link.pdf"
```

Relative paths resolve from the bulk file’s directory. The default separator is `->`; override it with `--separator` when needed.

Preview and apply:

```bash
ghostlink bulk links.txt --dry-run -y
ghostlink bulk links.txt -y
```

Add `--conflict skip|backup|overwrite` only after inspecting existing destinations.

## Export a saved setup

```bash
ghostlink export links.json --profile dev
```

Relation sets can contain saved links and sync jobs. Use profiles to keep machine or role-specific setups separate.

## Apply or import

Preview before writing:

```bash
ghostlink apply links.json --profile dev --dry-run -y
ghostlink apply links.json --profile dev --save -y
```

`import` is an alias for `apply`:

```bash
ghostlink import links.json --profile work --relative --save -y
```

Confirm that destination parent directories exist before applying a relation set.
