"""Advisory ranking keeps unknowns, ownership, and captured inputs intact."""

import json
from types import SimpleNamespace

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.services import maintenance_queue
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
    before = {
        str(p): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    cache = str(tmp_path / "helpers")
    result = build_maintenance_queue(".", str(wiki), helper_cache_dir=cache)
    assert result["limit"] == 30
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
        str(p): (p.read_bytes(), p.stat().st_mtime_ns)
        for p in tmp_path.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize("limit", ["-5", "0", "1001", "1000000", "invalid"])
def test_queue_invalid_limits_fail_before_dispatch(monkeypatch, capsys, limit):
    monkeypatch.setattr(
        cli,
        "_dispatch_command",
        lambda args: pytest.fail("invalid input was dispatched"),
    )
    monkeypatch.setattr("sys.argv", ["llm-wiki", "queue", "--limit", limit])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "--limit" in output.err and "Traceback" not in output.err
    assert len(output.err) < 1500


@pytest.mark.parametrize("limit", [True, False, 1.5, "1", None, 0, -5, 1001, 1000000])
def test_queue_services_validate_limits_before_capture(monkeypatch, limit):
    monkeypatch.setattr(
        maintenance_queue,
        "capture_context_read",
        lambda *args, **kwargs: pytest.fail("invalid limit reached capture"),
    )
    with pytest.raises(ValueError, match="between 1 and 1000"):
        build_maintenance_queue(limit=limit)
    with pytest.raises(ValueError, match="between 1 and 1000"):
        compose_queue([], [], {}, {}, {}, limit=limit)


@pytest.mark.parametrize("count,limit", [(0, 1), (3, 3), (3, 1), (3, 1000)])
def test_queue_limit_metadata_and_counts(count, limit):
    pages = [
        {"canonical_path": f"modules/{i}.md", "kind": "modules", "role": "mixed"}
        for i in reversed(range(count))
    ]
    issues = {
        page["canonical_path"]: [
            LintIssue("placeholder", "Document the module behavior", "warning")
        ]
        for page in pages
    }
    result = compose_queue(pages, [], {}, issues, {}, limit=limit)
    assert result["schema_version"] == "llm-wiki-maintenance-queue/v1"
    assert result["limit"] == limit
    assert result["returned"] == len(result["items"]) == min(count, limit)
    assert result["total"] == count == result["returned"] + result["omitted"]
    assert all(item["classification"] == "actionable" for item in result["items"])
    assert [item["path"] for item in result["items"]] == [
        f"modules/{i}.md" for i in range(min(count, limit))
    ]
    assert compose_queue([], [], {}, {}, {})["limit"] == 30


def test_unknown_freshness_is_preserved_as_qualification_without_inventing_work():
    page = {"canonical_path": "modules/unknown.md", "kind": "modules", "role": "mixed"}
    result = compose_queue([page], [], {}, {}, {})
    assert result["total"] == result["returned"] == 0
    assert result["items"] == []
    assert result["qualification"]["freshness_states"] == {"unknown": 1}
    assert result["advisory"]


def test_text_queue_preserves_unknown_and_generic_authoring_qualification():
    page = {"canonical_path": "modules/unknown.md", "kind": "modules", "role": "mixed"}
    work = SimpleNamespace(
        canonical_path=page["canonical_path"],
        signals=("placeholder_semantic_prose",),
        status="open",
    )
    result = compose_queue([page], [work], {}, {}, {})
    rendered = maintenance_queue.render_queue(result)
    assert result["items"] == []
    assert "Advisory page queue: 0 of 0 (0 omitted)" in rendered
    assert "Captured page freshness: unknown: 1" in rendered
    assert "Generic authoring hint pages: 1" in rendered
    assert result["qualification"]["scope"] in rendered
    assert all(value in rendered for value in result["qualification"]["limitations"])


@pytest.mark.parametrize(
    "signal",
    [
        "generic_landing_context",
        "missing_or_placeholder_architecture_notes",
        "missing_or_placeholder_flow_behavior",
        "placeholder_semantic_prose",
        "copied_docstring_only_prose",
    ],
)
def test_generic_authoring_hint_does_not_request_repeated_maintenance(signal):
    page = {"canonical_path": "modules/policy.md", "kind": "modules", "role": "mixed"}
    work = SimpleNamespace(
        canonical_path=page["canonical_path"],
        title="Explain role",
        signals=(signal,),
        status="open",
    )
    result = compose_queue([page], [work], {}, {}, {})
    assert not result["items"] and result["qualification"]["authoring_hint_pages"] == 1
    assert result["qualification"]["freshness_states"] == {"unknown": 1}


def test_verified_defect_retains_unknown_qualification_and_all_returned_rows():
    pages = [
        {"canonical_path": f"modules/{n}.md", "kind": "modules", "role": "mixed"}
        for n in range(3)
    ]
    issues = {
        p["canonical_path"]: [
            LintIssue("broken-link", "The retained local link is missing", "error")
        ]
        for p in pages
    }
    result = compose_queue(pages, [], {}, issues, {}, limit=100)
    assert (
        result["total"] == result["returned"] == len(result["items"]) == 3
        and result["omitted"] == 0
    )
    assert all(
        i["freshness"]["state"] == "unknown" and i["classification"] == "actionable"
        for i in result["items"]
    )
    assert all(
        {r["code"] for r in i["reasons"]} == {"lint:broken-link", "freshness:unknown"}
        for i in result["items"]
    )


def test_concrete_worklist_evidence_is_not_lost_with_generic_hints():
    page = {"canonical_path": "modules/policy.md", "kind": "modules", "role": "mixed"}
    work = SimpleNamespace(
        canonical_path=page["canonical_path"],
        title="Repair owner",
        signals=("copied_docstring_only_prose", "verified_ownership_conflict"),
        status="open",
    )
    result = compose_queue([page], [work], {}, {}, {})
    assert (
        result["returned"] == 1 and result["items"][0]["classification"] == "actionable"
    )
    assert result["items"][0]["placeholder_signals"] == list(work.signals)


@pytest.mark.parametrize(
    "priority,evidence,expected", [("P0", True, 1), ("P2", True, 0), ("P0", False, 0)]
)
def test_boundary_flow_requires_real_source_entry_evidence_not_priority_alone(
    priority, evidence, expected
):
    page = {
        "canonical_path": "flows/http-api.md",
        "kind": "flows",
        "role": "mixed",
        "source_path": "server.py",
    }
    work = SimpleNamespace(
        canonical_path=page["canonical_path"],
        category="flow_behavior",
        priority=priority,
        source_path="server.py",
        title="Explain the HTTP request boundary",
        signals=("missing_or_placeholder_flow_behavior",),
        suggested_context=("source:server.py", "evidence:entrypoint:http-api")
        if evidence
        else (),
        status="open",
    )
    result = compose_queue([page], [work], {}, {}, {}, limit=100)
    assert result["total"] == result["returned"] == expected
    if expected:
        assert result["items"][0]["classification"] == "actionable"
        assert result["items"][0]["freshness"]["state"] == "unknown"


def test_unresolved_source_specific_review_hint_remains_a_full_queue_item(
    tmp_path, monkeypatch, capsys
):
    from llm_wiki_cli import api
    from llm_wiki_cli.services import analysis_capture
    from tests.developer_value.fixtures import POLICY_SOURCE

    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/policy.py").write_text(POLICY_SOURCE)
    api.bootstrap_wiki("src", "wiki")
    api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
    capsys.readouterr()
    before = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }
    original = analysis_capture.implementation_hash

    def incompatible(root, paths):
        from hashlib import sha256

        return (
            "sha256:"
            + sha256(("changed:" + original(root, paths)).encode()).hexdigest()
        )

    monkeypatch.setattr(analysis_capture, "implementation_hash", incompatible)
    result = build_maintenance_queue("src", "wiki", limit=100)
    item = next(row for row in result["items"] if row["path"] == "entities/Batch.md")
    assert item["record_ids"] and item["maintenance"]["pending"] >= 1
    assert any(
        r["code"]
        in {
            "maintenance:producer-incompatible",
            "maintenance:current-basis-unavailable",
        }
        for r in item["reasons"]
    )
    assert before == {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }


def test_queue_identity_binds_limit_even_when_items_match(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    first = build_maintenance_queue(".", str(wiki), limit=30)
    second = build_maintenance_queue(".", str(wiki), limit=1000)
    assert first["items"] == second["items"]
    assert first["queue_id"] != second["queue_id"]
    assert {k: v for k, v in first.items() if k not in {"queue_id", "limit"}} == {
        k: v for k, v in second.items() if k not in {"queue_id", "limit"}
    }
    assert second == build_maintenance_queue(".", str(wiki), limit=1000)
    monkeypatch.setattr(
        "sys.argv", ["llm-wiki", "queue", "--limit", "1000", "--format", "json"]
    )
    cli.main()
    assert json.loads(capsys.readouterr().out) == second


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
