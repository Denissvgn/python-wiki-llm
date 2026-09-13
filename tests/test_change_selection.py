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
    assert patch_paths(
        '--- "a/юникод.py"\t2026-09-13 00:00:00\n+++ "b/юникод.py"\t2026-09-13 00:00:01\n'
    ) == ["юникод.py"]


@pytest.mark.parametrize("retained_index", [False, True])
@pytest.mark.parametrize("fmt", ["json", "packet"])
def test_existing_page_provenance_wins_over_narrow_inventory_names(
    tmp_path, monkeypatch, retained_index, fmt
):
    from llm_wiki_cli.services.wiki_surface_index import (
        SURFACE_INDEX_FILENAME,
        WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    )

    monkeypatch.chdir(tmp_path)
    (tmp_path / "backend.py").write_text("class Shared: pass\n")
    wiki = tmp_path / "wiki"
    (wiki / "modules").mkdir(parents=True)
    (wiki / "entities").mkdir()
    (wiki / "modules/backend.md").write_text("# backend\n\n**Path:** `backend.py`\n")
    (wiki / "entities/Shared.md").write_text(
        "# Shared\n\n**Location:** `frontend/types.ts:12`\n"
    )
    (wiki / "entities/backend_Shared.md").write_text(
        "# Shared\n\n**Location:** `backend.py:1`\n"
    )
    if retained_index:
        (wiki / SURFACE_INDEX_FILENAME).write_text(
            json.dumps(
                {
                    "schema_version": WIKI_SURFACE_INDEX_SCHEMA_VERSION,
                    "pages": [
                        {
                            "source_path": "backend.py",
                            "canonical_path": "entities/Shared.md",
                        }
                    ],
                }
            )
        )
    changes = {"mode": "paths", "paths": ["backend.py"]}
    context = json.loads(
        build_budgeted_context(
            wiki_dir="wiki",
            request={
                "budget_tokens": 100_000,
                "budget_mode": "estimated",
                "changes": changes,
                "format": fmt,
            },
        ).rendered
    )
    findings = build_findings("", wiki_dir="wiki", changes=changes)
    expected = ["entities/backend_Shared.md", "modules/backend.md"]
    assert context["changes"]["affected_pages"]["backend.py"] == expected
    assert len(findings) == 1 and findings[0].wiki_pages == expected


def test_context_rejects_staged_selection_mutation(tmp_path, monkeypatch):
    from llm_wiki_cli.services import context_budget
    from llm_wiki_cli.services.context_packet import ContextPacketSourceMutationError

    monkeypatch.chdir(tmp_path)
    git(tmp_path, "init", "-q")
    for path in ("a.py", "b.py"):
        (tmp_path / path).write_text("def run(): return 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    for path in ("a.py", "b.py"):
        (tmp_path / path).write_text("def run(): return 2\n")
    git(tmp_path, "add", "a.py")
    fit = context_budget.fit_payload

    def change_index(*args, **kwargs):
        result = fit(*args, **kwargs)
        git(tmp_path, "add", "b.py")
        return result

    monkeypatch.setattr(context_budget, "fit_payload", change_index)
    with pytest.raises(ContextPacketSourceMutationError, match="source-selection"):
        build_budgeted_context(
            request={
                "budget_tokens": 100_000,
                "budget_mode": "estimated",
                "changes": {"mode": "staged"},
            }
        )


def test_patch_hunk_content_is_not_a_path():
    patch = (
        "--- a/real.py\n+++ b/real.py\n@@ -1,2 +1,2 @@\n"
        "--- a/false.py\n-rename from invented.py\n"
        "+++ b/false.py\n+rename to invented.py\n"
        "--- a/next.py\n+++ b/next.py\n@@ -0,0 +1 @@\n+pass\n"
    )
    assert patch_paths(patch) == ["next.py", "real.py"]


def test_git_patch_binary_mode_copy_and_unicode_match_name_status(tmp_path):
    git(tmp_path, "init", "-q")
    for name, data in (
        ("binary space.bin", b"\0before"),
        ("mode.sh", b"exit 0\n"),
        ("юникод.txt", b"copy me\n"),
    ):
        (tmp_path / name).write_bytes(data)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    (tmp_path / "binary space.bin").write_bytes(b"\0after")
    git(tmp_path, "update-index", "--chmod=+x", "mode.sh")
    (tmp_path / "copy space.txt").write_bytes((tmp_path / "юникод.txt").read_bytes())
    git(tmp_path, "add", "binary space.bin", "copy space.txt")
    for quoting in ("true", "false"):
        patch = git(
            tmp_path,
            "-c",
            f"core.quotePath={quoting}",
            "diff",
            "--cached",
            "--find-copies-harder",
        )
        assert patch_paths(patch) == [
            "binary space.bin",
            "copy space.txt",
            "mode.sh",
            "юникод.txt",
        ]


def test_source_root_with_leading_space(tmp_path):
    git(tmp_path, "init", "-q")
    src = tmp_path / " source"
    src.mkdir()
    (src / "app.py").write_text("pass\n")
    git(tmp_path, "add", ".")
    assert select_changes(src, {"mode": "staged"})["paths"] == ["app.py"]


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
