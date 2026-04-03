from __future__ import annotations

from ghostlink.output import prompts, renderers

from conftest import require_exports


def test_renderers_contract():
    require_exports(
        renderers,
        (
            "render_create_preview",
            "render_operation_summary",
            "render_find_results",
            "render_check_results",
            "render_status_report",
            "render_sync_diff_summary",
        ),
    )


def test_prompts_contract():
    require_exports(
        prompts,
        (
            "PromptOption",
            "prompt_text",
            "prompt_choice",
            "confirm_action",
            "confirm_review",
        ),
    )


def test_render_create_preview_smoke():
    preview = renderers.render_create_preview(
        "/tmp/source",
        "/tmp/destination",
        conflict="backup",
        dry_run=True,
    )

    assert "Review" in preview
    assert "backup" in preview
    assert "dry-run" in preview


def test_prompt_choice_and_confirm_smoke():
    option = prompts.PromptOption(key="2", label="Overwrite", value="overwrite")
    answers = iter(["x", "2"])
    choice = prompts.prompt_choice("Choose", [option], input_func=lambda _: next(answers))
    assert choice == "overwrite"
    assert prompts.confirm_action("Proceed?", input_func=lambda _: "y") is True
