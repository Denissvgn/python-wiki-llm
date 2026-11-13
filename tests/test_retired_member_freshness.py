"""Qualified retained history shares one freshness and coverage interpretation."""

from copy import deepcopy
from dataclasses import replace
import json
import sys

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands.bootstrap_cmd import execute_bootstrap
from llm_wiki_cli.services import ci_report, doctor_service
from llm_wiki_cli.services.bootstrap_service import BootstrapRequest
from llm_wiki_cli.services.documentation_native import evaluate_documentation_native_freshness
from llm_wiki_cli.services.health_details import capture_health_details
from llm_wiki_cli.services.knowledge_artifacts import (
    require_validated_artifacts,
    validate_knowledge_artifacts,
)
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_coverage import build_knowledge_coverage
from llm_wiki_cli.services.knowledge_evidence import UNKNOWN_ENTITY_NOT_FOUND
from llm_wiki_cli.services.knowledge_freshness import (
    KnowledgeFreshnessError,
    evaluate_knowledge_freshness,
    evaluate_validated_knowledge_freshness,
)
from llm_wiki_cli.services.knowledge_generation import build_knowledge_generation_plan
from llm_wiki_cli.services.knowledge_loader import KnowledgeLoadResult, load_knowledge_state
from llm_wiki_cli.services.knowledge_model import ComputedFreshness, KnowledgeLoadState
from llm_wiki_cli.services.source_retirement import SOURCE_MEMBER_REMOVED_HEADER
from tests.knowledge_fixtures import FIXTURE_SOURCE_PATH, fixture_hash
from tests.test_entity_retirement import _snapshot
from tests.test_entity_retirement_evidence import _retirement_inputs
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_sync_page_transitions import _bootstrap_project, _sync


RETIRED = "llm-wiki://entities/User"


@pytest.fixture(params=[False, True], ids=["historical", "unknown"])
def retired_state(tmp_path, request):
    inputs = _retirement_inputs(tmp_path, unknown=request.param)
    plan = build_knowledge_generation_plan(inputs)
    artifacts = validate_knowledge_artifacts(
        surface_index_bytes=plan.surface_index.content,
        knowledge_index_bytes=plan.knowledge_index.content,
        manifest=plan.committed_manifest,
    )
    live = _live_evaluation(
        artifacts.knowledge, source_hash_by_path=dict(inputs.source_content_hashes)
    )
    if RETIRED in live.concept_bases:
        live = replace(live, concept_bases={
            **live.concept_bases,
            RETIRED: replace(live.concept_bases[RETIRED],
                concept_observation_hash=None, unknown_reason=UNKNOWN_ENTITY_NOT_FOUND),
        })
    return plan, artifacts, live


@pytest.mark.parametrize("change", ["source", "missing-source", "producer", "options"])
def test_qualified_history_never_claims_a_live_comparison(retired_state, change):
    plan, artifacts, live = retired_state
    if change == "missing-source":
        live = replace(live, source_content_hashes={}, concept_bases={},
                       missing_source_paths=frozenset({FIXTURE_SOURCE_PATH}))
    elif change == "producer":
        live = replace(live, producer=replace(live.producer,
            tool=replace(live.producer.tool, version="99.0.0")))
    elif change == "options":
        live = replace(live, generation_options_hash=fixture_hash("other-options"))
    before = deepcopy(artifacts.knowledge_payload)
    reports = (
        evaluate_knowledge_freshness(artifacts, live),
        evaluate_validated_knowledge_freshness(artifacts, live),
        evaluate_knowledge_freshness(artifacts.knowledge, live,
                                    retirement_manifest=plan.committed_manifest),
    )
    for report in reports:
        result = report.by_locator[RETIRED]
        assert report.retired_locators == frozenset({RETIRED})
        assert result.state is ComputedFreshness.UNKNOWN
        assert result.reason_code == "freshness-not-modeled"
        assert not result.live_comparison_performed
        basis = next(c for c in artifacts.knowledge.concepts if c.locator == RETIRED).facets.structure.basis
        assert (result.recorded_basis is None) == (basis is None)
        if basis is not None:
            assert result.recorded_basis is not None
            assert result.recorded_basis.source_content_hash == basis.source_content_hash
        if change == "missing-source":
            assert report.by_locator["llm-wiki://modules/accounts"].state is ComputedFreshness.SOURCE_MISSING
    assert artifacts.knowledge_payload == before


