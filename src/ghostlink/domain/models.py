from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConflictPolicy(str, Enum):
    ASK = "ask"
    SKIP = "skip"
    OVERWRITE = "overwrite"
    BACKUP = "backup"


class JobType(str, Enum):
    LINK = "link"
    SYNC = "sync"


class RecordType(str, Enum):
    LINK = JobType.LINK.value
    SYNC = JobType.SYNC.value


class SyncMode(str, Enum):
    ONE_WAY = "one-way"


class CheckScopeKind(str, Enum):
    PATH = "path"
    FOLDER = "folder"
    SAVED = "saved"


class ScheduleBackend(str, Enum):
    LAUNCHD = "launchd"


class ScheduleState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class LinkStatus(str, Enum):
    OK = "ok"
    MISSING = "missing"
    BROKEN = "broken"
    MISMATCH = "mismatch"
    NOT_LINK = "not-link"


@dataclass(slots=True)
class LinkSpec:
    source: Path
    destination: Path
    conflict_policy: str = ConflictPolicy.ASK.value
    line_no: Optional[int] = None


@dataclass(slots=True)
class LinkOperationResult:
    spec: LinkSpec
    status: str
    message: str


@dataclass(slots=True)
class FindResult:
    link_path: Path
    target: Path
    broken: bool
    managed_name: Optional[str] = None


@dataclass(slots=True)
class CheckResult:
    label: str
    path: Path
    expected_target: Optional[Path]
    actual_target: Optional[Path]
    status: str
    message: str


@dataclass(slots=True)
class SavedLinkRecord:
    name: str
    source: str
    destination: str
    conflict_policy: str = ConflictPolicy.ASK.value
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    last_checked_at: Optional[str] = None
    last_status: Optional[str] = None
    type: str = JobType.LINK.value
    record_type: str = RecordType.LINK.value
    schema_version: int = 1


@dataclass(slots=True)
class SyncSpec:
    source: Path
    destination: Path
    mode: str = SyncMode.ONE_WAY.value
    include_rules: tuple[str, ...] = ()
    exclude_rules: tuple[str, ...] = (".DS_Store", "__pycache__")
    dry_run: bool = False
    ignore_names: tuple[str, ...] = (".DS_Store", "__pycache__")


@dataclass(slots=True)
class SyncDiffEntry:
    relative_path: Path
    action: str
    source: Optional[Path]
    destination: Optional[Path]
    reason: str


@dataclass(slots=True)
class SyncPlan:
    spec: SyncSpec
    entries: list[SyncDiffEntry]


@dataclass(slots=True)
class SyncRunResult:
    plan: SyncPlan
    applied: int
    skipped: int
    errors: list[str]


@dataclass(slots=True)
class SavedSyncRecord:
    name: str
    source: str
    destination: str
    mode: str = SyncMode.ONE_WAY.value
    include_rules: tuple[str, ...] = ()
    exclude_rules: tuple[str, ...] = (".DS_Store", "__pycache__")
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    last_checked_at: Optional[str] = None
    last_status: Optional[str] = None
    last_run_at: Optional[str] = None
    type: str = JobType.SYNC.value
    record_type: str = RecordType.SYNC.value
    schema_version: int = 1


@dataclass(slots=True)
class RegistryDocument:
    links: dict[str, SavedLinkRecord] = field(default_factory=dict)
    syncs: dict[str, SavedSyncRecord] = field(default_factory=dict)
    updated_at: str = field(default_factory=utc_now)
    schema_version: int = 1


@dataclass(slots=True)
class ScheduleSpec:
    name: str
    backend: str = ScheduleBackend.LAUNCHD.value
    interval_seconds: int = 1800
    command: tuple[str, ...] = ()
    program_arguments: tuple[str, ...] = ()
    enabled: bool = True
    label: Optional[str] = None
    working_directory: Optional[Path] = None
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class ScheduleStatus:
    state: str = ScheduleState.ENABLED.value
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    last_exit_code: Optional[int] = None
    last_message: Optional[str] = None
