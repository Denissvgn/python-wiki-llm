"""Strict knowledge-lint contract tests (KNOW-203)."""

from __future__ import annotations

import types
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli.commands import bootstrap_cmd, lint_cmd
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_governance import (
    GOVERNANCE_EXTENSION_KEY,
    ConceptGovernanceReference,
    GovernanceActor,
    GovernanceLedger,
    ReviewEvidence,
    add_review_event,
    concept_references_from_knowledge,
    reconcile_concepts,
    save_governance,
)
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeLoadIssue,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import (
    ComputedFreshness,
    EvidenceState,
)
from llm_wiki_cli.services.knowledge_observability import (
    BASIS_INCOMPATIBLE_HINTS,
)
from llm_wiki_cli.services.knowledge_orchestration import (
    RUNTIME_GENERATION_INPUT_KEY,
)
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_STATE_UNAVAILABLE,
    TOMBSTONE_UNKNOWN_PROVENANCE,
    ManifestTombstone,
    SyncManifest,
)
from llm_wiki_cli.services.verification_contracts import (
    ARTIFACT_INTEGRITY_CHECKER_ID,
    INTERNAL_LINKS_CHECKER_ID,
    VERIFICATION_RECEIPT_FILENAME,
    CheckerContract,
    build_artifact_verification_context,
    verify_and_write_receipt,
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
    "knowledge_governance",
    "knowledge_review",
    "knowledge_verification",
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


def _report_for_view(view, *, knowledge_drift_report=False):
    report = lint_cmd.LintReport(
        wiki_dir="wiki",
        src_dir="src",
        strict=True,
        knowledge_drift_report=knowledge_drift_report,
    )
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


def _verification_context(loaded, knowledge, *, knowledge_hash=None):
    assert loaded.manifest_basis is not None
    assert loaded.manifest_basis.artifact_hashes is not None
    hashes = loaded.manifest_basis.artifact_hashes
    return build_artifact_verification_context(
        knowledge,
        knowledge_hash=knowledge_hash or hashes.knowledge_index_hash,
        surface_index_hash=hashes.surface_index_hash,
        evaluated_envelope_hash=hashes.evaluated_envelope_hash,
        governance_hash=hashes.governance_hash,
    )


def test_missing_lint_source_probes_are_unique_and_deterministic(
    tmp_path,
    monkeypatch,
):
    def concept(source_path):
        basis = (
            None
            if source_path is None
            else types.SimpleNamespace(source_path=source_path)
        )
        return types.SimpleNamespace(
            facets=types.SimpleNamespace(structure=types.SimpleNamespace(basis=basis))
        )

    knowledge = types.SimpleNamespace(
        concepts=[
            concept("missing.py"),
            concept("present.py"),
            concept("missing.py"),
            concept("captured.py"),
            concept(None),
        ]
    )
    load_result = types.SimpleNamespace(knowledge=knowledge)
    snapshot = types.SimpleNamespace(
        root=tmp_path,
        captured_content_hashes={"captured.py": "sha256:" + ("0" * 64)},
    )
    probed = []

    def fake_lstat(path):
        probed.append(path.relative_to(tmp_path).as_posix())
        if path.name == "missing.py":
            raise FileNotFoundError(path)
        return types.SimpleNamespace()

    monkeypatch.setattr(Path, "lstat", fake_lstat)

    missing = lint_cmd._reliably_missing_source_paths(
        load_result,
        snapshot,
    )

    assert probed == ["missing.py", "present.py"]
    assert missing == frozenset({"missing.py"})


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
            assert strict.knowledge_summary.concepts_evaluated == 6
            assert strict.knowledge_summary.freshness_evaluated is True
        else:
            assert strict.knowledge_summary is None
        return

    assert strict.knowledge_summary is not None
    assert strict.knowledge_summary.availability == (case.expected_availability.value)
    assert strict.knowledge_summary.reason == case.expected_reason.value
    assert strict.knowledge_summary.degraded_reason == case.expected_reason.value
    assert strict.knowledge_summary.concepts_evaluated == 0
    assert strict.knowledge_summary.freshness_counts is None
    assert strict.knowledge_summary.evidence_issue_counts is None
    assert strict.knowledge_summary.freshness_evaluated is False
    assert strict.knowledge_summary.concepts_total == 0
    assert strict.knowledge_summary.concepts_by_kind == {}
    assert strict.knowledge_summary.evidence_by_state == {}
    assert strict.knowledge_summary.freshness_by_state == {}
    assert all(finding.severity == "error" for finding in findings)
    for reason in case.expected_issue_codes:
        matching = [
            finding for finding in findings if f"[reason={reason}]" in finding.message
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
    assert report.knowledge_summary.concepts_evaluated == 6
    assert report.knowledge_summary.freshness_evaluated is True
    assert report.knowledge_summary.freshness_by_state["current"] == 3
    assert report.knowledge_summary.freshness_by_state["unknown"] == 3
    assert report.knowledge_summary.freshness_counts == (
        report.knowledge_summary.freshness_by_state
    )
    assert report.knowledge_summary.evidence_issue_counts == {
        "invalid": 0,
        "missing": 0,
        "unknown": 1,
    }
    assert report.knowledge_summary.degraded_reason is None
    assert set(report.knowledge_summary.phase_durations_ms) == {
        "load",
        "evaluate",
        "check",
    }
    assert all(
        isinstance(value, int) and value >= 0
        for value in report.knowledge_summary.phase_durations_ms.values()
    )
    payload = lint_cmd.report_to_dict(report)
    assert payload["knowledge_summary"] == {
        "availability": "ready",
        "reason": "all-projection-commitments-match",
        "freshness": "evaluated (6 concepts)",
        "concepts_evaluated": 6,
        "freshness_counts": {
            "basis-incompatible": 0,
            "current": 3,
            "nonsemantic-source-change": 0,
            "source-changed": 0,
            "source-missing": 0,
            "unknown": 3,
        },
        "evidence_issue_counts": {
            "invalid": 0,
            "missing": 0,
            "unknown": 1,
        },
        "degraded_reason": None,
        "phase_durations_ms": report.knowledge_summary.phase_durations_ms,
        "freshness_evaluated": True,
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
    assert "Freshness: evaluated (6 concepts)" in lint_cmd.render_text(report)
    assert "- Freshness: evaluated (6 concepts)" in lint_cmd.render_markdown(
        report
    )


def test_lint_sets_observability_summary_after_knowledge_checks_close(
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
    events = []
    real_set_summary = lint_cmd._set_knowledge_summary

    @contextmanager
    def recording_phase(_profiler, name):
        events.append((name, "start"))
        try:
            yield
        finally:
            events.append((name, "end"))

    def recording_set_summary(*args, **kwargs):
        events.append(("knowledge_summary", "set"))
        return real_set_summary(*args, **kwargs)

    monkeypatch.setattr(lint_cmd, "_profile_phase", recording_phase)
    monkeypatch.setattr(lint_cmd, "_set_knowledge_summary", recording_set_summary)

    report = lint_cmd.build_report(
        wiki,
        str(source_root),
        strict=True,
        profiler=object(),
    )

    assert report.knowledge_summary is not None
    assert events.index(("knowledge_checks", "end")) < events.index(
        ("knowledge_summary", "set")
    )
    assert {
        name
        for name, event in events
        if event == "start" and name.startswith("knowledge_")
    } == {
        "knowledge_load",
        "knowledge_freshness",
        "knowledge_checks",
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
    assert not any(
        diagnostic.category == "knowledge_freshness"
        for diagnostic in changed.diagnostics
    )
    reported = lint_cmd.build_report(
        "docs/llm_wiki",
        ".",
        strict=True,
        knowledge_drift_report=True,
    )
    warnings = [
        diagnostic
        for diagnostic in reported.diagnostics
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


def test_native_drift_is_opt_in_report_only_without_suppressing_manifest_integrity(
    tmp_path,
    monkeypatch,
    capsys,
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
    capsys.readouterr()
    source.write_text(
        "class User:\n"
        "    def save(self):\n"
        "        return True\n",
        encoding="utf-8",
    )

    disabled = lint_cmd.build_report(
        "docs/llm_wiki",
        ".",
        strict=True,
    )
    reported = lint_cmd.build_report(
        "docs/llm_wiki",
        ".",
        strict=True,
        knowledge_drift_report=True,
    )

    assert not any(
        finding.category == "knowledge_freshness"
        for finding in (*disabled.issues, *disabled.diagnostics)
    )
    assert any(
        issue.category == "sync_manifest" for issue in disabled.issues
    )
    assert not disabled.passed

    assert any(
        diagnostic.category == "knowledge_freshness"
        and "[reason=concept-observation-changed]" in diagnostic.message
        for diagnostic in reported.diagnostics
    )
    assert not any(
        issue.category == "knowledge_freshness" for issue in reported.issues
    )
    assert any(issue.category == "sync_manifest" for issue in reported.issues)
    assert not reported.passed


def test_report_mode_reports_live_generation_option_drift_without_blocking(
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

    report = lint_cmd.build_report(
        "docs/llm_wiki",
        ".",
        strict=True,
        knowledge_drift_report=True,
        include_tests=[" GO ", "go"],
    )

    findings = [
        diagnostic
        for diagnostic in report.diagnostics
        if diagnostic.category == "knowledge_freshness"
        and "[reason=generation-options-changed]" in diagnostic.message
    ]
    assert report.passed
    assert {finding.target for finding in findings} == {
        "llm-wiki://entities/User",
        "llm-wiki://modules/app",
    }
    expected_hint = BASIS_INCOMPATIBLE_HINTS["generation-options-changed"]
    assert {finding.reason_code for finding in findings} == {
        "generation-options-changed"
    }
    assert {finding.hint for finding in findings} == {expected_hint}
    payload_findings = [
        finding
        for finding in lint_cmd.report_to_dict(report)["diagnostics"]
        if finding.get("reason_code") == "generation-options-changed"
    ]
    assert {finding["hint"] for finding in payload_findings} == {expected_hint}
    assert f"Hint: {expected_hint}" in lint_cmd.render_text(report)
    assert f"Hint: {expected_hint}" in lint_cmd.render_markdown(report)
    assert report.knowledge_summary is not None
    assert report.knowledge_summary.freshness_by_state["basis-incompatible"] == 2


def test_only_freshness_diagnostics_gain_structured_reason_and_hint():
    report = lint_cmd.LintReport(wiki_dir="wiki", src_dir="src")
    report.diagnostics.extend(
        [
            lint_cmd.LintIssue(
                category="knowledge_freshness",
                message="incompatible",
                reason_code="generation-options-changed",
                hint=BASIS_INCOMPATIBLE_HINTS["generation-options-changed"],
            ),
            lint_cmd.LintIssue(
                category="unsupported_sources",
                message="unsupported",
                severity="warning",
            ),
        ]
    )

    diagnostics = lint_cmd.report_to_dict(report)["diagnostics"]

    assert diagnostics[0]["reason_code"] == "generation-options-changed"
    assert diagnostics[0]["hint"] == BASIS_INCOMPATIBLE_HINTS[
        "generation-options-changed"
    ]
    assert "reason_code" not in diagnostics[1]
    assert "hint" not in diagnostics[1]


def test_report_mode_reports_invalid_live_generation_policy_without_blocking(
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
    wiki = tmp_path / "docs" / "llm_wiki"
    manifest = SyncManifest.load(wiki)
    manifest.generation_inputs[RUNTIME_GENERATION_INPUT_KEY] = {
        "data_flow_enabled": True,
        "dependency_graph_detail": "unsupported",
        "workflows_enabled": True,
    }
    manifest.save(wiki)

    report = lint_cmd.build_report(
        wiki,
        str(tmp_path),
        strict=True,
        knowledge_drift_report=True,
    )

    findings = [
        diagnostic
        for diagnostic in report.diagnostics
        if "[reason=live-evaluation-invalid]" in diagnostic.message
    ]
    assert report.passed
    assert len(findings) == 1
    assert findings[0].category == "knowledge_freshness"
    assert findings[0].target == (
        "manifest_generation_inputs."
        f"{RUNTIME_GENERATION_INPUT_KEY}.dependency_graph_detail"
    )
    assert report.knowledge_summary is not None
    assert report.knowledge_summary.freshness_evaluated is False


def test_report_mode_reports_live_option_hashing_failure_without_blocking(
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
    monkeypatch.setattr(
        lint_cmd,
        "RUNTIME_GENERATION_OPTION_DEFAULTS",
        {"api_contracts_enabled": False},
    )

    report = lint_cmd.build_report(
        "docs/llm_wiki",
        ".",
        strict=True,
        knowledge_drift_report=True,
    )

    findings = [
        diagnostic
        for diagnostic in report.diagnostics
        if "[reason=live-evaluation-invalid]" in diagnostic.message
    ]
    assert report.passed
    assert len(findings) == 1
    assert findings[0].category == "knowledge_freshness"
    assert findings[0].target == "generation_options.data_flow_enabled"
    assert report.knowledge_summary is not None
    assert report.knowledge_summary.freshness_evaluated is False


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


def test_governance_and_review_projection_failures_have_distinct_categories():
    load_issues = (
        KnowledgeLoadIssue(
            code="governance-bundle-mismatch",
            artifact_path=".llm-wiki-governance.json",
            field="bundle_id",
            message="bundle differs",
        ),
        KnowledgeLoadIssue(
            code="governance-invalid",
            artifact_path=".llm-wiki-governance.json",
            field="review_events.rv_invalid",
            message="review is malformed",
        ),
    )
    report = lint_cmd.LintReport(wiki_dir="wiki", src_dir="src", strict=True)

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, load_issues=load_issues),
    )

    assert [issue.category for issue in report.issues] == [
        "knowledge_governance",
        "knowledge_review",
    ]


def test_expired_human_review_is_reported_separately_from_machine_status(tmp_path):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    selected = knowledge.concepts[0]
    governed = replace(
        selected,
        extensions={
            **dict(selected.extensions),
            GOVERNANCE_EXTENSION_KEY: {
                "uid": "lw:guide:0123456789abcdef0123456789abcdef",
                "reviews": {
                    "items": [
                        {
                            "event_id": "rv_" + ("a" * 64),
                            "state": "expired",
                            "reasons": ["scope-changed"],
                        }
                    ]
                },
            },
        },
    )
    view = replace(
        view,
        knowledge=replace(
            knowledge,
            concepts=(governed, *knowledge.concepts[1:]),
        ),
    )
    report = lint_cmd.LintReport(
        wiki_dir=str(tmp_path),
        src_dir="src",
        strict=True,
    )

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, view=view),
    )

    reviews = [
        issue for issue in report.issues if issue.category == "knowledge_review"
    ]
    assert len(reviews) == 1
    assert "[reason=scope-changed]" in reviews[0].message
    assert all(
        issue.category != "knowledge_verification" for issue in report.issues
    )


def test_strict_lint_evaluates_retained_review_missing_from_projection(tmp_path):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    archived = ConceptGovernanceReference(
        locator="llm-wiki://guides/Archived",
        concept_kind="guide",
        natural_key="guide:guides/Archived.md",
    )
    ledger = reconcile_concepts(
        GovernanceLedger.empty("lint-review-fixture"),
        (*concept_references_from_knowledge(knowledge), archived),
    )
    archived_uid = next(
        uid
        for uid, allocation in ledger.concepts.items()
        if allocation.locator == archived.locator
    )
    ledger = add_review_event(
        ledger,
        archived_uid,
        section_locator=(
            "llm-wiki://guides/Archived#section/description/1"
        ),
        scope_hash=fixture_hash("archived-section"),
        evidence=ReviewEvidence(mode="no-source"),
        reviewer=GovernanceActor("human", "reviewer.example"),
        method="manual-review",
        method_version="1",
        authored_at="2026-07-27T10:00:00Z",
    )
    written = save_governance(tmp_path, ledger)
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    assert view.manifest_basis is not None
    assert view.manifest_basis.artifact_hashes is not None
    view = replace(
        view,
        manifest_basis=replace(
            view.manifest_basis,
            artifact_hashes=replace(
                view.manifest_basis.artifact_hashes,
                governance_hash=written.content_hash,
            ),
        ),
    )
    report = lint_cmd.LintReport(
        wiki_dir=str(tmp_path),
        src_dir="src",
        strict=True,
    )

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, view=view),
    )

    reviews = [
        issue for issue in report.issues if issue.category == "knowledge_review"
    ]
    assert len(reviews) == 1
    assert "[reason=concept-missing,section-missing]" in reviews[0].message
    assert reviews[0].path is None
    assert reviews[0].target.startswith("rv_")


def test_strict_lint_accepts_current_passing_receipt_without_running_checker(
    tmp_path,
    monkeypatch,
):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    context = _verification_context(loaded, knowledge)
    verify_and_write_receipt(
        tmp_path,
        context,
        [ARTIFACT_INTEGRITY_CHECKER_ID],
    )
    monkeypatch.setattr(
        CheckerContract,
        "run",
        lambda *_args, **_kwargs: pytest.fail(
            "strict lint must not execute receipt checkers"
        ),
    )
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    report = lint_cmd.LintReport(
        wiki_dir=str(tmp_path),
        src_dir="src",
        strict=True,
    )

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, view=view),
    )

    assert not [
        issue
        for issue in report.issues
        if issue.category == "knowledge_verification"
    ]


def test_strict_lint_surfaces_stale_and_failed_receipts(tmp_path):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    stale_context = _verification_context(
        loaded,
        knowledge,
        knowledge_hash=fixture_hash("stale-knowledge"),
    )
    receipt = verify_and_write_receipt(
        tmp_path,
        stale_context,
        [INTERNAL_LINKS_CHECKER_ID],
    )
    assert receipt.result.value == "failed"
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    report = lint_cmd.LintReport(
        wiki_dir=str(tmp_path),
        src_dir="src",
        strict=True,
    )

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, view=view),
    )

    findings = [
        issue
        for issue in report.issues
        if issue.category == "knowledge_verification"
    ]
    assert len(findings) == 2
    assert any("knowledge-changed" in issue.message for issue in findings)
    assert any(
        "[reason=verification-check-failed]" in issue.message
        for issue in findings
    )


