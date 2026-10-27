"""Independent selection, identity, collection and fail-closed aggregate cases."""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import subprocess
import zipfile

import pytest

from release import pr_ci as ci


ROOT = Path(__file__).parents[1]


@pytest.fixture
def policy():
    return {
        "schema": ci.SCHEMA,
        "revision": 1,
        "always": [],
        "groups": {
            "python": {
                "tests": [],
                "lanes": ["ubuntu"],
                "jobs": ["typecheck"],
                "helpers": [],
            },
            "docs": {
                "tests": ["tests/test_docs.py"],
                "lanes": ["ubuntu"],
                "jobs": [],
                "helpers": [],
            },
            "query": {
                "tests": ["tests/test_query.py", "tests/test_api.py"],
                "lanes": ["ubuntu"],
                "jobs": ["typecheck"],
                "helpers": [],
            },
        },
        "rules": [
            {"paths": ["README.md", "docs/**"], "groups": ["docs"]},
            {"paths": ["src/pkg/query.py"], "groups": ["query"]},
        ],
        "owners": {},
    }


@pytest.fixture
def sources():
    return {
        "src/pkg/query.py": b"def lookup(): pass\n",
        "src/pkg/api.py": b"from . import query\n",
        "tests/test_query.py": b"from pkg import query\ndef test_query(): pass\n",
        "tests/test_api.py": b"from pkg import api\ndef test_api(): pass\n",
        "tests/test_docs.py": b"def test_docs(): pass\n",
        "tests/test_unrelated.py": b"def test_other(): pass\n",
    }


def changed(path, status="M", old=None):
    return {"status": status, "path": path, "old": old or path}


def selection(policy, sources, rows, body=None, entries=()):
    return ci.select(policy, sources, sources, rows, body, {"entries": list(entries)})


def test_documentation_selects_only_relevant_checks_even_with_many_wiki_objects(
    policy, sources
):
    result = selection(
        policy,
        sources,
        [
            changed("README.md"),
            *[changed(f"docs/llm_wiki/.llm-wiki/storage/{i}.json") for i in range(600)],
        ],
    )
    assert result["lanes"]["ubuntu"]["selectors"] == ["tests/test_docs.py"]
    assert set(result["jobs"]) == {"activation-proof", "wiki-integrity"}
    assert set(result["lanes"]) == {"ubuntu"}
    assert result["lanes"]["ubuntu"]["profile"] == "dev"
    assert result["qualification"] is False


def test_exact_query_change_keeps_consumers_without_full_test_collection(
    policy, sources
):
    result = selection(policy, sources, [changed("src/pkg/query.py")])
    assert result["lanes"]["ubuntu"]["selectors"] == [
        "tests/test_api.py",
        "tests/test_query.py",
    ]
    assert "typecheck" in result["jobs"]
    assert all(
        value not in {"tests", "tests/", "-k", "-m"}
        for value in result["lanes"]["ubuntu"]["selectors"]
    )


def test_entire_inventory_is_never_an_implicit_pr_fallback(policy, sources):
    policy["groups"]["query"]["tests"] = [p for p in sources if p.startswith("tests/")]
    with pytest.raises(ci.SelectionError, match="complete test inventory"):
        selection(policy, sources, [changed("src/pkg/query.py")])


def test_unmapped_python_uses_reverse_import_consumers(policy, sources):
    policy["rules"] = []
    result = selection(policy, sources, [changed("src/pkg/query.py")])
    assert result["lanes"]["ubuntu"]["selectors"] == [
        "tests/test_api.py",
        "tests/test_query.py",
    ]


def test_malformed_fixture_is_data_and_selects_only_its_referencing_test(
    policy, sources
):
    path = "tests/fixtures/invalid_syntax/broken.py"
    sources[path] = b"def ( intentionally invalid fixture"
    sources["tests/test_query.py"] = (
        b'FIXTURE = "invalid_syntax"\ndef test_query(): pass\n'
    )
    docs = selection(policy, sources, [changed("README.md")])
    assert docs["lanes"]["ubuntu"]["selectors"] == ["tests/test_docs.py"]
    result = selection(policy, sources, [changed(path)])
    assert result["lanes"]["ubuntu"]["selectors"] == ["tests/test_query.py"]


