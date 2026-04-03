from __future__ import annotations

from ghostlink.storage.registry import (
    REGISTRY_SCHEMA_VERSION,
    RegistryNotFoundError,
    RegistryDocument,
    RegistryStore,
    default_registry_path,
    load_registry_document,
    remove_registry_record,
    save_registry_document,
    upsert_registry_record,
    update_registry_record,
    utc_now_iso,
)
from ghostlink.storage.run_log import (
    RUN_LOG_SCHEMA_VERSION,
    RunLogEntry,
    append_run_log_entry,
    default_run_log_path,
    read_run_log_entries,
)

from conftest import require_exports


def test_registry_storage_contract():
    require_exports(
        __import__("ghostlink.storage.registry", fromlist=["RegistryStore"]),
        (
            "REGISTRY_SCHEMA_VERSION",
            "RegistryError",
            "RegistryFormatError",
            "RegistryNotFoundError",
            "RegistryConflictError",
            "RegistryDocument",
            "RegistryStore",
            "default_registry_path",
            "utc_now_iso",
            "load_registry_document",
            "save_registry_document",
            "list_registry_records",
            "upsert_registry_record",
            "update_registry_record",
            "remove_registry_record",
        ),
    )
    assert REGISTRY_SCHEMA_VERSION == 1
    assert default_registry_path().name == "registry.json"


def test_run_log_storage_contract():
    require_exports(
        __import__("ghostlink.storage.run_log", fromlist=["RunLogEntry"]),
        (
            "RUN_LOG_SCHEMA_VERSION",
            "RunLogEntry",
            "default_run_log_path",
            "utc_now_iso",
            "append_run_log_entry",
            "read_run_log_entries",
        ),
    )
    assert RUN_LOG_SCHEMA_VERSION == 1
    assert default_run_log_path().name == "runs.jsonl"


def test_registry_store_round_trip(tmp_path):
    registry_path = tmp_path / "registry.json"
    store = RegistryStore(registry_path)

    saved = save_registry_document(
        RegistryDocument(
            records=[
                {
                    "name": "docs-link",
                    "type": "link",
                    "source": "~/Docs",
                    "destination": "~/Desktop/Docs",
                }
            ]
        ),
        path=registry_path,
    )

    assert saved.schema_version == REGISTRY_SCHEMA_VERSION
    assert registry_path.exists()

    loaded = load_registry_document(registry_path)
    assert len(loaded.records) == 1
    assert loaded.records[0]["name"] == "docs-link"

    upserted = upsert_registry_record(
        {
            "name": "docs-link",
            "type": "link",
            "source": "~/Docs",
            "destination": "~/Desktop/Docs-v2",
        },
        path=registry_path,
    )
    assert upserted["destination"].endswith("Docs-v2")
    assert store.get_record("docs-link", "link")["destination"].endswith("Docs-v2")

    updated = update_registry_record(
        "docs-link",
        {"last_status": "ok"},
        path=registry_path,
        record_type="link",
    )
    assert updated["last_status"] == "ok"

    assert remove_registry_record("docs-link", path=registry_path, record_type="link") is True
    assert store.list_records() == []


def test_run_log_round_trip(tmp_path):
    log_path = tmp_path / "runs.jsonl"

    entry = append_run_log_entry(
        {
            "action": "check",
            "status": "ok",
            "name": "docs-link",
            "message": "all good",
            "details": {"count": 1},
        },
        path=log_path,
    )

    assert entry.schema_version == RUN_LOG_SCHEMA_VERSION
    assert log_path.exists()

    entries = read_run_log_entries(log_path)
    assert len(entries) == 1
    assert entries[0].action == "check"
    assert entries[0].status == "ok"
    assert entries[0].details == {"count": 1}


def test_registry_document_round_trip_keeps_link_and_sync_records(tmp_path):
    registry_path = tmp_path / "registry.json"

    saved = save_registry_document(
        RegistryDocument(
            records=[
                {
                    "name": "docs-link",
                    "type": "link",
                    "source": "~/Docs",
                    "destination": "~/Desktop/Docs",
                },
                {
                    "name": "skills-sync",
                    "type": "sync",
                    "source": "~/skills",
                    "destination": "~/backup/skills",
                    "mode": "one-way",
                },
            ]
        ),
        path=registry_path,
    )

    names = {(record["name"], record["type"]) for record in saved.records}
    assert ("docs-link", "link") in names
    assert ("skills-sync", "sync") in names


def test_update_registry_record_missing_raises(tmp_path):
    registry_path = tmp_path / "registry.json"

    try:
        update_registry_record("missing", {"last_status": "ok"}, path=registry_path, record_type="link")
    except RegistryNotFoundError:
        pass
    else:
        raise AssertionError("expected RegistryNotFoundError")
