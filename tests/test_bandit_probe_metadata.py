"""Timing reports distinguish local execution from GitHub Actions observations."""
from tests.bandit_contract_probe import timing_context


def test_local_timing_does_not_claim_hosted_execution(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.setenv("GITHUB_RUN_ID", "stale")
    value = timing_context()
    assert value["execution_context"]["kind"] == "local"
    assert value["execution_context"]["run_id"] is None
    assert value["timing_scope"].startswith("local ")


def test_github_timing_preserves_run_identity_and_scope_limits(monkeypatch):
    for key, value in {"GITHUB_ACTIONS": "true", "GITHUB_REPOSITORY": "owned/repo",
                       "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2",
                       "RUNNER_ENVIRONMENT": "github-hosted"}.items():
        monkeypatch.setenv(key, value)
    value = timing_context()
    assert value["execution_context"] == {"kind": "github-actions", "repository": "owned/repo",
        "run_id": "123", "run_attempt": "2", "runner_environment": "github-hosted"}
    assert value["timing_scope"].startswith("GitHub Actions ")
    assert "not workflow wall-clock savings" in value["timing_scope"]
