from __future__ import annotations

from pathlib import Path

from ghostlink.domain.models import LinkSpec, SyncSpec
from ghostlink.services.config_service import export_relation_set, load_profile_specs, load_profile_syncs
from ghostlink.services.link_service import load_bulk_specs
from ghostlink.services.sync_service import build_sync_plan


def test_bulk_specs_are_relative_to_bulk_file(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    bulk = tmp_path / "links.txt"
    bulk.write_text("source -> target-link\n", encoding="utf-8")

    specs = load_bulk_specs(bulk)

    assert len(specs) == 1
    assert specs[0].source == source
    assert specs[0].destination == tmp_path / "target-link"


def test_sync_plan_marks_extra_and_copy(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.mkdir()
    destination.mkdir()
    (source / "new.txt").write_text("new", encoding="utf-8")
    (destination / "old.txt").write_text("old", encoding="utf-8")

    plan = build_sync_plan(SyncSpec(source=source, destination=destination))

    actions = {entry.relative_path.as_posix(): entry.action for entry in plan.entries}
    assert actions["new.txt"] == "copy"
    assert actions["old.txt"] == "extra"


def test_relation_set_export_and_profile_load(tmp_path: Path) -> None:
    export_file = tmp_path / "links.json"
    source = tmp_path / "source"
    destination = tmp_path / "dest-link"
    source.mkdir()

    payload = export_relation_set(
        [
            {
                "name": "docs-link",
                "source": str(source),
                "destination": str(destination),
                "conflict_policy": "ask",
            }
        ],
        output_path=export_file,
        profile_name="dev",
        relative=True,
    )

    assert "dev" in payload["profiles"]
    loaded = load_profile_specs(export_file, profile_name="dev", relative_links=True)
    assert loaded[0][0] == "docs-link"
    assert loaded[0][1].destination == destination
    assert loaded[0][1].source == Path("source")


def test_relation_set_can_include_sync_profiles(tmp_path: Path) -> None:
    export_file = tmp_path / "links.json"
    source = tmp_path / "source"
    destination = tmp_path / "dest-link"
    sync_dest = tmp_path / "backup"
    source.mkdir()

    payload = export_relation_set(
        [
            {
                "name": "docs-link",
                "source": str(source),
                "destination": str(destination),
                "conflict_policy": "ask",
            }
        ],
        output_path=export_file,
        profile_name="dev",
        sync_records=[
            {
                "name": "docs-sync",
                "source": str(source),
                "destination": str(sync_dest),
                "mode": "one-way",
            }
        ],
    )

    assert payload["profiles"]["dev"]["syncs"][0]["name"] == "docs-sync"
    syncs = load_profile_syncs(export_file, profile_name="dev")
    assert syncs[0][0] == "docs-sync"
    assert syncs[0][1].destination == sync_dest
