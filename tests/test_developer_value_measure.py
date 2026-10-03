"""Provider provenance, actual cold/warm measurements, and evidence controls."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import pytest

from tests.developer_value import measure, runtime

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def provider(tmp_path):
    root = tmp_path / "provider"
    package = root / "src/llm_wiki_cli"
    shutil.copytree(ROOT / "src/llm_wiki_cli", package,
                    ignore=shutil.ignore_patterns("__pycache__", "target", "node_modules", "*.pyc"))
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in package.rglob("*") if p.is_file()}
    (root / ".developer-value-provider.json").write_text(json.dumps({
        "schema_version": "developer-value-provider-snapshot/v1", "source_revision": "owned-test-snapshot",
        "files": files}))
    return root


def fresh(script: str, *args: str):
    bootstrap = f"import sys\nfrom pathlib import Path\nsys.path.insert(0,{str(ROOT)!r})\n"
    result = subprocess.run([sys.executable, "-I", "-c", bootstrap + script, *args],
                            cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_retained_source_is_imported_instead_of_editable_checkout(provider):
    result = fresh(
        "from tests.developer_value.runtime import load_provider,provider_identity\nimport json\n"
        "api=load_provider(Path(sys.argv[1]))\nprint(json.dumps(provider_identity()))\n", str(provider))
    assert Path(result["module"]).is_relative_to(provider / "src")
    assert result["snapshot"]["source_revision"] == "owned-test-snapshot"
    assert result["model_execution_established"] is False


def test_different_already_imported_provider_cannot_be_silently_replaced(provider):
    runtime.load_provider(ROOT)
    with pytest.raises(ValueError, match="already imported"):
        runtime.load_provider(provider)


@pytest.mark.parametrize("mutation", ["changed", "added", "missing"])
def test_snapshot_changes_are_rejected_before_provider_execution(provider, mutation):
    api = provider / "src/llm_wiki_cli/api.py"
    if mutation == "changed":
        api.write_text('raise RuntimeError("mutated source must not execute")\n')
    elif mutation == "added":
        (api.parent / "unexpected.py").write_text('raise RuntimeError("uncommitted extra source")\n')
    else:
        (api.parent / "config.py").unlink()
    result = fresh(
        "from tests.developer_value.runtime import load_provider\nimport json\n"
        "try:\n load_provider(Path(sys.argv[1]))\nexcept (ValueError,OSError) as e:\n"
        " print(json.dumps({'rejected':True,'type':type(e).__name__}))\n"
        "else:\n print(json.dumps({'rejected':False}))\n", str(provider))
    assert result["rejected"]
    assert result["type"] != "RuntimeError"


def test_workspace_preparation_preserves_unrelated_existing_content(tmp_path):
    runtime.load_provider(ROOT)
    marker = tmp_path / "owner.txt"
    marker.write_text("User content must survive.\n")
    with pytest.raises(ValueError, match="new or empty"):
        runtime.prepare_workspace("library", tmp_path, tiny=True)
    assert marker.read_text() == "User content must survive.\n"
    assert not (tmp_path / "src").exists()


def test_storage_modes_and_source_only_requests_are_explicit():
    assert measure.request("tiny", "context-v1")["schema_version"] == "llm-wiki-task-request/v1"
    native = measure.request("tiny", "context-v2")
    assert "options" not in native
    compact = measure.request("tiny", "context-v2-compact")
    assert compact["storage_options"] == {"selection": "required-facets-v1", "receipt": "compact-v1"}
    assert measure.request("tiny", "context-source-only")["options"]["knowledge_mode"] == "off"


def test_logical_signatures_ignore_transport_identity_but_preserve_contract_and_gaps():
    output = {"ok": True, "state": "incomplete", "coverage": [{"requirement_id": "contract", "state": "present",
              "satisfied": True, "reason": "observed", "fact_ids": ["old"]}],
              "facts": [{"facet": "source-contract", "selector": "policy.py:Batch.cap", "state": "present",
                         "observation": {"default": "3"}, "qualification": {"behavior": "not-evaluated"},
                         "fact_id": "old"}]}
    altered = deepcopy(output)
    altered["facts"][0]["fact_id"] = "new"
    altered["coverage"][0]["fact_ids"] = ["new"]
    signature = measure.logical_signature("context-v2", output, [])
    assert measure.logical_signature("context-v2", altered, []) == signature
    altered["facts"][0]["observation"]["default"] = "4"
    assert measure.logical_signature("context-v2", altered, []) != signature
    altered = deepcopy(output)
    altered["coverage"][0]["state"] = "omitted"
    altered["coverage"][0]["satisfied"] = False
    assert measure.logical_signature("context-v2", altered, []) != signature


def test_timed_read_and_mutation_restore_equivalent_inputs(provider, tmp_path):
    output = tmp_path / "measurements"
    result = fresh(
        "from tests.developer_value.measure import run\nimport json\n"
        "r=run(Path(sys.argv[1]),Path(sys.argv[2]),selected_projects=['tiny'],"
        "selected_lanes=['context-v1','context-v2','changed-sync'],warm=1)\n"
        "print(json.dumps(r))\n", str(provider), str(output))
    assert result["total_samples"] == result["completed_calls"] == 6
    assert result["all_logical_outputs_repeatable"]
    assert result["model_execution_established"] is result["field_evidence_established"] is False
    plan = json.loads((output / "plan.json").read_text())
    assert plan["cold_repetitions"] == plan["warm_repetitions"] == 1
    assert plan["disk_cache"] == "uncontrolled"
    assert plan["provider"]["module"].startswith(str(provider))
    for report in result["workloads"]:
        directory = output / f"tiny-{report['lane']}"
        first = json.loads((directory / "sample-0.json").read_text())
        second = json.loads((directory / "sample-1.json").read_text())
        assert first["condition"] == "first-call-fresh-worker"
        assert second["condition"] == "warm-worker"
        assert first["wall_ns"] > 0 and first["cpu_ns"] > 0
        if report["lane"].startswith("context-"):
            assert not first["wiki_changed_paths"] and not second["wiki_changed_paths"]
            assert first["result"]["canonical_validated"]
            assert any(not c["satisfied"] for c in first["result"]["coverage"])
        else:
            assert first["workspace_copy_ns"] > 0 and second["workspace_copy_ns"] > 0
            assert first["result"]["exit_code"] == second["result"]["exit_code"] == 0
            assert first["wiki_changed_paths"] == second["wiki_changed_paths"]
    resumed = fresh(
        "from tests.developer_value.measure import run\nimport json\n"
        "r=run(Path(sys.argv[1]),Path(sys.argv[2]),selected_projects=['tiny'],"
        "selected_lanes=['context-v1','context-v2','changed-sync'],warm=1,resume=True)\n"
        "print(json.dumps(r))\n", str(provider), str(output))
    assert result == resumed
    directory = output / "tiny-context-v1"
    report = json.loads((directory / "summary.json").read_bytes())
    for field in ("canonical_contexts_validated", "cli_successes"):
        invalid = deepcopy(report)
        invalid[field] += 1
        with pytest.raises(ValueError, match="summary differs"):
            measure.validate_retained_workload(directory, invalid, plan, "tiny", "context-v1")
    preparation_path = directory / "preparation.json"
    preparation_bytes = preparation_path.read_bytes()
    preparation_path.unlink()
    with pytest.raises(ValueError, match="preparation changed or is missing"):
        measure.validate_retained_workload(directory, report, plan, "tiny", "context-v1")
    preparation_path.write_bytes(preparation_bytes)
    retained_source = directory / "inputs/src/policy.py"
    source_bytes = retained_source.read_bytes()
    retained_source.write_bytes(source_bytes + b"\n# Unreviewed baseline modification\n")
    with pytest.raises(ValueError, match="preparation inputs differ"):
        measure.validate_retained_workload(directory, report, plan, "tiny", "context-v1")
    retained_source.write_bytes(source_bytes)
    sample_path = output / "tiny-context-v1/sample-0.json"
    original = sample_path.read_bytes()
    changed = json.loads(original)
    changed["wall_ns"] = 1
    sample_path.write_text(json.dumps(changed))
    rejected = fresh(
        "from tests.developer_value.measure import run\nimport json\n"
        "try:\n run(Path(sys.argv[1]),Path(sys.argv[2]),selected_projects=['tiny'],"
        "selected_lanes=['context-v1','context-v2','changed-sync'],warm=1,resume=True)\n"
        "except ValueError as e:\n print(json.dumps({'rejected':True,'reason':str(e)}))\n"
        "else:\n print(json.dumps({'rejected':False}))\n", str(provider), str(output))
    assert rejected["rejected"] and "sample bytes changed" in rejected["reason"]
    sample_path.write_bytes(original)
    summary_path = output / "tiny-context-v1/summary.json"
    summary = json.loads(summary_path.read_bytes())
    summary["completed_calls"] = 100
    summary_path.write_text(json.dumps(summary))
    rejected = fresh(
        "from tests.developer_value.measure import run\nimport json\n"
        "try:\n run(Path(sys.argv[1]),Path(sys.argv[2]),selected_projects=['tiny'],"
        "selected_lanes=['context-v1','context-v2','changed-sync'],warm=1,resume=True)\n"
        "except ValueError as e:\n print(json.dumps({'rejected':True,'reason':str(e)}))\n"
        "else:\n print(json.dumps({'rejected':False}))\n", str(provider), str(output))
    assert rejected["rejected"] and "summary differs" in rejected["reason"]


def test_measurement_refuses_unrelated_output_and_invalid_parameters(tmp_path):
    marker = tmp_path / "user.txt"
    marker.write_text("preserved")
    with pytest.raises(ValueError, match="unrelated nonempty"):
        measure.run(ROOT, tmp_path, selected_projects=["tiny"], selected_lanes=["search"], warm=0)
    assert marker.read_text() == "preserved"
    invalid: list[dict[str, Any]] = [{"selected_projects": ["external"]},
                                    {"selected_lanes": ["arbitrary-command"]}, {"warm": -1}]
    for keyword in invalid:
        with pytest.raises(ValueError, match="unsupported"):
            measure.run(ROOT, tmp_path / "unused", **keyword)


def test_strict_validation_lane_uses_supported_cli_options(provider, tmp_path):
    result = fresh(
        "from tests.developer_value.measure import run\nimport json\n"
        "r=run(Path(sys.argv[1]),Path(sys.argv[2]),selected_projects=['tiny'],"
        "selected_lanes=['strict-validation'],warm=0)\nprint(json.dumps(r))\n",
        str(provider), str(tmp_path / "validation"))
    assert result["completed_calls"] == result["total_samples"] == 1
    sample = json.loads((tmp_path / "validation/tiny-strict-validation/sample-0.json").read_text())
    assert sample["result"]["exit_code"] == 0
    assert "unrecognized arguments" not in sample["result"]["stderr"]
    assert sample["result"]["integrity"]["status"] == "validated"
    assert sample["result"]["expected_change"] is True
    assert sample["result"]["content_commitments"]


def test_noop_sync_cannot_pass_changed_source_measurement(tmp_path, monkeypatch):
    runtime.load_provider(ROOT)
    prepared = tmp_path / "prepared"
    measure.prepare("tiny", "changed-sync", prepared)
    monkeypatch.setattr(runtime, "run_cli", lambda argv: {"exit_code": 0, "stdout": "", "stderr": ""})
    output = tmp_path / "noop-results"
    report = measure.worker(ROOT, "tiny", "changed-sync", prepared, output, 0)
    sample = json.loads((output / "sample-0.json").read_bytes())
    assert report["completed_calls"] == 0
    assert report["logical_outputs_repeatable"] is False
    assert sample["error"]["type"] == "ObservedWorkflowFailure"
    assert sample["result"]["expected_change"] is False
    freshness = sample["result"]["integrity"]["inspection"]["concept"]["concept"]["freshness"]
    assert freshness["state"] == "source-changed"
