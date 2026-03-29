#!/usr/bin/env python3
"""
symlink_helper.py

A macOS CLI helper to create symbolic links interactively or in bulk.

Features
- Interactive mode:
  - prompts for source path and destination folder/name
  - can create links to files or folders
  - validates paths before writing
  - optional backup/overwrite/skip behavior
- Bulk mode:
  - reads a text file with one mapping per line
  - supports comments and blank lines
  - useful for creating many symlinks at once
- Dry run:
  - shows what would happen without changing anything
- Safe defaults:
  - expands ~ and environment variables
  - resolves relative paths
  - prevents linking a path onto itself

Bulk file format
- Default separator: ->

Examples
  /Users/me/Documents/project -> /Users/me/Desktop/project-link
  ~/Music/Albums -> ~/Desktop/Albums
  "~/My Files/report.pdf" -> "~/Desktop/report-link.pdf"

Comments start with #
Blank lines are ignored.

Usage
  python3 symlink_helper.py
  python3 symlink_helper.py --interactive
  python3 symlink_helper.py --bulk links.txt
  python3 symlink_helper.py --bulk links.txt --separator ","
  python3 symlink_helper.py --dry-run --bulk links.txt
"""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Optional, Tuple


# ---------- constants ----------

MACOS_SKIP_PREFIXES: tuple[str, ...] = (
    "/System/Volumes/VM",
    "/System/Volumes/Preboot",
    "/System/Volumes/Recovery",
    "/private/var/vm",
    "/private/var/db/dslocal",
    "/dev",
    "/net",
    "/home",
)


# ---------- data models ----------

@dataclass
class LinkSpec:
    source: Path
    destination: Path
    line_no: Optional[int] = None


@dataclass
class OperationResult:
    spec: LinkSpec
    status: str
    message: str


@dataclass
class FindResult:
    link_path: Path
    target: Path
    broken: bool


# ---------- path utilities ----------

def expand_path(raw: str, base_dir: Optional[Path] = None) -> Path:
    value = os.path.expandvars(os.path.expanduser(raw.strip()))
    p = Path(value)
    if not p.is_absolute():
        if base_dir is None:
            base_dir = Path.cwd()
        p = (base_dir / p).resolve()
    return p


def normalize_destination(source: Path, dest_input: str, link_name: Optional[str], base_dir: Optional[Path] = None) -> Path:
    dest_path = expand_path(dest_input, base_dir=base_dir)

    if dest_path.exists() and dest_path.is_dir():
        final_name = link_name.strip() if link_name and link_name.strip() else source.name
        return dest_path / final_name

    if dest_input.endswith("/"):
        final_name = link_name.strip() if link_name and link_name.strip() else source.name
        return dest_path / final_name

    return dest_path


