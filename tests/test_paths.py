"""Tests for shared path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_wiki_cli.services.paths import (
    display_project_path,
    normalize_source_path,
    portable_source_root_label,
    shell_quote,
)


def test_display_project_path_is_checkout_relative_and_posix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)

    assert display_project_path(project / "custom" / "wiki") == "custom/wiki"
    assert display_project_path(Path("custom") / "wiki") == "custom/wiki"


@pytest.mark.parametrize("value", [None, "", "   ", "``", "`   `", '""', "''"])
def test_normalize_source_path_returns_none_for_empty_values(value):
    assert normalize_source_path(value) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("./pkg/module.py", "pkg/module.py"),
        ("`./pkg/module.py`", "pkg/module.py"),
        ('"./pkg/module.py"', "pkg/module.py"),
        ("'./pkg/module.py'", "pkg/module.py"),
        (" ./pkg\\module.py ", "pkg/module.py"),
        ("././pkg/module.py", "pkg/module.py"),
    ],
)
def test_normalize_source_path_cleans_generated_relative_paths(value, expected):
    assert normalize_source_path(value) == expected


def test_normalize_source_path_relativizes_absolute_paths_under_src_dir(tmp_path):
    src_dir = tmp_path / "src"
    source_file = src_dir / "pkg" / "module.py"
    source_file.parent.mkdir(parents=True)
    source_file.write_text("class Module: pass\n", encoding="utf-8")

    assert normalize_source_path(str(source_file), str(src_dir)) == "pkg/module.py"


def test_normalize_source_path_keeps_absolute_paths_outside_src_dir(tmp_path):
    src_dir = tmp_path / "src"
    outside_file = tmp_path / "external" / "module.py"
    src_dir.mkdir()
    outside_file.parent.mkdir()
    outside_file.write_text("class Module: pass\n", encoding="utf-8")

    assert (
        normalize_source_path(str(outside_file), str(src_dir))
        == outside_file.as_posix()
    )


def test_normalize_source_path_keeps_absolute_paths_outside_relative_src_dir(
    tmp_path, monkeypatch
):
    project = tmp_path / "project"
    outside_file = tmp_path / "external" / "module.py"
    project.mkdir()
    outside_file.parent.mkdir()
    outside_file.write_text("class Module: pass\n", encoding="utf-8")
    monkeypatch.chdir(project)

    assert normalize_source_path(str(outside_file), ".") == outside_file.as_posix()


def test_shell_quote_quotes_strings_and_paths_for_posix_shell():
    assert shell_quote("plain") == "plain"
    assert shell_quote("docs/My File.md") == "'docs/My File.md'"
    assert shell_quote(Path("docs/My File.md")) == "'docs/My File.md'"


def test_portable_source_root_label_is_relative_or_redacted(tmp_path):
    source_root = tmp_path / "source"
    nested_root = source_root / "packages" / "app"
    external_root = tmp_path / "external"
    nested_root.mkdir(parents=True)
    external_root.mkdir()

    assert portable_source_root_label(source_root, base=source_root) == "."
    assert (
        portable_source_root_label(nested_root, base=source_root)
        == "packages/app"
    )
    assert (
        portable_source_root_label(external_root, base=source_root)
        == "<external-source-root>"
    )


@pytest.mark.parametrize(
    "value",
    [
        r"C:\Users\owner\project",
        r"C:project",
        "/home/owner/project",
    ],
)
def test_portable_source_root_label_redacts_foreign_absolute_path(
    tmp_path,
    value,
):
    assert (
        portable_source_root_label(value, base=tmp_path) == "<external-source-root>"
    )
