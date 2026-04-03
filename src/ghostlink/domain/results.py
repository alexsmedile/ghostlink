from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from ghostlink.domain.models import FindResult, LinkOperationResult, SyncRunResult


class ResultStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    WARNING = "warning"


@dataclass(slots=True)
class FindSummary:
    found: int
    broken: int


@dataclass(slots=True)
class LinkCheckEntry:
    path: Path
    status: str
    message: str


@dataclass(slots=True)
class LinkCheckResult:
    entries: list[LinkCheckEntry]
    status: str


@dataclass(slots=True)
class RegistryOperationResult:
    status: str
    message: str


@dataclass(slots=True)
class ScheduleOperationResult:
    status: str
    message: str


@dataclass(slots=True)
class OperationSummary:
    counts: dict[str, int]

    @classmethod
    def from_statuses(cls, statuses: Iterable[str]) -> "OperationSummary":
        return cls(dict(Counter(statuses)))

    def count(self, status: str) -> int:
        return self.counts.get(status, 0)
