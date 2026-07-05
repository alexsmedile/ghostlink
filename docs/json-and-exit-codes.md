# JSON Output & Exit Codes

## JSON Output

Pass `--json` to non-interactive commands for machine-readable output. It can appear before or after the command name:

```bash
ghostlink find ~/Desktop --json
ghostlink check --saved --json
ghostlink status --json
ghostlink sync diff docs-sync --config links.json --profile dev --json
ghostlink list --json
ghostlink history --type link --json
ghostlink index ~/Projects --dry-run --json
```

Successful command paths and empty-result checks emit JSON. Some validation errors and interactive cancellation paths still use human-readable output; fully structured error coverage remains planned.

## Exit Codes

| Command | Non-zero when |
|---|---|
| `create` / bulk | any operation fails |
| `find` | broken links are found |
| `check --saved` | a saved link is missing, broken, or mismatched |
| `check` | same as `check --saved`; non-zero when selected issues are found |
| `index` | discovery or registry mutation fails |
| `cleanup` | validation fails, input is malformed, or confirmation is declined |
| `sync diff` | there is work to do |
| `sync run` | execution errors |
| `schedule run` | the job itself returns non-zero |
