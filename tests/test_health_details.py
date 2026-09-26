"""Coverage arithmetic, captured provenance and explicit report migration."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import runpy
from typing import Any, cast

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.services import ci_report, doctor_service, lint_service
from llm_wiki_cli.services.health_details import capture_health_details
from llm_wiki_cli.services.inventory_cache import InventoryCacheStats
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeLoadIssue,
    KnowledgeLoadResult,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import EvidenceState, KnowledgeLoadState
from llm_wiki_cli.services.knowledge_observability import KnowledgePhaseDurations
from llm_wiki_cli.services.knowledge_verification import (
    attach_machine_verification_read_view,
)
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from tests.knowledge_fixtures import fixture_hash
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state
from tests.test_knowledge_health_refresh import (
    recorded_project as recorded_project,
    _command,
    _files,
)


def _report(root, scenario="current"):
    root.mkdir(parents=True, exist_ok=True)
    if scenario in {"absent", "unsupported", "invalid"}:
        code = (
            "knowledge-schema-version-unsupported"
            if scenario == "unsupported"
            else "knowledge-invalid"
        )
        loaded = KnowledgeLoadResult(
            status={
                "absent": KnowledgeLoadState.ABSENT,
                "unsupported": KnowledgeLoadState.INVALID,
                "invalid": KnowledgeLoadState.DEGRADED,
            }[scenario],
            surface=None if scenario == "unsupported" else {},
            knowledge=None,
            manifest_basis=None,
            underlying_status=KnowledgeLoadState.INVALID
            if scenario == "invalid"
            else None,
            issues=()
            if scenario == "absent"
            else (KnowledgeLoadIssue(code, ".llm-wiki-knowledge.json", "fixture"),),
        )
        view = build_knowledge_read_view(loaded)
    else:
        _committed_state(root, producer_version="2.2.0")
        loaded = load_knowledge_state(root)
        knowledge = loaded.knowledge
        assert knowledge is not None
        kwargs = {}
        if scenario in {"producer-changed", "unknown-version"}:
            version = "2.3.0" if scenario == "producer-changed" else "unknown"
            kwargs["producer"] = replace(
                knowledge.bundle.producer,
                tool=replace(knowledge.bundle.producer.tool, version=version),
            )
        if scenario == "source-missing":
            kwargs["missing_source_paths"] = frozenset({"src/accounts.py"})
        if scenario in {"source-changed", "nonsemantic"}:
            kwargs["source_hash_by_path"] = {
                "src/accounts.py": fixture_hash("changed-source")
            }
            if scenario == "source-changed":
                kwargs["observation_by_locator"] = {
                    c.locator: fixture_hash("changed:" + c.locator)
                    for c in knowledge.concepts
                }
        if scenario in {"live-basis-missing", "partial"}:
            kwargs["omit_locators"] = frozenset(c.locator for c in knowledge.concepts)
        live = _live_evaluation(knowledge, **kwargs)
        if scenario == "recorded-basis-missing":
            concept = next(
                c
                for c in knowledge.concepts
                if c.document.page_kind.value == "entities"
            )
            changed = replace(
                concept,
                facets=replace(
                    concept.facets,
                    structure=replace(
                        concept.facets.structure,
                        evidence=EvidenceState.UNKNOWN,
                        basis=None,
                    ),
                ),
            )
            knowledge = replace(
                knowledge,
                concepts=tuple(
                    changed if c.locator == concept.locator else c
                    for c in knowledge.concepts
                ),
            )
            loaded = replace(loaded, knowledge=knowledge, validated_artifacts=None)
        view = build_knowledge_read_view(
            loaded,
            live_evaluation=None
            if scenario in {"unevaluated", "no-live-evaluation"}
            else live,
            snapshot_only=scenario == "unevaluated",
        )
    view = attach_machine_verification_read_view(root, view)
    report = lint_service.LintReport(
        wiki_dir=str(root),
        src_dir=str(root),
        strict=True,
        knowledge_drift_report=True,
        knowledge_enabled=scenario != "absent",
        knowledge_view=view,
    )
    lint_service._check_knowledge_lint(
        report,
        lint_service._KnowledgeLintState(enabled=scenario != "absent", view=view),
    )
    lint_service._set_knowledge_summary(
        report,
        view,
        durations=KnowledgePhaseDurations(load_ms=1, evaluate_ms=1, check_ms=1),
    )
    report.health_details = capture_health_details(
        view,
        wiki_dir=report.wiki_dir,
        src_dir=report.src_dir,
        evaluation_failed=scenario == "partial",
    )
    return report


def _doctor(report, strict=True, schema="v3") -> dict[str, Any]:
    return cast(
        dict[str, Any],
        doctor_service.compose_doctor_report(
            report, strict=strict, wiki_dir=report.wiki_dir, src_dir=report.src_dir
        ).to_payload(report_schema=schema),
    )


def _ci(report, schema="v3") -> dict[str, Any]:
    return ci_report.build_ci_check_payload(
        report,
        report_schema=schema,
        runtime={
            "cache": InventoryCacheStats(
                enabled=False, path=None, status="disabled"
            ).to_dict(),
            "report": {
                "path": None,
                "explicit": False,
                "status": "disabled",
                "error": None,
            },
        },
    )


@pytest.mark.parametrize(
    "scenario,state,current,comparable,attempted",
    [
        ("current", "current", 3, 3, 3),
        ("source-changed", "source-changed", 0, 3, 3),
        ("nonsemantic", "nonsemantic-source-change", 0, 3, 3),
        ("source-missing", "source-missing", 0, 0, 3),
        ("producer-changed", "basis-incompatible", 0, 0, 3),
        ("unknown-version", "basis-incompatible", 0, 0, 3),
        ("live-basis-missing", "unknown", 0, 0, 0),
        ("partial", "unknown", 0, 0, 0),
    ],
)
def test_primary_partition_and_compatible_comparison_are_distinct(
    tmp_path, scenario, state, current, comparable, attempted
):
    report = _report(tmp_path, scenario)
    payload = _doctor(report)
    ci_report.validate_doctor_payload(payload, expected_strict=True)

    ci = _ci(report)
    ci_report.validate_ci_check_payload(ci, cli_exit=0 if report.passed else 1)
    detail = payload["health_details"]
    coverage = detail["coverage"]
    assert (coverage["total"], coverage["modeled"], coverage["unmodeled"]) == (6, 3, 3)
    assert coverage["outcomes"][state] == 3
    assert coverage["outcomes"]["current"] == current
    assert (
        coverage["comparable"] == comparable
        and coverage["comparison_attempted"] == attempted
    )
    assert (
        sum(coverage["outcomes"].values()) + coverage["unmodeled"] == coverage["total"]
    )
    assert detail["evaluation"]["state"] == (
        "partial" if scenario == "partial" else "evaluated"
    )
    assert detail["snapshot"]["validated"] is True
    assert ci["knowledge_health"]["health_details"] == detail
    assert detail["basis"]["recorded"]["tool"]["version"] == "2.2.0"
    if scenario == "producer-changed":
        assert detail["basis"]["live"]["tool"]["version"] == "2.3.0"
    assert detail["basis"]["analysis_contract"] is None


@pytest.mark.parametrize(
    "scenario",
    ["unevaluated", "no-live-evaluation", "absent", "unsupported", "invalid"],
)
def test_unevaluated_and_unavailable_counts_remain_null(tmp_path, scenario):
    payload = _doctor(_report(tmp_path, scenario))
    ci_report.validate_doctor_payload(payload, expected_strict=True)
    detail = payload["health_details"]
    assert detail["basis"]["live"] is None and detail["reasons"] == []
    assert all(
        detail["coverage"][name] is None
        for name in ("evaluated", "comparison_attempted", "comparable", "outcomes")
    )
    if scenario in {"unevaluated", "no-live-evaluation"}:
        assert detail["evaluation"]["state"] == "not-evaluated"
        assert detail["coverage"]["total"] == 6
        assert detail["coverage"]["modeled"] == 3
    else:
        assert detail["evaluation"]["state"] == "unavailable"
        assert all(value is None for value in detail["coverage"].values())
        assert detail["basis"]["recorded"] is None


def test_missing_recorded_basis_does_not_reclassify_modeled_concept(tmp_path):
    payload = _doctor(_report(tmp_path, "recorded-basis-missing"))
    ci_report.validate_doctor_payload(payload, expected_strict=True)
    coverage = payload["health_details"]["coverage"]
    assert coverage["modeled"] == 3 and coverage["unmodeled"] == 3
    assert coverage["outcomes"]["unknown"] == 1 and coverage["outcomes"]["current"] == 2


@pytest.fixture
def detailed_payload(tmp_path):
    return _doctor(_report(tmp_path))


@pytest.mark.parametrize(
    "path,value",
    [
        (("schema_version",), "llm-wiki-doctor/v999"),
        (("health_details", "schema_version"), "future/v1"),
        (("health_details", "scope", "wiki_dir"), "fixture/wiki"),
        (("health_details", "scope", "src_dir"), "fixture/source"),
        (("health_details", "scope", "selection", "state"), "future"),
        (
            ("health_details", "scope", "selection", "fingerprint"),
            fixture_hash("unconfigured"),
        ),
        (("health_details", "coverage", "total"), 7),
        (("health_details", "coverage", "modeled"), True),
        (("health_details", "coverage", "unmodeled"), -1),
        (("health_details", "coverage", "evaluated"), None),
        (("health_details", "coverage", "comparison_attempted"), 0),
        (("health_details", "coverage", "comparable"), 4),
        (("health_details", "coverage", "outcomes", "unknown"), 1),
        (("health_details", "coverage", "outcomes", "current"), 3.0),
        (("health_details", "coverage", "outcomes", "future"), 0),
        (("health_details", "snapshot", "knowledge_index_hash"), None),
        (("health_details", "snapshot", "live_source_hash"), "sha256:bad"),
        (("health_details", "snapshot", "validated"), False),
        (("health_details", "basis", "recorded"), None),
        (("health_details", "basis", "live"), None),
        (("health_details", "basis", "analysis_contract"), "invented-compatibility"),
        (("health_details", "basis", "live", "tool", "version"), "3.0.0"),
        (
            ("health_details", "basis", "live", "generation_options_hash"),
            fixture_hash("different-options"),
        ),
        (("health_details", "evaluation", "state"), "not-evaluated"),
        (("health_details", "reasons"), []),
        (("health_details", "unrecognized"), 0),
    ],
)
def test_v3_rejects_inconsistent_closed_contract(detailed_payload, path, value):
    target = detailed_payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ci_report.CiCheckReportError):
        ci_report.validate_doctor_payload(detailed_payload, expected_strict=True)


def test_capture_is_immutable_and_does_not_read_current_files(tmp_path, monkeypatch):
    report = _report(tmp_path / "wiki", "producer-changed")
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("def original(): pass\n", encoding="utf-8")
    snapshot = build_source_snapshot(source)
    captured = capture_health_details(
        report.knowledge_view,
        wiki_dir=report.wiki_dir,
        src_dir=str(source),
        source_snapshot=snapshot,
    )
    expected = captured.to_payload()
    snapshot.captured_content_hashes.clear()
    (source / "app.py").write_text("changed after evaluation\n", encoding="utf-8")

    def reject_read(*args, **kwargs):
        pytest.fail("serialization must not reread mutable files")

    monkeypatch.setattr(Path, "read_text", reject_read)
    monkeypatch.setattr(Path, "read_bytes", reject_read)
    mutated = captured.to_payload()
    mutated["basis"]["live"]["tool"]["version"] = "new-install"
    assert captured.to_payload() == expected
    assert expected["basis"]["live"]["tool"]["version"] == "2.3.0"


def test_primary_concept_counts_ignore_overlapping_lint_diagnostics(tmp_path):
    report = _report(tmp_path, "producer-changed")
    assert report.health_details is not None
    before = report.health_details.to_payload()
    report.diagnostics.extend(deepcopy(report.diagnostics))
    after = capture_health_details(
        report.knowledge_view, wiki_dir=report.wiki_dir, src_dir=report.src_dir
    ).to_payload()
    assert before == after
    assert sum(row["concepts"] for row in after["reasons"]) == 6


def test_legacy_payloads_and_capability_contract_keep_defaults(tmp_path, monkeypatch):
    report = _report(tmp_path)
    doctor = doctor_service.compose_doctor_report(
        report, strict=False, wiki_dir=report.wiki_dir, src_dir=report.src_dir
    )
    assert doctor.to_payload()["schema_version"] == "llm-wiki-doctor/v1"
    assert "health_details" not in doctor.to_payload()
    assert _ci(report, "v1")["knowledge_health"] == doctor.to_payload()
    assert _ci(report, "v2")["knowledge_health"] == doctor.to_payload()
    monkeypatch.setattr(api, "build_doctor_report", lambda *args, **kwargs: doctor)
    assert api.doctor()["schema_version"] == "llm-wiki-doctor/v1"
    assert api.doctor(report_schema="v3")["schema_version"] == "llm-wiki-doctor/v3"
    parser = cli._build_parser()
    assert parser.parse_args(["doctor", "--capabilities"]).capabilities
    assert parser.parse_args(["doctor"]).report_schema == "v1"
    assert parser.parse_args(["ci-check"]).report_schema == "v1"
    with pytest.raises(SystemExit):
        parser.parse_args(["doctor", "--capabilities", "--report-schema", "v3"])


def test_v3_cannot_be_built_by_relabelling_a_legacy_evaluation(tmp_path):
    report = _report(tmp_path)
    report.health_details = None
    with pytest.raises(ValueError, match="captured during evaluation"):
        _doctor(report)
    with pytest.raises(ValueError, match="captured during evaluation"):
        _ci(report)


def test_v3_preserves_required_output_failure_and_nested_scope_checks(tmp_path):
    report = _report(tmp_path)
    payload = _ci(report)
    payload["runtime"]["report"] = {
        "path": "report.md",
        "explicit": True,
        "status": "failed",
        "error": "disk full",
    }
    payload["command_exit_code"] = 2
    ci_report.validate_ci_check_payload(payload, cli_exit=2)
    with pytest.raises(ci_report.CiCheckReportError):
        ci_report.validate_ci_check_payload(payload, cli_exit=0)
    payload["wiki_dir"] = "foreign/wiki"
    with pytest.raises(ci_report.CiCheckReportError):
        ci_report.validate_ci_check_payload(payload, cli_exit=2)


def test_action_reader_accepts_v3_but_still_rejects_duplicate_json(tmp_path):
    renderer = runpy.run_path(
        str(Path(__file__).parents[1] / "integrations/github-action/render_summary.py")
    )
    payload = _doctor(_report(tmp_path / "wiki"))
    path = tmp_path / "doctor.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert (
        renderer["load_report"](
            path, doctor_exit_code=payload["exit_code"], expected_strict=True
        )
        == payload
    )
    raw = path.read_text()
    path.write_text(
        raw.replace('"total": 6', '"total": 6, "total": 6'), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicate"):
        renderer["load_report"](
            path, doctor_exit_code=payload["exit_code"], expected_strict=True
        )


def test_one_evaluation_serves_both_v3_reports_without_metrics_expansion(
    recorded_project, monkeypatch
):
    from llm_wiki_cli.services import knowledge_consumption

    calls = {"inventory": 0, "freshness": 0}
    inventory = lint_service.get_inventory_result
    freshness = knowledge_consumption.evaluate_knowledge_freshness

    def collect(*args, **kwargs):
        calls["inventory"] += 1
        return inventory(*args, **kwargs)

    def evaluate(*args, **kwargs):
        calls["freshness"] += 1
        return freshness(*args, **kwargs)

    monkeypatch.setattr(lint_service, "get_inventory_result", collect)
    monkeypatch.setattr(knowledge_consumption, "evaluate_knowledge_freshness", evaluate)
    before = _files(Path.cwd())
    report = lint_service.build_report(
        "wiki",
        "source",
        strict=True,
        knowledge_drift_report=True,
        include_plugins=False,
        include_health_details=True,
    )
    doctor = _doctor(report)
    ci = _ci(report)
    ci_report.validate_doctor_payload(doctor, expected_strict=True)
    assert doctor["health_details"] == ci["knowledge_health"]["health_details"]
    assert doctor["status"] == "healthy"
    assert calls == {"inventory": 1, "freshness": 1}
    assert before == _files(Path.cwd())
    assert "health_details" not in lint_service.report_to_dict(report)
    assert report.knowledge_summary is not None
    assert "basis" not in report.knowledge_summary.aggregate_payload()
    assert "scope" not in report.knowledge_summary.aggregate_payload()


@pytest.mark.parametrize("command", ["doctor", "ci-check"])
def test_v3_is_an_explicit_cli_choice_on_a_real_packed_wiki(
    recorded_project, command, capsys
):
    capsys.readouterr()
    flags = (
        ["--strict"]
        if command == "doctor"
        else ["--no-report", "--no-cache", "--no-plugins", "--knowledge-drift-report"]
    )
    _command(
        [
            command,
            "--wiki-dir",
            "wiki",
            "--src-dir",
            "source",
            "--format",
            "json",
            "--report-schema",
            "v3",
            *flags,
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    if command == "doctor":
        ci_report.validate_doctor_payload(payload, expected_strict=True)
        details = payload["health_details"]
    else:
        ci_report.validate_ci_check_payload(payload, cli_exit=0)
        details = payload["knowledge_health"]["health_details"]
    assert details["coverage"]["modeled"] > 0
    assert details["coverage"]["outcomes"]["current"] == details["coverage"]["modeled"]
    assert details["snapshot"]["live_source_hash"] is not None


def test_bounded_primary_examples_are_order_independent_with_exact_omissions(tmp_path):
    report = _report(tmp_path)
    view = report.knowledge_view
    assert view is not None and view.knowledge is not None
    knowledge = view.knowledge
    original = next(
        c for c in knowledge.concepts if c.document.page_kind.value == "modules"
    )
    added = tuple(
        replace(
            original,
            locator=f"llm-wiki://modules/copy_{n}",
            document=replace(
                original.document,
                page_id=f"copy_{n}",
                canonical_path=f"modules/copy_{n}.md",
            ),
        )
        for n in range(10)
    )
    knowledge = replace(knowledge, concepts=knowledge.concepts + added)
    loaded = KnowledgeLoadResult(
        status=KnowledgeLoadState.VALID,
        surface=view.surface,
        knowledge=knowledge,
        manifest_basis=view.manifest_basis,
    )
    forward = build_knowledge_read_view(
        loaded, live_evaluation=_live_evaluation(knowledge)
    )
    reverse_knowledge = replace(knowledge, concepts=tuple(reversed(knowledge.concepts)))
    reverse = build_knowledge_read_view(
        replace(loaded, knowledge=reverse_knowledge),
        live_evaluation=_live_evaluation(reverse_knowledge),
    )

    def capture(value):
        return capture_health_details(
            value, wiki_dir=str(tmp_path), src_dir=str(tmp_path)
        ).to_payload()

    assert capture(forward) == capture(reverse)
    group = next(
        row
        for row in capture(forward)["reasons"]
        if row["code"] == "recorded-basis-matches-live-evaluation"
    )
    assert (
        group["concepts"] == 13
        and len(group["examples"]) == 3
        and group["omitted"] == 10
    )


def test_unsupported_legacy_doctor_projection_is_accepted_by_its_existing_reader(
    tmp_path,
):
    payload = _doctor(_report(tmp_path, "unsupported"), schema="v1")
    assert payload["snapshot_parity"]["state"] == "not-available"
    assert payload["status"] == "unhealthy"
    ci_report.validate_doctor_payload(payload, expected_strict=True)


@pytest.mark.parametrize("scenario", ["current", "producer-changed"])
def test_action_v3_receipt_is_bound_to_validated_report_bytes(tmp_path, scenario):
    import hashlib

    renderer = runpy.run_path(
        str(Path(__file__).parents[1] / "integrations/github-action/render_summary.py")
    )
    payload = _doctor(_report(tmp_path / "wiki", scenario))
    path = tmp_path / "doctor.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    report = renderer["load_report"](
        path, doctor_exit_code=payload["exit_code"], expected_strict=True
    )
    renderer["_write_receipt"](
        str(receipt),
        report_path=path,
        report=report,
        fail_on="degraded",
        doctor_exit_code=payload["exit_code"],
        dashboard_exit_code=0 if payload["status"] == "healthy" else 1,
    )
    parsed = json.loads(receipt.read_text())
    assert parsed["schema_version"] == "llm-wiki-doctor-dashboard/v2"
    assert parsed["report_schema_version"] == "llm-wiki-doctor/v3"
    assert parsed["report_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert parsed["status"] == payload["status"]
    summary = renderer["render_summary"](report, fail_on="degraded")
    assert "Doctor v1 supplies" not in summary
    assert "full v3 JSON" in summary
    assert len(summary.splitlines()) <= 40 and len(summary.encode()) <= 8192


@pytest.mark.parametrize("schema", ["v1", "v3"])
def test_action_receipt_rejects_report_changed_after_validation(tmp_path, schema):
    renderer = runpy.run_path(
        str(Path(__file__).parents[1] / "integrations/github-action/render_summary.py")
    )
    payload = _doctor(_report(tmp_path / "wiki"), schema=schema)
    path = tmp_path / "doctor.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    report = renderer["load_report"](path, doctor_exit_code=0, expected_strict=True)
    payload["wiki_dir"] = "different/wiki"
    if schema == "v3":
        payload["health_details"]["scope"]["wiki_dir"] = "different/wiki"
    path.write_text(json.dumps(payload), encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    with pytest.raises(ValueError, match="changed after validation"):
        renderer["_write_receipt"](
            str(receipt),
            report_path=path,
            report=report,
            fail_on="degraded",
            doctor_exit_code=0,
            dashboard_exit_code=0,
        )
    assert not receipt.exists()


@pytest.mark.parametrize("mode", ["missing", "wrong-locator"])
def test_incomplete_freshness_cannot_be_promoted_to_v3(tmp_path, mode):
    from llm_wiki_cli.services.health_contract import HealthDetailsError

    report = _report(tmp_path)
    view = report.knowledge_view
    assert view is not None and view.freshness is not None
    results = dict(view.freshness.by_locator)
    first = next(iter(results))
    if mode == "missing":
        del results[first]
    else:
        results[first] = replace(results[first], locator="llm-wiki://modules/foreign")
    view = replace(view, freshness=replace(view.freshness, by_locator=results))
    with pytest.raises(HealthDetailsError, match="freshness"):
        capture_health_details(view, wiki_dir=report.wiki_dir, src_dir=report.src_dir)


def test_ready_report_cannot_discard_captured_evidence(detailed_payload):
    unavailable = capture_health_details(
        None, wiki_dir=detailed_payload["wiki_dir"], src_dir=detailed_payload["src_dir"]
    ).to_payload()
    detailed_payload["health_details"] = unavailable
    with pytest.raises(ci_report.CiCheckReportError, match="inventory availability"):
        ci_report.validate_doctor_payload(detailed_payload, expected_strict=True)


def test_unevaluated_capture_cannot_claim_legacy_currentness(tmp_path):
    report = _report(tmp_path, "unevaluated")
    payload = _doctor(report)
    current = _doctor(_report(tmp_path / "current"))
    for field in (
        "status",
        "exit_code",
        "freshness",
        "drift",
        "degraded_reasons",
        "unhealthy_reasons",
    ):
        payload[field] = current[field]
    with pytest.raises(ci_report.CiCheckReportError, match="unevaluated evidence"):
        ci_report.validate_doctor_payload(payload, expected_strict=True)


def test_v3_preflight_failure_has_no_invented_zero_coverage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = api.doctor(wiki_dir="missing", report_schema="v3")
    ci_report.validate_doctor_payload(result, expected_strict=False)
    assert result["health_details"]["evaluation"]["state"] == "failed"
    assert all(value is None for value in result["health_details"]["coverage"].values())
    assert result["status"] == "absent"
