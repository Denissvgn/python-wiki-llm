"""Eligibility diagnostics keep missing evidence and unavailable models visible."""

import json
import sys
from dataclasses import replace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.cli import main
from llm_wiki_cli.services import context_packet, knowledge_coverage
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_coverage import build_knowledge_coverage
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import ComputedFreshness, EvidenceState
from llm_wiki_cli.services.mcp_server import McpWikiService
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state


def _cli(monkeypatch, arguments):
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments])
    try:
        main()
    except SystemExit as exc:
        return exc.code
    return 0


@pytest.fixture
def loaded(tmp_path):
    _committed_state(tmp_path)
    return load_knowledge_state(tmp_path)


def _reconcile(report):
    counts = report["counts"]
    assert counts["total"] == counts["modeled"] + counts["unmodeled"]
    assert counts["compared"] <= counts["modeled"]
    for key in ("total", "modeled", "unmodeled", "compared"):
        assert counts[key] == sum(row[key] for row in report["by_kind"].values())
    if report["freshness_evaluated"]:
        assert sum(counts["modeled_freshness"].values()) == counts["modeled"]
        assert sum(report["reasons"].values()) == counts["total"]


def test_live_and_snapshot_coverage_use_eligibility_denominators(loaded):
    live = build_knowledge_coverage(
        build_knowledge_read_view(
            loaded,
            live_evaluation=_live_evaluation(loaded.knowledge),
        )
    )
    assert live["counts"] == {
        "total": 6,
        "modeled": 3,
        "unmodeled": 3,
        "compared": 3,
        "modeled_freshness": {
            state.value: (3 if state is ComputedFreshness.CURRENT else 0)
            for state in ComputedFreshness
        },
    }
    assert live["reasons"]["freshness-not-modeled"] == 3
    snapshot = build_knowledge_coverage(
        build_knowledge_read_view(loaded, snapshot_only=True)
    )
    assert snapshot["counts"] == {
        "total": 6,
        "modeled": 3,
        "unmodeled": 3,
        "compared": 0,
        "modeled_freshness": None,
    }
    assert snapshot["reasons"] is None
    assert snapshot["read_scope"] == "snapshot-only"
    _reconcile(live)
    _reconcile(snapshot)


def test_missing_basis_stays_modeled_and_requires_followup(loaded):
    knowledge = loaded.knowledge
    live = _live_evaluation(knowledge)
    target = knowledge.concepts[0]
    missing = replace(
        target,
        facets=replace(
            target.facets,
            structure=replace(
                target.facets.structure,
                basis=None,
                evidence=EvidenceState.MISSING,
            ),
        ),
    )
    changed = replace(knowledge, concepts=(missing, *knowledge.concepts[1:]))
    report = build_knowledge_coverage(
        build_knowledge_read_view(
            replace(loaded, knowledge=changed),
            live_evaluation=live,
        )
    )
    assert report["counts"]["modeled"] == 3
    assert report["counts"]["compared"] == 2
    assert report["counts"]["modeled_freshness"]["unknown"] == 1
    assert report["reasons"]["recorded-basis-unavailable"] == 1
    _reconcile(report)


def test_unknown_labels_are_bounded_and_never_echo_input_identities(loaded, tmp_path):
    view = build_knowledge_read_view(
        loaded, live_evaluation=_live_evaluation(loaded.knowledge)
    )
    assert view.knowledge is not None and view.freshness is not None
    target = view.knowledge.concepts[0]
    marker = "PRIVATE_SENTINEL_" + "x" * 100000
    knowledge = replace(
        view.knowledge,
        concepts=(
            replace(target, concept_kind=marker),
            *view.knowledge.concepts[1:],
        ),
    )
    outcomes = dict(view.freshness.by_locator)
    outcomes[target.locator] = replace(outcomes[target.locator], reason_code=marker)
    report = build_knowledge_coverage(
        replace(
            view,
            knowledge=knowledge,
            freshness=replace(view.freshness, by_locator=outcomes),
        )
    )
    assert report["by_kind"]["other"]["modeled"] == 1
    assert report["reasons"]["other"] == 1
    serialized = json.dumps(report)
    assert "PRIVATE_SENTINEL_" not in serialized
    assert "llm-wiki://" not in serialized
    assert str(tmp_path) not in serialized
    assert len(serialized.encode()) <= knowledge_coverage.MAX_COVERAGE_BYTES
    _reconcile(report)