def same_path(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except FileNotFoundError:
        return a.absolute() == b.absolute()


# ---------- validation ----------

def validate_spec(spec: LinkSpec) -> Tuple[bool, str]:
    if not spec.source.exists():
        return False, f"source does not exist: {spec.source}"

    if spec.destination.exists() and same_path(spec.source, spec.destination):
        return False, "source and destination resolve to the same path"

    parent = spec.destination.parent
    if not parent.exists():
        return False, f"destination parent folder does not exist: {parent}"

    if parent.is_file():
        return False, f"destination parent is not a folder: {parent}"

    return True, "ok"


# ---------- create logic ----------

def backup_path(path: Path) -> Path:
    idx = 1
    while True:
        candidate = path.with_name(f"{path.name}.backup-{idx}")
        if not candidate.exists():
            return candidate
        idx += 1


def create_symlink(
    spec: LinkSpec,
    on_conflict: str = "ask",
    dry_run: bool = False,
    assume_yes: bool = False,
) -> OperationResult:
    ok, reason = validate_spec(spec)
    if not ok:
        return OperationResult(spec, "error", reason)

    dest = spec.destination

    if dest.exists() or dest.is_symlink():
        if on_conflict == "skip":
            return OperationResult(spec, "skipped", f"destination exists: {dest}")
        if on_conflict == "overwrite":
            if dry_run:
                return OperationResult(spec, "dry-run", f"would remove existing destination and create symlink: {dest} -> {spec.source}")
            remove_existing(dest)
        elif on_conflict == "backup":
            backup = backup_path(dest)
            if dry_run:
                return OperationResult(spec, "dry-run", f"would move existing destination to {backup} and create symlink: {dest} -> {spec.source}")
            dest.rename(backup)
        else:
            if assume_yes:
                remove_existing(dest)
            else:
                choice = ask_conflict_choice(dest)
                if choice == "s":
                    return OperationResult(spec, "skipped", f"destination exists: {dest}")
                if choice == "o":
                    if dry_run:
                        return OperationResult(spec, "dry-run", f"would remove existing destination and create symlink: {dest} -> {spec.source}")
                    remove_existing(dest)
                if choice == "b":
                    backup = backup_path(dest)
                    if dry_run:
                        return OperationResult(spec, "dry-run", f"would move existing destination to {backup} and create symlink: {dest} -> {spec.source}")
                    dest.rename(backup)

    if dry_run:
        return OperationResult(spec, "dry-run", f"would create symlink: {dest} -> {spec.source}")

    try:
        os.symlink(spec.source, dest)
        return OperationResult(spec, "created", f"{dest} -> {spec.source}")
    except OSError as e:
        return OperationResult(spec, "error", f"failed to create symlink: {e}")


def remove_existing(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        raise IsADirectoryError(
            f"refusing to remove existing directory automatically: {path}. "
            "Use backup mode, skip mode, or remove it manually."
        )
    else:
        path.unlink(missing_ok=True)


def ask_conflict_choice(dest: Path) -> str:
    while True:
        print(f"Destination already exists: {dest}")
        print("Choose: [s]kip  [o]verwrite  [b]ackup existing")
        choice = input("> ").strip().lower()
        if choice in {"s", "o", "b"}:
            return choice
        print("Please type s, o, or b.")


# ---------- interactive mode ----------

def prompt_non_empty(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("Please enter a value.")


def interactive_collect(base_dir: Optional[Path] = None) -> Optional[LinkSpec]:
    print("\nSymlink Helper — interactive mode\n")

    source_raw = prompt_non_empty("Source file/folder path: ")
    source = expand_path(source_raw, base_dir=base_dir)

    if not source.exists():
        print(f"Source does not exist: {source}")
        return None

    print("\nDestination options:")
    print("1) Enter a target folder, then choose a symlink name")
    print("2) Enter the full destination path directly")
    mode = input("Choose [1/2] (default 1): ").strip() or "1"

    if mode == "1":
        target_folder_raw = prompt_non_empty("Target folder path: ")
        link_name = input(f"Symlink name (default: {source.name}): ").strip() or source.name
        destination = normalize_destination(source, target_folder_raw, link_name, base_dir=base_dir)
    else:
        destination_raw = prompt_non_empty("Full destination path for the symlink: ")
        destination = normalize_destination(source, destination_raw, None, base_dir=base_dir)

    spec = LinkSpec(source=source, destination=destination)

    ok, reason = validate_spec(spec)
    if not ok:
        print(f"\nValidation error: {reason}")
        return None

    print("\nReady to create:")
    print(f"  source      {spec.source}")
    print(f"  symlink at  {spec.destination}")
    return spec


# ---------- bulk parsing ----------

def strip_outer_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_bulk_line(line: str, separator: str) -> Optional[Tuple[str, str]]:
    text = line.strip()
    if not text or text.startswith("#"):
        return None

    if separator in text:
        left, right = text.split(separator, 1)
        return strip_outer_quotes(left), strip_outer_quotes(right)

    try:
        parts = next(csv.reader([text], skipinitialspace=True))
        if len(parts) == 2:
            return strip_outer_quotes(parts[0]), strip_outer_quotes(parts[1])
    except Exception:
        pass

    try:
        parts = shlex.split(text)
        if len(parts) == 2:
            return parts[0], parts[1]
    except Exception:
        pass

    raise ValueError(
        f"could not parse line. Use '{separator}' or two CSV columns or two shell-like paths."
    )


def load_bulk_specs(file_path: Path, separator: str = "->") -> List[LinkSpec]:
    specs: List[LinkSpec] = []
    base_dir = file_path.parent.resolve()

    with file_path.open("r", encoding="utf-8") as fh:
        for idx, raw_line in enumerate(fh, start=1):
            parsed = parse_bulk_line(raw_line, separator)
            if parsed is None:
                continue

            source_raw, dest_raw = parsed
            source = expand_path(source_raw, base_dir=base_dir)
            destination = expand_path(dest_raw, base_dir=base_dir)
            specs.append(LinkSpec(source=source, destination=destination, line_no=idx))

    return specs


# ---------- find logic ----------

def walk_symlinks(
    root: Path,
    max_depth: Optional[int] = None,
    skip_prefixes: tuple[str, ...] = MACOS_SKIP_PREFIXES,
) -> Generator[FindResult, None, None]:
    stack: List[tuple[Path, int]] = [(root, 0)]
    while stack:
        current, depth = stack.pop()
        try:
            entries = list(os.scandir(current))
        except PermissionError:
            continue
        for entry in entries:
            if entry.is_symlink():
                target = Path(os.readlink(entry.path))
                broken = not os.path.exists(entry.path)
                yield FindResult(link_path=Path(entry.path), target=target, broken=broken)
            elif entry.is_dir(follow_symlinks=False):
                abs_path = os.path.abspath(entry.path)
                if any(abs_path.startswith(p) for p in skip_prefixes):
                    continue
                if max_depth is not None and depth + 1 > max_depth:
                    continue
                stack.append((Path(entry.path), depth + 1))


# ---------- reporting ----------

def print_result(result: OperationResult) -> None:
    prefix = {
        "created": "[OK]",
        "dry-run": "[DRY]",
        "skipped": "[SKIP]",
        "error": "[ERR]",
    }.get(result.status, "[INFO]")

    line = f"{prefix} {result.message}"
    if result.spec.line_no is not None:
        line = f"line {result.spec.line_no}: {line}"
    print(line)


def print_summary(results: List[OperationResult]) -> int:
    created = sum(r.status == "created" for r in results)
    dry = sum(r.status == "dry-run" for r in results)
    skipped = sum(r.status == "skipped" for r in results)
    errors = sum(r.status == "error" for r in results)

    print("\nSummary")
    print(f"  created : {created}")
    print(f"  dry-run : {dry}")
    print(f"  skipped : {skipped}")
    print(f"  errors  : {errors}")

    return 1 if errors else 0


def print_find_result(result: FindResult) -> None:
    if result.broken:
        print(f"[BROKEN] {result.link_path} -> {result.target}  (target missing)")
    else:
        print(f"[LINK]   {result.link_path} -> {result.target}")


def print_find_summary(results: List[FindResult]) -> int:
    found = len(results)
    broken = sum(r.broken for r in results)
    print("\nSummary")
    print(f"  found  : {found}")
    print(f"  broken : {broken}")
    return 1 if broken else 0


def write_find_results(results: List[FindResult], output_path: Path) -> None:
    found = len(results)
    broken = sum(r.broken for r in results)
    with output_path.open("w", encoding="utf-8") as fh:
        for result in results:
            if result.broken:
                fh.write(f"[BROKEN] {result.link_path} -> {result.target}  (target missing)\n")
            else:
                fh.write(f"[LINK]   {result.link_path} -> {result.target}\n")
        fh.write("\nSummary\n")
        fh.write(f"  found  : {found}\n")
        fh.write(f"  broken : {broken}\n")


# ---------- cli ----------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create macOS symbolic links interactively or in bulk."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--interactive",
        action="store_true",
        help="run in interactive mode",
    )
    group.add_argument(
        "--bulk",
        type=str,
        metavar="FILE",
        help="read link mappings from a text file",
    )
    group.add_argument(
        "--find",
        nargs="?",
        const=".",
        metavar="DIR",
        help="search for symlinks under DIR (default: current directory)",
    )

    parser.add_argument(
        "--broken",
        action="store_true",
        help="(find mode) only show broken symlinks",
    )
    parser.add_argument(
        "--depth",
        type=int,
        metavar="N",
        help="(find mode) maximum recursion depth",
    )
    parser.add_argument(
        "--output",
        type=str,
        metavar="FILE",
        help="(find mode) save results to a text file",
    )
    parser.add_argument(
        "--separator",
        default="->",
        help="separator for bulk mode (default: ->)",
    )
    parser.add_argument(
        "--conflict",
        choices=["ask", "skip", "overwrite", "backup"],
        default="ask",
        help="what to do if destination exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show actions without creating links",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="assume yes for prompts where reasonable",
    )
    return parser


def run_interactive(args: argparse.Namespace) -> int:
    spec = interactive_collect()
    if spec is None:
        return 1

    confirm = "y" if args.yes else input("Create this symlink? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return 1

    result = create_symlink(
        spec,
        on_conflict=args.conflict,
        dry_run=args.dry_run,
        assume_yes=args.yes,
    )
    print_result(result)
    return 1 if result.status == "error" else 0


def run_bulk(args: argparse.Namespace) -> int:
    file_path = expand_path(args.bulk)
    if not file_path.exists():
        print(f"Bulk file not found: {file_path}")
        return 1

    try:
        specs = load_bulk_specs(file_path, separator=args.separator)
    except Exception as e:
        print(f"Failed to load bulk file: {e}")
        return 1

    if not specs:
        print("No link entries found.")
        return 1

    print(f"Loaded {len(specs)} link entries from {file_path}")
    if not args.yes:
        confirm = input("Continue? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return 1

    results = [
        create_symlink(
            spec,
            on_conflict=args.conflict,
            dry_run=args.dry_run,
            assume_yes=args.yes,
        )
        for spec in specs
    ]

    for result in results:
        print_result(result)

    return print_summary(results)


def run_find(args: argparse.Namespace) -> int:
    root = expand_path(args.find)
    if not root.exists() or not root.is_dir():
        print(f"Not a directory: {root}")
        return 1

    header = f"Searching for symlinks under: {root}"
    if args.broken:
        header += "  (broken only)"
    if args.depth is not None:
        header += f"  (depth limit: {args.depth})"
    print(header)

    results: List[FindResult] = []
    for result in walk_symlinks(root, max_depth=args.depth):
        if args.broken and not result.broken:
            continue
        print_find_result(result)
        results.append(result)

    rc = print_find_summary(results)

    if args.output:
        output_path = expand_path(args.output)
        write_find_results(results, output_path)
        print(f"\u2192 saved to {output_path}")

    return rc


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if (args.broken or args.depth is not None or args.output) and not args.find:
        parser.error("--broken, --depth, and --output only apply with --find")

    if not args.interactive and not args.bulk and not args.find:
        args.interactive = True

    if args.find:
        return run_find(args)
    if args.bulk:
        return run_bulk(args)
    return run_interactive(args)


if __name__ == "__main__":  # python3 -m symlink_cli.core
    sys.exit(main())