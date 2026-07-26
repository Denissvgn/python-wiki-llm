"""Strict knowledge-lint contract tests (KNOW-203)."""

from __future__ import annotations

import types
from dataclasses import replace

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeLoadIssue,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import (
    ComputedFreshness,
    EvidenceState,
)
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_STATE_UNAVAILABLE,
    TOMBSTONE_UNKNOWN_PROVENANCE,
    ManifestTombstone,
    SyncManifest,
)
from tests.knowledge_fixtures import FIXTURE_SOURCE_PATH, fixture_hash
from tests.test_knowledge_compatibility import (
    COMPATIBILITY_CASES,
    _materialize_case,
)
from tests.test_knowledge_freshness import (
    MODULE_LOCATOR,
    USER_LOCATOR,
    _live_evaluation,
)
from tests.test_knowledge_loader import _committed_state

KNOWLEDGE_CATEGORIES = {
    "knowledge_schema",
    "knowledge_projection",
    "knowledge_snapshot",
    "knowledge_evidence",
    "knowledge_freshness",
}


def _write_fixture_sources(root, fixture) -> None:
    for relative_path, content in fixture.source_files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _knowledge_findings(report):
    return [
        finding
        for finding in (*report.issues, *report.diagnostics)
        if finding.category in KNOWLEDGE_CATEGORIES
    ]


def _report_for_view(view):
    report = lint_cmd.LintReport(wiki_dir="wiki", src_dir="src", strict=True)
    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, view=view),
    )
    return report


def _loaded_knowledge(tmp_path):
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    return loaded, loaded.knowledge


@pytest.mark.parametrize(
    "case",
    COMPATIBILITY_CASES,
    ids=lambda case: case.id,
)
def test_strict_lint_applies_shared_compatibility_policy_only_when_enabled(
    tmp_path,
    monkeypatch,
    case,
):
    source_root = tmp_path / "checkout"
    wiki = source_root / "docs" / "llm_wiki"
    wiki.mkdir(parents=True)
    fixture = _materialize_case(wiki, case)
    _write_fixture_sources(source_root, fixture)
    monkeypatch.setattr(
        lint_cmd,
        "build_runtime_live_evaluation",
        lambda inputs: _live_evaluation(inputs.knowledge),
    )

    non_strict = lint_cmd.build_report(
        wiki,
        str(source_root),
        strict=False,
    )
    strict = lint_cmd.build_report(
        wiki,
        str(source_root),
        strict=True,
    )

    assert _knowledge_findings(non_strict) == []
    assert non_strict.knowledge_summary is None
    findings = _knowledge_findings(strict)
    if not case.expected_issue_codes:
        assert findings == []
        if case.serves_knowledge:
            assert strict.knowledge_summary is not None
            assert strict.knowledge_summary.availability == "ready"
            assert strict.knowledge_summary.freshness_by_state["current"] == 3
        else:
            assert strict.knowledge_summary is None
        return

    assert strict.knowledge_summary is None
    assert all(finding.severity == "error" for finding in findings)
    for reason in case.expected_issue_codes:
        matching = [
            finding
            for finding in findings
            if f"[reason={reason}]" in finding.message
        ]
        assert len(matching) == 1
        expected_category = (
            "knowledge_schema"
            if reason
            in {
                "knowledge-invalid",
                "knowledge-schema-version-unsupported",
            }
            else "knowledge_projection"
        )
        assert matching[0].category == expected_category


