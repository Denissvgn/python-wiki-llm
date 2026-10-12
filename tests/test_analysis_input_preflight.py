"""Census gaps are bounded, actionable data and never compatibility authority."""

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.commands import doctor_cmd
from llm_wiki_cli.services import analysis_capture as capture
from llm_wiki_cli.services import extraction_service, sync_analysis_cache
from llm_wiki_cli.services.knowledge_envelope import ProducerComponentInput


@pytest.fixture
def package(tmp_path):
    root = tmp_path / "package"
    (root / "services").mkdir(parents=True)
    (root / "core.py").write_text("VALUE=1\n")
    rules = capture.registry()
    rules.update(shared=["core.py"], providers={"python": ["core.py"]},
                 classified_python_files=["core.py"], classified_helper_files=[])
    (root / "services/analysis_contracts.json").write_text(json.dumps(rules))
    return root, rules, {"python": rules["executors"]["python"]}


def test_current_provider_has_ready_readonly_census():
    status = api.get_analysis_input_status()
    assert status["status"] == "ready" and status["bounds"]["total"] == 0
    assert status["scope"] == "installed-provider-inputs"


def test_unclassified_python_and_helper_are_exact_paths_without_execution(package):
    root, _, entries = package
    (root / "added.py").write_text('raise RuntimeError("must never execute")\n')
    helper = root / "extractors/custom_scripts/added.js"
    helper.parent.mkdir(parents=True)
    helper.write_text('throw Error("must never execute");')
    report = capture.analysis_input_status(package_root=root)
    assert report["reason"] == "unclassified-analysis-inputs"
    assert report["paths"] == [
        {"kind": "unclassified-python", "path": "added.py"},
        {"kind": "unclassified-helper", "path": "extractors/custom_scripts/added.js"},
    ]
    assert "classify deliberately" in report["next_action"]
    captured = capture.capture_analysis(entries, package_root=root)
    assert captured == {} and capture.analysis_diagnostics(captured) == report
    component = capture.attach(ProducerComponentInput("agent-wiki-cli", "1.0.0", configuration={}), captured)
    assert component.configuration is None and "configuration-basis-unknown" in component.limitations
    assert capture.analysis_diagnostics({"diagnostics": report}) is None


def test_diagnostic_is_immutable_but_public_copy_can_be_changed(package):
    root, _, entries = package
    (root / "added.py").write_text("pass\n")
    captured = capture.capture_analysis(entries, package_root=root)
    assert isinstance(captured, capture._CapturedAnalysis)
    with pytest.raises(TypeError):
        captured._diagnostics = None
    report = capture.analysis_diagnostics(captured)
    assert report is not None
    report["paths"].clear()
    fresh = capture.analysis_diagnostics(captured)
    assert fresh is not None and len(fresh["paths"]) == 1


def test_new_unclassified_input_cannot_hide_behind_operation_cache(package):
    root, _, entries = package

    @capture.capture_operation
    def operation():
        assert capture.capture_analysis(entries, package_root=root)
        (root / "added.py").write_text("pass\n")
        return capture.capture_analysis(entries, package_root=root)

    result = operation()
    diagnostic = capture.analysis_diagnostics(result)
    assert diagnostic is not None
    assert result == {} and diagnostic["bounds"]["total"] == 1


def test_missing_registered_input_cannot_hide_behind_operation_cache(package):
    root, _, entries = package

    @capture.capture_operation
    def operation():
        assert capture.capture_analysis(entries, package_root=root)
        (root / "core.py").unlink()
        return capture.capture_analysis(entries, package_root=root)

    result = operation()
    diagnostic = capture.analysis_diagnostics(result)
    assert result == {} and diagnostic is not None
    assert diagnostic["paths"] == [{"kind": "missing-or-unsafe-producer-input", "path": "core.py"}]


def test_classified_consumer_preserves_identity_observation_change_invalidates_it(package):
    root, rules, entries = package
    original = capture.capture_analysis(entries, package_root=root)
    (root / "consumer.py").write_text("VALUE=2\n")
    rules["classified_python_files"].append("consumer.py")
    (root / "services/analysis_contracts.json").write_text(json.dumps(rules))
    assert capture.capture_analysis(entries, package_root=root) == original
    (root / "core.py").write_text("VALUE=3\n")
    changed = capture.capture_analysis(entries, package_root=root)
    assert changed["agent-wiki-cli"]["implementation"] != original["agent-wiki-cli"]["implementation"]
    assert changed["llm-wiki/extractor/python"]["implementation"] != original["llm-wiki/extractor/python"]["implementation"]


@pytest.mark.parametrize("state", ["missing", "symlink", "registry"])
def test_missing_or_unknown_inputs_are_fail_closed_and_explained(package, state):
    root, _, entries = package
    if state == "registry":
        (root / "services/analysis_contracts.json").write_text("{}")
    else:
        (root / "core.py").unlink()
        if state == "symlink":
            (root / "core.py").symlink_to(root / "outside.py")
    result = capture.capture_analysis(entries, package_root=root)
    diagnostic = capture.analysis_diagnostics(result)
    assert diagnostic is not None
    assert result == {} and diagnostic["status"] == "unavailable"
    assert capture.analysis_input_status(package_root=root)["status"] == "unavailable"