def test_changed_test_cannot_be_omitted_by_an_additive_proposal(policy, sources):
    body = '<!-- pr-ci-selection\n{"groups":["docs"],"tests":[],"reason":"Also check prose"}\n-->'
    result = selection(policy, sources, [changed("tests/test_query.py")], body)
    assert result["lanes"]["ubuntu"]["selectors"] == [
        "tests/test_docs.py",
        "tests/test_query.py",
    ]


@pytest.mark.parametrize(
    "body",
    [
        '<!-- pr-ci-selection\n{"groups":[],"tests":[],"reason":"skip"}\n-->',
        '<!-- pr-ci-selection\n{"groups":["missing"],"tests":[],"reason":"unknown"}\n-->',
        '<!-- pr-ci-selection\n{"groups":["docs","docs"],"tests":[],"reason":"duplicate"}\n-->',
        '<!-- pr-ci-selection\n{"groups":["docs"],"tests":[],"reason":"x","skip":true}\n-->',
        '<!-- pr-ci-selection\n{"groups":[],"tests":["tests; echo unsafe"],"reason":"x"}\n-->',
        "<!-- pr-ci-selection {broken} -->",
        '<!-- pr-ci-selection\n{"groups":[],"tests":["../test_escape.py"],"reason":"x"}\n-->',
    ],
)
def test_malformed_unknown_or_shell_proposals_cannot_pass(policy, sources, body):
    with pytest.raises(ci.SelectionError):
        selection(policy, sources, [changed("README.md")], body)


def test_repeated_proposal_is_rejected(policy, sources):
    block = '<!-- pr-ci-selection\n{"groups":["docs"],"tests":[],"reason":"x"}\n-->'
    with pytest.raises(ci.SelectionError, match="repeated"):
        selection(policy, sources, [changed("README.md")], block + block)


def test_unknown_source_without_a_test_owner_blocks(policy, sources):
    sources["src/pkg/unmodeled.py"] = b"VALUE = 1\n"
    with pytest.raises(ci.SelectionError, match="no trusted"):
        selection(policy, sources, [changed("src/pkg/unmodeled.py")])


def test_removed_regression_does_not_silently_disappear(policy, sources):
    after = {p: raw for p, raw in sources.items() if p != "tests/test_query.py"}
    with pytest.raises(ci.SelectionError, match="deleted regression"):
        ci.select(
            policy,
            sources,
            after,
            [changed("tests/test_query.py", "D")],
            None,
            {"entries": []},
        )


def test_renamed_regression_selects_its_new_path_and_old_owners(policy, sources):
    after = dict(sources)
    after["tests/test_renamed.py"] = after.pop("tests/test_unrelated.py")
    result = ci.select(
        policy,
        sources,
        after,
        [changed("tests/test_renamed.py", "R100", "tests/test_unrelated.py")],
        None,
        {"entries": []},
    )
    assert result["lanes"]["ubuntu"]["selectors"] == ["tests/test_renamed.py"]


@pytest.mark.parametrize(
    "raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b"[" * 34 + b"0" + b"]" * 34]
)
def test_strict_metadata_bounds_and_duplicate_keys(raw):
    with pytest.raises(ci.SelectionError):
        ci.strict_json(raw)


@pytest.mark.parametrize(
    "value",
    [
        "/tests/test_a.py",
        "tests/../test_a.py",
        "tests\\test_a.py",
        "tests/test_a.py\n--help",
        "tests",
        "-k",
    ],
)
def test_canonical_explicit_selectors_only(value):
    with pytest.raises(ci.SelectionError):
        ci.selector(value)


