# Commands Reference

## Create

```bash
# fast-path (positional)
ghostlink <source> <destination>

# explicit
ghostlink create --source ~/Docs --dest ~/Desktop/Docs

# relative symlink
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --relative

# dry-run preview
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --dry-run
```

Conflict handling:

```bash
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --conflict backup
ghostlink create --source ~/Docs --dest ~/Desktop/Docs --conflict overwrite -y
# options: ask | skip | overwrite | backup
```

## Bulk Create

```bash
ghostlink bulk links.txt
ghostlink create --bulk links.txt --separator ","
ghostlink create --bulk links.txt --dry-run
ghostlink create --bulk links.txt --conflict overwrite -y
```

See [bulk-format.md](bulk-format.md) for the file format.

## Find

```bash
ghostlink find ~/Desktop
ghostlink find ~/Desktop --broken
ghostlink find ~/Desktop --broken --depth 2
ghostlink find ~/Desktop --broken --output broken.txt
```

## Check

```bash
ghostlink check ~/Desktop
ghostlink check --saved
```

## Repair

```bash
ghostlink repair docs-link -y
ghostlink repair --saved -y
ghostlink repair --bulk links.txt -y
```

## Save and Manage Records

```bash
ghostlink save --name docs-link --source ~/Docs --dest ~/Desktop/Docs

ghostlink list
ghostlink show docs-link
ghostlink rename docs-link docs-shortcut
ghostlink remove docs-shortcut
ghostlink status
```
