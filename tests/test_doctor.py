"""Contract tests for the composed knowledge-health command."""

from __future__ import annotations

import json
import types
from dataclasses import replace
from pathlib import Path

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import bootstrap_cmd, doctor_cmd
from llm_wiki_cli.services import (
    doctor_service,
    extraction_service,
    knowledge_verification,
    lint_service,
)
from llm_wiki_cli.services.contracts import DOCTOR_SCHEMA_VERSION
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadReason,
)
from llm_wiki_cli.services.knowledge_loader import (
    KnowledgeLoadIssue,
    KnowledgeLoadResult,
    load_knowledge_state,
)
from llm_wiki_cli.services.knowledge_model import KnowledgeLoadState
from llm_wiki_cli.services.knowledge_observability import KnowledgePhaseDurations
from llm_wiki_cli.services.knowledge_verification import (
    attach_machine_verification_read_view,
)
from llm_wiki_cli.services.wiki_surface_index import SURFACE_INDEX_FILENAME
from tests.knowledge_fixtures import (
    DoctorExitFixture,
    doctor_exit_fixtures,
    fixture_hash,
    one_module_two_entities_fixture,
)
from tests.test_knowledge_freshness import _live_evaluation
from tests.test_knowledge_loader import _committed_state


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    ("kwargs", "error"),
    [
        ({"strict": 1}, TypeError),
        ({"allow_external_src": 1}, TypeError),
        ({"parallel_jobs": True}, TypeError),
        ({"parallel_jobs": 0}, ValueError),
    ],
)
def test_doctor_rejects_ambiguous_runtime_options(kwargs, error):
    with pytest.raises(error):
        doctor_service.build_doctor_report(**kwargs)


def _lint_for_fixture(
    root: Path,
    fixture: DoctorExitFixture,
) -> lint_service.LintReport:
    if fixture.scenario == "absent":
        view = build_knowledge_read_view(
            KnowledgeLoadResult(
                status=KnowledgeLoadState.ABSENT,
                surface={},
                knowledge=None,
                manifest_basis=None,
            ),
            snapshot_only=True,
        )
        view = attach_machine_verification_read_view(root, view)
        return lint_service.LintReport(
            wiki_dir=str(root),
            src_dir=str(root),
            strict=True,
            knowledge_drift_report=True,
            knowledge_enabled=False,
            knowledge_view=view,
        )

    _committed_state(root)
    loaded = load_knowledge_state(root)
    assert loaded.knowledge is not None
    if fixture.scenario == "current":
        view = build_knowledge_read_view(
            loaded,
            live_evaluation=_live_evaluation(loaded.knowledge),
        )
    elif fixture.scenario == "unevaluated":
        view = build_knowledge_read_view(loaded, snapshot_only=True)
    elif fixture.scenario == "stale-confirmed":
        view = build_knowledge_read_view(
            loaded,
            live_evaluation=_live_evaluation(
                loaded.knowledge,
                source_hash_by_path={
                    "src/accounts.py": fixture_hash("doctor:changed-source")
                },
                observation_by_locator={
                    concept.locator: fixture_hash(
                        f"doctor:changed-observation:{concept.locator}"
                    )
                    for concept in loaded.knowledge.concepts
                    if concept.facets.structure.basis is not None
                },
            ),
        )
    else:
        raise AssertionError(f"unknown doctor fixture scenario {fixture.scenario}")

    view = attach_machine_verification_read_view(root, view)
    report = lint_service.LintReport(
        wiki_dir=str(root),
        src_dir=str(root),
        strict=True,
        knowledge_drift_report=True,
        knowledge_enabled=True,
        knowledge_view=view,
    )
    lint_service._check_knowledge_lint(
        report,
        lint_service._KnowledgeLintState(enabled=True, view=view),
    )
    lint_service._set_knowledge_summary(
        report,
        view,
        durations=KnowledgePhaseDurations(load_ms=1, evaluate_ms=1, check_ms=1),
    )
    return report


@pytest.mark.parametrize(
    "fixture",
    doctor_exit_fixtures(),
    ids=lambda fixture: fixture.name,
)
def test_fixture_backed_command_contract_covers_all_four_exit_codes(
    tmp_path: Path,
    monkeypatch,
    capsys,
    fixture: DoctorExitFixture,
) -> None:
    root = tmp_path / fixture.name
    root.mkdir()
    lint = _lint_for_fixture(root, fixture)
    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(root),
        src_dir=str(root),
    )
    assert report.status.value == fixture.expected_status
    assert report.exit_code == fixture.expected_exit_code

    monkeypatch.setattr(doctor_cmd, "build_doctor_report", lambda *_a, **_k: report)
    args = types.SimpleNamespace(
        wiki_dir=str(root),
        src_dir=str(root),
        strict=False,
        allow_external_src=False,
        helper_cache_dir=None,
        include_tests=None,
        jobs=1,
        requested_jobs=1,
        format="json",
    )
    if fixture.expected_exit_code:
        with pytest.raises(SystemExit) as raised:
            doctor_cmd.run(args)
        assert raised.value.code == fixture.expected_exit_code
    else:
        doctor_cmd.run(args)
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == DOCTOR_SCHEMA_VERSION
    assert payload["status"] == fixture.expected_status
    assert payload["exit_code"] == fixture.expected_exit_code