def lane_plan():
    return {
        "schema": ci.SCHEMA,
        "mode": "pull-request",
        "pull_request": 8,
        "repository": "owner/repo",
        "candidate_sha": "a" * 40,
        "candidate_tree": "b" * 40,
        "base_sha": "c" * 40,
        "head_sha": "d" * 40,
        "run_id": 100,
        "run_attempt": 2,
        "policy_sha256": "e" * 64,
        "jobs": ["activation-proof", "wiki-integrity"],
        "lanes": {
            "ubuntu": {
                **ci.LANES["ubuntu"],
                "selectors": ["tests/test_sample.py"],
                "helpers": [],
            }
        },
        "skip_edges": [],
        "qualification": False,
    }


def xml(cases):
    import xml.etree.ElementTree as et

    suite = et.Element("testsuite")
    for name, reason in cases:
        case = et.SubElement(
            suite, "testcase", classname="tests.test_sample", name=name
        )
        if reason is not None:
            et.SubElement(case, "skipped", message="Skipped: " + reason)
    return et.tostring(suite)


def collection(names):
    nodes = ["tests/test_sample.py::" + name for name in names]
    return {"collected": nodes, "selected": nodes, "deselected": []}


def test_junit_requires_each_selected_collected_case():
    report = ci.verify_lane(
        lane_plan(),
        "ubuntu",
        collection(["test_a", "test_b"]),
        xml([("test_a", None), ("test_b", None)]),
        0,
    )
    assert (report["selected"], report["passed"], report["skipped"]) == (2, 2, 0)
    with pytest.raises(ci.SelectionError, match="omits"):
        ci.verify_lane(
            lane_plan(),
            "ubuntu",
            collection(["test_a", "test_b"]),
            xml([("test_a", None)]),
            0,
        )


@pytest.mark.parametrize(
    "problem", ["empty", "deselected", "duplicate", "wrong-file", "nonzero", "skip"]
)
def test_subset_execution_cannot_green_missing_or_unaccounted_work(problem):
    observed, raw, code = collection(["test_a"]), xml([("test_a", None)]), 0
    if problem == "empty":
        observed = collection([])
    elif problem == "deselected":
        observed["deselected"] = ["tests/test_sample.py::test_b"]
    elif problem == "duplicate":
        raw = xml([("test_a", None), ("test_a", None)])
    elif problem == "wrong-file":
        observed["collected"] = observed["selected"] = ["tests/test_other.py::test_a"]
    elif problem == "nonzero":
        code = 1
    elif problem == "skip":
        raw = xml([("test_a", "unavailable")])
    with pytest.raises(ci.SelectionError):
        ci.verify_lane(lane_plan(), "ubuntu", observed, raw, code)


def needs_for(plan):
    return {name: {"result": "success"} for name in {*plan["jobs"], "plan", "test"}}


def test_aggregate_requires_exact_native_reports_and_actual_skip_owner_pass():
    plan = lane_plan()
    edge = {
        "lane": "ubuntu",
        "node_id": "tests/test_sample.py::test_native",
        "reason": "Windows required",
        "owner_lane": "core-windows-3.13",
        "producer": "windows",
    }
    plan["skip_edges"] = [edge]
    plan["lanes"]["windows"] = {
        **ci.LANES["windows"],
        "selectors": [edge["node_id"]],
        "helpers": [],
    }
    ubuntu = ci.verify_lane(
        plan,
        "ubuntu",
        collection(["test_a", "test_native"]),
        xml([("test_a", None), ("test_native", edge["reason"])]),
        0,
    )
    windows = ci.verify_lane(
        plan, "windows", collection(["test_native"]), xml([("test_native", None)]), 0
    )
    reports = {"ubuntu": ubuntu, "windows": windows}
    assert ci.aggregate(plan, needs_for(plan), reports)["status"] == "passed"
    reports["windows"]["passed_nodes"] = []
    with pytest.raises(ci.SelectionError, match="actually pass"):
        ci.aggregate(plan, needs_for(plan), reports)


