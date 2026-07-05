from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ghostlink.cli.main import main
from ghostlink.storage.registry import load_registry
from ghostlink.storage.run_log import RUN_LOG_SCHEMA_VERSION, RunLogFormatError, read_run_log_entries


def save_link(registry: Path, name: str, source: Path, destination: Path, capsys) -> None:
    assert main(
        [
            "save",
            "--name",
            name,
            "--source",
            str(source),
            "--dest",
            str(destination),
            "--registry-path",
            str(registry),
        ]
    ) == 0
    capsys.readouterr()


def test_run_log_reads_structured_and_legacy_entries(tmp_path: Path) -> None:
    log = tmp_path / "runs.jsonl"
    log.write_text(
        "\n".join(
            [
                json.dumps({"timestamp": "2026-01-01T00:00:00+00:00", "action": "check", "status": "ok", "name": "docs"}),
                json.dumps({"timestamp": "2026-01-02T00:00:00+00:00", "job_type": "sync", "source": "/src", "destination": "/dest", "errors": []}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    entries = read_run_log_entries(log)

    assert [entry.action for entry in entries] == ["check", "sync"]
    assert entries[1].details["errors"] == []
    assert entries[1].schema_version == RUN_LOG_SCHEMA_VERSION


def test_run_log_rejects_malformed_lines(tmp_path: Path) -> None:
    log = tmp_path / "runs.jsonl"
    log.write_text("not-json\n", encoding="utf-8")

    try:
        read_run_log_entries(log)
    except RunLogFormatError as error:
        assert "line 1" in str(error)
    else:
        raise AssertionError("expected malformed run log to fail")


def test_list_reports_live_mismatch_without_mutating_registry(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    expected = tmp_path / "expected"
    actual = tmp_path / "actual"
    destination = tmp_path / "link"
    expected.mkdir()
    actual.mkdir()
    destination.symlink_to(actual)
    save_link(registry, "project", expected, destination, capsys)
    before = registry.read_text(encoding="utf-8")

    assert main(["list", "--registry-path", str(registry), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    observed = payload["items"][0]["observed"]
    assert observed["status"] == "mismatch"
    assert observed["actual_target"] == str(actual)
    assert observed["expected_target"] == str(expected)
    assert registry.read_text(encoding="utf-8") == before


def test_bare_check_defaults_to_saved_and_filters_issues(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    destination = tmp_path / "missing-link"
    source.mkdir()
    save_link(registry, "missing", source, destination, capsys)

    assert main(["check", "--registry-path", str(registry), "--issues", "--json"]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["scope"] == "saved"
    assert payload["results"][0]["status"] == "missing"
    assert load_registry(registry)["links"]["missing"]["last_status"] == "missing"


def test_check_rejects_ambiguous_scope_and_filters(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    assert main(["check", str(tmp_path), "--saved", "--registry-path", str(registry)]) == 2
    assert "not both" in capsys.readouterr().out
    assert main(["check", str(tmp_path), "--broken", "--issues", "--registry-path", str(registry)]) == 2


def test_index_is_idempotent_and_derives_collision_names(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    root = tmp_path / "root"
    target_a = tmp_path / "a"
    target_b = tmp_path / "b"
    (root / "one").mkdir(parents=True)
    (root / "two").mkdir(parents=True)
    target_a.mkdir()
    target_b.mkdir()
    (root / "one" / "project").symlink_to(target_a)
    (root / "two" / "project").symlink_to(target_b)

    assert main(["index", str(root), "-y", "--on-conflict", "keep", "--registry-path", str(registry), "--json"]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["saved"] == ["project", "project-2"]

    assert main(["index", str(root), "-y", "--on-conflict", "keep", "--registry-path", str(registry), "--json"]) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["saved"] == []
    assert second["summary"]["managed"] == 2


def test_index_dry_run_and_adopt_conflict(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    root = tmp_path / "root"
    old_target = tmp_path / "old"
    actual_target = tmp_path / "actual"
    destination = root / "project"
    root.mkdir()
    old_target.mkdir()
    actual_target.mkdir()
    destination.symlink_to(actual_target)
    save_link(registry, "project", old_target, destination, capsys)

    assert main(["index", str(root), "--dry-run", "--registry-path", str(registry), "--json"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert preview["summary"]["conflicts"] == 1
    assert load_registry(registry)["links"]["project"]["source"] == str(old_target)

    assert main(["index", str(root), "-y", "--on-conflict", "adopt", "--registry-path", str(registry), "--json"]) == 0
    adopted = json.loads(capsys.readouterr().out)
    assert adopted["adopted"] == ["project"]
    assert load_registry(registry)["links"]["project"]["source"] == str(actual_target)


def test_index_saves_broken_symlink_status(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    root = tmp_path / "root"
    root.mkdir()
    (root / "broken").symlink_to(tmp_path / "missing")

    assert main(["index", str(root), "-y", "--on-conflict", "keep", "--registry-path", str(registry)]) == 0
    capsys.readouterr()

    assert load_registry(registry)["links"]["broken"]["last_status"] == "broken"


def test_history_lists_and_filters_lifecycle_events(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    log = tmp_path / "runs.jsonl"
    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: log)
    source = tmp_path / "source"
    destination = tmp_path / "link"
    source.mkdir()
    save_link(registry, "docs", source, destination, capsys)

    assert main(["history", "--action", "save", "--type", "link", "--name", "docs", "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert len(payload["events"]) == 1
    assert payload["events"][0]["action"] == "save"


def test_successful_create_is_recorded_but_dry_run_is_not(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    log = tmp_path / "runs.jsonl"
    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: log)
    source = tmp_path / "source"
    source.mkdir()

    assert main(["create", "--source", str(source), "--dest", str(tmp_path / "preview"), "--dry-run", "-y", "--registry-path", str(registry)]) == 0
    capsys.readouterr()
    assert read_run_log_entries(log) == []

    assert main(["create", "--source", str(source), "--dest", str(tmp_path / "created"), "-y", "--registry-path", str(registry)]) == 0
    capsys.readouterr()
    events = read_run_log_entries(log)
    assert [event.action for event in events] == ["create"]
    assert events[0].destination == str(tmp_path / "created")


def test_dry_runs_do_not_append_lifecycle_events(tmp_path: Path, capsys, monkeypatch) -> None:
    registry = tmp_path / "registry.json"
    log = tmp_path / "runs.jsonl"
    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: log)
    source = tmp_path / "source"
    destination = tmp_path / "link"
    source.mkdir()
    save_link(registry, "docs", source, destination, capsys)
    before = len(read_run_log_entries(log))

    assert main(["repair", "docs", "--dry-run", "-y", "--registry-path", str(registry)]) == 0
    capsys.readouterr()

    assert len(read_run_log_entries(log)) == before


def test_registry_cleanup_requires_explicit_names_for_yes(tmp_path: Path, capsys) -> None:
    registry = tmp_path / "registry.json"
    source = tmp_path / "source"
    source.mkdir()
    save_link(registry, "missing", source, tmp_path / "missing", capsys)

    assert main(["cleanup", "registry", "-y", "--registry-path", str(registry)]) == 2
    assert "requires at least one --name" in capsys.readouterr().out

    assert main(["cleanup", "registry", "--name", "missing", "-y", "--registry-path", str(registry), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["removed"] == ["missing"]
    assert load_registry(registry)["links"] == {}


def test_history_cleanup_requires_boundary_and_prunes_atomically(tmp_path: Path, capsys, monkeypatch) -> None:
    log = tmp_path / "runs.jsonl"
    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: log)
    old = datetime.now(timezone.utc) - timedelta(days=100)
    recent = datetime.now(timezone.utc) - timedelta(days=1)
    log.write_text(
        json.dumps({"timestamp": old.isoformat(), "action": "create", "status": "ok"})
        + "\n"
        + json.dumps({"timestamp": recent.isoformat(), "action": "check", "status": "ok"})
        + "\n",
        encoding="utf-8",
    )

    assert main(["cleanup", "history", "--older-than", "90d", "--dry-run", "--json"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert len(preview["remove"]) == 1

    assert main(["cleanup", "history", "--older-than", "90d", "-y"]) == 0
    capsys.readouterr()
    entries = read_run_log_entries(log)
    assert [entry.action for entry in entries] == ["check", "cleanup-history"]


def test_history_cleanup_refuses_malformed_log_without_rewriting(tmp_path: Path, capsys, monkeypatch) -> None:
    log = tmp_path / "runs.jsonl"
    monkeypatch.setattr("ghostlink.cli.main.default_run_log_path", lambda: log)
    original = "not-json\n"
    log.write_text(original, encoding="utf-8")

    assert main(["cleanup", "history", "--older-than", "90d", "-y"]) == 2

    assert "line 1" in capsys.readouterr().out
    assert log.read_text(encoding="utf-8") == original
