from __future__ import annotations

from pathlib import Path

from ghostlink.domain import models, paths, results, validation

from conftest import require_dataclass_fields, require_exports


def test_domain_models_contract():
    require_exports(
        models,
        (
            "LinkSpec",
            "ConflictPolicy",
            "RecordType",
            "SyncMode",
            "CheckScopeKind",
            "ScheduleBackend",
            "ScheduleState",
            "LinkStatus",
            "SavedLinkRecord",
            "SavedSyncRecord",
            "RegistryDocument",
            "SyncSpec",
            "SyncDiffEntry",
            "SyncPlan",
            "ScheduleSpec",
            "ScheduleStatus",
        ),
    )

    require_dataclass_fields(models.LinkSpec, {"source", "destination", "conflict_policy", "line_no"})
    require_dataclass_fields(
        models.SavedLinkRecord,
        {"name", "source", "destination", "conflict_policy", "created_at", "last_checked_at", "last_status", "record_type", "schema_version"},
    )
    require_dataclass_fields(
        models.SavedSyncRecord,
        {"name", "source", "destination", "mode", "include_rules", "exclude_rules", "created_at", "last_run_at", "last_status", "record_type", "schema_version"},
    )
    require_dataclass_fields(models.RegistryDocument, {"links", "syncs", "updated_at", "schema_version"})
    require_dataclass_fields(models.SyncSpec, {"source", "destination", "mode", "include_rules", "exclude_rules", "dry_run"})
    require_dataclass_fields(models.ScheduleSpec, {"name", "backend", "interval_seconds", "command", "enabled", "label"})
    require_dataclass_fields(models.ScheduleStatus, {"state", "last_run_at", "next_run_at", "last_exit_code", "last_message"})


def test_domain_paths_contract():
    require_exports(paths, ("normalize_path", "normalize_path_text", "expand_path", "same_path", "is_within_directory"))

    assert paths.normalize_path_text("docs", cwd="/tmp/work") == "/tmp/work/docs"
    assert paths.same_path("/tmp/work/../work/docs", "/tmp/work/docs")


def test_domain_validation_contract():
    require_exports(
        validation,
        (
            "ValidationSeverity",
            "ValidationIssue",
            "ValidationResult",
            "validate_name",
            "validate_path_text",
            "validate_conflict_policy",
            "validate_link_spec",
            "validate_check_request",
            "validate_sync_spec",
            "validate_schedule_spec",
            "validate_bulk_separator",
            "normalize_record_path",
        ),
    )

    relative = models.LinkSpec(source=Path("source"), destination=Path("destination"))
    same = models.LinkSpec(source=Path("/tmp/work"), destination=Path("/tmp/work"))

    assert validation.validate_link_spec(relative).valid is True
    assert validation.validate_link_spec(same).valid is False


def test_domain_results_contract():
    require_exports(
        results,
        (
            "ResultStatus",
            "FindResult",
            "FindSummary",
            "LinkOperationResult",
            "LinkCheckEntry",
            "LinkCheckResult",
            "SyncRunResult",
            "RegistryOperationResult",
            "ScheduleOperationResult",
        ),
    )
