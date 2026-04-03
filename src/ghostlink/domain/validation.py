from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ghostlink.domain.models import LinkSpec, SyncSpec
from ghostlink.domain.paths import expand_path, same_path


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(slots=True)
class ValidationIssue:
    severity: str
    message: str


@dataclass(slots=True)
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def message(self) -> str:
        if not self.issues:
            return "ok"
        return self.issues[0].message

    def __iter__(self):
        yield self.valid
        yield self.message


def validate_name(name: str) -> ValidationResult:
    ok, reason = validate_saved_name(name)
    if ok:
        return ValidationResult(True)
    return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, reason)])


def validate_path_text(path_text: str) -> ValidationResult:
    if not path_text.strip():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, "path cannot be empty")])
    return ValidationResult(True)


def validate_conflict_policy(policy: str) -> ValidationResult:
    if policy not in {"ask", "skip", "overwrite", "backup"}:
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"invalid conflict policy: {policy}")])
    return ValidationResult(True)


def validate_link_spec(spec: LinkSpec) -> ValidationResult:
    if spec.source.is_absolute() and not spec.source.exists():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"source does not exist: {spec.source}")])
    if spec.source.is_absolute() and spec.destination.exists() and same_path(spec.source, spec.destination):
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, "source and destination resolve to the same path")])
    parent = spec.destination.parent
    if spec.destination.is_absolute() and not parent.exists():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"destination parent folder does not exist: {parent}")])
    if spec.destination.is_absolute() and parent.is_file():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"destination parent is not a folder: {parent}")])
    return ValidationResult(True)


def validate_check_request(request: Any) -> ValidationResult:
    return ValidationResult(True)


def validate_sync_spec(spec: SyncSpec) -> ValidationResult:
    if not spec.source.exists():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"source does not exist: {spec.source}")])
    if not spec.source.is_dir():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"source is not a folder: {spec.source}")])
    if same_path(spec.source, spec.destination):
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, "source and destination resolve to the same path")])
    parent = spec.destination.parent
    if not parent.exists():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"destination parent folder does not exist: {parent}")])
    if parent.is_file():
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, f"destination parent is not a folder: {parent}")])
    return ValidationResult(True)


def validate_schedule_spec(spec: Any) -> ValidationResult:
    return ValidationResult(True)


def validate_bulk_separator(separator: str) -> ValidationResult:
    if not separator:
        return ValidationResult(False, [ValidationIssue(ValidationSeverity.ERROR.value, "separator cannot be empty")])
    return ValidationResult(True)


def validate_saved_name(name: str) -> tuple[bool, str]:
    value = name.strip()
    if not value:
        return False, "name cannot be empty"
    if "/" in value:
        return False, "name cannot contain /"
    return True, "ok"


def validate_output_path(path: Path) -> tuple[bool, str]:
    parent = path.parent
    if not parent.exists():
        return False, f"output parent folder does not exist: {parent}"
    return True, "ok"


def normalize_record_path(path_text: str, base_dir: str | Path | None = None) -> str:
    return str(expand_path(path_text, Path(base_dir) if base_dir else None))