def test_json_contract_has_fixed_sections_and_complete_freshness_counts(
    tmp_path: Path,
) -> None:
    fixture = doctor_exit_fixtures()[0]
    lint = _lint_for_fixture(tmp_path, fixture)

    payload = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    ).to_payload()

    assert set(payload) == {
        "schema_version",
        "status",
        "exit_code",
        "strict",
        "wiki_dir",
        "src_dir",
        "availability",
        "freshness",
        "snapshot_parity",
        "governance",
        "drift",
        "verification_receipt",
        "degraded_reasons",
        "unhealthy_reasons",
    }
    assert set(payload["freshness"]["counts_by_state"]) == {
        "unknown",
        "current",
        "nonsemantic-source-change",
        "source-changed",
        "basis-incompatible",
        "source-missing",
    }
    assert payload["freshness"]["disclosure"].startswith("evaluated (")
    assert payload["snapshot_parity"]["state"] == "valid"
    assert payload["governance"]["state"] == "not-present"
    assert payload["verification_receipt"]["state"] == "absent"


def test_human_report_is_compact_and_contains_every_required_section(
    tmp_path: Path,
) -> None:
    lint = _lint_for_fixture(tmp_path, doctor_exit_fixtures()[0])
    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    rendered = doctor_service.render_doctor_text(report)

    assert len(rendered.splitlines()) <= 12
    for label in (
        "Availability:",
        "Freshness:",
        "Snapshot parity:",
        "Governance:",
        "Drift:",
        "Verification receipt:",
    ):
        assert label in rendered


