"""Integration boundaries for the conditional release owner and its PR trigger."""

from pathlib import Path
import tomllib
import xml.etree.ElementTree as ET

import pytest
import yaml

from release import helper_ownership as h, pr_ci, preflight_contracts as contracts

ROOT = Path(__file__).parents[1]
CASE = "tests/test_future.py::test_leaves"
NODE = CASE + "[new-.tsx]"
REASON = "Prepared typescript helper required; owned by toolchains"


def test_new_family_enters_trusted_selection_before_it_has_any_skip_edges():
    example = b'def test_leaves(require_prepared_diagnostics_helper):\n    require_prepared_diagnostics_helper("typescript")\n'
    local = {
        "tests/test_future.py": example,
        "tests/test_unaffected.py": b"def test_other(): pass",
    }
    baseline = {
        "always": [],
        "groups": {
            "python": {"tests": [], "lanes": ["ubuntu"], "jobs": [], "helpers": []}
        },
        "rules": [],
        "owners": {},
    }
    plan = pr_ci.select(
        baseline,
        {},
        local,
        [
            {
                "old": "tests/test_future.py",
                "path": "tests/test_future.py",
                "status": "A",
            }
        ],
        None,
        {"entries": []},
    )
    assert plan["typescript_families"] == [CASE]
    assert "typescript-ownership" in plan["jobs"]
    assert plan["lanes"]["ubuntu"]["helpers"] == ["typescript"]
    assert pr_ci.typescript_families(local, {"release/skip-allowlist.json"}) == [CASE]
    assert pr_ci.typescript_families(local, {"tests/test_unaffected.py"}) == []


def test_ownership_names_both_missing_obligations_and_checks_each_lane():
    case = ET.Element("testcase")
    ET.SubElement(case, "skipped", message=REASON)
    lanes = list(h.LANE.values())
    absent = h.ownership_errors({NODE: case}, [], lanes, set())
    assert all(any(NODE in p and lane in p for p in absent) for lane in lanes)
    assert any("Run toolchain owner suites" in p for p in absent)
    entries = [
        dict(lane=lane, node_id=NODE, reason=REASON, owner_lane="toolchains")
        for lane in lanes
    ]
    assert h.ownership_errors({NODE: case}, entries, lanes, {NODE}) == []
    assert len(h.ownership_errors({NODE: case}, entries, lanes, set())) == 1
    assert h.ownership_errors({NODE: case}, [*entries, entries[0]], lanes, {NODE})


def test_owner_selector_reader_rejects_deselection_and_conditional_bypass(tmp_path):
    path = tmp_path / h.WORKFLOW
    path.parent.mkdir(parents=True)
    content = (ROOT / h.WORKFLOW).read_text()
    assert any(
        s.startswith("tests/test_retired_member_freshness.py::")
        for s in h.owner_selectors(ROOT)
    )
    for original, substitution in [
        (
            "python -m pytest -q\n          tests/test_ts_extract.py",
            "python -m pytest -q -k subset\n          tests/test_ts_extract.py",
        ),
        (
            "- name: " + h.OWNER_STEP,
            "- name: " + h.OWNER_STEP + "\n        continue-on-error: true",
        ),
    ]:
        assert original in content
        path.write_text(content.replace(original, substitution))
        with pytest.raises(ValueError):
            h.owner_selectors(tmp_path)


def test_freshness_producers_select_the_publication_consumer_on_native_lanes():
    policy = pr_ci.policy_load(ROOT / "release")
    for name in (
        "source_retirement",
        "knowledge_freshness",
        "knowledge_coverage",
        "documentation_native",
    ):
        path = f"src/llm_wiki_cli/services/{name}.py"
        groups = {
            g
            for rule in policy["rules"]
            if path in rule["paths"]
            for g in rule["groups"]
        }
        assert "publication-retirement" in groups
    group = policy["groups"]["publication-retirement"]
    assert group["tests"] == [h.contracts.PUBLICATION_CASE]
    assert set(group["lanes"]) == {"ubuntu", "windows", "macos"}
    capture = yaml.safe_load(
        (ROOT / ".github/workflows/reviewed-wiki-capture.yml").read_text()
    )
    steps = capture["jobs"]["capture"]["steps"]
    probe = next(
        i for i, s in enumerate(steps) if "--publication-only" in s.get("run", "")
    )
    assert probe < next(i for i, s in enumerate(steps) if s.get("id") == "capture")
    assert "[dev,tokens]" in steps[probe]["run"] and "if" not in steps[probe]


def test_metadata_check_finds_historical_stale_version_links_and_residue(tmp_path):
    (tmp_path / "tests").mkdir()
    for name in ("CHANGELOG.md", "pyproject.toml", "tests/test_package_metadata.py"):
        (tmp_path / name).write_bytes((ROOT / name).read_bytes())
    assert contracts.release_input_errors(tmp_path) == []
    version = tomllib.loads((tmp_path / "pyproject.toml").read_text())["project"]["version"]
    file = tmp_path / "tests/test_package_metadata.py"
    file.write_text(file.read_text().replace(f'== "{version}"', '== "0.0.0"'))
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        changelog.read_text().replace(f"v{version}...HEAD", "v0.0.0...HEAD")
    )
    (tmp_path / "build").mkdir()
    issues = contracts.release_input_errors(tmp_path)
    assert len(issues) == 3 and all(
        any(x in issue for issue in issues)
        for x in ("assertion", "[Unreleased]", "residue")
    )


def test_shared_fixture_wrappers_and_keyword_calls_select_future_consumers():
    files = {
        "tests/conftest.py": b"""@pytest.fixture(name='ts_cache')
def wrapped(require_prepared_diagnostics_helper):
    require = require_prepared_diagnostics_helper
    return require(language='typescript')
""",
        "tests/test_future.py": b"class TestConsumer:\n    def test_new(self, ts_cache): pass",
    }
    assert pr_ci.typescript_families(files, {"tests/test_future.py"}) == [
        "tests/test_future.py::TestConsumer::test_new"
    ]


def test_reviewed_selection_jobs_keep_the_native_and_prepared_profiles():
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"]
    probe = jobs["typescript-ownership"]
    assert (
        probe["needs"] == "plan"
        and "needs.plan.outputs.typescript-ownership" in probe["if"]
    )
    assert "typescript-ownership" in jobs["complete"]["needs"]
    rows = probe["strategy"]["matrix"]["include"]
    assert {(r["os"], r["python"]) for r in rows if r["profile"] == "core"} == {
        ("windows-2025", "3.13.17"),
        ("ubuntu-24.04", "3.11"),
        ("macos-15", "3.14"),
    }
    assert [(r["os"], r["python"]) for r in rows if r["profile"] == "prepared"] == [
        ("ubuntu-24.04", "3.13")
    ]
