"""Preparation finds strict source drift before costly rehearsal or policy proof."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from release import (
    knowledge_maintenance as maintenance,
    policy_renewal,
    preparation,
    preflight,
)
from tests.test_knowledge_health_refresh import recorded_project as recorded_project

ROOT = Path(__file__).parents[1]


def test_frozen_source_has_a_source_hash_without_claiming_a_git_diff(monkeypatch):
    monkeypatch.setattr(
        preparation.manual,
        "git",
        lambda *_a, **_kw: subprocess.CompletedProcess([], 128, "", "no Git metadata"),
    )
    config = json.loads((ROOT / maintenance.POLICY_PATH).read_bytes())
    result = preparation.source_status(ROOT, config)
    assert result["status"] in {"source-current", "capture-required"}, result
    assert result["capture_diff_status"] == "unavailable"
    assert result["selected_changes_since_capture"] == []


def test_source_current_inspection_does_not_claim_native_execution(recorded_project):
    source, wiki, *_ = recorded_project
    result = preparation.source_status(
        source.parent,
        {"wiki_dir": wiki.name, "src_dir": source.name, "selection": None},
    )
    assert result["status"] == "source-current", result
    assert result["runtime_verified"] is False


@pytest.mark.parametrize("kind", ["nonsemantic", "added", "removed"])
def test_exact_selected_source_changes_block_even_when_semantics_could_match(
    recorded_project, kind
):
    source, wiki, *_ = recorded_project
    root = source.parent
    config = {"wiki_dir": wiki.name, "src_dir": source.name, "selection": None}
    if kind == "nonsemantic":
        path = source / "models.py"
        path.write_bytes(path.read_bytes() + b"\n# selected source changed\n")
    elif kind == "added":
        (source / "new.py").write_text("VALUE = 1\n")
    else:
        (source / "models.py").unlink()
    result = preparation.source_status(root, config)
    assert result["status"] == "capture-required", result
    assert (
        result["current_source_hash"] != result["captured_source_hash"]
        or result["selection_issue"]
    )


def test_missing_or_modified_writer_metadata_is_unknown(tmp_path):
    assert (
        preparation.source_status(
            tmp_path, {"wiki_dir": "wiki", "selection": "selection"}
        )["status"]
        == "unknown"
    )


@pytest.mark.parametrize(
    "mode,source,blocked",
    [
        ("required", "capture-required", True),
        ("required", "source-current", False),
        ("required", "unknown", False),
        ("shadow", "capture-required", False),
    ],
)
def test_dependency_guard_requires_proven_strict_source_drift(
    monkeypatch, mode, source, blocked
):
    monkeypatch.setattr(
        preparation,
        "policy_status",
        lambda _: {"configuration": {"mode": mode, "wiki_dir": "docs/llm_wiki"}},
    )
    monkeypatch.setattr(preparation, "source_status", lambda *_: {"status": source})
    monkeypatch.setattr(
        preparation.preflight_targets, "inspect", lambda *_: {"status": "unknown"}
    )
    monkeypatch.setattr(
        maintenance, "version_check", lambda *_: {"status": "full-preflight-required"}
    )
    result = preparation.capture_prerequisite(ROOT)
    assert result["required"] is blocked
    if blocked:
        with pytest.raises(ValueError, match="before policy evaluation"):
            preparation.require_capture_current(ROOT)
    else:
        assert preparation.require_capture_current(ROOT) == result


def test_known_target_runtime_drift_precedes_policy_proof(monkeypatch):
    monkeypatch.setattr(
        preparation,
        "policy_status",
        lambda _: {"configuration": {"mode": "required", "wiki_dir": "docs/llm_wiki"}},
    )
    monkeypatch.setattr(
        preparation, "source_status", lambda *_: {"status": "source-current"}
    )
    monkeypatch.setattr(
        preparation.preflight_targets,
        "inspect",
        lambda *_: {"status": "capture-required"},
    )
    monkeypatch.setattr(
        maintenance, "version_check", lambda *_: {"status": "full-preflight-required"}
    )
    assert preparation.capture_prerequisite(ROOT)["required"] is True


def test_preflight_exposes_source_capture_before_expensive_execution(monkeypatch):
    monkeypatch.setattr(
        preparation,
        "source_status",
        lambda *_: {
            "status": "capture-required",
            "changed_recorded_paths": ["selected.py"],
        },
    )
    result = preflight._maintenance(ROOT)
    assert result["status"] == "blocked"
    assert result["sources"]["changed_recorded_paths"] == ["selected.py"]
    assert "before final rehearsal" in result["reason"]


@pytest.mark.parametrize("operation", ["evaluate", "prepare"])
def test_policy_proof_waits_for_wiki_before_any_api_write_or_proof_replay(
    monkeypatch, tmp_path, operation
):
    calls = []
    monkeypatch.setattr(policy_renewal, "main_identity", lambda *_: "a" * 40)

    def blocked(_):
        raise ValueError("wiki capture first")

    monkeypatch.setattr(preparation, "require_capture_current", blocked)
    client = SimpleNamespace(
        request=lambda *a: calls.append(a), get=lambda *a: calls.append(a)
    )
    with pytest.raises(ValueError, match="wiki capture first"):
        if operation == "evaluate":
            policy_renewal.evaluate(
                ROOT, "example/repo", client, apply=True, correlation="one"
            )
        else:
            policy_renewal.prepare(
                ROOT,
                "example/repo",
                client,
                run_id=1,
                attempt=1,
                output=tmp_path / "proposal",
                verifier=lambda *a, **kw: calls.append(a),
            )
    assert calls == [] and not (tmp_path / "proposal").exists()


def test_policy_status_uses_comparator_digest_and_preserves_historical_proof(
    monkeypatch,
):
    config = json.loads((ROOT / maintenance.POLICY_PATH).read_bytes())
    monkeypatch.setattr(
        maintenance,
        "composite_policy_digest",
        lambda _: config["activation"]["implementation_sha256"],
    )
    original = preparation.policy_status(ROOT)
    historical = original["historical_proof_source_sha"]
    assert original["status"] == "current" and historical
    monkeypatch.setattr(maintenance, "composite_policy_digest", lambda _: "f" * 64)
    changed = preparation.policy_status(ROOT)
    assert changed["status"] == "approval-required"
    assert changed["historical_proof_source_sha"] == historical
    assert changed["configuration"]["mode"] == "required"


def test_plan_dependency_order_places_capture_merge_before_policy_and_final_rehearsal(
    monkeypatch,
):
    proof = preparation.capture_prerequisite(ROOT)
    proof = deepcopy(proof)
    proof["required"] = True
    proof["policy"]["status"] = "approval-required"
    monkeypatch.setattr(
        preparation.manual,
        "source",
        lambda _: {
            "candidate_sha": "a" * 40,
            "candidate_tree": "b" * 40,
            "version": "4.1.0",
        },
    )
    monkeypatch.setattr(preparation, "capture_prerequisite", lambda _: proof)
    monkeypatch.setattr(preflight, "_environment", lambda _: {"status": "observed"})
    monkeypatch.setattr(preflight, "_helper", lambda *_: {"status": "ready"})
    result = preparation.inspect(ROOT)
    steps = {row["id"]: row for row in result["steps"]}
    assert result["next_action"] == "wiki-preview"
    assert steps["policy-evaluate"]["requires"] == ["wiki-commit-and-merge"]
    assert steps["policy-evaluate"]["status"] == "waiting-wiki"
    assert steps["final-plan"]["requires"] == [
        "wiki-commit-and-merge",
        "policy-approval-review",
    ]
    assert result["publication_authority"] is False
