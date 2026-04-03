from __future__ import annotations

import json
from pathlib import Path

from ghostlink.cli.main import main


def test_legacy_find_flag_runs() -> None:
    rc = main(["--find", ".", "--depth", "0"])
    assert rc == 0


def test_find_broken_output_and_exit_code(tmp_path: Path, capsys) -> None:
    root = tmp_path / "root"
    root.mkdir()
    live_target = tmp_path / "live-target"
    live_target.mkdir()
    broken_target = tmp_path / "missing-target"
    output_file = tmp_path / "broken.txt"

    (root / "live-link").symlink_to(live_target)
    (root / "broken-link").symlink_to(broken_target)

    rc = main(["find", str(root), "--broken", "--output", str(output_file)])

    output = capsys.readouterr().out
    saved = output_file.read_text(encoding="utf-8")
    assert rc == 1
    assert "[BROKEN]" in output
    assert "broken-link" in saved
    assert "Summary" in saved


def test_find_json_output(tmp_path: Path, capsys) -> None:
    root = tmp_path / "root"
    target = tmp_path / "target"
    root.mkdir()
    target.mkdir()
    (root / "live-link").symlink_to(target)

    rc = main(["find", str(root), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["summary"]["found"] == 1
    assert payload["results"][0]["broken"] is False


def test_find_depth_limits_recursion(tmp_path: Path, capsys) -> None:
    root = tmp_path / "root"
    nested = root / "nested"
    deep = nested / "deep"
    target = tmp_path / "target"
    root.mkdir()
    nested.mkdir()
    deep.mkdir()
    target.mkdir()

    (root / "root-link").symlink_to(target)
    (nested / "nested-link").symlink_to(target)
    (deep / "deep-link").symlink_to(target)

    rc = main(["find", str(root), "--depth", "1"])

    output = capsys.readouterr().out
    assert rc == 0
    assert "root-link" in output
    assert "nested-link" in output
    assert "deep-link" not in output


def test_fast_path_creates_symlink_after_confirmation(tmp_path: Path, capsys, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "dest-link"

    answers = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    rc = main([str(source), str(destination)])

    output = capsys.readouterr().out
    assert rc == 0
    assert destination.is_symlink()
    assert destination.resolve() == source.resolve()
    assert "[OK]" in output


def test_fast_path_supports_dry_run(tmp_path: Path, capsys, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "dest-link"

    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    rc = main([str(source), str(destination), "--dry-run"])

    output = capsys.readouterr().out
    assert rc == 0
    assert not destination.exists()
    assert "[DRY]" in output


def test_create_relative_symlink(tmp_path: Path, capsys, monkeypatch) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "nested" / "dest-link"
    source.mkdir()
    destination.parent.mkdir()

    answers = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    rc = main(["create", "--source", str(source), "--dest", str(destination), "--relative"])

    output = capsys.readouterr().out
    assert rc == 0
    assert destination.is_symlink()
    assert destination.resolve() == source.resolve()
    assert destination.readlink() == Path("../source")
    assert "[OK]" in output


def test_bulk_alias_uses_create_flow(tmp_path: Path, capsys, monkeypatch) -> None:
    bulk_file = tmp_path / "links.txt"
    source = tmp_path / "source"
    destination = tmp_path / "dest-link"
    source.mkdir()
    bulk_file.write_text(f"{source} -> {destination}\n", encoding="utf-8")

    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    rc = main(["bulk", str(bulk_file)])

    output = capsys.readouterr().out
    assert rc == 0
    assert destination.is_symlink()
    assert "[OK]" in output


def test_save_list_show_remove_round_trip(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    assert main(
        [
            "save",
            "--name",
            "docs-link",
            "--source",
            "src",
            "--dest",
            str(tmp_path / "docs-link"),
            "--registry-path",
            str(registry),
        ]
    ) == 0

    assert main(["list", "--registry-path", str(registry)]) == 0
    listed = capsys.readouterr().out
    assert "docs-link" in listed

    assert main(["show", "docs-link", "--registry-path", str(registry)]) == 0
    shown = capsys.readouterr().out
    assert "name: docs-link" in shown

    assert main(["remove", "docs-link", "--registry-path", str(registry)]) == 0
    removed = capsys.readouterr().out
    assert "Removed: docs-link" in removed


def test_sync_record_round_trip_and_rename(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    destination = tmp_path / "dest"
    source.mkdir()
    destination.mkdir()

    assert main(
        [
            "save",
            "--name",
            "skills-sync",
            "--type",
            "sync",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0

    assert main(["list", "--registry-path", str(registry)]) == 0
    listed = capsys.readouterr().out
    assert "skills-sync" in listed
    assert "\tsync\t" in listed

    assert main(["show", "skills-sync", "--registry-path", str(registry)]) == 0
    shown = capsys.readouterr().out
    assert "type: sync" in shown

    assert main(["rename", "skills-sync", "skills-sync-v2", "--registry-path", str(registry)]) == 0
    renamed = capsys.readouterr().out
    assert "Renamed: skills-sync -> skills-sync-v2" in renamed

    assert main(["remove", "skills-sync-v2", "--registry-path", str(registry)]) == 0
    removed = capsys.readouterr().out
    assert "Removed: skills-sync-v2" in removed


def test_save_rejects_duplicate_name_across_record_types(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    destination = tmp_path / "dest"
    source.mkdir()
    destination.mkdir()

    assert main(
        [
            "save",
            "--name",
            "shared-name",
            "--source",
            str(source),
            "--dest",
            str(destination / "link"),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    rc = main(
        [
            "save",
            "--name",
            "shared-name",
            "--type",
            "sync",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    )
    output = capsys.readouterr().out
    assert rc == 1
    assert "record already exists: shared-name" in output


def test_sync_save_diff_and_schedule_preview(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    destination = tmp_path / "dest"
    source.mkdir()
    (source / "file.txt").write_text("hello", encoding="utf-8")
    destination.mkdir()

    assert main(
        [
            "sync",
            "save",
            "--name",
            "skills-sync",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0

    diff_rc = main(["sync", "diff", "skills-sync", "--registry-path", str(registry)])
    diff_output = capsys.readouterr().out
    assert diff_rc == 1
    assert "[COPY] file.txt" in diff_output

    assert main(
        [
            "schedule",
            "add",
            "skills-sync",
            "--every",
            "30m",
            "--registry-path",
            str(registry),
        ]
    ) == 0
    schedule_output = capsys.readouterr().out
    assert "com.ghostlink.skills-sync" in schedule_output


def test_sync_run_updates_saved_status_and_writes_log(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    run_log = tmp_path / "runs.jsonl"
    source = tmp_path / "source"
    destination = tmp_path / "dest"
    source.mkdir()
    destination.mkdir()
    (source / "file.txt").write_text("hello", encoding="utf-8")

    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: run_log)

    assert main(
        [
            "sync",
            "save",
            "--name",
            "skills-sync",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "sync",
            "run",
            "skills-sync",
            "--dry-run",
            "--registry-path",
            str(registry),
        ]
    ) == 0
    output = capsys.readouterr().out
    assert "Applied: 0" in output

    assert main(["show", "skills-sync", "--registry-path", str(registry)]) == 0
    shown = capsys.readouterr().out
    assert "last_status: ok" in shown
    assert "last_run_at:" in shown

    payload = json.loads(run_log.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["job_type"] == "sync"
    assert payload["dry_run"] is True


def test_schedule_write_list_and_remove_round_trip(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    launch_agents = tmp_path / "LaunchAgents"
    source = tmp_path / "source"
    destination = tmp_path / "dest"
    source.mkdir()
    destination.mkdir()

    monkeypatch.setattr("ghostlink.cli.main.ScheduleService", lambda: __import__("ghostlink.services.schedule_service", fromlist=["ScheduleService"]).ScheduleService(launch_agents_dir=launch_agents))

    assert main(
        [
            "sync",
            "save",
            "--name",
            "skills-sync",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "schedule",
            "add",
            "skills-sync",
            "--every",
            "30m",
            "--write",
            "--registry-path",
            str(registry),
        ]
    ) == 0
    add_output = capsys.readouterr().out
    assert "Wrote schedule preview" in add_output
    assert (launch_agents / "com.ghostlink.skills-sync.plist").exists()

    assert main(["schedule", "list", "--registry-path", str(registry)]) == 0
    listed = capsys.readouterr().out
    assert "skills-sync" in listed

    assert main(["schedule", "remove", "skills-sync", "--registry-path", str(registry)]) == 0
    removed = capsys.readouterr().out
    assert "Removed schedule: skills-sync" in removed

    assert main(["show", "skills-sync", "--registry-path", str(registry)]) == 0
    shown = capsys.readouterr().out
    assert "type: sync" in shown


def test_schedule_run_updates_heartbeat_metadata(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    run_log = tmp_path / "runs.jsonl"
    launch_agents = tmp_path / "LaunchAgents"
    source = tmp_path / "source"
    destination = tmp_path / "dest"
    source.mkdir()
    destination.mkdir()
    (source / "file.txt").write_text("hello", encoding="utf-8")

    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: run_log)
    monkeypatch.setattr(
        "ghostlink.cli.main.ScheduleService",
        lambda: __import__("ghostlink.services.schedule_service", fromlist=["ScheduleService"]).ScheduleService(launch_agents_dir=launch_agents),
    )

    assert main(
        [
            "sync",
            "save",
            "--name",
            "skills-sync",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "schedule",
            "add",
            "skills-sync",
            "--every",
            "30m",
            "--write",
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(["schedule", "run", "skills-sync", "--registry-path", str(registry)]) == 0
    run_output = capsys.readouterr().out
    assert "Applied: 1" in run_output

    assert main(["schedule", "list", "--registry-path", str(registry)]) == 0
    listed = capsys.readouterr().out
    assert "skills-sync" in listed
    assert "\tok\t" in listed

    assert main(["schedule", "show", "skills-sync", "--registry-path", str(registry)]) == 0
    shown = capsys.readouterr().out
    assert "last_run_at:" in shown
    assert "last_exit_code: 0" in shown
    assert "last_message:" in shown


def test_export_and_apply_relation_set_round_trip(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    export_file = tmp_path / "links.json"
    source = tmp_path / "source"
    destination = tmp_path / "saved-link"
    source.mkdir()

    assert main(
        [
            "save",
            "--name",
            "saved-link",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "export",
            str(export_file),
            "--profile",
            "dev",
            "--registry-path",
            str(registry),
        ]
    ) == 0
    export_output = capsys.readouterr().out
    payload = json.loads(export_file.read_text(encoding="utf-8"))
    assert "Exported 1 link(s)" in export_output
    assert "dev" in payload["profiles"]

    destination.unlink(missing_ok=True)
    assert main(["apply", str(export_file), "--profile", "dev", "-y"]) == 0
    apply_output = capsys.readouterr().out
    assert destination.is_symlink()
    assert destination.resolve() == source.resolve()
    assert "[OK]" in apply_output


def test_export_includes_syncs_and_sync_diff_can_use_config(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    export_file = tmp_path / "links.json"
    source = tmp_path / "source"
    destination = tmp_path / "saved-link"
    sync_dest = tmp_path / "backup"
    source.mkdir()
    (source / "file.txt").write_text("hello", encoding="utf-8")
    sync_dest.mkdir()

    assert main(
        [
            "save",
            "--name",
            "saved-link",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(
        [
            "sync",
            "save",
            "--name",
            "docs-sync",
            "--source",
            str(source),
            "--dest",
            str(sync_dest),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(["export", str(export_file), "--profile", "dev", "--registry-path", str(registry)]) == 0
    payload = json.loads(export_file.read_text(encoding="utf-8"))
    assert payload["profiles"]["dev"]["syncs"][0]["name"] == "docs-sync"
    capsys.readouterr()

    rc = main(["sync", "diff", "docs-sync", "--config", str(export_file), "--profile", "dev", "--json"])
    diff_payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert diff_payload["summary"]["copy"] == 1


def test_status_json_output(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    destination = tmp_path / "saved-link"
    source.mkdir()

    assert main(
        [
            "save",
            "--name",
            "saved-link",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    rc = main(["status", "--json", "--registry-path", str(registry)])
    payload = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert payload["summary"]["unknown"] == 1
    assert payload["items"][0]["name"] == "saved-link"


def test_import_profile_with_relative_links_and_save(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    relation_file = tmp_path / "links.json"
    source = tmp_path / "assets" / "source"
    destination = tmp_path / "links" / "dest-link"
    source.mkdir(parents=True)
    destination.parent.mkdir()
    relation_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "profiles": {
                    "work": {
                        "links": [
                            {
                                "name": "work-link",
                                "source": "assets/source",
                                "destination": "links/dest-link",
                                "conflict_policy": "ask",
                            }
                        ]
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    assert main(
        [
            "import",
            str(relation_file),
            "--profile",
            "work",
            "--relative",
            "--save",
            "-y",
            "--registry-path",
            str(registry),
        ]
    ) == 0
    output = capsys.readouterr().out
    assert destination.is_symlink()
    assert destination.resolve() == source.resolve()
    assert destination.readlink() == Path("../assets/source")
    assert "[OK]" in output

    assert main(["show", "work-link", "--registry-path", str(registry)]) == 0
    shown = capsys.readouterr().out
    assert f"destination: {destination}" in shown
    assert f"source: {source}" in shown


def test_check_saved_reports_missing(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    source.mkdir()
    destination = tmp_path / "missing-link"

    assert main(
        [
            "save",
            "--name",
            "saved-link",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0

    rc = main(["check", "--saved", "--registry-path", str(registry)])
    output = capsys.readouterr().out
    assert rc == 1
    assert "[MISSING] saved-link" in output


def test_check_saved_updates_status_and_status_command_summarizes(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    destination = tmp_path / "saved-link"
    source.mkdir()
    destination.symlink_to(source)

    assert main(
        [
            "save",
            "--name",
            "saved-link",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0

    assert main(["check", "--saved", "--registry-path", str(registry)]) == 0
    check_output = capsys.readouterr().out
    assert "[OK] saved-link" in check_output

    assert main(["status", "--registry-path", str(registry)]) == 0
    status_output = capsys.readouterr().out
    assert "Summary" in status_output
    assert "ok" in status_output
    assert "saved-link\tlink\tok" in status_output


def test_check_saved_writes_run_log(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    run_log = tmp_path / "runs.jsonl"
    source = tmp_path / "source"
    destination = tmp_path / "saved-link"
    source.mkdir()
    destination.symlink_to(source)

    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: run_log)

    assert main(
        [
            "save",
            "--name",
            "saved-link",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    assert main(["check", "--saved", "--registry-path", str(registry)]) == 0
    capsys.readouterr()

    lines = run_log.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[-1])
    assert payload["action"] == "check"
    assert payload["name"] == "saved-link"
    assert payload["status"] == "ok"


def test_repair_saved_recreates_missing_link(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    run_log = tmp_path / "runs.jsonl"
    source = tmp_path / "source"
    destination = tmp_path / "saved-link"
    source.mkdir()

    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: run_log)

    assert main(
        [
            "save",
            "--name",
            "saved-link",
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()

    rc = main(["repair", "saved-link", "--registry-path", str(registry), "-y"])
    output = capsys.readouterr().out

    assert rc == 0
    assert destination.is_symlink()
    assert destination.resolve() == source.resolve()
    assert "[OK]" in output

    payload = json.loads(run_log.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["action"] == "repair"
    assert payload["name"] == "saved-link"
    assert payload["status"] == "created"


def test_repair_bulk_recreates_missing_links(tmp_path: Path, capsys) -> None:
    bulk_file = tmp_path / "links.txt"
    source = tmp_path / "source"
    destination = tmp_path / "dest-link"
    source.mkdir()
    bulk_file.write_text(f"{source} -> {destination}\n", encoding="utf-8")

    rc = main(["repair", "--bulk", str(bulk_file), "-y"])
    output = capsys.readouterr().out

    assert rc == 0
    assert destination.is_symlink()
    assert "[OK]" in output
