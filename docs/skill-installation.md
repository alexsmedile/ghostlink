# Skill Installation

This repo includes a reusable Codex skill at `skills/ghostlink-skill`.

## Install From This Repo

If you use a GitHub repo-path skill installer, point it at:

- repo: `alexsmedile/ghostlink`
- path: `skills/ghostlink-skill`

Example with Codex's GitHub skill installer helper:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo alexsmedile/ghostlink \
  --path skills/ghostlink-skill
```

That installs the skill into `~/.codex/skills/ghostlink-skill`.

## Install Manually

You can also copy the folder directly:

```bash
mkdir -p ~/.codex/skills
cp -R skills/ghostlink-skill ~/.codex/skills/ghostlink-skill
```

Restart Codex after installation so the skill is discovered.

## What The Skill Covers

The skill is intended for requests such as:

- create a symlink safely
- build or validate a bulk links file
- find broken symlinks
- save a link for later checks
- inspect or repair a saved link setup with `ghostlink`
