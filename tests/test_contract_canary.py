"""Bounded early producer evidence and placement before complete release suites."""

import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest
import yaml

from release import contract_canary as c
from release import preflight_contracts
from tests.test_preflight_runner import preparation_metadata as preparation_metadata

ROOT = Path(__file__).parents[1]


def evidence(selectors):
    nodes = [s if "[" in s else s + "[case]" for s in selectors]
    collection = {"collected": nodes, "selected": nodes[:], "deselected": []}
    return collection, nodes[:], {n: ET.Element("testcase") for n in nodes}


def test_every_bounded_contract_must_be_collected_started_and_passed():
    values = evidence(c.FIXTURES)
    assert c.validate_results(c.FIXTURES, *values) == {"collected": len(c.FIXTURES), "passed": len(c.FIXTURES), "skipped": 0}


@pytest.mark.parametrize("mutation", ["missing", "deselected", "duplicate", "unstarted", "extra", "failure", "error", "skipped"])
def test_partial_or_substituted_contract_results_never_pass(mutation):
    collection, started, cases = evidence(c.FIXTURES)
    first = collection["collected"][0]
    if mutation == "missing":
        for values in (collection["collected"], collection["selected"], started):
            values.remove(first)
        cases.pop(first)
    elif mutation == "deselected":
        collection["selected"].remove(first)
        collection["deselected"].append(first)
    elif mutation == "duplicate":
        collection["collected"].append(first)
    elif mutation == "unstarted":
        started.remove(first)
    elif mutation == "extra":
        extra = "tests/test_other.py::test_unrelated"
        collection["collected"].append(extra)
        collection["selected"].append(extra)
        started.append(extra)
        cases[extra] = ET.Element("testcase")
    else:
        ET.SubElement(cases[first], mutation)
    with pytest.raises((ValueError, RuntimeError)):
        c.validate_results(c.FIXTURES, collection, started, cases)


def test_canary_uses_actual_multiline_tracer_and_tampered_output_controls():
    assert "tests/test_core_shard_runner.py::test_pure_coverage_reader_preserves_raw_union_for_multiline_statement_hits" in c.COVERAGE
    assert "tests/test_core_shard_runner.py::test_multiline_coverage_reader_rejects_rehashed_xml_hits" in c.COVERAGE
    assert "tests/test_core_shard_runner.py::test_unexecuted_source_files_cannot_disappear_from_coverage_denominator" in c.COVERAGE


def test_multiline_fixture_cannot_silently_drop_its_native_tracer_variant():
    nodes = [s + "[case]" for s in c.COVERAGE[2:]]
    nodes += [c.COVERAGE[0] + "[continuation-events]"]
    nodes += [c.COVERAGE[1] + f"[continuation-events-{line}-{hits}]" for line, hits in ((10, 0), (15, 1))]
    collection = {"collected": nodes, "selected": nodes[:], "deselected": []}
    with pytest.raises(ValueError, match="real tracer"):
        c.validate_results(c.COVERAGE, collection, nodes[:], {n: ET.Element("testcase") for n in nodes})


def test_full_producers_join_all_early_contract_and_health_owners():
    jobs = yaml.safe_load((ROOT / ".github/workflows/release-qualification.yml").read_text())["jobs"]
    assert set(jobs["admission"]["needs"]) == {"readiness", "contract-canary", "windows-canary", "smoke-parity", "knowledge-maintenance"}
    assert jobs["action"]["needs"] == ["freeze", "readiness"]
    assert jobs["knowledge-maintenance"]["needs"] == ["freeze", "action", "readiness"]
    gate = jobs["admission"]["steps"][0]
    assert gate["env"]["CONTRACTS"] == "${{ needs.contract-canary.result }}"
    assert gate["env"]["MAINTENANCE"] == "${{ needs.knowledge-maintenance.result }}"
    assert 'test "${CONTRACTS}" = success' in gate["run"] and 'test "${MAINTENANCE}" = success' in gate["run"]
    for name in ("core", "core-ubuntu-plan", "core-windows-plan", "toolchains", "ubuntu-suites"):
        assert "admission" in jobs[name]["needs"]
        assert "needs.admission.result == 'success'" in jobs[name]["if"]
    for name in ("contract-canary", "windows-canary"):
        run = next(s for s in jobs[name]["steps"] if "contract_canary.py run" in s.get("run", ""))
        assert "continue-on-error" not in run
        assert "--identity incoming/source/identity.json" in run["run"]
        assert "--source-sha" in run["run"] and "--expected-prefix" in run["run"]


@pytest.mark.parametrize("gate", ["CONTRACTS", "MAINTENANCE"])
@pytest.mark.parametrize("state", ["failure", "skipped"])
def test_early_contract_or_health_failure_cannot_pass_admission(gate, state):
    jobs = yaml.safe_load((ROOT / ".github/workflows/release-qualification.yml").read_text())["jobs"]
    command = jobs["admission"]["steps"][0]["run"]
    environment = {**os.environ, **{name: "success" for name in ("READINESS", "CONTRACTS", "MAINTENANCE", "NATIVE", "PARITY")}}
    environment[gate] = state
    bash = shutil.which("bash")
    assert bash is not None
    assert subprocess.run([bash, "-e", "-o", "pipefail", "-c", command], env=environment).returncode != 0


