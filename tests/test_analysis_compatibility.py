"""Compatibility changes comparison eligibility, never exact provenance."""

from dataclasses import replace
from copy import deepcopy
from typing import Any, cast
import json
from pathlib import Path
import platform
import sys

import pytest

from llm_wiki_cli.services import analysis_compatibility as ac, analysis_capture as capture
from llm_wiki_cli.services import ci_report, doctor_service, lint_service
from llm_wiki_cli.services.knowledge_envelope import ProducerComponentInput, build_producer_record
from tests.test_knowledge_health_refresh import recorded_project as recorded_project, _version


def component(version="1.0.0", implementation="a", runtime="b", configuration=None):
    base = ProducerComponentInput("agent-wiki-cli", version, configuration=configuration or {"schema": "v1"})
    captured = {base.component_id: {"implementation": "sha256:" + implementation * 64,
        "runtime": "sha256:" + runtime * 64,
        "provenance": {"python": "3.14.0", "platform": "darwin/arm64", "helper": ""}}}
    return build_producer_record(tool=capture.attach(base, capture._issued(captured))).tool


def test_version_only_change_preserves_analysis_and_exact_provenance():
    before, after = component(), component("1.0.1")
    assert before.version != after.version
    left, right = ac.component_record(before), ac.component_record(after)
    assert left is not None and right is not None
    assert left["identity"] == right["identity"]
    assert ac.compare_components(before, after) is None
    assert ac.compare_components(before, after, policy="exact-v1") == "version"
    assert ac.compare_components(before, after, plugins=True) == "version"


@pytest.mark.parametrize("change", ["implementation", "runtime", "configuration"])
@pytest.mark.parametrize("policy", ["auto", "exact-v1", "analysis-v1"])
def test_same_version_cannot_hide_changed_analysis(change, policy):
    options: dict[str, Any] = {change: {"schema": "v2"} if change == "configuration" else "c"}
    assert ac.compare_components(component(), component(**options), policy=policy) == "configuration"


def test_missing_and_tampered_records_do_not_claim_compatibility():
    current = component()
    legacy = replace(current, extensions={})
    assert ac.compare_components(current, legacy) == "configuration"
    assert ac.compare_components(legacy, legacy, policy="analysis-v1") == "configuration"
    record = deepcopy(ac.component_record(current))
    assert record is not None
    record["implementation"] = "sha256:" + "f" * 64
    with pytest.raises(ValueError, match="identity"):
        ac.component_record(replace(current, extensions={ac.EXTENSION: record}))
    record = deepcopy(ac.component_record(current))
    assert record is not None
    record["component"] = "other/component"
    with pytest.raises(ValueError, match="another component"):
        ac.component_record(replace(current, extensions={ac.EXTENSION: record}))


