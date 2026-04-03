from __future__ import annotations

import importlib
import sys

from ghostlink import main


def _alias(submodule: str) -> None:
    target = importlib.import_module(f"ghostlink.{submodule}" if submodule else "ghostlink")
    name = f"symlink_cli.{submodule}" if submodule else "symlink_cli"
    sys.modules[name] = target


for module_name in (
    "cli",
    "cli.main",
    "cli.parser",
    "compat",
    "compat.legacy_flags",
    "domain",
    "domain.models",
    "domain.paths",
    "domain.results",
    "domain.validation",
    "integrations",
    "integrations.launchd",
    "output",
    "output.prompts",
    "output.renderers",
    "services",
    "services.check_service",
    "services.config_service",
    "services.find_service",
    "services.link_service",
    "services.registry_service",
    "services.schedule_service",
    "services.sync_service",
    "storage",
    "storage.registry",
    "storage.run_log",
):
    _alias(module_name)


__all__ = ["main"]
