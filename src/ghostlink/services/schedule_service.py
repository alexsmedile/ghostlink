from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ghostlink.domain.models import ScheduleSpec, ScheduleStatus
from ghostlink.integrations.launchd import LaunchdAdapter, default_label, launch_agent_path


def parse_interval(value: str) -> int:
    text = value.strip().lower()
    if text.endswith("m"):
        return int(text[:-1]) * 60
    if text.endswith("h"):
        return int(text[:-1]) * 3600
    raise ValueError("supported intervals use m or h, for example 30m or 2h")


def format_interval(seconds: int) -> str:
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    return f"{seconds // 60}m"


@dataclass(slots=True)
class ScheduleRecord:
    name: str
    backend: str
    interval_seconds: int
    enabled: bool = True
    schema_version: int = 1


@dataclass(slots=True)
class SchedulePlan:
    record: ScheduleRecord
    status: ScheduleStatus
    job_spec: object
    plist_path: Path
    plist_text: str


class ScheduleService:
    def __init__(self, registry_path: Path | None = None, launch_agents_dir: Path | None = None) -> None:
        self.registry_path = registry_path
        self.launch_agents_dir = launch_agents_dir or (Path.home() / "Library" / "LaunchAgents")
        self.adapter = LaunchdAdapter()

    def plan(self, spec: ScheduleSpec) -> SchedulePlan:
        label = spec.label or default_label(spec.name)
        program_arguments = tuple(spec.program_arguments or spec.command)
        job_spec = self.adapter.build_job_spec(
            label=label,
            program_arguments=program_arguments,
            start_interval=spec.interval_seconds,
            working_directory=str(spec.working_directory) if spec.working_directory else None,
        )
        plist_text = self.adapter.render_plist(job_spec)
        plist_path = self.launch_agents_dir / f"{label}.plist"
        record = ScheduleRecord(name=spec.name, backend=spec.backend, interval_seconds=spec.interval_seconds, enabled=spec.enabled)
        status = ScheduleStatus()
        return SchedulePlan(record=record, status=status, job_spec=job_spec, plist_path=plist_path, plist_text=plist_text)

    def preview(self, spec: ScheduleSpec, command: list[str]) -> tuple[Path, str]:
        plan = self.plan(
            ScheduleSpec(
                name=spec.name,
                backend=spec.backend,
                interval_seconds=spec.interval_seconds,
                command=tuple(command),
                program_arguments=tuple(command),
                enabled=spec.enabled,
                label=spec.label,
                working_directory=spec.working_directory,
            )
        )
        return plan.plist_path, plan.plist_text