def test_capture_rejects_unclassified_or_missing_inputs(tmp_path):
    package = tmp_path / "package"
    (package / "services").mkdir(parents=True)
    (package / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    rules = capture.registry()
    rules.update(shared=["core.py"], providers={"python": ["core.py"]}, classified_python_files=["core.py"])
    (package / "services/analysis_contracts.json").write_text(json.dumps(rules), encoding="utf-8")
    registry = {"python": rules["executors"]["python"]}
    assert capture.capture_analysis(registry, package_root=package)
    (package / "unclassified.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert capture.capture_analysis(registry, package_root=package) == {}
    (package / "unclassified.py").unlink()
    (package / "core.py").unlink()
    assert capture.capture_analysis(registry, package_root=package) == {}


def test_custom_executor_does_not_receive_builtin_identity():
    result = capture.capture_analysis({"python": "custom:Extractor"}, languages={"python"})
    assert "llm-wiki/extractor/python" not in result


def test_pure_comparison_does_not_read_files(monkeypatch):
    before, after = component(), component("1.0.1")
    def refuse(*args, **kwargs):
        raise AssertionError("comparison performed filesystem I/O")
    monkeypatch.setattr(Path, "read_bytes", refuse)
    monkeypatch.setattr(Path, "read_text", refuse)
    assert ac.compare_components(before, after) is None


def test_inventory_cache_reuses_version_only_changes_but_not_custom_providers(tmp_path, monkeypatch):
    from llm_wiki_cli.config import EXTRACTOR_REGISTRY
    from llm_wiki_cli.services import inventory_cache
    from llm_wiki_cli.services.source_snapshot import build_source_snapshot

    monkeypatch.chdir(tmp_path)
    (tmp_path / "model.py").write_bytes(b"class User: pass\n")
    snapshot = build_source_snapshot(tmp_path)
    def key(custom=False):
        return inventory_cache.build_inventory_cache_key(tmp_path, snapshot, deep=True, include_empty=False,
            extractor_registry={"python": "custom:Extractor" if custom else EXTRACTOR_REGISTRY["python"]})
    before, custom = key(), key(True)
    monkeypatch.setattr(inventory_cache, "LLM_WIKI_VERSION", "metadata-only-change")
    assert key() == before
    assert key(True) != custom


def test_extraction_captures_implementation_once_per_operation(tmp_path, monkeypatch):
    from llm_wiki_cli.services.extraction_service import get_inventory_result
    from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions

    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    (source / "model.py").write_bytes(b"class User: pass\n")
    calls = []
    original = capture.implementation_hash
    def counted(root, paths):
        calls.append(tuple(paths))
        return original(root, paths)
    monkeypatch.setattr(capture, "implementation_hash", counted)
    result = get_inventory_result(str(source), deep=True, include_plugins=False,
        cache_options=InventoryCacheOptions(enabled=True, cache_dir=str(tmp_path / "cache")))
    assert result.analysis_components
    assert len(calls) == len(set(calls)) == 3  # Shared core, Python, infrastructure.


def test_reserved_metadata_cannot_override_the_owned_capture():
    forged = ProducerComponentInput("agent-wiki-cli", "1.0", configuration={},
                                   extensions={ac.EXTENSION: ac.component_record(component())})
    with pytest.raises(ValueError, match="owned"):
        capture.attach(forged, {})


@pytest.mark.parametrize("recorded_project", ["current"], indirect=True)
def test_migrated_wiki_automatically_uses_v4_and_cross_version_comparison(recorded_project, monkeypatch):
    _version(monkeypatch, "9.8.7")
    report = lint_service.build_report("wiki", "source", strict=True, knowledge_drift_report=True,
                                      include_plugins=False, include_health_details=True)
    doctor = doctor_service.compose_doctor_report(report, strict=True, wiki_dir="wiki", src_dir="source").to_payload()
    assert doctor["schema_version"] == "llm-wiki-doctor/v4"
    assert doctor["status"] == "healthy"
    details = cast(dict[str, Any], doctor["health_details"])
    assert details["basis"]["recorded"]["tool"]["version"] == "9.8.6"
    assert details["basis"]["live"]["tool"]["version"] == "9.8.7"
    ci_report.validate_doctor_payload(doctor, expected_strict=True)
    with pytest.raises(ValueError, match="exact-v1"):
        doctor_service.compose_doctor_report(report, strict=True, wiki_dir="wiki", src_dir="source").to_payload(report_schema="v3")
    legacy = doctor_service.build_doctor_report("wiki", "source", strict=True, report_schema="v3", comparison_policy="exact-v1").to_payload(report_schema="v3")
    assert legacy["status"] == "unhealthy"
    ci_report.validate_doctor_payload(legacy, expected_strict=True)


@pytest.mark.parametrize("recorded_project", ["current"], indirect=True)
def test_source_change_still_fails_after_compatible_version_change(recorded_project, monkeypatch):
    source, _, _, _ = recorded_project
    _version(monkeypatch, "9.8.7")
    path = source / "models.py"
    path.write_text(path.read_text() + "    active: bool\n", encoding="utf-8")
    report = doctor_service.build_doctor_report("wiki", "source", strict=True).to_payload()
    assert report["status"] == "unhealthy"
    assert cast(dict, report["drift"])["confirmed_stale"] > 0


def test_native_portable_observation_contract(tmp_path, pytestconfig):
    from llm_wiki_cli import __version__
    from llm_wiki_cli.config import EXTRACTOR_REGISTRY
    from llm_wiki_cli.services.extraction_service import get_inventory_result
    from llm_wiki_cli.services.knowledge_evidence import normalize_module_observation

    fixture_path = Path(__file__).with_name("fixtures") / "analysis-portability.json"
    fixture = json.loads(fixture_path.read_text("utf-8"))
    for name, content in fixture["sources"].items():
        (tmp_path / name).write_bytes(content.encode("utf-8"))
    result = get_inventory_result(str(tmp_path), deep=True, include_plugins=False)
    observed = {name: normalize_module_observation(value) for name, value in result.inventory.items()}
    assert observed == fixture["observations"]
    assert result.analysis_components is not None
    assert set(result.analysis_components) >= {"agent-wiki-cli", "llm-wiki/extractor/python"}
    assert result.extractor_registry["python"] == EXTRACTOR_REGISTRY["python"]
    evidence = {
        "schema_version": "llm-wiki-analysis-conformance/v1", "status": "pass",
        "python": list(sys.version_info[:2]), "platform": sys.platform,
        "machine": platform.machine(), "producer_version": __version__,
        "fixture_sha256": __import__("hashlib").sha256(fixture_path.read_bytes()).hexdigest(),
        "observations": observed, "components": result.analysis_components,
    }
    xml = getattr(pytestconfig.option, "xmlpath", None)
    if xml:
        path = Path(pytestconfig.invocation_params.dir) / xml
        output = path.with_name(path.stem + "-analysis.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")



def test_plain_caller_metadata_is_not_an_authorized_capture():
    value = ProducerComponentInput("agent-wiki-cli", "1.0", configuration={})
    with pytest.raises(ValueError, match="owner-issued"):
        capture.attach(value, {})
    result = capture.capture_analysis({})
    with pytest.raises(TypeError, match="immutable"):
        result["agent-wiki-cli"]["runtime"] = "sha256:" + "0" * 64



def test_isolated_comparison_versions_match_public_protocol_registry():
    from llm_wiki_cli.services import contracts
    assert ac.SCHEMA == contracts.ANALYSIS_COMPATIBILITY_SCHEMA_VERSION
    assert ac.COMPARISON_SCHEMA == contracts.ANALYSIS_COMPARISON_SCHEMA_VERSION
    assert ac.SCHEMA in contracts.PROTOCOL_VERSIONS
    assert ac.COMPARISON_SCHEMA in contracts.PROTOCOL_VERSIONS
