import json

import pytest

from llm_wiki_cli.services.bootstrap_runtime import build_module_page_map
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.impact import build_impact, render_github, render_summary
from llm_wiki_cli.services.wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
)
from tests.test_change_selection import git


@pytest.mark.parametrize("shape", ["library", "web", "packages"])
def test_reviewed_fixture_repositories_have_correct_direct_mappings(
    tmp_path, monkeypatch, shape
):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    src.mkdir()
    wiki = tmp_path / "wiki"
    (wiki / "modules").mkdir(parents=True)
    paths = []
    for index in range(10):
        path = f"pkg{index}/модуль.py" if shape == "packages" else f"part{index}.py"
        target = src / path
        target.parent.mkdir(exist_ok=True)
        code = f"def operation_{index}():\n    return {index}\n"
        if shape == "web":
            code = (
                f'from fastapi import FastAPI\napp = FastAPI()\n@app.get("/item/{index}")\n'
                + code
            )
        elif index:
            code = "import part0\n" + code
        target.write_text(code, encoding="utf-8")
        paths.append(path)
    inventory = get_inventory_result(src, deep=True).inventory
    mapping = build_module_page_map(inventory)
    for page in mapping.values():
        (wiki / "modules" / (page + ".md")).write_text("# Existing module\n")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    report = build_impact(
        src_dir="src", wiki_dir="wiki", changes={"mode": "paths", "paths": paths}
    )
    assert len(report["findings"]) == 10
    for finding in report["findings"]:
        assert finding["severity"] == "info"
        assert finding["wiki_pages"] == [
            f"modules/{mapping[finding['source_path']]}.md"
        ]
    assert report == build_impact(
        src_dir="src",
        wiki_dir="wiki",
        changes={"mode": "paths", "paths": list(reversed(paths))},
    )
    if shape == "web":
        assert len(report["contracts"]["operations"]) == 10
    if shape == "library":
        assert len(report["dependencies"]["edges"]) == 9
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_impact_equivalent_inputs_have_identical_json_and_markdown(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    git(tmp_path, "init", "-q")
    (tmp_path / "app.py").write_text("def run(): return 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    base = git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "app.py").write_text("def run(): return 2\n")
    git(tmp_path, "add", ".")
    staged = build_impact(changes={"mode": "staged"})
    paths = build_impact(changes={"mode": "paths", "paths": ["app.py"]})
    git(tmp_path, "commit", "-qm", "candidate")
    ranged = build_impact(changes={"mode": "range", "base": base, "head": "HEAD"})
    assert (
        json.dumps(staged, sort_keys=True)
        == json.dumps(paths, sort_keys=True)
        == json.dumps(ranged, sort_keys=True)
    )
    assert render_summary(staged) == render_summary(paths) == render_summary(ranged)


def test_github_bounds_and_untrusted_path_escaping(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for index in range(60):
        (tmp_path / f"file{index}.py").write_text("def call(): pass\n")
    report = build_impact(
        changes={"mode": "paths", "paths": [f"file{i}.py" for i in range(60)]}
    )
    report["findings"][0]["annotation_path"] = "a,b:c%file.py\n::error::injected"
    report["findings"][0]["reason"] = "<script> | ` %\n::error::injected"
    text = render_github(report)
    assert len([line for line in text.splitlines() if line.startswith("::")]) == 50
    assert "%2C" in text and "%3A" in text and "%25" in text and "%0A" in text
    summary = render_summary(report)
    assert "omitted: 10" in summary
    assert len(summary.encode("utf-8")) <= 65536
    assert "<script>" not in summary


def test_impact_does_not_claim_wiki_was_unchanged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    git(tmp_path, "init", "-q")
    (tmp_path / "app.py").write_text("def run(): return 1\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "example"\n')
    wiki = tmp_path / "wiki"
    (wiki / "modules").mkdir(parents=True)
    (wiki / "modules/app.md").write_text("# app\nReturns 1.\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    (tmp_path / "app.py").write_text("def run(): return 2\n")
    (wiki / "modules/app.md").write_text("# app\nReturns 2.\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "renamed"\n')
    git(tmp_path, "add", ".")
    patch = git(tmp_path, "diff", "--cached")
    report = build_impact(patch, wiki_dir="wiki")
    assert report == build_impact(wiki_dir="wiki", changes={"mode": "staged"})
    assert report == build_impact(
        wiki_dir="wiki",
        changes={
            "mode": "paths",
            "paths": ["app.py", "pyproject.toml", "wiki/modules/app.md"],
        },
    )
    assert len(report["findings"]) == 2
    assert all(f["severity"] == "info" for f in report["findings"])
    assert all(
        "were not changed" not in f["reason"] and "without" not in f["reason"]
        for f in report["findings"]
    )


def test_deleted_sources_preserve_unknown_or_retained_coverage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    wiki = tmp_path / "wiki"
    (wiki / "modules").mkdir(parents=True)
    (wiki / "modules/old.md").write_text("# Old\n")
    (wiki / SURFACE_INDEX_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": WIKI_SURFACE_INDEX_SCHEMA_VERSION,
                "pages": [
                    {"source_path": "old.py", "canonical_path": "modules/old.md"}
                ],
            }
        )
    )
    report = build_impact(
        wiki_dir="wiki",
        changes={"mode": "paths", "paths": ["old.py", "gone.hs", "gone.lhs"]},
    )
    assert len(report["findings"]) == 3
    by_source = {f["source_path"]: f for f in report["findings"]}
    assert by_source["old.py"]["wiki_pages"] == ["modules/old.md"]
    assert "retire" in by_source["old.py"]["suggested_follow_up"]
    for path in ("gone.hs", "gone.lhs"):
        assert "unknown" in by_source[path]["suggested_follow_up"]
        assert by_source[path]["wiki_pages"] == []
    assert all(f["severity"] == "info" for f in report["findings"])
