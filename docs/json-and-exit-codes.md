# JSON Output & Exit Codes

## JSON Output

Pass `--json` to any command for machine-readable output:

```bash
ghostlink find ~/Desktop --json
ghostlink check --saved --json
ghostlink status --json
ghostlink sync diff docs-sync --config links.json --profile dev --json
```

## Exit Codes

| Command | Non-zero when |
|---|---|
| `create` / bulk | any operation fails |
| `find` | broken links are found |
| `check --saved` | a saved link is missing, broken, or mismatched |
| `sync diff` | there is work to do |
| `sync run` | execution errors |
| `schedule run` | the job itself returns non-zero |
