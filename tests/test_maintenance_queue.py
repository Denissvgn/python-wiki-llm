"""Advisory ranking keeps unknowns, ownership, and captured inputs intact."""

import json
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services.knowledge_freshness import ConceptFreshnessResult
from llm_wiki_cli.services.knowledge_model import ComputedFreshness
from llm_wiki_cli.services.lint_service import LintIssue
from llm_wiki_cli.services.maintenance_queue import (
    compose_queue,
    build_maintenance_queue,
)
from tests.test_mcp import _write_wiki


def test_observed_change_ownership_lint_reachability_and_fan_in():
    pages = [
        {
            "canonical_path": p,
            "kind": "modules",
            "role": "mixed",
            "source_path": s,
            "outgoing_internal_links": links,
        }
        for p, s, links in [
            ("index.md", None, ["modules/changed.md"]),
            ("modules/changed.md", "changed.py", []),
            ("modules/unknown.md", None, []),
            ("modules/nonsemantic.md", "same.py", []),
        ]
    ]
    fresh = {
        p: ConceptFreshnessResult(p, state, state.value, None, None, True, state.value)
        for p, state in [
            ("modules/changed.md", ComputedFreshness.SOURCE_CHANGED),
            ("modules/nonsemantic.md", ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE),
        ]
    }
    work = [
        SimpleNamespace(
            canonical_path="modules/changed.md",
            title="Explain changed",
            signals=("placeholder",),
            status="open",
        )
    ]
    issues = {
        "modules/changed.md": [LintIssue("broken-link", "Missing target", "warning")]
    }
    args = (pages, work, fresh, issues, {"changed.py": {"fan_in": 6}})
    queue = compose_queue(*args)
    assert queue == compose_queue(list(reversed(pages)), *args[1:])
    changed = queue["items"][0]
    assert changed["path"] == "modules/changed.md"
    assert changed["ownership"]["semantic_section"] == "Description"
    assert changed["source_fan_in"] == 6 and changed["reachable_from_index"]
    assert changed["lint_severity"] == "warning"
    unknown = next(i for i in queue["items"] if i["path"].endswith("unknown.md"))
    assert unknown["freshness"]["state"] == "unknown"
    assert unknown["classification"] == "informational"
    nonsemantic = next(
        i for i in queue["items"] if i["path"].endswith("nonsemantic.md")
    )
    assert nonsemantic["classification"] == "informational"
    assert queue["advisory"] and "exit_code" not in queue
    assert compose_queue(*args, limit=1)["items"] == queue["items"][:1]


def test_live_queue_cli_deterministic_read_only_and_never_gates(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    (tmp_path / "app.py").write_text("class User:\n    pass\n")
    before = {str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    cache = str(tmp_path / "helpers")
    result = build_maintenance_queue(".", str(wiki), helper_cache_dir=cache)
    assert result == build_maintenance_queue(".", str(wiki), helper_cache_dir=cache)
    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "queue",
            "--wiki-dir",
            str(wiki),
            "--format",
            "json",
            "--helper-cache-dir",
            cache,
        ],
    )
    cli.main()
    assert json.loads(capsys.readouterr().out) == result
    assert all(item["freshness"]["state"] == "unknown" for item in result["items"])
    assert before == {
        str(p): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }


def test_queue_rejects_symlinked_wiki_and_invalid_limit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    (wiki / "guides").mkdir(exist_ok=True)
    (wiki / "guides" / "linked.md").symlink_to(wiki / "index.md")
    with pytest.raises(ValueError, match="limit"):
        build_maintenance_queue(".", str(wiki), limit=0)
    with pytest.raises(Exception, match="symlink|path policy"):
        build_maintenance_queue(".", str(wiki))


def test_stale_selection_basis_keeps_queue_freshness_unknown(tmp_path, monkeypatch):
    from tests.test_context_packet_knowledge import (
        _materialize_ready_project,
        _write_mismatched_source_selection,
    )

    tree, _ = _materialize_ready_project(tmp_path, monkeypatch)
    _write_mismatched_source_selection(tree)
    before = {str(p): p.read_bytes() for p in tree["root"].rglob("*") if p.is_file()}
    result = build_maintenance_queue(".", str(tree["wiki_root"]))
    assert result["basis"]["source_selection_compatible"] is False
    assert result["items"]
    assert all(item["freshness"]["state"] == "unknown" for item in result["items"])
    assert all(
        item["freshness"]["reason"] == "source-selection-basis-incompatible"
        for item in result["items"]
    )
    assert before == {
        str(p): p.read_bytes() for p in tree["root"].rglob("*") if p.is_file()
    }