def test_local_freeze_checks_installed_archive_before_full_host_core(tmp_path, preparation_metadata):
    from release import preflight_runner as r

    commands = r.stage_commands("freeze", ROOT, tmp_path, candidate_sha="a" * 40, version="4.2.0")
    names = [p.name for p in commands]
    assert names.index("freeze-source") < names.index("install-contract-source") < names.index("early-release-contracts")
    probe = commands[-1]
    assert probe.cwd == tmp_path / "contract-source" and probe.expected_prefix == tmp_path / "contract-environment"
    assert "[dev,tokens]" in commands[-2].argv[-1] and probe.timeout == 600
    assert "strict-host-core" not in names


def test_failed_worker_is_retained_before_any_later_profile(tmp_path, monkeypatch):
    root = tmp_path / "candidate"
    root.mkdir()
    args = SimpleNamespace(root=root, output=tmp_path / "evidence", archive=tmp_path / "source.tar",
                           identity=tmp_path / "identity.json", expected_prefix=tmp_path / "venv", source_sha="a" * 40,
                           helper_cache_dir=tmp_path / "selected-cache")
    monkeypatch.setattr(c, "verify_candidate", lambda args: {})
    seen = []

    def fail(command, cwd, environment, log, **kwargs):
        seen.append(command)
        assert environment["LLM_WIKI_CACHE_DIR"] == str(args.helper_cache_dir)
        assert environment.get("PYTEST_ADDOPTS") is None
        log.write_text("Original fixture failure")
        return {"exit_code": 1, "error": None}

    monkeypatch.setenv("PYTEST_ADDOPTS", "--deselect all")
    monkeypatch.setattr(c.runner, "invoke", fail)
    assert c.run(args) == 1 and len(seen) == 1
    report = json.loads((args.output / "result.json").read_text())
    assert report["status"] == "failed" and report["profiles"][0]["exit_code"] == 1
    assert (args.output / "fixtures-inherited.log").is_file()


def test_zero_worker_exit_without_collection_evidence_fails(tmp_path, monkeypatch):
    root = tmp_path / "candidate"
    root.mkdir()
    args = SimpleNamespace(root=root, output=tmp_path / "evidence", archive=tmp_path / "source.tar",
                           identity=tmp_path / "identity.json", expected_prefix=tmp_path / "venv", source_sha="a" * 40,
                           helper_cache_dir=None)
    monkeypatch.setattr(c, "verify_candidate", lambda args: {})
    monkeypatch.setattr(c.runner, "invoke", lambda *a, **kw: {"exit_code": 0, "error": None})
    assert c.run(args) == 1
    assert json.loads((args.output / "result.json").read_text())["profiles"][0]["error"]


def test_source_mutation_after_profiles_records_a_terminal_failure(tmp_path, monkeypatch):
    root = tmp_path / "candidate"
    root.mkdir()
    args = SimpleNamespace(root=root, output=tmp_path / "evidence", archive=tmp_path / "source.tar",
                           identity=tmp_path / "identity.json", expected_prefix=tmp_path / "venv", source_sha="a" * 40,
                           helper_cache_dir=None)
    calls = []

    def source(args):
        calls.append(args)
        if len(calls) == 2:
            raise ValueError("Frozen source changed")
        return {}

    monkeypatch.setattr(c, "verify_candidate", source)
    monkeypatch.setattr(c, "verify_profile", lambda *a: {"passed": 1})
    monkeypatch.setattr(c.runner, "invoke", lambda *a, **kw: {"exit_code": 0, "error": None})
    assert c.run(args) == 1
    result = json.loads((args.output / "result.json").read_text())
    assert result["status"] == "failed" and result["error"] == "Frozen source changed"


def test_contract_registry_contains_early_producer_and_current_dependencies():
    contract = preflight_contracts.qualification_contract(ROOT)
    rows = {x["id"]: x for x in contract["jobs"]}
    assert rows["contract-canary"]["owner"] == "release/contract_canary.py"
    assert rows["contract-canary"]["needs"] == ["freeze"]
    assert "knowledge-maintenance" in rows["admission"]["needs"]


def test_bounded_native_diagnostic_uses_reviewed_main_without_a_new_source_change():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release-contract-checks.yml").read_text())
    assert set(workflow.get("on", workflow.get(True))) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    for name, version in (("linux", "3.11.18"), ("windows", "3.13.17")):
        job = workflow["jobs"][name]
        setup = next(s for s in job["steps"] if str(s.get("uses", "")).startswith("actions/setup-python@"))
        assert setup["with"]["python-version"] == version
        binding = next(s["run"] for s in job["steps"] if s.get("name") == "Bind the diagnostic to reviewed main")
        assert 'test "${GITHUB_REF}" = refs/heads/main' in binding
        assert 'test "${WORKFLOW_SHA}" = "${CANDIDATE_SHA}"' in binding
        freeze = next(s["run"] for s in job["steps"] if s.get("id") == "freeze")
        assert "core_shard_runner.py freeze" in freeze
        check = next(s for s in job["steps"] if "contract_canary.py run" in s.get("run", ""))
        assert "--identity" in check["run"] and "--archive" in check["run"] and "continue-on-error" not in check
        checkout = next(s for s in job["steps"] if str(s.get("uses", "")).startswith("actions/checkout@"))
        assert checkout["with"]["persist-credentials"] is False
