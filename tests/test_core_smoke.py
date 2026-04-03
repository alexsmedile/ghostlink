from __future__ import annotations

from pathlib import Path

from ghostlink import core
from symlink_cli import core as compat_core


def test_validate_spec_rejects_missing_source(tmp_path):
    spec = core.LinkSpec(source=tmp_path / "missing", destination=tmp_path / "dest")

    ok, reason = core.validate_spec(spec)

    assert ok is False
    assert "source does not exist" in reason


def test_parse_bulk_line_supports_separator_and_quotes():
    parsed = core.parse_bulk_line('"/Users/me/My Files/report.pdf" -> "~/Desktop/report-link.pdf"', "->")

    assert parsed == ("/Users/me/My Files/report.pdf", "~/Desktop/report-link.pdf")


def test_load_bulk_specs_resolves_relative_paths_against_bulk_file(tmp_path):
    bulk_file = tmp_path / "links.txt"
    bulk_file.write_text("assets/project -> links/project-link\n", encoding="utf-8")

    specs = core.load_bulk_specs(bulk_file)

    assert len(specs) == 1
    assert specs[0].source == (bulk_file.parent / "assets/project").resolve()
    assert specs[0].destination == (bulk_file.parent / "links/project-link").resolve()
    assert specs[0].line_no == 1


def test_print_find_result_marks_broken_links(capsys):
    result = core.FindResult(link_path=Path("/tmp/link"), target=Path("/tmp/missing"), broken=True)

    core.print_find_result(result)

    assert "[BROKEN]" in capsys.readouterr().out


def test_prompt_non_empty_keeps_asking_until_input_is_present(monkeypatch):
    answers = iter(["", "   ", "value"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    assert core.prompt_non_empty("Label: ") == "value"


def test_symlink_cli_compat_module_still_resolves():
    assert compat_core.main is core.main