def test_strict_lint_rejects_malformed_receipt(tmp_path):
    loaded, _knowledge = _loaded_knowledge(tmp_path)
    (tmp_path / VERIFICATION_RECEIPT_FILENAME).write_bytes(b"{not-json\n")
    view = build_knowledge_read_view(loaded, snapshot_only=True)
    report = lint_cmd.LintReport(
        wiki_dir=str(tmp_path),
        src_dir="src",
        strict=True,
    )

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(enabled=True, view=view),
    )

    findings = [
        issue
        for issue in report.issues
        if issue.category == "knowledge_verification"
    ]
    assert len(findings) == 1
    assert "[reason=verification-receipt-invalid]" in findings[0].message


def test_live_evaluation_failure_is_suppressed_without_report_mode():
    report = lint_cmd.LintReport(wiki_dir="wiki", src_dir="src", strict=True)

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(
            enabled=True,
            freshness_error_field="captured_paths[0]",
            freshness_error_message="source hash is unavailable",
        ),
    )

    assert report.issues == []
    assert report.diagnostics == []


def test_live_evaluation_failure_is_report_only_under_explicit_mode():
    report = lint_cmd.LintReport(
        wiki_dir="wiki",
        src_dir="src",
        strict=True,
        knowledge_drift_report=True,
    )

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(
            enabled=True,
            freshness_error_field="captured_paths[0]",
            freshness_error_message="source hash is unavailable",
        ),
    )

    assert report.issues == []
    assert [
        (issue.category, issue.path, issue.target)
        for issue in report.diagnostics
    ] == [
        (
            "knowledge_freshness",
            ".llm-wiki-knowledge.json",
            "captured_paths[0]",
        )
    ]
    assert "[reason=live-evaluation-invalid]" in report.diagnostics[0].message


