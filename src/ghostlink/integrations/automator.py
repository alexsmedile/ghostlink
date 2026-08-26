from __future__ import annotations

import plistlib
import shutil
from pathlib import Path

WORKFLOW_NAME = "Ghostlink Quick Link.workflow"
SERVICE_MENU_TITLE = "Ghostlink: Create Symlink Here…"

_APPLESCRIPT_SOURCE = """-- Ghostlink Quick Action
-- Invoked as a Finder Service on a selected folder.
-- Prompts for a link name and a destination folder, then creates the symlink via ghostlink.

on run {input, parameters}
\tif (count of input) is 0 then
\t\tdisplay notification "No folder selected." with title "Ghostlink"
\t\treturn input
\tend if

\tset sourceAlias to item 1 of input
\tset sourcePath to POSIX path of sourceAlias
\tif sourcePath ends with "/" then set sourcePath to text 1 thru -2 of sourcePath

\tset sourceName to do shell script "basename " & quoted form of sourcePath

\tset linkName to text returned of (display dialog "Link name for:" & return & sourcePath default answer sourceName with title "Ghostlink: Name")

\tset destPosix to POSIX path of (choose folder with prompt "Choose where to place the \\"" & linkName & "\\" link:")
\tif destPosix ends with "/" then set destPosix to text 1 thru -2 of destPosix

\tset destPath to destPosix & "/" & linkName

\tset ghostlinkBin to "GHOSTLINK_BIN_PLACEHOLDER"

\ttry
\t\tset cmd to quoted form of ghostlinkBin & " create --source " & quoted form of sourcePath & " --dest " & quoted form of destPath & " -y"
\t\tset cmdOutput to do shell script cmd
\t\tdisplay notification destPath & " \\u2192 " & sourcePath with title "Ghostlink: Linked"
\ton error errMsg
\t\tdisplay alert "Ghostlink failed" message errMsg as critical
\tend try

\treturn input
end run
"""


def render_applescript_source(ghostlink_bin: str) -> str:
    return _APPLESCRIPT_SOURCE.replace("GHOSTLINK_BIN_PLACEHOLDER", ghostlink_bin)


def render_info_plist() -> bytes:
    doc = {
        "NSServices": [
            {
                "NSBackgroundColorName": "background",
                "NSIconName": "NSActionTemplate",
                "NSMenuItem": {"default": SERVICE_MENU_TITLE},
                "NSMessage": "runWorkflowAsService",
                "NSRequiredContext": {"NSApplicationIdentifier": "com.apple.finder"},
                "NSSendFileTypes": ["public.folder"],
            }
        ]
    }
    return plistlib.dumps(doc)


def render_document_wflow(ghostlink_bin: str) -> bytes:
    script_source = render_applescript_source(ghostlink_bin)
    doc = {
        "AMApplicationBuild": "509",
        "AMApplicationVersion": "2.10",
        "AMDocumentVersion": "2",
        "actions": [
            {
                "action": {
                    "AMAccepts": {
                        "Container": "List",
                        "Optional": True,
                        "Types": ["com.apple.applescript.object"],
                    },
                    "AMActionVersion": "1.0.2",
                    "AMApplication": ["Automator"],
                    "AMParameterProperties": {"source": {}},
                    "AMProvides": {
                        "Container": "List",
                        "Types": ["com.apple.applescript.object"],
                    },
                    "ActionBundlePath": "/System/Library/Automator/Run AppleScript.action",
                    "ActionName": "Run AppleScript",
                    "ActionParameters": {"source": script_source},
                    "BundleIdentifier": "com.apple.Automator.RunScript",
                    "CFBundleVersion": "1.0.2",
                    "CanShowSelectedItemsWhenRun": False,
                    "CanShowWhenRun": True,
                    "Category": ["AMCategoryUtilities"],
                    "Class Name": "RunScriptAction",
                    "InputUUID": "C0417148-5375-45F9-8439-4C7EE6733FB9",
                    "Keywords": ["Run"],
                    "OutputUUID": "14C8F971-8A01-4C75-93B3-C69BC4811527",
                    "UUID": "4E138A06-65BF-45E2-A877-290301C31310",
                    "UnlocalizedApplications": ["Automator"],
                    "arguments": {
                        "0": {
                            "default value": (
                                "on run {input, parameters}\n\t\n"
                                "\t(* Your script goes here *)\n\t\n"
                                "\treturn input\nend run"
                            ),
                            "name": "source",
                            "required": "0",
                            "type": "0",
                            "uuid": "0",
                        }
                    },
                    "conversionLabel": 0,
                    "isViewVisible": 1,
                    "location": "309.000000:253.000000",
                },
                "isViewVisible": 1,
            }
        ],
        "connectors": {},
        "workflowMetaData": {
            "applicationBundleID": "com.apple.finder",
            "applicationBundleIDsByPath": {
                "/System/Library/CoreServices/Finder.app": "com.apple.finder"
            },
            "applicationPath": "/System/Library/CoreServices/Finder.app",
            "applicationPaths": ["/System/Library/CoreServices/Finder.app"],
            "inputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "outputTypeIdentifier": "com.apple.Automator.nothing",
            "presentationMode": 15,
            "processesInput": False,
            "serviceApplicationBundleID": "com.apple.finder",
            "serviceApplicationPath": "/System/Library/CoreServices/Finder.app",
            "serviceInputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": False,
            "systemImageName": "NSActionTemplate",
            "useAutomaticInputType": False,
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }
    return plistlib.dumps(doc)


def services_directory() -> Path:
    return Path.home() / "Library" / "Services"


def workflow_install_path() -> Path:
    return services_directory() / WORKFLOW_NAME


def install_quick_link_workflow(ghostlink_bin: str, target: Path | None = None) -> Path:
    destination = target or workflow_install_path()
    contents_dir = destination / "Contents"
    contents_dir.mkdir(parents=True, exist_ok=True)
    (contents_dir / "Info.plist").write_bytes(render_info_plist())
    (contents_dir / "document.wflow").write_bytes(render_document_wflow(ghostlink_bin))
    return destination


def uninstall_quick_link_workflow(target: Path | None = None) -> bool:
    destination = target or workflow_install_path()
    if not destination.exists():
        return False
    shutil.rmtree(destination)
    return True


def refresh_launch_services() -> None:
    pbs = Path("/System/Library/CoreServices/pbs")
    if pbs.exists():
        import subprocess

        subprocess.run([str(pbs), "-flush"], check=False, capture_output=True)