def test_empty_ready_model_is_not_unavailable(loaded):
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    assert view.knowledge is not None
    report = build_knowledge_coverage(
        replace(view, knowledge=replace(view.knowledge, concepts=()))
    )
    assert report["availability"] == "ready"
    assert report["counts"]["total"] == 0
    assert report["by_kind"] == {}


def test_coverage_adapters_read_a_foreign_project_without_initialization(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/catalog.py").write_text(
        "class Item:\n    price: int\n", encoding="utf-8"
    )
    api.bootstrap_wiki("src", "wiki")

    def snapshot():
        return {
            str(p.relative_to(tmp_path)): p.read_bytes()
            for p in tmp_path.rglob("*")
            if p.is_file()
        }

    before = snapshot()
    service = McpWikiService(src_dir="src", wiki_dir="wiki")
    public = api.get_knowledge_coverage(src_dir="src", wiki_dir="wiki", live=True)
    assert public == service.get_knowledge_coverage(live=True)
    assert (
        public["counts"] is not None
        and public["counts"]["modeled_freshness"] is not None
    )
    assert public["counts"]["modeled"] == public["counts"]["compared"] == 2
    assert public["counts"]["modeled_freshness"]["current"] == 2
    assert (
        _cli(
            monkeypatch,
            [
                "knowledge",
                "coverage",
                "--src-dir",
                "src",
                "--wiki-dir",
                "wiki",
                "--live",
                "--format",
                "json",
            ],
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == public
    query_service = api.build_documentation_query_service("src", wiki_dir="wiki")
    assert api.get_knowledge_coverage(service=query_service) == public
    monkeypatch.setattr(
        context_packet,
        "capture_context_read",
        lambda *a, **k: pytest.fail("snapshot scanned source"),
    )
    assert _cli(monkeypatch, ["knowledge", "coverage", "--wiki-dir", "wiki"]) == 0
    rendered = capsys.readouterr().out
    assert "not evaluated" in rendered
    assert "Unmodeled is not stale" in rendered
    assert snapshot() == before
    assert not (tmp_path / "AGENTS.md").exists()


def test_unavailable_snapshot_has_safe_cli_error_and_live_absence_is_not_zero(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "wiki").mkdir()
    (tmp_path / "wiki/index.md").write_text("# A legacy wiki\n", encoding="utf-8")
    assert (
        _cli(
            monkeypatch,
            ["knowledge", "coverage", "--wiki-dir", "wiki", "--format", "json"],
        )
        == 1
    )
    output = capsys.readouterr()
    assert output.out == ""
    error = json.loads(output.err)["error"]
    assert error["code"] == "workspace-state-error"
    assert error["details"] == {"field": "wiki_dir"}
    assert str(tmp_path) not in output.err
    report = api.get_knowledge_coverage(src_dir="src", wiki_dir="wiki", live=True)
    assert report["availability"] == "absent"
    assert report["counts"] is report["by_kind"] is report["reasons"] is None


@pytest.mark.parametrize("live", [False, True])
def test_coverage_rejects_wiki_mutation_after_read(tmp_path, monkeypatch, live):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("class Item:\n    pass\n", encoding="utf-8")
    api.bootstrap_wiki("src", "wiki")
    build = knowledge_coverage.build_knowledge_coverage

    def mutate(view):
        report = build(view)
        (tmp_path / "wiki/index.md").write_text(
            "# Changed during report\n", encoding="utf-8"
        )
        return report

    monkeypatch.setattr(knowledge_coverage, "build_knowledge_coverage", mutate)
    with pytest.raises(api.WorkspaceStateError) as failure:
        api.get_knowledge_coverage(src_dir="src", wiki_dir="wiki", live=live)
    assert failure.value.code == "context-read-mutated"
    assert failure.value.details == {"field": "wiki_dir"}