def test_index_only_retirement_extension_does_not_grant_an_exemption(retired_state):
    _, artifacts, live = retired_state
    result = evaluate_knowledge_freshness(artifacts.knowledge, live).by_locator[RETIRED]
    expected = "concept-observation-changed" if result.recorded_basis else "recorded-basis-unavailable"
    assert result.reason_code == expected


@pytest.mark.parametrize("mutation", ["marker", "tombstone", "mapping", "revived", "basis"])
def test_manifest_context_cannot_exempt_an_invalid_retirement(retired_state, mutation):
    plan, artifacts, live = retired_state
    manifest = plan.committed_manifest
    knowledge = artifacts.knowledge
    if mutation == "marker":
        manifest = replace(manifest, generation_inputs={})
    elif mutation == "tombstone":
        manifest = replace(manifest, tombstones={})
    elif mutation == "mapping":
        manifest = replace(manifest, page_source_mappings={})
    elif mutation == "revived":
        sources = deepcopy(dict(manifest.sources))
        sources[FIXTURE_SOURCE_PATH]["entities"].append("User")
        manifest = replace(manifest, sources=sources)
    else:
        concept = next(c for c in knowledge.concepts if c.locator == RETIRED)
        other = next(c for c in knowledge.concepts if c.locator == "llm-wiki://modules/accounts")
        knowledge = replace(knowledge, concepts=tuple(
            replace(c, facets=replace(c.facets, structure=other.facets.structure))
            if c is concept else c for c in knowledge.concepts
        ))
    with pytest.raises(KnowledgeFreshnessError, match="retirement_manifest"):
        evaluate_knowledge_freshness(knowledge, live, retirement_manifest=manifest)


def test_retirement_coverage_reconciles_live_snapshot_and_health_details(retired_state):
    plan, artifacts, live = retired_state
    loaded = KnowledgeLoadResult(
        status=KnowledgeLoadState.VALID, surface=artifacts.surface_payload,
        knowledge=artifacts.knowledge, manifest_basis=plan.committed_manifest,
        validated_artifacts=artifacts,
    )
    for snapshot in (False, True):
        view = build_knowledge_read_view(loaded, live_evaluation=live, snapshot_only=snapshot)
        counts = build_knowledge_coverage(view)["counts"]
        assert view.retired_locators == frozenset({RETIRED})
        assert counts["modeled"] == 2
        assert counts["unmodeled"] == counts["total"] - 2
        assert counts["compared"] == (0 if snapshot else 2)
        details = capture_health_details(view, wiki_dir="wiki", src_dir="source").to_payload()
        assert details["coverage"]["modeled"] == counts["modeled"]
        assert details["coverage"]["unmodeled"] == counts["unmodeled"]
        if not snapshot:
            assert view.freshness is not None
            assert counts["modeled_freshness"]["unknown"] == 0
            assert view.freshness.counts[ComputedFreshness.UNKNOWN] == counts["unmodeled"]
            assert details["coverage"]["outcomes"]["current"] == 2
        else:
            assert details["coverage"]["outcomes"] is None
    unevaluated = evaluate_knowledge_freshness(artifacts)
    assert unevaluated.by_locator[RETIRED].reason_code == "live-evaluation-not-performed"


def test_retirement_metadata_cannot_be_replaced_on_a_validation_receipt(retired_state):
    _, artifacts, _ = retired_state
    object.__setattr__(artifacts, "retired_locators", frozenset())
    with pytest.raises(TypeError, match="replaced"):
        require_validated_artifacts(artifacts)


def _json_command(monkeypatch, capsys, arguments, expected_exit):
    monkeypatch.setattr(sys, "argv", ["llm-wiki", *arguments, "--format", "json"])
    capsys.readouterr()
    exit_code = 0
    try:
        cli.main()
    except SystemExit as exc:
        exit_code = exc.code
    output = capsys.readouterr()
    if exit_code != expected_exit and output.out.startswith("{"):
        failed = json.loads(output.out)
        pytest.fail(json.dumps({key: failed.get(key) for key in (
            "status", "degraded_reasons", "unhealthy_reasons", "drift", "health_details",
        )}, indent=2))
    assert exit_code == expected_exit, output.err
    return json.loads(output.out)


def _sync_command(monkeypatch, capsys, common):
    monkeypatch.setattr(sys, "argv", ["llm-wiki", "sync", *common])
    capsys.readouterr()
    cli.main()
    capsys.readouterr()


