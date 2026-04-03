from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LaunchdJobSpec:
    label: str
    program_arguments: tuple[str, ...]
    start_interval: int
    working_directory: str | None = None


def sanitize_label_fragment(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in text:
        text = text.replace("--", "-")
    return text.strip("-")


def default_label(name: str) -> str:
    return f"com.ghostlink.{sanitize_label_fragment(name)}"


def launch_agent_name(job_name: str) -> str:
    return default_label(job_name)


def launch_agent_path(job_name: str) -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{launch_agent_name(job_name)}.plist"


def render_launchd_plist(job_name: str, every: str, command: list[str]) -> str:
    minutes = parse_interval_minutes(every)
    program_arguments = "\n".join(f"      <string>{arg}</string>" for arg in command)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
        "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
        "<plist version=\"1.0\">\n"
        "<dict>\n"
        f"  <key>Label</key>\n  <string>{launch_agent_name(job_name)}</string>\n"
        "  <key>ProgramArguments</key>\n  <array>\n"
        f"{program_arguments}\n"
        "  </array>\n"
        "  <key>StartInterval</key>\n"
        f"  <integer>{minutes * 60}</integer>\n"
        "  <key>RunAtLoad</key>\n  <true/>\n"
        "</dict>\n"
        "</plist>\n"
    )


class LaunchdAdapter:
    def build_job_spec(
        self,
        label: str,
        program_arguments: tuple[str, ...],
        start_interval: int,
        working_directory: str | None = None,
    ) -> LaunchdJobSpec:
        return LaunchdJobSpec(
            label=label,
            program_arguments=program_arguments,
            start_interval=start_interval,
            working_directory=working_directory,
        )

    def render_plist(self, job: LaunchdJobSpec) -> str:
        program_arguments = "\n".join(f"      <string>{arg}</string>" for arg in job.program_arguments)
        working_directory = ""
        if job.working_directory:
            working_directory = (
                "  <key>WorkingDirectory</key>\n"
                f"  <string>{job.working_directory}</string>\n"
            )
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" "
            "\"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n"
            "<plist version=\"1.0\">\n"
            "<dict>\n"
            f"  <key>Label</key>\n  <string>{job.label}</string>\n"
            "  <key>ProgramArguments</key>\n  <array>\n"
            f"{program_arguments}\n"
            "  </array>\n"
            f"{working_directory}"
            "  <key>StartInterval</key>\n"
            f"  <integer>{job.start_interval}</integer>\n"
            "  <key>RunAtLoad</key>\n  <true/>\n"
            "</dict>\n"
            "</plist>\n"
        )


def parse_interval_minutes(every: str) -> int:
    value = every.strip().lower()
    if value.endswith("m"):
        return int(value[:-1])
    if value.endswith("h"):
        return int(value[:-1]) * 60
    raise ValueError("supported intervals use m or h, for example 30m or 2h")
