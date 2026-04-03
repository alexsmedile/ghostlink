from __future__ import annotations

import argparse

from ghostlink.domain.models import ConflictPolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghostlink",
        description="Create, find, check, save, sync, and schedule symlink workflows.",
        epilog=(
            "Simple usage:\n"
            "  ghostlink\n"
            "  ghostlink <source> <destination>\n"
            "  ghostlink bulk <file>\n\n"
            "Advanced usage:\n"
            "  ghostlink create --source <path> --dest <path>\n"
            "  ghostlink find <path> --broken --depth 2\n"
            "  ghostlink check --saved\n"
            "  ghostlink repair --saved -y\n"
            "  ghostlink export links.json --profile dev"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--registry-path",
        type=str,
        help="override the registry file location",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON output")
    subparsers = parser.add_subparsers(dest="command")

    create = subparsers.add_parser("create", help="create one symlink or many from a file")
    create.add_argument("--source", type=str)
    create.add_argument("--dest", type=str)
    create.add_argument("--bulk", type=str, metavar="FILE")
    create.add_argument("--separator", default="->")
    create.add_argument(
        "--conflict",
        choices=[item.value for item in ConflictPolicy],
        default=ConflictPolicy.ASK.value,
    )
    create.add_argument("--dry-run", action="store_true")
    create.add_argument("-y", "--yes", action="store_true")
    create.add_argument("--relative", action="store_true", help="create a relative symlink target")
    create.add_argument("--save-name", type=str, help="save the created link with this name")

    find = subparsers.add_parser("find", help="find symlinks in a folder")
    find.add_argument("path", nargs="?", default=".")
    find.add_argument("--broken", action="store_true")
    find.add_argument("--depth", type=int)
    find.add_argument("--output", type=str)

    check = subparsers.add_parser("check", help="check one path, one folder, or saved items")
    check.add_argument("path", nargs="?")
    check.add_argument("--saved", action="store_true")
    check.add_argument("--broken", action="store_true")

    repair = subparsers.add_parser("repair", help="repair one saved link, all saved links, or a bulk file")
    repair.add_argument("name", nargs="?")
    repair.add_argument("--saved", action="store_true")
    repair.add_argument("--bulk", type=str, metavar="FILE")
    repair.add_argument("--separator", default="->")
    repair.add_argument(
        "--conflict",
        choices=[item.value for item in ConflictPolicy],
        default=ConflictPolicy.OVERWRITE.value,
    )
    repair.add_argument("--dry-run", action="store_true")
    repair.add_argument("-y", "--yes", action="store_true")

    export = subparsers.add_parser("export", help="export saved links to a portable relation-set file")
    export.add_argument("file")
    export.add_argument("--profile", default="default")
    export.add_argument("--name", action="append", dest="names")
    export.add_argument("--relative", action="store_true", help="store link paths relative to the export file")

    apply_cmd = subparsers.add_parser("apply", help="apply a relation-set file")
    apply_cmd.add_argument("file")
    apply_cmd.add_argument("--profile", default="default")
    apply_cmd.add_argument(
        "--conflict",
        choices=[item.value for item in ConflictPolicy],
        default=ConflictPolicy.ASK.value,
    )
    apply_cmd.add_argument("--dry-run", action="store_true")
    apply_cmd.add_argument("-y", "--yes", action="store_true")
    apply_cmd.add_argument("--relative", action="store_true", help="create relative symlink targets")
    apply_cmd.add_argument("--save", action="store_true", help="save applied links into the registry")

    import_cmd = subparsers.add_parser("import", help="alias for apply")
    import_cmd.add_argument("file")
    import_cmd.add_argument("--profile", default="default")
    import_cmd.add_argument(
        "--conflict",
        choices=[item.value for item in ConflictPolicy],
        default=ConflictPolicy.ASK.value,
    )
    import_cmd.add_argument("--dry-run", action="store_true")
    import_cmd.add_argument("-y", "--yes", action="store_true")
    import_cmd.add_argument("--relative", action="store_true", help="create relative symlink targets")
    import_cmd.add_argument("--save", action="store_true", help="save applied links into the registry")

    save = subparsers.add_parser("save", help="save a link or sync record")
    save.add_argument("--name", required=True)
    save.add_argument("--source", required=True)
    save.add_argument("--dest", required=True)
    save.add_argument("--type", choices=["link", "sync"], default="link")
    save.add_argument(
        "--conflict",
        choices=[item.value for item in ConflictPolicy],
        default=ConflictPolicy.ASK.value,
    )

    subparsers.add_parser("list", help="list saved records")

    show = subparsers.add_parser("show", help="show one saved record")
    show.add_argument("name")

    remove = subparsers.add_parser("remove", help="remove one saved record")
    remove.add_argument("name")

    rename = subparsers.add_parser("rename", help="rename one saved record")
    rename.add_argument("old_name")
    rename.add_argument("new_name")

    sync = subparsers.add_parser("sync", help="plan and run one-way folder syncs")
    sync_subparsers = sync.add_subparsers(dest="sync_command", required=True)
    sync_diff = sync_subparsers.add_parser("diff", help="show a one-way sync diff")
    sync_diff.add_argument("--source", type=str)
    sync_diff.add_argument("--dest", type=str)
    sync_diff.add_argument("--config", type=str)
    sync_diff.add_argument("--profile", default="default")
    sync_diff.add_argument("name", nargs="?")
    sync_run = sync_subparsers.add_parser("run", help="run a one-way sync")
    sync_run.add_argument("--source", type=str)
    sync_run.add_argument("--dest", type=str)
    sync_run.add_argument("--config", type=str)
    sync_run.add_argument("--profile", default="default")
    sync_run.add_argument("name", nargs="?")
    sync_run.add_argument("--dry-run", action="store_true")
    sync_run.add_argument("-y", "--yes", action="store_true")
    sync_save = sync_subparsers.add_parser("save", help="save a one-way sync job")
    sync_save.add_argument("--name", required=True)
    sync_save.add_argument("--source", required=True)
    sync_save.add_argument("--dest", required=True)

    schedule = subparsers.add_parser("schedule", help="preview launchd schedules for saved jobs")
    schedule_subparsers = schedule.add_subparsers(dest="schedule_command", required=True)
    schedule_add = schedule_subparsers.add_parser("add", help="add or update a schedule")
    schedule_add.add_argument("name")
    schedule_add.add_argument("--every", required=True)
    schedule_add.add_argument("--write", action="store_true")
    schedule_subparsers.add_parser("list", help="list schedules")
    schedule_show = schedule_subparsers.add_parser("show", help="show one saved schedule")
    schedule_show.add_argument("name")
    schedule_run = schedule_subparsers.add_parser("run", help="run one scheduled job and update heartbeat metadata")
    schedule_run.add_argument("name")
    schedule_remove = schedule_subparsers.add_parser("remove", help="remove one schedule")
    schedule_remove.add_argument("name")

    subparsers.add_parser("status", help="show the latest saved status information")

    return parser
