"""Advisory ranking keeps unknowns, ownership, and captured inputs intact."""

import json
from types import SimpleNamespace
from typing import Any

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


@pytest.mark.parametrize("variant,availability", [("legacy", "unadopted"), ("adopted-flat", "ready"), ("native-absent", "unavailable")])
def test_actual_queue_custody_reaches_api_cli_and_local_mcp_without_writes(tmp_path, monkeypatch, capsys, variant, availability):
    from llm_wiki_cli import api
    from llm_wiki_cli.services import mcp_server
    from tests.test_mcp import RecordingMcpServer
    from tests.developer_value.combined_workflows import prepare_combined, source_after, client_after, BEFORE_PROSE
    from tests.developer_value.workflow_fixtures import sync_workflow, write_description

    monkeypatch.chdir(tmp_path)
    project = prepare_combined(tmp_path, variant)
    capsys.readouterr()
    service = mcp_server.McpWikiService(**project.options)
    server = RecordingMcpServer()
    mcp_server._register_mcp_tools(server, service)

    def readonly(operation):
        before = {path: (raw, (project.root / path).stat().st_mtime_ns) for path, raw in project.tree().items()}
        value = operation()
        assert before == {path: (raw, (project.root / path).stat().st_mtime_ns) for path, raw in project.tree().items()}
        assert not (tmp_path / "source-execution-tripwire").exists()
        return value

    def check(stage):
        response: dict[str, Any] = dict(readonly(lambda: api.build_maintenance_queue(**project.options)))
        custody = response["qualification"]["ordinary_review_custody"]
        assert custody["availability"] == availability
        assert custody["durable_owner_available"] is (variant == "adopted-flat")
        assert custody["source_prose_correctness"] == "not-established"
        assert custody["review_route"]["interface"] == "inspect_concept"
        assert response["advisory"] and "exit_code" not in response
        assert readonly(lambda: server.tool_functions["get_maintenance_queue"]()) == response
        monkeypatch.setattr("sys.argv", ["llm-wiki", "queue", "--src-dir", str(project.source), "--wiki-dir", str(project.wiki), "--format", "json"])
        readonly(cli.main)
        cli_response = json.loads(capsys.readouterr().out)
        assert cli_response["qualification"]["ordinary_review_custody"] == custody
        assert cli_response["advisory"] and "exit_code" not in cli_response
        assert cli_response["returned"] == len(cli_response["items"])
        monkeypatch.setattr("sys.argv", ["llm-wiki", "queue", "--src-dir", str(project.source), "--wiki-dir", str(project.wiki)])
        readonly(cli.main)
        text = capsys.readouterr().out
        assert "Ordinary durable review custody: " + availability in text
        assert "Source/prose correctness is not established" in text
        assert custody["review_route"]["instruction"] in text and custody["limitation"] in text
        if variant == "legacy" and stage in {"clean", "synced"}:
            assert response["total"] == 0
            assert BEFORE_PROSE in (project.wiki / "entities/Harbor.md").read_text()
        return response

    check("clean")
    if variant == "legacy":
        (project.source / "policy.py").write_text(source_after())
        (project.source / "client.py").write_text(client_after())
        assert check("edited")["total"] > 0
        sync_workflow(project)
        capsys.readouterr()
        check("synced")
    elif variant == "adopted-flat":
        write_description(project, BEFORE_PROSE + " Requires renewed explicit review.", "entities/Harbor.md")
        availability = "partial"
        check("prose-edited")


def test_captured_queue_qualification_discloses_partial_basis_and_truncation():
    from llm_wiki_cli.services.maintenance_status import MaintenanceStatusReport

    payload = {"availability": "ready", "adoption_id": "owned", "live_evaluation_performed": True,
               "requires_sync": False, "coverage": {"issues": [], "untracked_semantic_total": 0}}
    report = MaintenanceStatusReport(payload, {}, {})
    full = compose_queue([], [], {}, {}, {}, maintenance_report=report)
    assert full["qualification"]["ordinary_review_custody"]["availability"] == "ready"
    for field, value in [("requires_sync", True), ("live_evaluation_performed", False),
                         ("coverage", {"issues": [{"reason": "capture-unavailable"}], "untracked_semantic_total": 1})]:
        partial = MaintenanceStatusReport({**payload, field: value}, {}, {})
        queue = compose_queue([], [], {}, {}, {}, maintenance_report=partial)
        assert queue["qualification"]["ordinary_review_custody"]["availability"] == "partial"
        assert queue["qualification"]["ordinary_review_custody"]["durable_owner_available"]
        assert queue["qualification"]["ordinary_review_custody"]["source_prose_correctness"] == "not-established"
    pages = [{"canonical_path": f"modules/{i}.md", "kind": "modules", "role": "mixed"} for i in range(3)]
    issues = {page["canonical_path"]: [LintIssue("broken-link", "Missing target", "error")] for page in pages}
    bounded = compose_queue(pages, [], {}, issues, {}, maintenance_report=report, limit=1)
    assert bounded["returned"] == 1 and bounded["total"] == 3 and bounded["omitted"] == 2
    assert bounded["qualification"]["ordinary_review_custody"] == full["qualification"]["ordinary_review_custody"]
    assert "1 of 3 (2 omitted)" in maintenance_queue.render_queue(bounded)


def test_queue_reuses_exactly_one_capture_for_custody_qualification(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    wiki = _write_wiki(tmp_path)
    original = maintenance_queue.capture_context_read
    captures = []

    def capture(*args, **kwargs):
        value = original(*args, **kwargs)
        captures.append(value)
        return value

    monkeypatch.setattr(maintenance_queue, "capture_context_read", capture)
    result = build_maintenance_queue(".", str(wiki))
    assert len(captures) == 1
    assert result["qualification"]["ordinary_review_custody"]["availability"] == "unavailable"


def test_validated_adopted_manifest_without_captured_status_is_partial(tmp_path, monkeypatch, capsys):
    from dataclasses import replace
    from tests.developer_value.combined_workflows import prepare_combined

    monkeypatch.chdir(tmp_path)
    project = prepare_combined(tmp_path, "adopted-flat")
    capsys.readouterr()
    original = maintenance_queue.capture_context_read
    captures = []

    def no_report(*args, **kwargs):
        captured = original(*args, **kwargs)
        assert captured.knowledge_view.manifest_basis is not None
        assert captured.knowledge_view.manifest_basis.maintenance_state is not None
        captures.append(captured)
        return replace(captured, knowledge_view=replace(captured.knowledge_view, maintenance_report=None))

    monkeypatch.setattr(maintenance_queue, "capture_context_read", no_report)
    before = {path: (raw, (project.root / path).stat().st_mtime_ns) for path, raw in project.tree().items()}
    result = build_maintenance_queue(**project.options)
    custody = result["qualification"]["ordinary_review_custody"]
    assert custody["availability"] == "partial" and custody["durable_owner_available"]
    assert custody["evidence"] == "validated-native-manifest" and not custody["live_evaluation_performed"]
    assert custody["source_prose_correctness"] == "not-established"
    assert len(captures) == 1
    assert before == {path: (raw, (project.root / path).stat().st_mtime_ns) for path, raw in project.tree().items()}