def test_path_and_serialized_byte_limits_keep_truthful_omissions(package):
    root, _, _ = package
    for i in range(120):
        directory = root / (("保持" * 30) + str(i))
        directory.mkdir()
        (directory / ("module" + str(i) + ".py")).write_text("pass\n")
    status = capture.analysis_input_status(package_root=root, limit=100)
    assert status["bounds"]["total"] == 120
    assert status["bounds"]["returned"] == len(status["paths"]) < 100
    assert status["bounds"]["omitted"] == 120 - len(status["paths"])
    assert status["bounds"]["truncated"] is True
    assert len(json.dumps(status, ensure_ascii=True, sort_keys=True).encode()) <= capture.INPUT_STATUS_MAX_BYTES
    capture.validate_analysis_diagnostics(status)


@pytest.mark.parametrize("limit", [True, 0, 101, "20"])
def test_invalid_census_limit_is_rejected(limit):
    with pytest.raises(api.InvalidRequestError):
        api.get_analysis_input_status(limit=limit)


def test_cli_preflight_bypasses_project_inventory_and_has_failure_exit(package, monkeypatch, capsys):
    root, _, _ = package
    (root / "added.py").write_text("pass\n")
    monkeypatch.setattr(api, "get_analysis_input_status", lambda: capture.analysis_input_status(package_root=root))
    monkeypatch.setattr(doctor_cmd, "build_doctor_report", lambda *a, **k: pytest.fail("scanned project source"))
    with pytest.raises(SystemExit) as error:
        doctor_cmd.run(SimpleNamespace(analysis_inputs=True, report_schema="auto", format="json"))
    assert error.value.code == 2
    assert json.loads(capsys.readouterr().out)["paths"][0]["path"] == "added.py"


def test_inventory_and_task_callers_receive_diagnostic_without_trusted_components(package, tmp_path, monkeypatch):
    root, _, entries = package
    (root / "added.py").write_text("pass\n")
    captured = capture.capture_analysis(entries, package_root=root)
    monkeypatch.chdir(tmp_path)
    Path("app.py").write_text("def cap(value: int):\n    return value\n")
    original = capture.capture_analysis
    monkeypatch.setattr(capture, "capture_analysis", lambda *a, **k: captured)
    result = extraction_service.get_inventory_result(extraction_service.InventoryRequest(src_dir="."))
    diagnostic = result.analysis_input_status
    assert diagnostic is not None and diagnostic["paths"][0]["path"] == "added.py"
    assert result.analysis_components == {}
    request = {"schema_version": "llm-wiki-task-request/v2", "requirements": [
        {"id": "cap", "facet": "source-contract", "selector": "app.py:cap"}],
        "options": {"knowledge_mode": "off", "budget_tokens": 32000}}
    task = api.build_task_context(request)
    assert task.ok
    diagnostic = task.to_payload()["work"]["analysis_input_status"]
    assert diagnostic["reason"] == "unclassified-analysis-inputs"
    api.validate_task_context(task.rendered, request)
    monkeypatch.setattr(capture, "capture_analysis", original)


def test_sync_cache_miss_has_bounded_actionable_diagnostic(package, tmp_path, monkeypatch, capsys):
    root, _, entries = package
    (root / "added.py").write_text("pass\n")
    captured = capture.capture_analysis(entries, package_root=root)
    monkeypatch.setattr(sync_analysis_cache, "capture_analysis", lambda *a, **k: captured)
    monkeypatch.setattr(sync_analysis_cache, "implementation_hash", lambda: "sha256:" + "0" * 64)
    options = SimpleNamespace(initialize_surfaces=False, knowledge_format=None, wiki_dir=tmp_path,
                              helper_cache_dir=None)
    manifest = SimpleNamespace(maintenance_state=None)
    snapshot = SimpleNamespace(root=tmp_path, files_by_language={"python": ["app.py"]})
    assert sync_analysis_cache.input_key(options, snapshot, manifest, {}) is None
    line = capsys.readouterr().out.strip()
    assert line.startswith("Analysis input preflight: ")
    value = json.loads(line.split(": ", 1)[1])
    assert value["paths"][0]["path"] == "added.py"


def test_diagnostics_cannot_claim_ready_or_forge_bounds(package):
    root, _, _ = package
    (root / "added.py").write_text("pass\n")
    report = capture.analysis_input_status(package_root=root)
    capture.validate_analysis_diagnostics(report)
    for change in ("ready", "counts", "scope", "extra"):
        value = deepcopy(report)
        if change == "ready":
            value["status"] = "ready"
        elif change == "counts":
            value["bounds"]["omitted"] = 100
        elif change == "scope":
            value["scope"] = "verified-analysis"
        else:
            value["authority"] = "trusted"
        with pytest.raises(ValueError):
            capture.validate_analysis_diagnostics(value)