def test_report_mode_never_downgrades_projection_integrity():
    report = lint_cmd.LintReport(
        wiki_dir="wiki",
        src_dir="src",
        strict=True,
        knowledge_drift_report=True,
    )

    lint_cmd._check_knowledge_lint(
        report,
        lint_cmd._KnowledgeLintState(
            enabled=True,
            load_issues=(
                KnowledgeLoadIssue(
                    code="knowledge-invalid",
                    artifact_path=".llm-wiki-knowledge.json",
                    field="concepts[0]",
                    message="invalid concept",
                ),
            ),
        ),
    )

    assert report.diagnostics == []
    assert len(report.issues) == 1
    assert report.issues[0].category == "knowledge_schema"


def test_nonsemantic_source_change_requires_report_mode_and_does_not_fail(tmp_path):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    live = _live_evaluation(
        knowledge,
        source_hash_by_path={
            FIXTURE_SOURCE_PATH: fixture_hash("live:byte-only-source-change")
        },
    )
    view = build_knowledge_read_view(loaded, live_evaluation=live)

    report = _report_for_view(view)

    assert report.passed
    assert report.issues == []
    assert not any(
        finding.category == "knowledge_freshness"
        for finding in report.diagnostics
    )

    reported = _report_for_view(view, knowledge_drift_report=True)
    diagnostics = [
        finding
        for finding in reported.diagnostics
        if finding.category == "knowledge_freshness"
    ]
    assert reported.passed
    assert reported.issues == []
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