def test_strict_ready_state_reports_current_summary_and_optional_json(
    tmp_path,
    monkeypatch,
):
    wiki = tmp_path / "wiki"
    source_root = tmp_path / "repository"
    wiki.mkdir()
    source_root.mkdir()
    fixture, _plan, _result = _committed_state(wiki)
    _write_fixture_sources(source_root, fixture)
    monkeypatch.setattr(
        lint_cmd,
        "build_runtime_live_evaluation",
        lambda inputs: _live_evaluation(inputs.knowledge),
    )

    report = lint_cmd.build_report(wiki, str(source_root), strict=True)

    assert _knowledge_findings(report) == []
    assert report.knowledge_summary is not None
    assert report.knowledge_summary.availability == "ready"
    assert report.knowledge_summary.reason == "all-projection-commitments-match"
    assert report.knowledge_summary.concepts_total == 6
    assert report.knowledge_summary.freshness_by_state["current"] == 3
    assert report.knowledge_summary.freshness_by_state["unknown"] == 3
    payload = lint_cmd.report_to_dict(report)
    assert payload["knowledge_summary"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "concepts_total": 6,
        "concepts_by_kind": {
            "change-log-document": 1,
            "code-entity": 2,
            "navigation-document": 1,
            "source-module": 1,
            "workflow": 1,
        },
        "evidence_by_state": {
            "invalid": 0,
            "missing": 0,
            "not-applicable": 2,
            "present": 3,
            "unknown": 1,
        },
        "freshness_by_state": {
            "basis-incompatible": 0,
            "current": 3,
            "nonsemantic-source-change": 0,
            "source-changed": 0,
            "source-missing": 0,
            "unknown": 3,
        },
    }


def test_markerless_legacy_manifest_skips_knowledge_lint_and_summary(tmp_path):
    wiki = tmp_path / "wiki"
    source_root = tmp_path / "repository"
    source_root.mkdir()
    for dirname in ("entities", "modules", "workflows", "infrastructure"):
        (wiki / dirname).mkdir(parents=True)
    (wiki / "index.md").write_text("# Index\n", encoding="utf-8")
    (wiki / "log.md").write_text("# Log\n", encoding="utf-8")
    SyncManifest.build_from_inventory({}, str(source_root), {}, {}).save(wiki)

    report = lint_cmd.build_report(wiki, str(source_root), strict=True)

    assert _knowledge_findings(report) == []
    assert report.knowledge_summary is None
    assert "knowledge_summary" not in lint_cmd.report_to_dict(report)


