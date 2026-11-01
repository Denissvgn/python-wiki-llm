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


def test_action_runtime_policy_selects_release_contracts():
    policy = ci.policy_load(ROOT / "release")
    sources = registry_sources(policy)
    path = "release/action-runtimes.json"
    sources[path] = b'{"actions": {}}\n'
    result = ci.select(
        policy,
        sources,
        sources,
        [{"status": "M", "old": path, "path": path}],
        None,
        {"entries": []},
    )
    assert "tests/test_release_workflows.py" in result["lanes"]["ubuntu"]["selectors"]
    assert "tests/test_action_runtimes.py" in result["lanes"]["ubuntu"]["selectors"]
    assert "tests/test_pytest_portability.py" in result["lanes"]["ubuntu"]["selectors"]
    assert "typecheck" in result["jobs"]


def test_git_delivery_contract_selects_each_native_platform():
    policy = ci.policy_load(ROOT / "release")
    sources = registry_sources(policy)
    path = "tests/test_wiki_git_delivery.py"
    result = ci.select(
        policy,
        sources,
        sources,
        [{"status": "M", "old": path, "path": path}],
        None,
        {"entries": []},
    )
    for lane in ("ubuntu", "windows", "macos"):
        assert path in result["lanes"][lane]["selectors"]


@pytest.mark.parametrize("path,consumer", [
    ("release/hosted_evidence.py", "tests/test_qualified_bundle_reader.py"),
    ("tests/test_qualified_bundle_reader.py", "tests/test_qualified_bundle_reader.py"),
    ("src/llm_wiki_cli/services/sync_transitions.py", "tests/test_sync_page_transitions.py"),
    ("src/llm_wiki_cli/services/sync_transition_execution.py", "tests/test_sync_page_transitions.py"),
    ("tests/test_sync_page_transitions.py", "tests/test_sync_page_transitions.py"),
])
def test_archive_and_page_transition_contracts_select_native_platforms(path, consumer):
    policy = ci.policy_load(ROOT / "release")
    sources = registry_sources(policy)
    sources[consumer] = b"def test_contract(): pass\n"
    sources[path] = b"def contract(): pass\n"
    result = ci.select(
        policy, sources, sources,
        [{"status": "M", "old": path, "path": path}], None, {"entries": []},
    )
    for lane in ("ubuntu", "windows", "macos"):
        assert consumer in result["lanes"][lane]["selectors"]


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


@pytest.mark.parametrize("path", [
    "pyrightconfig.json", "ruff.toml", "tests/verify_installed_provider.py",
])
def test_runtime_validation_inputs_select_typed_release_contracts(path):
    policy = ci.policy_load(ROOT / "release")
    sources = registry_sources(policy)
    sources[path] = b"# Runtime validation input.\n"
    result = ci.select(
        policy, sources, sources,
        [{"status": "M", "old": path, "path": path}], None, {"entries": []},
    )
    assert "typecheck" in result["jobs"]
    selected = result["lanes"]["ubuntu"]["selectors"]
    assert "tests/test_static_quality_architecture.py" in selected
    assert "tests/test_preflight_runner.py" in selected


def test_runtime_validation_ownership_remains_bounded_to_declared_inputs():
    policy = ci.policy_load(ROOT / "release")
    sources = registry_sources(policy)
    path = "unreviewed-validation-config.toml"
    with pytest.raises(ci.SelectionError, match="no trusted contract/test ownership"):
        ci.select(
            policy, sources, sources,
            [{"status": "M", "old": path, "path": path}], None, {"entries": []},
        )