def test_strict_mode_escalates_indeterminate_drift(tmp_path: Path) -> None:
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    assert loaded.knowledge is not None
    locator = next(
        concept.locator
        for concept in loaded.knowledge.concepts
        if concept.facets.structure.basis is not None
    )
    view = build_knowledge_read_view(
        loaded,
        live_evaluation=_live_evaluation(
            loaded.knowledge,
            omit_locators=frozenset({locator}),
        ),
    )
    lint = lint_service.LintReport(
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
        strict=True,
        knowledge_drift_report=True,
        knowledge_enabled=True,
        knowledge_view=view,
    )
    lint_service._set_knowledge_summary(
        lint,
        view,
        durations=KnowledgePhaseDurations(),
    )
    lint_service._check_knowledge_lint(
        lint,
        lint_service._KnowledgeLintState(enabled=True, view=view),
    )

    normal = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )
    strict = doctor_service.compose_doctor_report(
        lint,
        strict=True,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert normal.status is doctor_service.DoctorStatus.DEGRADED
    assert strict.status is doctor_service.DoctorStatus.UNHEALTHY
    assert strict.unhealthy_reasons == ("freshness-indeterminate",)


def test_degraded_availability_and_expired_review_each_return_exit_one(
    tmp_path: Path,
) -> None:
    base = _lint_for_fixture(tmp_path, doctor_exit_fixtures()[0])
    assert base.knowledge_view is not None
    degraded_view = replace(
        base.knowledge_view,
        availability=KnowledgeAvailability.DEGRADED,
        reason=KnowledgeReadReason.DEGRADED_INVALID,
        load_state=KnowledgeLoadState.DEGRADED,
        underlying_load_state=KnowledgeLoadState.INVALID,
        knowledge=None,
        manifest_basis=None,
        freshness=None,
        counts=None,
    )
    degraded_lint = lint_service.LintReport(
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
        strict=True,
        knowledge_drift_report=True,
        knowledge_enabled=True,
        knowledge_view=degraded_view,
    )

    degraded = doctor_service.compose_doctor_report(
        degraded_lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert degraded.status is doctor_service.DoctorStatus.DEGRADED
    assert degraded.exit_code == 1
    assert set(degraded.degraded_reasons) == {
        "knowledge-degraded",
        "freshness-unevaluated",
    }

    base.issues.append(
        lint_service.LintIssue(
            category="knowledge_review",
            message="Review is expired [reason=review-expired].",
        )
    )
    expired = doctor_service.compose_doctor_report(
        base,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert expired.status is doctor_service.DoctorStatus.DEGRADED
    assert expired.exit_code == 1
    assert expired.governance["expired_reviews"] == 1
    assert expired.degraded_reasons == ("expired-reviews",)


def test_mixed_snapshot_and_invalid_governance_are_unhealthy(
    tmp_path: Path,
) -> None:
    _committed_state(tmp_path)
    loaded = load_knowledge_state(tmp_path)
    ready = build_knowledge_read_view(loaded, snapshot_only=True)
    mixed_view = replace(
        ready,
        availability=KnowledgeAvailability.DEGRADED,
        reason=KnowledgeReadReason.DEGRADED_MIXED_SNAPSHOT,
        load_state=KnowledgeLoadState.DEGRADED,
        underlying_load_state=KnowledgeLoadState.MIXED_SNAPSHOT,
        knowledge=None,
        manifest_basis=None,
        freshness=None,
        counts=None,
    )
    lint = lint_service.LintReport(
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
        strict=True,
        knowledge_drift_report=True,
        knowledge_enabled=True,
        knowledge_view=mixed_view,
        issues=[
            lint_service.LintIssue(
                category="knowledge_governance",
                message=(
                    "Knowledge governance is invalid "
                    "[reason=governance-projection-mismatch]."
                ),
            )
        ],
    )

    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert report.status is doctor_service.DoctorStatus.UNHEALTHY
    assert set(report.unhealthy_reasons) == {
        "mixed-snapshot",
        "invalid-governance",
    }


@pytest.mark.parametrize(
    ("code", "artifact_path", "field"),
    (
        (
            "governance-invalid",
            ".llm-wiki-governance.json",
            "review_events.rv_invalid",
        ),
        (
            "knowledge-invalid",
            ".llm-wiki-knowledge.json",
            (
                "knowledge_index_bytes.governance_projection.concepts."
                "llm-wiki://concepts/account.reviews.total"
            ),
        ),
    ),
)
def test_malformed_review_projection_is_invalid_governance_not_expiry(
    tmp_path: Path,
    code: str,
    artifact_path: str,
    field: str,
) -> None:
    base = _lint_for_fixture(tmp_path, doctor_exit_fixtures()[0])
    assert base.knowledge_view is not None
    degraded = replace(
        base.knowledge_view,
        availability=KnowledgeAvailability.DEGRADED,
        reason=KnowledgeReadReason.DEGRADED_INVALID,
        load_state=KnowledgeLoadState.DEGRADED,
        underlying_load_state=KnowledgeLoadState.INVALID,
        knowledge=None,
        manifest_basis=None,
        freshness=None,
        counts=None,
    )
    lint = lint_service.LintReport(
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
        strict=True,
        knowledge_drift_report=True,
        knowledge_enabled=True,
        knowledge_view=degraded,
    )
    lint_service._check_knowledge_lint(
        lint,
        lint_service._KnowledgeLintState(
            enabled=True,
            view=degraded,
            load_issues=(
                KnowledgeLoadIssue(
                    code=code,
                    artifact_path=artifact_path,
                    field=field,
                    message="review is malformed",
                ),
            ),
        ),
    )

    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert report.status is doctor_service.DoctorStatus.UNHEALTHY
    assert report.exit_code == 2
    assert report.governance["state"] == "invalid"
    assert report.governance["expired_reviews"] == 0
    assert report.governance["reasons"] == [code]
    assert report.unhealthy_reasons == ("invalid-governance",)


def test_drift_classification_uses_structured_freshness_not_issue_prose(
    tmp_path: Path,
) -> None:
    fixture = next(
        item
        for item in doctor_exit_fixtures()
        if item.scenario == "stale-confirmed"
    )
    lint = _lint_for_fixture(tmp_path, fixture)
    lint.diagnostics = [
        replace(issue, message="Freshness wording changed.")
        for issue in lint.diagnostics
    ]

    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert report.status is doctor_service.DoctorStatus.UNHEALTHY
    assert report.exit_code == 2
    assert report.drift["state"] == "stale-confirmed"
    assert report.drift["confirmed_stale"] == 3
    assert report.drift["reasons"] == ["concept-observation-changed"]


def test_cli_parser_and_supported_api_expose_doctor(
    tmp_path: Path,
    monkeypatch,
) -> None:
    parsed = cli._build_parser().parse_args(
        [
            "doctor",
            "--wiki-dir",
            "wiki",
            "--src-dir",
            ".",
            "--format",
            "json",
            "--strict",
        ]
    )
    assert parsed.command == "doctor"
    assert parsed.format == "json"
    assert parsed.strict is True

    expected = {
        "schema_version": DOCTOR_SCHEMA_VERSION,
        "status": "healthy",
        "exit_code": 0,
    }
    fake = types.SimpleNamespace(to_payload=lambda: expected)
    monkeypatch.setattr(api, "build_doctor_report", lambda *_a, **_k: fake)

    assert api.doctor(".", wiki_dir="wiki", strict=True) == expected


def test_doctor_consumer_is_registered_in_shared_knowledge_fixture() -> None:
    values = one_module_two_entities_fixture().inputs_for("doctor")

    assert values["consumer"] == "doctor"


def test_service_composes_the_real_strict_lint_operation(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("app.py").write_text("class User:\n    pass\n", encoding="utf-8")
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

    report = doctor_service.build_doctor_report()

    assert report.status is doctor_service.DoctorStatus.HEALTHY
    assert report.exit_code == 0
    assert report.freshness["evaluated"] is True
    assert report.snapshot_parity["state"] == "valid"

    monkeypatch.setattr(
        "sys.argv",
        [
            "llm-wiki",
            "doctor",
            "--wiki-dir",
            "docs/llm_wiki",
            "--src-dir",
            ".",
            "--format",
            "json",
        ],
    )
    cli.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == DOCTOR_SCHEMA_VERSION
    assert payload["status"] == "healthy"
    assert payload["exit_code"] == 0


def test_doctor_disables_project_plugin_loading_by_default(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("app.py").write_text("class User:\n    pass\n", encoding="utf-8")
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

    def fail_plugin_load(*_args, **_kwargs):
        pytest.fail("doctor must not load project plugins by default")

    monkeypatch.setattr(
        extraction_service,
        "get_extractor_registry",
        fail_plugin_load,
    )
    monkeypatch.setattr(
        extraction_service,
        "_selected_runtime_plugin_components",
        fail_plugin_load,
    )
    monkeypatch.setattr(
        lint_service,
        "_run_plugin_lint_rules",
        fail_plugin_load,
    )

    report = doctor_service.build_doctor_report()

    assert report.status is doctor_service.DoctorStatus.HEALTHY


def test_doctor_reuses_single_lint_verification_receipt_read(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    Path("app.py").write_text("class User:\n    pass\n", encoding="utf-8")
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

    original = knowledge_verification.load_verification_receipt
    reads = 0

    def counted_load(*args, **kwargs):
        nonlocal reads
        reads += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(
        knowledge_verification,
        "load_verification_receipt",
        counted_load,
    )
    monkeypatch.setattr(
        lint_service,
        "load_verification_receipt",
        counted_load,
    )

    report = doctor_service.build_doctor_report()

    assert reads == 1
    assert report.verification_receipt["state"] == "absent"


def test_readme_documents_doctor_contract_and_all_exit_codes() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("### `doctor`", 1)[1].split("\n### ", 1)[0]

    assert "llm-wiki doctor" in section
    assert "llm-wiki-doctor/v1" in section
    assert "llm_wiki_cli.api.doctor" in section
    for exit_code, status in enumerate(("healthy", "degraded", "unhealthy", "absent")):
        assert f"| `{exit_code}` | `{status}` |" in section


def test_extractor_failure_does_not_misclassify_declared_knowledge_as_absent(
    tmp_path: Path,
) -> None:
    _committed_state(tmp_path)
    lint = lint_service.LintReport(
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
        strict=True,
        issues=[
            lint_service.LintIssue(
                category="extractor_failure",
                message="Python extraction failed.",
            )
        ],
    )

    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert report.status is doctor_service.DoctorStatus.UNHEALTHY
    assert report.exit_code == 2
    assert report.availability == {
        "state": "unsupported",
        "reason": "knowledge-evaluation-unavailable",
        "usable": False,
    }


def test_partial_knowledge_initialization_is_unhealthy_instead_of_absent(
    tmp_path: Path,
) -> None:
    view = build_knowledge_read_view(
        KnowledgeLoadResult(
            status=KnowledgeLoadState.ABSENT,
            surface={},
            knowledge=None,
            manifest_basis=None,
        ),
        snapshot_only=True,
    )
    lint = lint_service.LintReport(
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
        strict=True,
        knowledge_enabled=True,
        knowledge_view=view,
    )

    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert report.status is doctor_service.DoctorStatus.UNHEALTHY
    assert report.exit_code == 2
    assert report.availability["state"] == "unsupported"


def test_surface_only_partial_initialization_is_not_reported_absent(
    tmp_path: Path,
) -> None:
    (tmp_path / SURFACE_INDEX_FILENAME).write_text("{}\n", encoding="utf-8")
    lint = lint_service.LintReport(
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
        strict=True,
    )

    report = doctor_service.compose_doctor_report(
        lint,
        strict=False,
        wiki_dir=str(tmp_path),
        src_dir=str(tmp_path),
    )

    assert report.status is doctor_service.DoctorStatus.UNHEALTHY
    assert report.exit_code == 2
    assert report.availability["state"] == "unsupported"
