from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ghostlink.domain.models import LinkSpec
from ghostlink.domain.paths import expand_path, normalize_destination
from ghostlink.domain.validation import validate_link_spec


@dataclass(slots=True)
class PromptOption:
    key: str
    label: str
    value: str


def prompt_non_empty(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("Please enter a value.")


def choose_action() -> str:
    print("\nWhat do you want to do?")
    print("1) Create a symlink")
    print("2) Find symlinks")
    print("3) Check saved links")
    print("4) List saved items")
    choice = input("Choose [1-4] (default 1): ").strip() or "1"
    return choice


def prompt_text(label: str, input_func: Callable[[str], str] = input) -> str:
    return input_func(label).strip()


def prompt_choice(
    label: str,
    options: list[PromptOption],
    input_func: Callable[[str], str] = input,
) -> str:
    while True:
        answer = input_func(f"{label}: ").strip()
        for option in options:
            if answer == option.key:
                return option.value
        print("Please choose one of the listed options.")


def confirm_action(label: str, input_func: Callable[[str], str] = input) -> bool:
    return input_func(f"{label} [y/N]: ").strip().lower() == "y"


def confirm_review(
    label: str,
    details: str,
    input_func: Callable[[str], str] = input,
) -> bool:
    print(label)
    print(details)
    return confirm_action("Continue?", input_func=input_func)


def ask_conflict_choice(destination: Path) -> str:
    while True:
        print(f"This path already exists: {destination}")
        print("Choose: [s]kip  [o]verwrite  [b]ackup existing")
        choice = input("> ").strip().lower()
        if choice in {"s", "o", "b"}:
            return choice
        print("Please type s, o, or b.")


def interactive_collect(base_dir: Optional[Path] = None) -> Optional[LinkSpec]:
    print("\nSymlink Helper\n")
    source_raw = prompt_non_empty("Source file or folder path: ")
    source = expand_path(source_raw, base_dir=base_dir)
    if not source.exists():
        print(f"Source does not exist: {source}")
        return None
    print("\nDestination options:")
    print("1) Enter a target folder, then choose a link name")
    print("2) Enter the full destination path directly")
    mode = input("Choose [1/2] (default 1): ").strip() or "1"
    if mode == "1":
        target_folder_raw = prompt_non_empty("Target folder path: ")
        link_name = input(f"Link name (default: {source.name}): ").strip() or source.name
        destination = normalize_destination(source, target_folder_raw, link_name, base_dir=base_dir)
    else:
        destination_raw = prompt_non_empty("Full destination path for the symlink: ")
        destination = normalize_destination(source, destination_raw, None, base_dir=base_dir)
    spec = LinkSpec(source=source, destination=destination)
    ok, reason = validate_link_spec(spec)
    if not ok:
        print(f"\nValidation error: {reason}")
        return None
    print("\nReady to create:")
    print(f"  source      {spec.source}")
    print(f"  symlink at  {spec.destination}")
    return spec
