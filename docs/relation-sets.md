# Relation Sets

Portable JSON files that describe links and syncs — useful for rebuilding setups on a new machine.

## Export / Apply / Import

```bash
ghostlink export links.json --profile dev
ghostlink apply links.json --profile dev -y
ghostlink import links.json --profile work --relative --save -y
```

## File Format

```json
{
  "schema_version": 1,
  "profiles": {
    "dev": {
      "links": [
        {
          "name": "docs-link",
          "source": "~/Docs",
          "destination": "~/Desktop/Docs",
          "conflict_policy": "ask"
        }
      ],
      "syncs": [
        {
          "name": "docs-sync",
          "source": "~/Docs",
          "destination": "~/Backup/Docs",
          "mode": "one-way"
        }
      ]
    }
  }
}
```

## Rules

- `apply` and `import` read one profile at a time
- relation sets can include both `links` and `syncs`
- relative paths are resolved from the relation-set file location
- `--relative` creates relative symlink targets
- destination parent folders must already exist before apply