@pytest.mark.parametrize("state", ["skipped", "cancelled", "failure", None])
def test_required_job_cannot_pass_by_skipping_or_cancellation(state):
    plan = lane_plan()
    report = ci.verify_lane(
        plan, "ubuntu", collection(["test_a"]), xml([("test_a", None)]), 0
    )
    needs = needs_for(plan)
    needs["test"]["result"] = state
    with pytest.raises(ci.SelectionError, match="required producer"):
        ci.aggregate(plan, needs, {"ubuntu": report})


def test_aggregate_rejects_stale_attempt_and_allows_only_explicitly_unselected_jobs():
    plan = lane_plan()
    report = ci.verify_lane(
        plan, "ubuntu", collection(["test_a"]), xml([("test_a", None)]), 0
    )
    needs = needs_for(plan)
    needs["action"] = {"result": "skipped"}
    assert ci.aggregate(plan, needs, {"ubuntu": report})["status"] == "passed"
    report["run_attempt"] = 1
    with pytest.raises(ci.SelectionError, match="identity differs"):
        ci.aggregate(plan, needs, {"ubuntu": report})


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def commit(root, message):
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        message,
    )
    return git(root, "rev-parse", "HEAD")


def fixture_repository(tmp_path, policy, sources, candidate_policy=None):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "core.autocrlf", "false")
    for path, raw in sources.items():
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
    trusted = root / "release"
    trusted.mkdir()
    for name in ci.POLICY_FILES:
        (trusted / name).write_bytes((ROOT / "release" / name).read_bytes())
    (trusted / "pr-ci-policy.json").write_text(json.dumps(policy))
    (trusted / "skip-allowlist.json").write_text('{"entries":[]}')
    base = commit(root, "base policy")
    git(root, "switch", "--no-track", "-qc", "codex/fixture")
    assert not git(
        root, "for-each-ref", "--format=%(upstream:short)", "refs/heads/codex/fixture"
    )
    (root / "src/pkg/query.py").write_text("def lookup(): return 1\n")
    if candidate_policy is not None:
        (trusted / "pr-ci-policy.json").write_text(json.dumps(candidate_policy))
    head = commit(root, "bounded fix")
    git(root, "switch", "-q", "main")
    git(
        root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "merge",
        "--no-ff",
        "-qm",
        "test merge",
        head,
    )
    candidate = git(root, "rev-parse", "HEAD")
    event = {
        "repository": {"full_name": "owner/repo"},
        "pull_request": {
            "number": 8,
            "body": "",
            "base": {"ref": "main", "sha": base},
            "head": {"sha": head},
        },
    }
    return root, trusted, event, candidate


def test_real_git_plan_binds_base_head_merge_tree_and_refuses_candidate_policy(
    tmp_path, policy, sources
):
    root, trusted, event, candidate = fixture_repository(tmp_path, policy, sources)
    plan = ci.make_plan(root, trusted, event, candidate, "owner/repo", 10, 1)
    assert plan["candidate_tree"] == git(root, "rev-parse", "HEAD^{tree}")
    assert plan["base_sha"] == event["pull_request"]["base"]["sha"]
    (trusted / "pr-ci-policy.json").write_text(
        json.dumps({**policy, "always": ["docs"]})
    )
    with pytest.raises(ci.SelectionError, match="trusted base"):
        ci.make_plan(root, trusted, event, candidate, "owner/repo", 10, 1)


def test_head_only_success_is_not_test_merge_evidence(tmp_path, policy, sources):
    root, trusted, event, _ = fixture_repository(tmp_path, policy, sources)
    head = event["pull_request"]["head"]["sha"]
    git(root, "switch", "--detach", "-q", head)
    with pytest.raises(ci.SelectionError, match="test merge"):
        ci.make_plan(root, trusted, event, head, "owner/repo", 10, 1)


