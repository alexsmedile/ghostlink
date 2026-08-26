from __future__ import annotations

import plistlib

from ghostlink.integrations.automator import (
    SERVICE_MENU_TITLE,
    install_quick_link_workflow,
    render_document_wflow,
    render_info_plist,
    uninstall_quick_link_workflow,
)

from conftest import require_exports


def test_automator_integration_contract():
    require_exports(
        __import__("ghostlink.integrations.automator", fromlist=["install_quick_link_workflow"]),
        (
            "WORKFLOW_NAME",
            "SERVICE_MENU_TITLE",
            "render_applescript_source",
            "render_info_plist",
            "render_document_wflow",
            "workflow_install_path",
            "install_quick_link_workflow",
            "uninstall_quick_link_workflow",
            "refresh_launch_services",
        ),
    )


def test_render_info_plist_declares_folder_service():
    doc = plistlib.loads(render_info_plist())
    service = doc["NSServices"][0]
    assert service["NSMenuItem"]["default"] == SERVICE_MENU_TITLE
    assert service["NSSendFileTypes"] == ["public.folder"]
    assert service["NSRequiredContext"]["NSApplicationIdentifier"] == "com.apple.finder"


def test_render_document_wflow_embeds_ghostlink_binary_path():
    doc = plistlib.loads(render_document_wflow("/usr/local/bin/ghostlink"))
    source = doc["actions"][0]["action"]["ActionParameters"]["source"]
    assert '"/usr/local/bin/ghostlink"' in source
    assert " create " in source


def test_install_and_uninstall_quick_link_workflow(tmp_path):
    target = tmp_path / "Ghostlink Quick Link.workflow"

    installed = install_quick_link_workflow("/usr/local/bin/ghostlink", target=target)

    assert installed == target
    assert (target / "Contents" / "Info.plist").exists()
    assert (target / "Contents" / "document.wflow").exists()
    plistlib.loads((target / "Contents" / "Info.plist").read_bytes())
    plistlib.loads((target / "Contents" / "document.wflow").read_bytes())

    removed = uninstall_quick_link_workflow(target=target)
    assert removed is True
    assert not target.exists()

    removed_again = uninstall_quick_link_workflow(target=target)
    assert removed_again is False