def test_bootstrap_lint_reuses_live_basis_and_allows_nonsemantic_change(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "app.py"
    source.write_text("class User:\n    pass\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    bootstrap_cmd.run(
        types.SimpleNamespace(
            src_dir=".",
            wiki_dir="docs/llm_wiki",
            overwrite=False,
            depth="full",
            skip_workflows=True,
        )
    )
    calls = {"snapshot": 0, "inventory": 0, "load": 0, "live": 0}
    real_snapshot = lint_cmd.build_source_snapshot
    real_inventory = lint_cmd.get_inventory_result
    real_load = lint_cmd.load_knowledge_state
    real_live = lint_cmd.build_runtime_live_evaluation

    def counted_snapshot(*args, **kwargs):
        calls["snapshot"] += 1
        return real_snapshot(*args, **kwargs)

    def counted_inventory(*args, **kwargs):
        calls["inventory"] += 1
        return real_inventory(*args, **kwargs)

    def counted_load(*args, **kwargs):
        calls["load"] += 1
        return real_load(*args, **kwargs)

    def counted_live(*args, **kwargs):
        calls["live"] += 1
        return real_live(*args, **kwargs)

    monkeypatch.setattr(lint_cmd, "build_source_snapshot", counted_snapshot)
    monkeypatch.setattr(lint_cmd, "get_inventory_result", counted_inventory)
    monkeypatch.setattr(lint_cmd, "load_knowledge_state", counted_load)
    monkeypatch.setattr(lint_cmd, "build_runtime_live_evaluation", counted_live)

    current = lint_cmd.build_report("docs/llm_wiki", ".", strict=True)

    assert current.passed
    assert calls == {"snapshot": 1, "inventory": 1, "load": 1, "live": 1}
    assert current.knowledge_summary is not None
    assert current.knowledge_summary.freshness_by_state["current"] == 2

    source.write_text("# formatting note\nclass User:\n    pass\n", encoding="utf-8")
    changed = lint_cmd.build_report("docs/llm_wiki", ".", strict=True)

    assert changed.passed
    assert not any(issue.category == "sync_manifest" for issue in changed.issues)
    warnings = [
        diagnostic
        for diagnostic in changed.diagnostics
        if diagnostic.category == "knowledge_freshness"
    ]
    assert {warning.target for warning in warnings} == {
        "llm-wiki://entities/User",
        "llm-wiki://modules/app",
    }
    assert all(
        "[reason=source-bytes-changed-concept-observation-unchanged]" in warning.message
        for warning in warnings
    )


def test_projection_failures_have_stable_strict_categories_and_locations():
    load_issues = (
        KnowledgeLoadIssue(
            code="knowledge-invalid",
            artifact_path="knowledge.json",
            field="concepts[0]",
            message="invalid concept",
        ),
        KnowledgeLoadIssue(
            code="markdown-snapshot-mismatch",
            artifact_path="modules/accounts.md",
            field="bundle.snapshot.markdown_tree_hash",
            message="snapshot differs",
        ),
        KnowledgeLoadIssue(
            code="declared-artifact-missing",
            artifact_path="wiki_surface_index.json",
            field="artifact_hashes.surface_index_hash",
            message="declared artifact is absent",
        ),
    )
    report = lint_cmd.LintReport(wiki_dir="wiki", src_dir="src", strict=True)

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, load_issues=load_issues),
    )

    assert [(issue.category, issue.path, issue.target) for issue in report.issues] == [
        (
            "knowledge_projection",
            "wiki_surface_index.json",
            ("artifact_hashes.surface_index_hash"),
        ),
        ("knowledge_schema", "knowledge.json", "concepts[0]"),
        (
            "knowledge_snapshot",
            "modules/accounts.md",
            "bundle.snapshot.markdown_tree_hash",
        ),
    ]
    assert all(issue.severity == "error" for issue in report.issues)
    assert {
        issue.message.split("[reason=", 1)[1].split("]", 1)[0]
        for issue in report.issues
    } == {
        "declared-artifact-missing",
        "knowledge-invalid",
        "markdown-snapshot-mismatch",
    }
    payload = lint_cmd.report_to_dict(report)
    assert "knowledge_summary" not in payload
    assert all(
        set(issue) == {"category", "message", "severity", "path", "target"}
        for issue in payload["issues"]
    )


def test_live_evaluation_failure_is_a_field_specific_freshness_error():
    report = lint_cmd.LintReport(wiki_dir="wiki", src_dir="src", strict=True)

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(
            enabled=True,
            freshness_error_field="captured_paths[0]",
            freshness_error_message="source hash is unavailable",
        ),
    )

    assert [(issue.category, issue.path, issue.target) for issue in report.issues] == [
        (
            "knowledge_freshness",
            ".llm-wiki-knowledge.json",
            "captured_paths[0]",
        )
    ]
    assert "[reason=live-evaluation-invalid]" in report.issues[0].message


def test_nonsemantic_source_change_is_warning_and_does_not_fail(tmp_path):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    live = _live_evaluation(
        knowledge,
        source_hash_by_path={
            FIXTURE_SOURCE_PATH: fixture_hash("live:byte-only-source-change")
        },
    )
    view = build_knowledge_read_view(loaded, live_evaluation=live)

    report = _report_for_view(view)

    diagnostics = [
        finding
        for finding in report.diagnostics
        if finding.category == "knowledge_freshness"
    ]
    assert report.passed
    assert report.issues == []
    assert {finding.target for finding in diagnostics} == {
        USER_LOCATOR,
        MODULE_LOCATOR,
        "llm-wiki://entities/AccountService",
    }
    assert {finding.severity for finding in diagnostics} == {"warning"}
    assert all(
        "[reason=source-bytes-changed-concept-observation-unchanged]" in finding.message
        for finding in diagnostics
    )