def test_candidate_policy_cannot_lower_its_own_pr_floor(tmp_path, policy, sources):
    policy["rules"].append(
        {"paths": ["release/pr-ci-policy.json"], "groups": ["query"]}
    )
    lowered = copy.deepcopy(policy)
    lowered["groups"]["query"]["tests"] = []
    root, _, event, candidate = fixture_repository(tmp_path, policy, sources, lowered)
    trusted = tmp_path / "base-only"
    trusted.mkdir()
    for name in ci.POLICY_FILES:
        (trusted / name).write_bytes(
            subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(root),
                    "show",
                    event["pull_request"]["base"]["sha"] + ":release/" + name,
                ]
            )
        )
    result = ci.make_plan(root, trusted, event, candidate, "owner/repo", 10, 1)
    assert result["lanes"]["ubuntu"]["selectors"] == [
        "tests/test_api.py",
        "tests/test_query.py",
    ]


def test_git_and_source_bytes_are_bounded_before_inventory_materialization(
    tmp_path, policy, sources, monkeypatch
):
    root, _, _, candidate = fixture_repository(tmp_path, policy, sources)
    catalog = ci.tree(root, candidate)
    monkeypatch.setattr(ci, "MAX_SOURCE", 16)
    with pytest.raises(ci.SelectionError, match="Git output limit"):
        ci.git(root, "show", candidate + ":src/pkg/query.py")
    monkeypatch.setattr(ci, "MAX_SOURCE", 64 * 1024 * 1024)
    monkeypatch.setattr(ci, "MAX_JSON", 16)
    with pytest.raises(ci.SelectionError, match="before read"):
        ci.blobs(root, catalog)


def test_missing_base_driver_has_no_candidate_fallback(tmp_path, policy, sources):
    root, trusted, event, candidate = fixture_repository(tmp_path, policy, sources)
    (trusted / "pr_ci.py").unlink()
    with pytest.raises(OSError):
        ci.make_plan(root, trusted, event, candidate, "owner/repo", 10, 1)


def test_policy_has_no_missing_or_arbitrary_execution_targets():
    policy = ci.policy_load(ROOT / "release")
    for group in policy["groups"].values():
        for selected in group["tests"]:
            assert (ROOT / ci.selector(selected).split("::")[0]).is_file()
    assert "typecheck" in policy["groups"]["ci-policy"]["jobs"]
    assert policy["groups"]["typescript"]["helpers"] == ["typescript"]


@pytest.mark.parametrize("revision", [None, True, 0, 2])
def test_unadmitted_bootstrap_policy_revision_is_refused(tmp_path, revision):
    value = json.loads((ROOT / "release/pr-ci-policy.json").read_text())
    if revision is None:
        value.pop("revision")
    else:
        value["revision"] = revision
    (tmp_path / "pr-ci-policy.json").write_text(json.dumps(value))
    with pytest.raises(ci.SelectionError, match="trusted selection policy"):
        ci.policy_load(tmp_path)


