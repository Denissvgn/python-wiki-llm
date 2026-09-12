import json
import subprocess

import pytest

from llm_wiki_cli.commands.review_cmd import build_findings
from llm_wiki_cli.services.change_selection import (
    affected_page_map,
    patch_paths,
    portable_path,
    select_changes,
)
from llm_wiki_cli.services.context_budget import build_budgeted_context
from llm_wiki_cli.services.source_snapshot import build_source_snapshot


def git(root, *args):
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            *args,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_equivalent_range_staged_paths_and_context_review_mapping(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    git(tmp_path, "init", "-q")
    src = tmp_path / "src"
    src.mkdir()
    (src / "old.py").write_text("class Old:\n    pass\n")
    (src / "удалить.py").write_text("def remove(): pass\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    base = git(tmp_path, "rev-parse", "HEAD")
    (src / "old.py").rename(src / "новый.py")
    (src / "удалить.py").unlink()
    git(tmp_path, "add", "-A")
    staged = select_changes(src, {"mode": "staged"})
    explicit = select_changes(
        src, {"mode": "paths", "paths": ["old.py", "новый.py", "удалить.py"]}
    )
    git(tmp_path, "commit", "-qm", "candidate")
    ranged = select_changes(src, {"mode": "range", "base": base, "head": "HEAD"})
    assert staged["paths"] == explicit["paths"] == ranged["paths"]
    assert staged["paths_id"] == ranged["paths_id"]
    request = {
        "budget_tokens": 100_000,
        "budget_mode": "estimated",
        "changes": explicit["request"],
    }
    context = json.loads(build_budgeted_context("src", request=request).rendered)
    findings = build_findings("", src_dir="src", changes=explicit["request"])
    assert context["changes"]["affected_pages"]["новый.py"] == next(
        f.wiki_pages for f in findings if f.source_path == "новый.py"
    )
    for mode in (explicit["request"], ranged["request"] | {}):
        # The API expects selection inputs, not resolved provenance fields.
        mode = {k: v for k, v in mode.items() if k in {"mode", "paths", "base", "head"}}
        current = json.loads(
            build_budgeted_context("src", request={**request, "changes": mode}).rendered
        )
        assert (
            current["changes"]["affected_pages"] == context["changes"]["affected_pages"]
        )


def test_non_git_windows_paths_and_no_ambiguous_suffix_mapping(tmp_path):
    chosen = select_changes(
        tmp_path, {"mode": "paths", "paths": [r"pkg\модуль.py", "./pkg/модуль.py"]}
    )
    assert chosen["paths"] == ["pkg/модуль.py"]
    assert affected_page_map(["module.py"], {"a/module.py": {}, "b/module.py": {}}) == {
        "module.py": []
    }
    with pytest.raises(ValueError, match="Git changes"):
        select_changes(tmp_path, {"mode": "staged"})
    for path in ("../escape.py", r"C:\src\app.py", "/app.py", "a//b.py"):
        with pytest.raises(ValueError):
            portable_path(path)


def test_patch_deletion_rename_and_git_quoted_utf8():
    patch = '--- a/deleted.py\n+++ /dev/null\nrename from old.py\nrename to new.py\n+++ "b/\\320\\260.py"\n'
    assert patch_paths(patch) == ["deleted.py", "new.py", "old.py", "а.py"]


def test_selection_control_expands_only_selected_sources(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/a.py").write_text("def a(): pass\n")
    (tmp_path / "hidden.py").write_text("def hidden(): pass\n")
    config = tmp_path / ".llm-wiki/source-selection.json"
    config.parent.mkdir()
    config.write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["src"],
                "exclude": [],
            }
        )
    )
    snapshot = build_source_snapshot(tmp_path)
    selection = select_changes(
        tmp_path,
        {"mode": "paths", "paths": ["hidden.py", ".llm-wiki/source-selection.json"]},
        snapshot=snapshot,
    )
    assert selection["selection_boundary_changed"]
    assert selection["paths"] == ["src/a.py"]
