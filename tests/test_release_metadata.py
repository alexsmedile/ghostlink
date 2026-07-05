from __future__ import annotations

import re
from pathlib import Path

from ghostlink import __version__


ROOT = Path(__file__).resolve().parents[1]
SEMVER_PATTERN = r"\d+\.\d+\.\d+"


def _required_match(pattern: str, path: Path) -> str:
    match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
    assert match is not None, f"version not found in {path.relative_to(ROOT)}"
    return match.group(1)


def test_project_release_versions_are_aligned() -> None:
    versions = {
        "package": __version__,
        "pyproject": _required_match(
            rf'^version = "({SEMVER_PATTERN})"$', ROOT / "pyproject.toml"
        ),
        "readme badge": _required_match(
            rf"badge/version-({SEMVER_PATTERN})-blue", ROOT / "README.md"
        ),
        "changelog": _required_match(
            rf"^## ({SEMVER_PATTERN})$", ROOT / "CHANGELOG.md"
        ),
    }

    assert set(versions.values()) == {__version__}, versions


def test_active_skill_matches_latest_snapshot() -> None:
    skill_dir = ROOT / "skills" / "ghostlink-skill"
    active_version = _required_match(
        rf'^  version: "({SEMVER_PATTERN})"$', skill_dir / "SKILL.md"
    )
    snapshot_versions = []
    for path in (skill_dir / "versions").glob("SKILL@*.md"):
        match = re.fullmatch(rf"SKILL@({SEMVER_PATTERN})\.md", path.name)
        assert match is not None, f"invalid skill snapshot name: {path.name}"
        snapshot_versions.append(match.group(1))

    assert snapshot_versions
    newest = max(snapshot_versions, key=lambda value: tuple(map(int, value.split("."))))
    assert active_version == newest
    assert (skill_dir / "versions" / f"SKILL@{active_version}.md").read_bytes() == (
        skill_dir / "SKILL.md"
    ).read_bytes()