def test_unknown_freshness_is_disabled_by_default_and_explicitly_reportable(
    tmp_path,
):
    loaded, _knowledge = _loaded_knowledge(tmp_path)
    view = build_knowledge_read_view(loaded)
    assert view.freshness is not None
    assert view.freshness.by_locator[USER_LOCATOR].state is ComputedFreshness.UNKNOWN

    report = _report_for_view(view)
    assert report.passed
    assert report.issues == []
    assert report.diagnostics == []

    reported = _report_for_view(view, knowledge_drift_report=True)
    diagnostic = next(
        finding
        for finding in reported.diagnostics
        if finding.target == USER_LOCATOR
    )
    assert reported.passed
    assert reported.issues == []
    assert "[reason=live-evaluation-not-performed]" in diagnostic.message


def test_missing_freshness_result_is_disabled_by_default_and_reportable(
    tmp_path,
):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    view = build_knowledge_read_view(
        loaded,
        live_evaluation=_live_evaluation(knowledge),
    )
    assert view.freshness is not None
    incomplete_freshness = replace(
        view.freshness,
        by_locator={
            locator: finding
            for locator, finding in view.freshness.by_locator.items()
            if locator != USER_LOCATOR
        },
    )
    incomplete_view = replace(view, freshness=incomplete_freshness)

    report = _report_for_view(incomplete_view)
    assert report.passed
    assert report.issues == []
    assert report.diagnostics == []

    reported = _report_for_view(
        incomplete_view,
        knowledge_drift_report=True,
    )
    diagnostic = next(
        finding
        for finding in reported.diagnostics
        if finding.target == USER_LOCATOR
    )
    assert reported.passed
    assert reported.issues == []
    assert "[reason=freshness-result-missing]" in diagnostic.message


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
def test_promised_structural_stale_states_require_report_mode(
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
    assert report.passed
    assert report.issues == []
    assert report.diagnostics == []

    reported = _report_for_view(view, knowledge_drift_report=True)
    finding = next(
        diagnostic
        for diagnostic in reported.diagnostics
        if diagnostic.target == USER_LOCATOR
    )
    assert reported.passed
    assert reported.issues == []
    assert finding.category == "knowledge_freshness"
    assert finding.severity == "warning"
    assert finding.path == "entities/User.md"
    assert f"[reason={expected_reason}]" in finding.message
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