@pytest.mark.parametrize(
    ("live_kwargs", "expected_state", "expected_reason"),
    [
        (
            {
                "source_hash_by_path": {
                    FIXTURE_SOURCE_PATH: fixture_hash("live:semantic-source-change")
                },
                "observation_by_locator": {
                    USER_LOCATOR: fixture_hash("live:user-observation-change")
                },
            },
            ComputedFreshness.SOURCE_CHANGED,
            "concept-observation-changed",
        ),
        (
            {"missing_source_paths": frozenset({FIXTURE_SOURCE_PATH})},
            ComputedFreshness.SOURCE_MISSING,
            "reliably-mapped-source-missing",
        ),
        (
            {"extractor_ref_by_locator": {USER_LOCATOR: "fixture-python-ast"}},
            ComputedFreshness.BASIS_INCOMPATIBLE,
            "extractor-selection-changed",
        ),
    ],
)
def test_promised_structural_stale_states_are_strict_errors(
    tmp_path,
    live_kwargs,
    expected_state,
    expected_reason,
):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    view = build_knowledge_read_view(
        loaded,
        live_evaluation=_live_evaluation(knowledge, **live_kwargs),
    )
    assert view.freshness is not None
    assert view.freshness.by_locator[USER_LOCATOR].state is expected_state

    report = _report_for_view(view)

    issue = next(finding for finding in report.issues if finding.target == USER_LOCATOR)
    assert issue.category == "knowledge_freshness"
    assert issue.severity == "error"
    assert issue.path == "entities/User.md"
    assert f"[reason={expected_reason}]" in issue.message
    assert view.knowledge == knowledge


@pytest.mark.parametrize(
    "evidence_state",
    [EvidenceState.MISSING, EvidenceState.INVALID, EvidenceState.UNKNOWN],
)
def test_promised_structural_evidence_must_be_present(
    tmp_path,
    evidence_state,
):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    original = next(
        concept for concept in knowledge.concepts if concept.locator == USER_LOCATOR
    )
    replacement = replace(
        original,
        facets=replace(
            original.facets,
            structure=replace(
                original.facets.structure,
                evidence=evidence_state,
                basis=None,
            ),
        ),
    )
    modified = replace(
        knowledge,
        concepts=tuple(
            replacement if concept.locator == USER_LOCATOR else concept
            for concept in knowledge.concepts
        ),
    )
    view = build_knowledge_read_view(
        replace(loaded, knowledge=modified),
        live_evaluation=_live_evaluation(modified),
    )

    report = _report_for_view(view)

    issue = next(finding for finding in report.issues if finding.target == USER_LOCATOR)
    assert issue.category == "knowledge_evidence"
    assert issue.path == "entities/User.md"
    assert f"[reason=promised-evidence-{evidence_state.value}]" in issue.message


def test_unknown_structural_tombstone_without_mapping_is_still_strict(tmp_path):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    assert loaded.manifest_basis is not None
    original = next(
        concept for concept in knowledge.concepts if concept.locator == USER_LOCATOR
    )
    unknown = replace(
        original,
        facets=replace(
            original.facets,
            structure=replace(
                original.facets.structure,
                evidence=EvidenceState.UNKNOWN,
                basis=None,
            ),
        ),
    )
    modified = replace(
        knowledge,
        concepts=tuple(
            unknown if concept.locator == USER_LOCATOR else concept
            for concept in knowledge.concepts
        ),
    )
    path = original.document.canonical_path
    mappings = dict(loaded.manifest_basis.page_source_mappings)
    mappings.pop(path)
    baselines = dict(loaded.manifest_basis.evidence_baselines)
    baselines.pop(path)
    tombstones = dict(loaded.manifest_basis.tombstones)
    tombstones[path] = ManifestTombstone(
        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
        unknown_reason=MANIFEST_STATE_UNAVAILABLE,
    )
    manifest = replace(
        loaded.manifest_basis,
        page_source_mappings=mappings,
        evidence_baselines=baselines,
        tombstones=tombstones,
    )
    view = build_knowledge_read_view(
        replace(loaded, knowledge=modified, manifest_basis=manifest),
        live_evaluation=_live_evaluation(modified),
    )

    report = _report_for_view(view)

    issue = next(finding for finding in report.issues if finding.target == USER_LOCATOR)
    assert issue.category == "knowledge_evidence"
    assert "[reason=promised-evidence-unknown]" in issue.message
