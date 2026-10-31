"""Production registry ownership needed before selective workflow rollout."""

from pathlib import Path

import pytest

from release import pr_ci as ci


ROOT = Path(__file__).parents[1]


def registry_sources(policy):
    # Registry selectors are available in the later source proposal. Keep this
    # fixture independent of which proposal adds their implementation files.
    return {
        selected.partition("::")[0]: b"def test_contract(): pass\n"
        for group in policy["groups"].values()
        for selected in group["tests"]
    }


def test_analysis_capture_selects_qualification_contracts():
    policy = ci.policy_load(ROOT / "release")
    sources = registry_sources(policy)
    path = "release/analysis_conformance.py"
    sources[path] = b"def capture(): pass\n"
    result = ci.select(
        policy,
        sources,
        sources,
        [{"status": "M", "old": path, "path": path}],
        None,
        {"entries": []},
    )
    assert "tests/test_analysis_qualification.py" in result["lanes"]["ubuntu"]["selectors"]
    assert "typecheck" in result["jobs"]


@pytest.mark.parametrize(
    "path",
    [
        "release/knowledge-maintenance.json",
        "release/policy-activations/" + "a" * 64 + ".json",
    ],
)
def test_policy_approval_inputs_select_their_consumers(path):
    policy = ci.policy_load(ROOT / "release")
    before = registry_sources(policy)
    before["release/knowledge-maintenance.json"] = b'{"activation": {}}\n'
    after = {**before, path: b'{"activation": {"run_id": 1}}\n'}
    result = ci.select(
        policy,
        before,
        after,
        [{"status": "M" if path in before else "A", "old": path, "path": path}],
        None,
        {"entries": []},
    )
    assert {
        "tests/test_knowledge_maintenance.py",
        "tests/test_policy_activation.py",
        "tests/test_policy_renewal.py",
        "tests/test_qualification_automation.py",
        "tests/test_hosted_evidence.py",
        "tests/test_preflight_targets.py",
    } <= set(result["lanes"]["ubuntu"]["selectors"])
    assert {"activation-proof", "wiki-integrity", "typecheck"} <= set(result["jobs"])
