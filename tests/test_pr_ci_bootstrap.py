"""Production registry ownership needed before selective workflow rollout."""

from pathlib import Path

from release import pr_ci as ci


ROOT = Path(__file__).parents[1]


def test_analysis_capture_selects_qualification_contracts():
    policy = ci.policy_load(ROOT / "release")
    # Registry selectors are available in the later source proposal. Keep this
    # fixture independent of which proposal adds their implementation files.
    sources = {
        selected.partition("::")[0]: b"def test_contract(): pass\n"
        for group in policy["groups"].values()
        for selected in group["tests"]
    }
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
