"""Freeze non-qualifying optimization baselines from exact Git objects.

This analysis tool does not replace release qualification or registry checks.
Generated contracts and evidence belong in an ignored, create-only directory.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import tempfile
import tarfile
from typing import Any

import yaml

WORKFLOW = ".github/workflows/release-qualification.yml"
PROMOTION_WORKFLOW = ".github/workflows/publish.yml"
SHA = re.compile(r"[0-9a-f]{40}\Z")
SCHEMA = "agent-wiki-optimization-baseline/v1"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        result = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
        return result.hexdigest()


def load_json(path: Path) -> Any:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value
    def invalid(value):
        raise ValueError(f"non-finite JSON value: {value}")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique, parse_constant=invalid)


def verify_baseline(directory: Path) -> tuple[dict, dict]:
    baseline = load_json(directory / "baseline.json")
    source = baseline["source"]["sha"]
    if (baseline["schema_version"] != SCHEMA or baseline["qualifying"] is not False
            or not SHA.fullmatch(source) or baseline["harness"]["source_sha"] != source
            or baseline["role"] not in {"selected", "historical"}):
        raise ValueError("invalid baseline identity")
    if set(baseline["files"]) != {"candidate-source.tar", "qualification-harnesses.tar", "contract.json"}:
        raise ValueError("baseline evidence allowlist differs")
    for name, expected in baseline["files"].items():
        path = directory / name
        if path.is_symlink() or file_digest(path) != expected:
            raise ValueError(f"baseline file commitment differs: {name}")
        if name.endswith(".tar"):
            with tarfile.open(path) as archive:
                if archive.pax_headers.get("comment") != source:
                    raise ValueError("archive commit does not match baseline")
    contract = load_json(directory / "contract.json")
    if contract.get("promotion", {}).get("definition_sha256") != baseline["inputs"].get(PROMOTION_WORKFLOW):
        raise ValueError("promotion reference commitment differs")
    if PROMOTION_WORKFLOW not in baseline["inputs"]:
        raise ValueError("promotion reference is missing")
    return baseline, contract


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *arguments], stdin=subprocess.DEVNULL,
                          capture_output=True, check=True, timeout=120).stdout


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or path.as_posix() != value
            or ".." in path.parts or "\\" in value or any(c in value for c in "$*?\n\r")
            or value.startswith("-")):
        raise ValueError(f"unsafe evidence/source path: {value!r}")
    return value


def source_bytes(root: Path, source: str, path: str) -> bytes:
    safe_path(path)
    if int(git(root, "cat-file", "-s", f"{source}:{path}")) > 2 * 1024 * 1024:
        raise ValueError(f"contract input too large: {path}")
    return git(root, "show", f"{source}:{path}")


def commands(script: str) -> list[list[str]]:
    # Parse declarations only. Never execute workflow shell supplied as input.
    result = []
    for line in script.replace("\\\n", " ").splitlines():
        if line.strip().startswith(("python ", "git archive ")):
            result.append(shlex.split(line))
    return result


def matrix_rows(job: dict) -> list[dict]:
    matrix = job.get("strategy", {}).get("matrix", {})
    if not matrix:
        return [{}]
    if "exclude" in matrix or ("include" in matrix and len(matrix) != 1):
        raise ValueError("mixed/include/exclude matrix requires an explicit profile resolver")
    if "include" in matrix:
        return matrix["include"]
    keys = sorted(matrix)
    return [dict(zip(keys, values)) for values in itertools.product(*(matrix[k] for k in keys))]


def resolve(value: Any, matrix: dict) -> Any:
    if isinstance(value, str):
        return re.sub(r"\$\{\{\s*matrix\.([\w-]+)\s*\}\}",
                      lambda m: str(matrix[m[1]]).lower() if isinstance(matrix[m[1]], bool)
                      else str(matrix[m[1]]), value)
    if isinstance(value, list):
        return [resolve(item, matrix) for item in value]
    if isinstance(value, dict):
        return {key: resolve(item, matrix) for key, item in value.items()}
    return value


def options(script: str, flag: str) -> list[str]:
    return [tokens[i + 1] for tokens in commands(script)
            for i, token in enumerate(tokens[:-1]) if token == flag]


def assignments(values: list[str]) -> dict[str, str]:
    result = {}
    for value in values:
        name, body = value.split("=", 1)
        if name in result:
            raise ValueError(f"duplicate obligation: {name}")
        result[name] = body
    return result


def workflow_contract(workflow: dict, input_hashes: dict, skip_entries: list[dict]) -> dict:
    jobs = workflow["jobs"]
    profiles = []
    for job_id, job in jobs.items():
        for matrix in matrix_rows(job):
            lane = resolve(job, matrix)
            steps = lane["steps"]
            executions = []
            for step in steps:
                for argv in commands(step.get("run", "")):
                    if argv[:3] == ["python", "-m", "pytest"]:
                        executions.append({
                            "step": step["name"], "argv": argv,
                            "selectors": [a for a in argv[3:] if a == "tests" or a.startswith("tests/")],
                            "condition": step.get("if"), "working_directory": step.get("working-directory"),
                            "environment": {**workflow.get("env", {}), **lane.get("env", {}), **step.get("env", {})},
                        })
            profiles.append({
                "job_id": job_id, "matrix": matrix, "name": lane["name"],
                "runner": lane["runs-on"], "condition": lane.get("if"),
                "python": [s.get("with", {}).get("python-version", "runner-default") for s in steps
                           if s.get("uses", "").startswith("actions/setup-python@")],
                "python_resolution": "declared version only; empty means runner default; actual patch/image not observed",
                "install_steps": [{"name": s.get("name"), "script": s["run"]} for s in steps
                                  if "pip install" in s.get("run", "")],
                "source_install_mode": "non-editable" if any('"./candidate[dev' in s.get("run", "") for s in steps)
                    else "see-frozen-job-definition",
                "candidate_input_hashes": input_hashes,
                "declared_extras": sorted(set(re.findall(r"\[(dev(?:,[a-z]+)*|mcp|tokens)\]",
                    "\n".join(s.get("run", "") for s in steps)))),
                "resolved_packages": None,
                "dependency_resolution": "declared inputs only; runner package versions are not inferred",
                "pytest": executions,
                "suite_runners": [{"argv": argv, "condition": step.get("if")}
                                  for step in steps for argv in commands(step.get("run", ""))
                                  if any(token.endswith(("/ubuntu_suites.py", "/ubuntu_shadow.py")) for token in argv)],
                "environment": {**workflow.get("env", {}), **lane.get("env", {})},
            })
    decision_script = "\n".join(s.get("run", "") for s in jobs["decision"]["steps"])
    gates = assignments(options(decision_script, "--gate"))
    if set(gates) != {f"RD-{n:02}" for n in range(14)}:
        raise ValueError("incomplete RD-00 through RD-13 decision obligations")
    owner_steps = jobs["owner-lanes"]["steps"]
    shadow_steps = [s for s in owner_steps if s.get("if") == "${{ inputs.ubuntu-suite-shadow }}"]
    owner_script = "\n".join(s.get("run", "") for s in owner_steps if s not in shadow_steps)
    owners = assignments(options(owner_script, "--owner-result"))
    owner_junit = assignments(options(owner_script, "--owner-junit"))
    if set(owners) != set(owner_junit) or not {e["owner_lane"] for e in skip_entries} <= owners.keys():
        raise ValueError("skip owner obligations have no producer or JUnit mapping")
    shadow_owners = {}
    if shadow_steps:
        shadow_script = "\n".join(s.get("run", "") for s in shadow_steps)
        shadow_results = assignments(options(shadow_script, "--owner-result"))
        shadow_junit = assignments(options(shadow_script, "--owner-junit"))
        if set(shadow_results) != set(owners) or set(shadow_junit) != set(owners):
            raise ValueError("shadow owner obligations differ from qualification")
        shadow_owners = {name: {"producer": value, "junit": shadow_junit[name]}
                         for name, value in shadow_results.items()}
    dependencies: dict[str, list[str]] = {}
    for dependency in options(decision_script, "--gate-dependency"):
        gate, producer = dependency.split("=", 1)
        if gate not in gates:
            raise ValueError("gate dependency has no obligation")
        dependencies.setdefault(gate, []).append(producer)
    graph = {}
    for name, job in jobs.items():
        needs = job.get("needs", [])
        needs = [needs] if isinstance(needs, str) else needs
        if not set(needs) <= jobs.keys():
            raise ValueError(f"unknown dependency in {name}")
        graph[name] = {"needs": needs, "condition": job.get("if"),
                       "artifacts": [s for s in job["steps"] if "artifact@" in s.get("uses", "")]}
    def visit(name: str, ancestors: set[str]):
        if name in ancestors:
            raise ValueError("cyclic workflow dependency")
        for parent in graph[name]["needs"]:
            visit(parent, ancestors | {name})
    for name in graph:
        visit(name, set())
    return {"profiles": profiles, "gates": gates, "gate_dependencies": dependencies,
            "shadow_owners": shadow_owners,
            "owners": {name: {"producer": value, "junit": owner_junit[name],
                              "skip_obligations": [e for e in skip_entries if e["owner_lane"] == name]}
                       for name, value in owners.items()},
            "graph": graph, "workflow_definition": workflow,
            "equivalence_scope": "Declared profiles only; not proof of identical resolved environments or test outcomes"}


def freeze(root: Path, source: str, output: Path, repository: str, *,
           required_ancestor: str | None, role: str = "selected") -> dict:
    if not SHA.fullmatch(source) or role not in {"selected", "historical"}:
        raise ValueError("a full immutable source SHA and explicit baseline role are required")
    if role == "selected" and required_ancestor is None:
        raise ValueError("selected baseline requires its prerequisite commit")
    if required_ancestor is not None:
        if not SHA.fullmatch(required_ancestor):
            raise ValueError("prerequisite must be a full commit SHA")
        git(root, "merge-base", "--is-ancestor", required_ancestor, source)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("repository must be owner/name")
    if output.exists() or output.is_symlink():
        raise ValueError("baseline output must be new")
    root, output = root.resolve(), output.absolute()
    git(root, "cat-file", "-e", source + "^{commit}")
    raw_workflow = source_bytes(root, source, WORKFLOW)
    workflow = yaml.safe_load(raw_workflow)
    # YAML 1.1 reads the unquoted GitHub 'on' key as a boolean. Keep the exact
    # YAML digest, and use a string key in the JSON representation.
    if True in workflow:
        workflow["on"] = workflow.pop(True)
    harness = next(s for s in workflow["jobs"]["freeze"]["steps"] if s.get("id") == "harness")
    archive_command = next(c for c in commands(harness["run"]) if c[:2] == ["git", "archive"])
    paths = [safe_path(p) for p in archive_command[archive_command.index("--") + 1:]]
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("harness paths must be nonempty and unique")
    tracked = git(root, "ls-tree", "-r", "--name-only", source).decode().splitlines()
    inputs = sorted(p for p in tracked if PurePosixPath(p).name in {
        "pyproject.toml", "package-lock.json", "Cargo.lock", "go.mod", "go.sum",
        "requirements.txt", "requirements.in", "requirements-ci.txt", "toolchain-lock.json",
        "skip-allowlist.json", "pyrightconfig.json", "ubuntu-suites.json", "ubuntu_suites.py", "ubuntu_shadow.py",
    } or p in {WORKFLOW, PROMOTION_WORKFLOW, ".github/workflows/ci.yml", "release/static_checks.py", "release/qualification.py"})
    hashes = {p: digest(source_bytes(root, source, p)) for p in inputs}
    skips = json.loads(source_bytes(root, source, "release/skip-allowlist.json"))["entries"]
    contract = workflow_contract(workflow, hashes, skips)
    promotion = yaml.safe_load(source_bytes(root, source, PROMOTION_WORKFLOW))
    if True in promotion:
        promotion["on"] = promotion.pop(True)
    contract["promotion"] = {
        "gate": "RD-13", "reference_source_sha": source,
        "definition_sha256": hashes[PROMOTION_WORKFLOW], "workflow_definition": promotion,
        "effective_verifier_revision": None,
        "trust_boundary": "protected default branch at promotion time; candidate definition is a reference, not authorization",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".baseline-", dir=output.parent) as temporary:
        staging = Path(temporary) / "result"
        staging.mkdir()
        archives = {}
        for filename, include in (("candidate-source.tar", []), ("qualification-harnesses.tar", paths)):
            git(root, "archive", "--format=tar", f"--output={staging / filename}", source, "--", *include)
            archives[filename] = file_digest(staging / filename)
        (staging / "contract.json").write_bytes(canonical(contract))
        identity = {
            "schema_version": SCHEMA, "role": role, "qualifying": False, "repository": repository,
            "source": {"sha": source, "tree": git(root, "rev-parse", source + "^{tree}").decode().strip(),
                       "commit_epoch": int(git(root, "show", "-s", "--format=%ct", source))},
            "prerequisite_commit": required_ancestor,
            "harness": {"source_sha": source, "paths": paths},
            "inputs": hashes,
            "files": {**archives, "contract.json": file_digest(staging / "contract.json")},
            "generator_sha256": file_digest(Path(__file__)),
            "release_eligibility": "not evaluated; no registry/tag checks, hosted execution, or publication",
        }
        (staging / "baseline.json").write_bytes(canonical(identity))
        staging.rename(output)
    return identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--required-ancestor")
    parser.add_argument("--role", choices=("selected", "historical"), default="selected")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = freeze(args.root, args.source, args.output, args.repository,
                    required_ancestor=args.required_ancestor, role=args.role)
    print(json.dumps({"source": result["source"], "role": result["role"], "qualifying": False}))


if __name__ == "__main__":
    main()
