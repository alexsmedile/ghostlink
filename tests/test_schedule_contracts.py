from __future__ import annotations

from ghostlink.integrations.launchd import LaunchdAdapter, LaunchdJobSpec, default_label, sanitize_label_fragment
from ghostlink.services.schedule_service import (
    ScheduleRecord,
    ScheduleService,
    ScheduleSpec,
    ScheduleStatus,
    format_interval,
    parse_interval,
)

from conftest import require_exports


def test_launchd_integration_contract():
    require_exports(
        __import__("ghostlink.integrations.launchd", fromlist=["LaunchdAdapter"]),
        (
            "LaunchdJobSpec",
            "LaunchdAdapter",
            "sanitize_label_fragment",
            "default_label",
        ),
    )
    assert sanitize_label_fragment("skills sync!") == "skills-sync"


def test_schedule_service_contract():
    require_exports(
        __import__("ghostlink.services.schedule_service", fromlist=["ScheduleService"]),
        (
            "ScheduleSpec",
            "ScheduleRecord",
            "ScheduleStatus",
            "ScheduleService",
            "parse_interval",
            "format_interval",
        ),
    )
    assert parse_interval("30m") == 1800
    assert format_interval(1800) == "30m"


def test_launchd_adapter_builds_plist_smoke():
    adapter = LaunchdAdapter()
    job = adapter.build_job_spec(
        label=default_label("skills sync"),
        program_arguments=("ghostlink", "sync", "run"),
        start_interval=1800,
        working_directory="/tmp/work",
    )

    plist = adapter.render_plist(job)

    assert isinstance(job, LaunchdJobSpec)
    assert "Label" in plist
    assert "ProgramArguments" in plist
    assert "com.ghostlink.skills-sync" in plist


def test_schedule_service_plans_without_side_effects(tmp_path):
    service = ScheduleService(
        registry_path=tmp_path / "schedules.json",
        launch_agents_dir=tmp_path / "LaunchAgents",
    )
    spec = ScheduleSpec(
        name="skills-sync",
        program_arguments=("ghostlink", "sync", "run", "skills-sync"),
        interval_seconds=parse_interval("30m"),
        working_directory=tmp_path / "work",
    )

    plan = service.plan(spec)

    assert isinstance(plan.record, ScheduleRecord)
    assert plan.record.schema_version == 1
    assert plan.record.name == "skills-sync"
    assert plan.job_spec.label == default_label("skills-sync")
    assert plan.plist_path == (tmp_path / "LaunchAgents" / "com.ghostlink.skills-sync.plist")
    assert "ProgramArguments" in plan.plist_text
    assert "com.ghostlink.skills-sync" in plan.plist_text
    assert format_interval(plan.record.interval_seconds) == "30m"
    assert plan.record.enabled is True