def test_actual_cli_executes_and_replays_only_selected_native_cases(
    tmp_path, policy, sources
):
    import os
    import sys

    available = [
        name
        for name, row in ci.LANES.items()
        if row["platform"] == sys.platform
        and sys.version.startswith(row["python"] + ".")
    ]
    local = available[0] if available else "ubuntu"
    policy["groups"]["query"]["lanes"] = [local]
    sources = {
        **sources,
        "tests/test_query.py": b"def test_query(): pass\n",
        "tests/test_api.py": b"def test_api(): pass\n",
    }
    root, trusted, _, _ = fixture_repository(tmp_path, policy, sources)
    # Pytest's root is an explicit interface coordinate, not inferred from a
    # temporary parent or the operator's checkout.
    config = root / "pytest.ini"
    config.write_text("[pytest]\n")
    git(root, "add", "pytest.ini")
    git(
        root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "test root",
    )
    # Build the same selected receipt but keep this post-merge fixture-only
    # configuration commit distinct from make_plan's merge-parent proof.
    plan = lane_plan()
    plan.update(
        {
            "candidate_sha": git(root, "rev-parse", "HEAD"),
            "candidate_tree": git(root, "rev-parse", "HEAD^{tree}"),
            "policy_sha256": ci.policy_identity(trusted),
            "run_id": 100,
            "run_attempt": 2,
            "lanes": {
                local: {
                    **ci.LANES[local],
                    "selectors": ["tests/test_query.py", "tests/test_api.py"],
                    "helpers": [],
                }
            },
        }
    )
    path = trusted / "plan.json"
    ci.write_json(path, plan)
    output = tmp_path / "reports" / local
    env = {k: v for k, v in os.environ.items() if not k.startswith("GITHUB_")}
    process = subprocess.run(
        [
            sys.executable,
            "-I",
            str(trusted / "pr_ci.py"),
            "run",
            "--root",
            str(root),
            "--plan",
            str(path),
            "--expected-sha256",
            ci.digest(path.read_bytes()),
            "--lane",
            local,
            "--output",
            str(output),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if not available:
        assert process.returncode == 2 and "native runtime differs" in process.stderr
        return
    assert process.returncode == 0, process.stdout + process.stderr
    reports = ci.lane_reports(plan, output.parent)
    assert reports[local]["passed"] == reports[local]["selected"] == 2
    report_path = output / "result.json"
    tampered = json.loads(report_path.read_text())
    tampered["passed"] = 1
    ci.write_json(report_path, tampered)
    with pytest.raises(ci.SelectionError, match="raw collection/JUnit"):
        ci.lane_reports(plan, output.parent)


def test_collection_plugin_records_every_case_before_deselection(tmp_path):
    suite = tmp_path / "test_sample.py"
    suite.write_text("def test_a(): pass\ndef test_b(): pass\n")
    output = tmp_path / "collection.json"
    import os
    import sys

    env = {
        **os.environ,
        "PYTHONPATH": str(ROOT / "release"),
        "PR_CI_COLLECTION": str(output),
    }
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(suite),
            "-q",
            "-p",
            "pr_ci_pytest",
            "-p",
            "no:cacheprovider",
            "-k",
            "test_a",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stdout + process.stderr
    observed = json.loads(output.read_text())
    assert (
        len(observed["collected"]) == 2
        and len(observed["selected"]) == len(observed["deselected"]) == 1
    )


class HostedFixture:
    def __init__(self, plan, receipt):
        self.run = {
            "id": 100,
            "run_attempt": 2,
            "status": "completed",
            "conclusion": "success",
            "event": "pull_request",
            "head_sha": plan["head_sha"],
            "path": ci.WORKFLOW,
            "name": "CI",
            "workflow_id": 9,
            "repository": {"id": 1, "full_name": "owner/repo"},
            "head_repository": {"id": 1, "full_name": "owner/repo"},
        }
        self.pr = {
            "number": 8,
            "merged_at": "2026-10-27T11:00:00Z",
            "merge_commit_sha": "f" * 40,
            "base": {
                "ref": "main",
                "sha": plan["base_sha"],
                "repo": {"full_name": "owner/repo"},
            },
            "head": {"sha": plan["head_sha"]},
        }
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("plan.json", ci.canonical(plan) + b"\n")
            archive.writestr("complete.json", ci.canonical(receipt) + b"\n")
        self.raw = buffer.getvalue()
        self.artifact = {
            "id": 25,
            "name": "pr-ci-complete-2",
            "expired": False,
            "size_in_bytes": len(self.raw),
            "digest": "sha256:" + ci.digest(self.raw),
            "created_at": "2026-10-27T10:02:00Z",
            "updated_at": "2026-10-27T10:02:00Z",
            "workflow_run": {
                "id": 100,
                "head_sha": plan["head_sha"],
                "repository_id": 1,
                "head_repository_id": 1,
            },
        }
        self.job = {
            "id": 44,
            "name": "CI complete",
            "run_id": 100,
            "conclusion": "success",
            "started_at": "2026-10-27T10:01:00Z",
            "completed_at": "2026-10-27T10:03:00Z",
        }

    def get(self, path):
        if path.startswith("/commits/"):
            return [self.pr]
        if path.startswith("/actions/workflows/ci.yml/runs"):
            return {"total_count": 1, "workflow_runs": [copy.deepcopy(self.run)]}
        if path == "/actions/runs/100":
            return copy.deepcopy(self.run)
        if path.startswith("/actions/runs/100/attempts/") and "/jobs?" in path:
            return {"total_count": 1, "jobs": [self.job]}
        if path.startswith("/actions/runs/100/artifacts"):
            return {"total_count": 1, "artifacts": [self.artifact]}
        if path == "/actions/workflows/9":
            return {"name": "CI", "path": ci.WORKFLOW}
        raise AssertionError(path)

    def archive(self, identifier):
        assert identifier == 25
        return self.raw


def main_fixture(monkeypatch):
    plan = lane_plan()
    report = ci.verify_lane(
        plan, "ubuntu", collection(["test_a"]), xml([("test_a", None)]), 0
    )
    receipt = ci.aggregate(plan, needs_for(plan), {"ubuntu": report})
    client = HostedFixture(plan, receipt)
    monkeypatch.setattr(
        ci,
        "git",
        lambda root, *args: (
            "f" * 40 if args == ("rev-parse", "HEAD") else plan["candidate_tree"]
        ).encode(),
    )
    return client


def test_main_reuses_authenticated_same_tree_evidence_without_executing_tests(
    monkeypatch,
):
    client = main_fixture(monkeypatch)
    result = ci.reuse_main(
        ROOT, ROOT / "release", "f" * 40, "owner/repo", 200, 1, client
    )
    assert result["mode"] == "main-reuse" and result["lanes"] == {}
    assert result["jobs"] == ["activation-proof", "wiki-integrity"]
    assert result["reuse"]["artifact_id"] == 25 and result["qualification"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "tree",
        "base",
        "head",
        "attempt",
        "expired",
        "digest",
        "size",
        "producer",
        "artifact-attempt",
        "pr-number",
    ],
)
def test_main_refuses_unrelated_or_stale_pr_evidence(monkeypatch, damage):
    client = main_fixture(monkeypatch)
    if damage == "tree":
        monkeypatch.setattr(ci, "git", lambda root, *args: b"0" * 40)
    elif damage == "base":
        client.pr["base"]["sha"] = "1" * 40
    elif damage == "head":
        client.pr["head"]["sha"] = "2" * 40
    elif damage == "attempt":
        client.run["run_attempt"] = 3
    elif damage == "expired":
        client.artifact["expired"] = True
    elif damage == "digest":
        client.artifact["digest"] = "sha256:" + "0" * 64
    elif damage == "size":
        client.artifact["size_in_bytes"] += 1
    elif damage == "producer":
        client.job["conclusion"] = "skipped"
    elif damage == "artifact-attempt":
        client.artifact["created_at"] = "2026-10-26T10:02:00Z"
    elif damage == "pr-number":
        client.pr["number"] = 9
    with pytest.raises(ci.SelectionError):
        ci.reuse_main(ROOT, ROOT / "release", "f" * 40, "owner/repo", 200, 1, client)


def test_a_new_run_during_download_invalidates_an_old_success(monkeypatch):
    client = main_fixture(monkeypatch)
    original = client.get
    calls = 0

    def get(path):
        nonlocal calls
        result = original(path)
        if path.startswith("/actions/workflows/ci.yml/runs"):
            calls += 1
            if calls == 2:
                return {"total_count": 1, "workflow_runs": [{**client.run, "id": 101}]}
        return result

    client.get = get
    with pytest.raises(ci.SelectionError, match="newer PR run"):
        ci.reuse_main(ROOT, ROOT / "release", "f" * 40, "owner/repo", 200, 1, client)
