"""Precise presentation must not alter stored comparison/hint contracts."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from llm_wiki_cli.services import analysis_compatibility as ac, analysis_capture
from llm_wiki_cli.services import ci_report, doctor_service, lint_service
from llm_wiki_cli.services.health_summary import detailed_health_rows
from llm_wiki_cli.services.knowledge_observability import knowledge_freshness_hint
from tests.test_analysis_compatibility import component
from tests.test_health_details import _ci
from tests.test_knowledge_health_refresh import recorded_project as recorded_project, _command, _sync


def test_diagnostics_do_not_expand_the_public_service_exports():
    from llm_wiki_cli.services import knowledge_observability

    assert "freshness_analysis_diagnostic" not in knowledge_observability.__all__


@pytest.mark.parametrize("options, expected", [
    ({"runtime": "c"}, ("runtime",)),
    ({"implementation": "c"}, ("implementation",)),
    ({"configuration": {"schema": "v2"}}, ("configuration",)),
    ({"runtime": "c", "implementation": "d", "configuration": {"schema": "v2"}},
     ("implementation", "configuration", "runtime")),
])
def test_diagnosis_retains_all_real_dimensions_without_changing_eligibility(options, expected):
    before, after = component(), component(**options)
    assert before.configuration_hash != after.configuration_hash
    result = ac.analysis_diagnostic({before.component_id: before}, {after.component_id: after})
    assert result["changes"] == {"agent-wiki-cli": expected}
    assert result["unavailable"] == ()
    assert all(name in result["description"] for name in expected)
    if expected == ("runtime",):
        assert "configuration changed" not in result["description"].lower()
        assert "target host" in result["hint"]
        assert "restore" not in result["hint"].lower()
    for policy in ("auto", "analysis-v1", "exact-v1"):
        assert ac.compare_components(before, after, policy=policy) == "configuration"


@pytest.mark.parametrize("damage", ["missing", "identity", "binding", "contract"])
def test_unavailable_comparisons_do_not_guess_a_dimension_or_relax_validation(damage):
    before = component()
    record = deepcopy(ac.component_record(before))
    if damage == "missing":
        after = replace(before, extensions={})
    elif damage == "binding":
        after = replace(before, configuration_hash="sha256:" + "0" * 64)
    else:
        record["runtime" if damage == "identity" else "contract"] = (
            "sha256:" + "c" * 64 if damage == "identity" else "unsupported-observations/v99"
        )
        if damage == "contract":
            record["identity"] = ac.digest({k: v for k, v in record.items() if k not in {"identity", "provenance"}})
        after = replace(before, extensions={ac.EXTENSION: record})
        if damage == "contract":
            after = replace(after, configuration_hash=ac.configuration_commitment(record))
    result = ac.analysis_diagnostic({before.component_id: before}, {after.component_id: after})
    assert result["changes"] == {}
    assert result["unavailable"] == ("agent-wiki-cli",)
    assert "unavailable" in result["description"].lower()
    assert "before" in result["hint"].lower()
    if damage != "missing":
        with pytest.raises(ValueError, match={"identity": "identity", "binding": "bound",
                                              "contract": "unsupported observation contract"}[damage]):
            ac.compare_components(before, after)
    else:
        assert ac.compare_components(before, after) == "configuration"


def test_no_captured_components_are_unavailable_rather_than_a_match():
    result = ac.analysis_diagnostic({}, {})
    assert result is not None and result["changes"] == {}
    assert "unavailable" in result["description"].lower()


def test_version_and_display_provenance_do_not_invent_analysis_drift(monkeypatch):
    before, after = component(), component("1.0.1")
    record = deepcopy(ac.component_record(after))
    record["provenance"]["platform"] = "different-display-provenance"
    after = replace(after, extensions={ac.EXTENSION: record})
    from pathlib import Path

    def refuse(*args, **kwargs):
        raise AssertionError("diagnostics performed filesystem I/O")

    monkeypatch.setattr(Path, "read_bytes", refuse)
    monkeypatch.setattr(Path, "read_text", refuse)
    assert ac.analysis_diagnostic({before.component_id: before}, {after.component_id: after}) is None
    assert ac.compare_components(before, after) is None
    assert ac.compare_components(before, after, policy="exact-v1") == "version"


def test_multiple_components_and_unavailable_detail_are_not_lost():
    before, runtime = component(), component(runtime="c")

    def python_component(value):
        record = deepcopy(ac.component_record(value))
        record["component"] = "llm-wiki/extractor/python"
        record["identity"] = ac.digest({k: v for k, v in record.items() if k not in {"identity", "provenance"}})
        return replace(value, component_id=record["component"],
                       configuration_hash=ac.configuration_commitment(record), extensions={ac.EXTENSION: record})

    python = python_component(before)
    configured = python_component(component(configuration={"schema": "v2"}))
    left = {python.component_id: python, before.component_id: before}
    right = {runtime.component_id: runtime, configured.component_id: configured}
    result = ac.analysis_diagnostic(left, right)
    assert list(result["changes"]) == ["agent-wiki-cli", "llm-wiki/extractor/python"]
    assert result["changes"] == {"agent-wiki-cli": ("runtime",),
                                  "llm-wiki/extractor/python": ("configuration",)}
    del right[python.component_id]
    result = ac.analysis_diagnostic(left, right)
    assert result["changes"] == {"agent-wiki-cli": ("runtime",)}
    assert result["unavailable"] == ("llm-wiki/extractor/python",)


@pytest.mark.parametrize("recorded_project", ["current"], indirect=True)
@pytest.mark.parametrize("dimensions", [("runtime",), ("implementation",), ("configuration",),
                                      ("implementation", "configuration", "runtime")])
def test_live_reports_explain_the_same_commitments_with_legacy_reasons(recorded_project, monkeypatch, capsys, dimensions):
    original = analysis_capture.capture_analysis

    def changed(*args, **kwargs):
        captured = original(*args, **kwargs)
        values = {key: dict(value) for key, value in captured.items()}
        # Configuration is captured by the component issuer, not the raw runtime owner.
        for dimension in set(dimensions) - {"configuration"}:
            values["agent-wiki-cli"][dimension] = "sha256:" + "f" * 64
        return analysis_capture._issued(values)

    monkeypatch.setattr(analysis_capture, "capture_analysis", changed)
    if "configuration" in dimensions:
        attach = analysis_capture.attach

        def configured(component, captured):
            if component.component_id == "agent-wiki-cli":
                component = replace(component, configuration={**(component.configuration or {}), "diagnostic-control": True})
            return attach(component, captured)

        monkeypatch.setattr(analysis_capture, "attach", configured)
    report = lint_service.build_report("wiki", "source", strict=True, knowledge_drift_report=True,
                                      include_plugins=False, include_health_details=True)
    findings = [d for d in report.diagnostics if d.category == "knowledge_freshness"]
    assert findings
    assert {d.reason_code for d in findings} == {"producer-tool-configuration-changed"}
    for finding in findings:
        assert all(name in finding.message for name in dimensions)
        assert "producer tool configuration changed" not in finding.message.lower()
        if dimensions == ("runtime",):
            assert "target host" in finding.hint
            assert "restore" not in finding.hint.lower()
    # Canonical compact projections retain exactly the historical hint vocabulary.
    assert knowledge_freshness_hint("basis-incompatible", findings[0].reason_code) == (
        "Restore the producer configuration used at sync, or re-run sync with "
        "the current producer configuration."
    )
    ci = _ci(report, schema="v4")
    ci_report.validate_ci_check_payload(ci, cli_exit=0)
    doctor_report = doctor_service.compose_doctor_report(report, strict=True, wiki_dir="wiki", src_dir="source")
    doctor = doctor_report.to_payload()
    ci_report.validate_doctor_payload(doctor, expected_strict=True)
    assert doctor["status"] == "unhealthy"
    assert ci["ok"] is True and ci["knowledge_health"]["status"] == "degraded"
    rows = dict(detailed_health_rows(json.loads(json.dumps(doctor))))
    assert all(name in rows["Analysis dimensions"] for name in dimensions)
    assert findings[0].hint == rows["Next action"]
    assert findings[0].message in lint_service.render_markdown(report)
    assert "Analysis dimensions" in doctor_service.render_doctor_text(doctor_report)
    from llm_wiki_cli import api
    from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService

    service = DocumentationGraphQueryService({}, knowledge_view=report.knowledge_view)
    explained = api.explain_evidence(findings[0].target, service=service)["evidence"]["freshness"]
    assert set(explained) == {"state", "reason", "description", "live_comparison_performed",
                              "recorded_basis", "live_basis", "hint"}
    assert explained["hint"] == findings[0].hint
    assert all(name in explained["description"] for name in dimensions)
    # Compact output remains usable by frozen projection consumers.
    assert service._compact_knowledge_freshness(findings[0].target)["hint"] == knowledge_freshness_hint(
        "basis-incompatible", findings[0].reason_code,
    )
    from llm_wiki_cli.services import mcp_server

    monkeypatch.setattr(mcp_server, "build_documentation_query_service", lambda *a, **kw: service)
    mcp = mcp_server.McpWikiService(src_dir="source", wiki_dir="wiki").explain_evidence(findings[0].target)
    assert mcp["evidence"]["freshness"] == explained
    from llm_wiki_cli.services.knowledge_projection import _project_freshness

    concept = next(c for c in report.knowledge_view.knowledge.concepts if c.locator == findings[0].target)
    projected = _project_freshness(concept, report.knowledge_view)
    assert set(projected) == {"state", "reason", "evaluated", "live_comparison_performed", "hint"}
    assert projected["hint"] == knowledge_freshness_hint("basis-incompatible", findings[0].reason_code)
    if dimensions == ("runtime",):
        capsys.readouterr()
        with pytest.raises(SystemExit) as exc:
            _command(["doctor", "--strict", "--format", "json", "--src-dir", "source", "--wiki-dir", "wiki"])
        assert exc.value.code == 2
        cli_report = json.loads(capsys.readouterr().out)
        assert dict(detailed_health_rows(cli_report))["Next action"] == findings[0].hint
    assert "Analysis dimensions" in ci_report.render_ci_summary(
        ci, result="PASS", cli_exit=0, json_state="available (validated llm-wiki-ci-check/v4)",
        markdown_state="available", tree_state="clean", status_records=[], status_count=0,
        status_limit=10, max_lines=40, max_bytes=8192,
    ).decode()
    if dimensions == ("runtime",):
        historical = deepcopy(ci)
        old_hint = knowledge_freshness_hint("basis-incompatible", findings[0].reason_code)
        for finding in historical["diagnostics"]:
            if finding["category"] == "knowledge_freshness":
                finding["hint"] = old_hint
        before = deepcopy(historical)
        ci_report.validate_ci_check_payload(historical, cli_exit=0)
        rendered = "\n".join(ci_report._health_detail_lines(historical))
        assert old_hint not in rendered
        assert "target host" in rendered
        assert historical == before


@pytest.mark.parametrize("recorded_project", ["current"], indirect=True)
def test_historical_runtime_guidance_is_not_replaced_by_an_unrelated_source_remedy(recorded_project, monkeypatch):
    source, _, _, _ = recorded_project
    (source / "action.yml").write_text(
        'name: Fixture\ndescription: Static action\nruns:\n  using: composite\n'
        '  steps:\n    - shell: bash\n      run: echo fixture\n', encoding="utf-8",
    )
    _sync()
    original = analysis_capture.capture_analysis

    def changed(*args, **kwargs):
        captured = original(*args, **kwargs)
        values = {key: dict(value) for key, value in captured.items()}
        values["llm-wiki/extractor/infrastructure"]["runtime"] = "sha256:" + "f" * 64
        return analysis_capture._issued(values)

    monkeypatch.setattr(analysis_capture, "capture_analysis", changed)
    model = source / "models.py"
    model.write_text(model.read_text() + "    enabled: bool\n", encoding="utf-8")
    report = lint_service.build_report("wiki", "source", strict=True, knowledge_drift_report=True,
                                      include_plugins=False, include_health_details=True)
    ci = _ci(report, schema="v4")
    outcomes = ci["knowledge_health"]["health_details"]["coverage"]["outcomes"]
    assert outcomes["source-changed"] > 0 and outcomes["basis-incompatible"] > 0
    assert "Review source changes" in dict(detailed_health_rows(ci["knowledge_health"]))["Next action"]
    for finding in ci["diagnostics"]:
        if finding.get("reason_code") == "extractor-configuration-changed":
            finding["hint"] = knowledge_freshness_hint("basis-incompatible", finding["reason_code"])
    ci_report.validate_ci_check_payload(ci, cli_exit=0 if report.passed else 1)
    rendered = "\n".join(ci_report._health_detail_lines(ci))
    assert "target host" in rendered
    assert "Restore the extractor configuration" not in rendered