@pytest.mark.parametrize("suffix", [".py", ".tsx"])
@pytest.mark.parametrize("empty", [False, True], ids=["surviving-member", "empty-module"])
def test_retirement_converges_across_doctor_ci_and_revival(
    tmp_path, monkeypatch, capsys, suffix, empty, require_prepared_diagnostics_helper,
):
    if suffix == ".tsx":
        cache = require_prepared_diagnostics_helper("typescript")
        monkeypatch.setenv("LLM_WIKI_CACHE_DIR", cache)
        removed, kept = "export interface Removed { value: string }\n", "export interface Kept { run(): number }\n"
    else:
        removed, kept = "class Removed:\n    value: str\n", "class Kept:\n    def run(self) -> int:\n        return 1\n"
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {"shapes" + suffix: kept + removed})
    common = ["--src-dir", ".", "--wiki-dir", str(wiki), "--jobs", "1"]
    baseline = _json_command(monkeypatch, capsys, ["doctor", *common], 0)
    assert baseline["status"] == "healthy"
    page = wiki / "entities/Removed.md"
    page.write_text(page.read_text() + "\n## Notes\n\nRetain authored history.\n", encoding="utf-8")
    _sync_command(monkeypatch, capsys, common)
    source = project / "pkg" / ("shapes" + suffix)
    source.write_text(("# empty\n" if suffix == ".py" else "// empty\n") if empty else kept)
    unsynced = _json_command(monkeypatch, capsys, ["doctor", *common], 1 if empty else 2)
    assert unsynced["drift"]["state"] == ("indeterminate" if empty else "stale-confirmed")
    _sync_command(monkeypatch, capsys, common)
    stable = _snapshot(wiki)
    _sync_command(monkeypatch, capsys, common)
    assert _snapshot(wiki) == stable
    assert page.read_text().startswith(SOURCE_MEMBER_REMOVED_HEADER)
    assert "Retain authored history." in page.read_text()
    for strict in (False, True):
        args = ["doctor", *common, *(["--strict"] if strict else [])]
        health = _json_command(monkeypatch, capsys, args, 0)
        assert health["status"] == "healthy"
        assert health["drift"]["confirmed_stale"] == 0
        assert health["drift"]["reasons"] == []
        assert health["health_details"]["coverage"]["outcomes"]["unknown"] == 0
        ci_report.validate_doctor_payload(health, expected_strict=strict)
    for drift in (False, True):
        args = ["ci-check", *common, "--no-report", *(["--knowledge-drift-report"] if drift else [])]
        result = _json_command(monkeypatch, capsys, args, 0)
        assert result["ok"] and result["issue_count"] == 0
        assert result["knowledge_health"]["status"] == "healthy"
        ci_report.validate_ci_check_payload(result, cli_exit=0)
    assert _snapshot(wiki) == stable
    source.write_text(kept + removed)
    _sync_command(monkeypatch, capsys, common)
    revived = _json_command(monkeypatch, capsys, ["doctor", *common], 0)
    assert revived["status"] == "healthy"
    assert SOURCE_MEMBER_REMOVED_HEADER not in page.read_text()
    assert "Retain authored history." in page.read_text()
    loaded = load_knowledge_state(wiki)
    assert loaded.validated_artifacts is not None
    assert loaded.validated_artifacts.retired_locators == frozenset()


def test_retirement_reports_preserve_supported_legacy_contracts(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {
        "shapes.py": "class Removed:\n    pass\nclass Kept:\n    pass\n",
    })
    (project / "pkg/shapes.py").write_text("class Kept:\n    pass\n")
    _sync(wiki)
    report = doctor_service.build_doctor_report(
        str(wiki), ".", comparison_policy="exact-v1",
    )
    for schema in ("v1", "v3", "v4"):
        payload = report.to_payload(report_schema=schema)
        assert payload["status"] == "healthy"
        ci_report.validate_doctor_payload(payload, expected_strict=False)


def test_native_documentation_checks_only_current_structural_promises(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "shapes.py").write_text("class Removed:\n    pass\nclass Kept:\n    pass\n")
    wiki = tmp_path / "wiki"
    execute_bootstrap(BootstrapRequest(source_root=source, wiki_root=wiki, source_adapter=True))
    (source / "shapes.py").write_text("class Kept:\n    pass\n")
    monkeypatch.chdir(tmp_path)
    _sync(wiki, src_dir="source")
    loaded = load_knowledge_state(wiki)
    assert loaded.knowledge is not None and loaded.manifest_basis is not None
    freshness = evaluate_documentation_native_freshness(
        knowledge=loaded.knowledge, manifest=loaded.manifest_basis, source_root=source,
    )
    assert freshness.current, freshness.reasons
    assert freshness.report.by_locator["llm-wiki://entities/Removed"].reason_code == "freshness-not-modeled"
