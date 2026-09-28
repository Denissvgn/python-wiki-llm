"""Immutable, non-qualifying inputs for release optimization comparisons."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import tarfile

import pytest
import yaml

from release import optimization_evidence as evidence


def workflow():
    common = {"name": "unit", "runs-on": "ubuntu-24.04", "steps": []}
    result = {"env": {"CI": "1"}, "jobs": {name: {**deepcopy(common), "name": name}
              for name in ("freeze", "core", "owner-lanes", "decision")}}
    jobs = result["jobs"]
    jobs["freeze"]["steps"] = [{"id": "harness", "run":
        'git archive --format=tar --output="$OUT/harness.tar" "$SHA" -- release/qualification.py tests/probe.py'}]
    jobs["core"].update({"needs": "freeze", "name": "core (${{ matrix.python }})",
        "strategy": {"matrix": {"python": ["3.10", "3.13"]}},
        "steps": [{"uses": "actions/setup-python@pinned", "with": {"python-version": "${{ matrix.python }}"}},
                  {"name": "install", "run": 'python -m pip install "./candidate[dev]"'},
                  {"name": "check", "working-directory": "candidate", "run":
                   'python -m pytest tests/test_a.py tests/test_b.py::TestCase::test_x -q -W error --junitxml=out.xml'}]})
    jobs["owner-lanes"]["steps"] = [{"run": 'python -I release/qualification.py verify-owner-lanes '
        '--owner-result "core=${{ needs.core.result }}" --owner-junit "core=evidence/core.xml"'}]
    jobs["decision"]["steps"] = [{"run": 'python -I release/qualification.py aggregate ' +
        " ".join(f'--gate "RD-{n:02}=success"' for n in range(14))}]
    return result


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    evidence.git(root, "init")
    for name, content in {
        evidence.WORKFLOW: yaml.safe_dump(workflow()),
        evidence.PROMOTION_WORKFLOW: yaml.safe_dump({"jobs": {"verify": {"runs-on": "ubuntu-24.04", "steps": []}}}),
        "release/qualification.py": "# owned verifier\n",
        "tests/probe.py": "# owned probe\n",
        "pyproject.toml": '[project]\nname="owned"\nversion="1.0.0"\n',
        "release/skip-allowlist.json": json.dumps({"entries": [{"owner_lane": "core"}]}),
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    evidence.git(root, "add", ".")
    evidence.git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", f"core.hooksPath={root / 'absent-hooks'}", "commit", "--no-gpg-sign", "-m", "fixture")
    return root, evidence.git(root, "rev-parse", "HEAD").decode().strip()


def test_freeze_reads_commit_not_dirty_worktree_and_binds_every_archive(repository, tmp_path):
    root, sha = repository
    (root / evidence.WORKFLOW).write_text("uncommitted invalid workflow")
    first = evidence.freeze(root, sha, tmp_path / "one", "owner/repo", required_ancestor=sha)
    second = evidence.freeze(root, sha, tmp_path / "two", "owner/repo", required_ancestor=sha)
    assert first == second and first["qualifying"] is False
    assert first["harness"]["source_sha"] == sha
    assert evidence.verify_baseline(tmp_path / "one")[0] == first
    for name, expected in first["files"].items():
        assert evidence.file_digest(tmp_path / "one" / name) == expected
    with tarfile.open(tmp_path / "one/candidate-source.tar") as archive:
        stream = archive.extractfile(evidence.WORKFLOW)
        assert stream is not None and b"uncommitted" not in stream.read()
    with tarfile.open(tmp_path / "one/qualification-harnesses.tar") as archive:
        assert {m.name for m in archive.getmembers() if m.isfile()} == {"release/qualification.py", "tests/probe.py"}
    contract = json.loads((tmp_path / "one/contract.json").read_text())
    profiles = [p for p in contract["profiles"] if p["job_id"] == "core"]
    assert [p["python"] for p in profiles] == [["3.10"], ["3.13"]]
    assert all(p["declared_extras"] == ["dev"] and p["resolved_packages"] is None for p in profiles)
    assert profiles[0]["pytest"][0]["selectors"] == ["tests/test_a.py", "tests/test_b.py::TestCase::test_x"]
    assert len(contract["gates"]) == 14 and contract["owners"]["core"]["skip_obligations"]
    assert contract["promotion"]["effective_verifier_revision"] is None
    assert contract["promotion"]["definition_sha256"] == first["inputs"][evidence.PROMOTION_WORKFLOW]
    with pytest.raises(ValueError, match="must be new"):
        evidence.freeze(root, sha, tmp_path / "one", "owner/repo", required_ancestor=sha)


@pytest.mark.parametrize("mutation", ["missing-gate", "duplicate-gate", "missing-owner", "unknown-dependency", "cycle", "matrix-exclude"])
def test_incomplete_or_ambiguous_workflow_cannot_be_a_baseline(mutation):
    value = workflow()
    jobs = value["jobs"]
    if mutation == "missing-gate":
        jobs["decision"]["steps"][0]["run"] = 'python -I release/qualification.py aggregate --gate RD-00=success'
    elif mutation == "duplicate-gate":
        jobs["decision"]["steps"][0]["run"] += ' --gate RD-00=failure'
    elif mutation == "missing-owner":
        jobs["owner-lanes"]["steps"] = []
    elif mutation == "unknown-dependency":
        jobs["core"]["needs"] = "absent"
    elif mutation == "cycle":
        jobs["freeze"]["needs"] = "core"
    else:
        jobs["core"]["strategy"]["matrix"]["exclude"] = []
    with pytest.raises(ValueError):
        evidence.workflow_contract(value, {}, [{"owner_lane": "core"}])


def test_selected_baseline_requires_exact_prerequisite_and_historical_is_explicit(repository, tmp_path):
    root, sha = repository
    with pytest.raises(ValueError, match="full immutable"):
        evidence.freeze(root, "HEAD", tmp_path / "alias", "owner/repo", required_ancestor=sha)
    with pytest.raises(ValueError, match="prerequisite"):
        evidence.freeze(root, sha, tmp_path / "missing", "owner/repo", required_ancestor=None)
    with pytest.raises(subprocess.CalledProcessError):
        evidence.freeze(root, sha, tmp_path / "wrong", "owner/repo", required_ancestor="0" * 40)
    historical = evidence.freeze(root, sha, tmp_path / "past", "owner/repo", required_ancestor=None, role="historical")
    assert historical["role"] == "historical" and not historical["qualifying"]


def test_actual_workflow_obligations_remain_complete():
    root = Path(__file__).parents[1]
    value = yaml.safe_load((root / evidence.WORKFLOW).read_text())
    skips = json.loads((root / "release/skip-allowlist.json").read_text())["entries"]
    contract = evidence.workflow_contract(value, {}, skips)
    assert contract["gates"]["RD-13"] == "BLOCKED"
    assert contract["gate_dependencies"]["RD-04"] == [
        "${{ needs.core.result }}", "${{ needs.core-windows.result }}", "${{ needs.ubuntu-suites.result }}"
    ]
    assert contract["gate_dependencies"]["RD-01"] == ["${{ needs.core-windows.result }}"]
    assert contract["owners"]["security-windows-2025"]["producer"] == "${{ needs.core-windows.result }}"
    sharded = [p for p in contract["profiles"] if p["job_id"] == "core-windows-shards"]
    assert len(sharded) == 2 and all(p["suite_runners"] for p in sharded)
    assert {p["matrix"]["shard"] for p in sharded} == {0, 1}
    assert contract["owners"]["slow"]["producer"] == "${{ needs.ubuntu-suites.result }}"
    assert set(contract["shadow_owners"]) == set(contract["owners"])
    assert contract["shadow_owners"]["slow"]["producer"] == "${{ needs.ubuntu-shadow.result }}"
    assert {"slow", "determinism", "security-windows-2025", "product-windows-2025"} <= contract["owners"].keys()
    profiles = [p for p in contract["profiles"] if p["job_id"] in {"ubuntu-suites", "security-behavior"}
                and p["runner"] == "ubuntu-24.04"]
    assert len(profiles) == 1
    assert all(p["python"] == ["3.13"] and p["declared_extras"] == ["dev"] for p in profiles)


@pytest.mark.parametrize("mutation", ["contract", "harness", "relabel", "allowlist", "qualifying"])
def test_baseline_consumers_reject_modified_or_relabelled_evidence(repository, tmp_path, mutation):
    root, sha = repository
    output = tmp_path / "out"
    result = evidence.freeze(root, sha, output, "owner/repo", required_ancestor=sha)
    if mutation in {"contract", "harness"}:
        name = "contract.json" if mutation == "contract" else "qualification-harnesses.tar"
        (output / name).write_bytes((output / name).read_bytes() + b"changed")
    else:
        if mutation == "relabel":
            result["source"]["sha"] = result["harness"]["source_sha"] = "f" * 40
        elif mutation == "allowlist":
            result["files"]["environment.env"] = "0" * 64
        else:
            result["qualifying"] = True
        (output / "baseline.json").write_bytes(evidence.canonical(result))
    with pytest.raises(ValueError):
        evidence.verify_baseline(output)
