"""Trusted, bounded selection and evidence for nonqualifying PR CI.

Policy and this driver come from the base revision. Proposals are additive data,
never commands. A missing trusted policy requires a separately reviewed bootstrap;
executing the candidate planner is deliberately not a fallback.
"""

from __future__ import annotations

import argparse
import ast
from fnmatch import fnmatchcase
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import sys
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


SCHEMA = "agent-wiki-pr-ci/v1"
POLICY_FILES = (
    "pr_ci.py",
    "pr_ci_pytest.py",
    "pr-ci-policy.json",
    "skip-allowlist.json",
    "hosted_evidence.py",
    "qualification.py",
    "toolchain-lock.json",
)
MAX_JSON = 4 * 1024 * 1024
MAX_SOURCE = 64 * 1024 * 1024
MAX_PATHS = 20_000
MAX_NODES = 50_000
SHA = re.compile(r"[0-9a-f]{40}")
WORKFLOW = ".github/workflows/ci.yml"
PROPOSAL = re.compile(r"<!-- pr-ci-selection\s*\n(.*?)\n-->", re.DOTALL)
LANES = {
    "ubuntu": {
        "os": "ubuntu-24.04",
        "python": "3.13",
        "platform": "linux",
        "baseline": "core-ubuntu-3.10",
    },
    "minimum-python": {
        "os": "ubuntu-24.04",
        "python": "3.10",
        "platform": "linux",
        "baseline": "core-ubuntu-3.10",
    },
    "windows": {
        "os": "windows-2025",
        "python": "3.13",
        "platform": "win32",
        "baseline": "core-windows-3.13",
    },
    "macos": {
        "os": "macos-15",
        "python": "3.14",
        "platform": "darwin",
        "baseline": "core-macos-3.14",
    },
    "toolchains": {
        "os": "ubuntu-24.04",
        "python": "3.13",
        "platform": "linux",
        "baseline": "toolchains",
    },
}
OWNER_LANES = {
    "core-ubuntu-3.10": "ubuntu",
    "core-windows-3.13": "windows",
    "core-macos-3.14": "macos",
    "security-windows-2025": "windows",
    "security-macos-15": "macos",
    "product-windows-2025": "windows",
    "security-ubuntu-24.04": "ubuntu",
    "product-ubuntu-24.04": "ubuntu",
    "toolchains": "toolchains",
    "mcp-3.10": "mcp-sdk",
    "mcp-3.13": "mcp-sdk",
    "oci": "p0-oci-integration",
}


class SelectionError(ValueError):
    """The proposed selection or its evidence is incomplete or untrusted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelectionError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def strict_json(raw: bytes) -> Any:
    require(len(raw) <= MAX_JSON, "JSON byte limit exceeded")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def invalid(value):
        raise SelectionError("nonfinite JSON: " + value)

    try:
        value = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)
    except RecursionError as exc:
        raise SelectionError("JSON nesting limit exceeded") from exc

    def bounded(item, depth=0):
        require(depth <= 32, "JSON nesting limit exceeded")
        if isinstance(item, (dict, list)):
            require(len(item) <= MAX_NODES, "JSON item limit exceeded")
            for child in item.values() if isinstance(item, dict) else item:
                bounded(child, depth + 1)

    bounded(value)
    return value


def bounded_file(path: Path, maximum: int) -> bytes:
    require(
        path.is_file() and not path.is_symlink() and path.stat().st_size <= maximum,
        "missing, linked or oversized input",
    )
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "input byte limit exceeded")
    return raw


def read_json(path: Path) -> Any:
    return strict_json(bounded_file(path, MAX_JSON))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink(), "output cannot be a symbolic link")
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_JSON, "output JSON byte limit exceeded")
    path.write_bytes(raw)


def git(root: Path, *args: str) -> bytes:
    process = subprocess.Popen(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        if process.stdout is None:
            raise SelectionError("Git output is unavailable")
        raw = process.stdout.read(MAX_SOURCE + 1)
        require(len(raw) <= MAX_SOURCE, "Git output limit exceeded")
        require(
            process.wait(timeout=30) == 0,
            "Git input is unavailable: " + " ".join(args[:2]),
        )
        return raw
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        if process.stdout is not None:
            process.stdout.close()


def safe_path(value: str) -> str:
    require(
        isinstance(value, str) and 0 < len(value) <= 4096, "invalid repository path"
    )
    path = PurePosixPath(value)
    require(
        not path.is_absolute()
        and str(path) == value
        and ".." not in path.parts
        and "\\" not in value,
        "noncanonical repository path",
    )
    require(
        all(ord(c) >= 32 and ord(c) != 127 for c in value), "control character in path"
    )
    return value


def selector(value: str) -> str:
    require(isinstance(value, str) and len(value) <= 4096, "invalid test selector")
    file, _, suffix = value.partition("::")
    safe_path(file)
    require(
        re.fullmatch(r"tests/(?:[A-Za-z0-9_-]+/)*test_[A-Za-z0-9_]+\.py", file)
        is not None,
        "only explicit repository test files or nodes may be selected",
    )
    require(
        not suffix or all(ord(c) >= 32 and ord(c) != 127 for c in suffix),
        "invalid test node",
    )
    require(not value.endswith("::"), "empty test node")
    if suffix:
        require(
            re.fullmatch(
                r"[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*(?:\[[^\r\n\x00]+\])?", suffix
            )
            is not None,
            "invalid test declaration or parameter identity",
        )
    return value


def matches(selected: str, node: str) -> bool:
    return (
        node == selected
        or node.startswith(selected + "::")
        or node.startswith(selected + "[")
    )


def compact(selectors: set[str]) -> list[str]:
    result: list[str] = []
    for value in sorted(selectors, key=lambda s: (s.count("::"), s)):
        if not any(matches(existing, value) for existing in result):
            result.append(value)
    return sorted(result)


def policy_identity(directory: Path) -> str:
    return digest(
        canonical(
            {name: digest((directory / name).read_bytes()) for name in POLICY_FILES}
        )
    )


def policy_load(directory: Path) -> dict:
    value = read_json(directory / "pr-ci-policy.json")
    require(
        isinstance(value, dict)
        and set(value) == {"schema", "revision", "groups", "rules", "owners", "always"}
        and value["schema"] == SCHEMA
        and type(value["revision"]) is int
        and value["revision"] == 1,
        "invalid trusted selection policy",
    )
    require(
        isinstance(value["groups"], dict) and value["groups"], "empty suite registry"
    )
    for name, group in value["groups"].items():
        require(
            re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name) is not None,
            "invalid suite identity",
        )
        require(
            set(group) == {"tests", "lanes", "jobs", "helpers"}, "unknown suite field"
        )
        require(
            all(isinstance(group[k], list) for k in group), "suite fields must be lists"
        )
        require(all(lane in LANES for lane in group["lanes"]), "unsupported suite lane")
        require(
            set(group["jobs"])
            <= {
                "typecheck",
                "mcp-sdk",
                "p0-oci-integration",
                "action",
                "dependency-controls",
                "package",
                "core-check-inputs",
                "core-check-comparison",
            },
            "unknown CI producer",
        )
        require(
            set(group["helpers"]) <= {"typescript", "go", "rust", "haskell"},
            "unknown helper",
        )
        for test in group["tests"]:
            selector(test)
    for rule in value["rules"]:
        require(
            set(rule) == {"paths", "groups"} and rule["paths"] and rule["groups"],
            "malformed scope rule",
        )
        require(set(rule["groups"]) <= value["groups"].keys(), "rule has unknown suite")
    require(set(value["always"]) <= value["groups"].keys(), "unknown baseline suite")
    return value


def tree(root: Path, revision: str) -> dict[str, tuple[str, str]]:
    require(SHA.fullmatch(revision) is not None, "revision must be a full Git SHA")
    rows = git(root, "ls-tree", "-rz", revision).split(b"\0")
    result = {}
    for raw in rows:
        if not raw:
            continue
        meta, name = raw.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        path = safe_path(name.decode("utf-8"))
        require(
            kind == "blob" and mode in {"100644", "100755"},
            "linked, submodule or unsupported tracked input",
        )
        result[path] = (mode, oid)
    require(0 < len(result) <= MAX_PATHS, "tracked input count limit exceeded")
    return result


def changes(root: Path, base: str, candidate: str) -> list[dict[str, str]]:
    raw = git(
        root, "diff", "--name-status", "-z", "--find-renames", base, candidate, "--"
    )
    fields = raw.split(b"\0")
    rows = []
    while fields and fields[0]:
        status = fields.pop(0).decode("ascii")
        require(
            re.fullmatch(r"[AMDT]|R[0-9]{1,3}", status) is not None,
            "unsupported diff status",
        )
        old = safe_path(fields.pop(0).decode("utf-8"))
        new = (
            safe_path(fields.pop(0).decode("utf-8")) if status.startswith("R") else old
        )
        require(status != "T", "file type changes require explicit review")
        rows.append({"status": status, "old": old, "path": new})
    require(0 < len(rows) <= MAX_PATHS, "empty or oversized candidate diff")
    return rows


def blobs(root: Path, catalog: dict[str, tuple[str, str]]) -> dict[str, bytes]:
    wanted = {path: oid for path, (_, oid) in catalog.items() if python_input(path)}
    identifiers = sorted(set(wanted.values()))
    if not identifiers:
        return {}
    metadata = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch-check"],
        input=("\n".join(identifiers) + "\n").encode(),
        capture_output=True,
        check=False,
    )
    require(metadata.returncode == 0, "source object sizes are unavailable")
    sizes = metadata.stdout.decode("ascii").splitlines()
    require(len(sizes) == len(identifiers), "source object size inventory differs")
    total = 0
    for oid, line in zip(identifiers, sizes):
        fields = line.split()
        require(
            len(fields) == 3 and fields[:2] == [oid, "blob"],
            "invalid source object size",
        )
        size = int(fields[2])
        require(0 <= size <= MAX_JSON, "Python source byte limit exceeded before read")
        total += size + len(oid) + 32
        require(total <= MAX_SOURCE, "source inventory exceeds byte bound before read")
    process = subprocess.run(
        ["git", "-C", str(root), "cat-file", "--batch"],
        input=("\n".join(identifiers) + "\n").encode(),
        capture_output=True,
        check=False,
    )
    require(
        process.returncode == 0 and len(process.stdout) <= MAX_SOURCE,
        "source inventory exceeds bound or is unavailable",
    )
    stream = io.BytesIO(process.stdout)
    objects = {}
    for oid in identifiers:
        header = stream.readline().decode().strip().split()
        require(
            len(header) == 3 and header[:2] == [oid, "blob"],
            "Git object identity differs",
        )
        size = int(header[2])
        require(0 <= size <= MAX_JSON, "Python source byte limit exceeded")
        raw = stream.read(size)
        require(len(raw) == size and stream.read(1) == b"\n", "truncated Git object")
        objects[oid] = raw
    return {path: objects[oid] for path, oid in wanted.items()}


def module_name(path: str) -> str:
    value = path.removeprefix("src/").removesuffix(".py").replace("/", ".")
    return value.removesuffix(".__init__")


def python_input(path: str) -> bool:
    return (
        path.endswith(".py")
        and path.startswith(("src/", "tests/", "release/"))
        and not path.startswith("tests/fixtures/")
    )


def imports(path: str, raw: bytes) -> set[str]:
    try:
        parsed = ast.parse(raw)
    except (SyntaxError, ValueError, UnicodeError) as exc:
        raise SelectionError("cannot classify Python input: " + path) from exc
    package = module_name(path).split(".")
    if not path.endswith("/__init__.py"):
        package.pop()
    result = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = package[: len(package) - node.level + 1] if node.level else []
            name = ".".join([*prefix, *([node.module] if node.module else [])])
            if name:
                result.add(name)
                result.update(
                    name + "." + alias.name for alias in node.names if alias.name != "*"
                )
    return result


def proposal(body: str | None, groups: dict) -> dict:
    require(
        body is None or isinstance(body, str) and len(body.encode()) <= MAX_JSON,
        "oversized PR description",
    )
    blocks = PROPOSAL.findall(body or "")
    require(
        len(blocks) <= 1
        and ((body or "").count("<!-- pr-ci-selection") == len(blocks)),
        "malformed or repeated agent proposal",
    )
    if not blocks:
        return {
            "groups": [],
            "tests": [],
            "reason": "trusted minimum selection; no additive agent proposal",
        }
    value = strict_json(blocks[0].encode())
    require(
        isinstance(value, dict) and set(value) == {"groups", "tests", "reason"},
        "agent proposal has unknown fields",
    )
    require(
        isinstance(value["reason"], str) and 0 < len(value["reason"]) <= 4096,
        "agent selection requires a reason",
    )
    for key in ("groups", "tests"):
        require(
            isinstance(value[key], list)
            and len(value[key]) <= 1000
            and all(isinstance(v, str) for v in value[key])
            and len(set(value[key])) == len(value[key]),
            "invalid or duplicate agent selectors",
        )
    require(set(value["groups"]) <= groups.keys(), "agent selected an unknown suite")
    for test in value["tests"]:
        selector(test)
    require(value["groups"] or value["tests"], "empty agent proposal")
    return value


def select(
    policy: dict,
    before: dict[str, bytes],
    after: dict[str, bytes],
    rows: list[dict],
    body: str | None,
    allowlist: dict,
) -> dict:
    """Select declared contracts plus direct/import consumers without executing them."""
    groups = set(policy["always"])
    reasons: dict[str, list[str]] = {}
    explicit_tests: set[str] = set()
    old_imports = {p: imports(p, raw) for p, raw in before.items() if python_input(p)}
    new_imports = {p: imports(p, raw) for p, raw in after.items() if python_input(p)}
    all_imports = {
        p: old_imports.get(p, set()) | new_imports.get(p, set())
        for p in old_imports.keys() | new_imports.keys()
    }
    unresolved = []
    for row in rows:
        path, old = row["path"], row["old"]
        found = set()
        for rule in policy["rules"]:
            if any(
                fnmatchcase(p, pattern)
                for p in {path, old}
                for pattern in rule["paths"]
            ):
                found.update(rule["groups"])
        if (
            path.startswith("tests/")
            and not path.startswith("tests/fixtures/")
            and Path(path).name.startswith("test_")
            and path.endswith(".py")
        ):
            if path not in after:
                unresolved.append(
                    path
                    + ": deleted regression requires an explicit replacement policy"
                )
            else:
                explicit_tests.add(path)
                found.add("python")
        if path.endswith(".py") and path in all_imports:
            owned = {
                p
                for p in all_imports
                if p.startswith("tests/")
                and Path(p).name.startswith("test_")
                and ({module_name(path), module_name(old)} & all_imports[p])
            }
            # A maintained rule names downstream interfaces. Otherwise include
            # reverse module consumers before looking for their test owners.
            if not found:
                affected = {module_name(path), module_name(old)}
                while True:
                    expanded = affected | {
                        module_name(p)
                        for p, deps in all_imports.items()
                        if not p.startswith("tests/") and deps & affected
                    }
                    if expanded == affected:
                        break
                    affected = expanded
                owned |= {
                    p
                    for p, deps in all_imports.items()
                    if p.startswith("tests/")
                    and Path(p).name.startswith("test_")
                    and deps & affected
                }
            explicit_tests.update(p for p in owned if p in after)
            if owned:
                found.add("python")
        if path.startswith("tests/fixtures/") and not found:
            parts = PurePosixPath(path).parts
            tokens = {
                path,
                path.removeprefix("tests/"),
                path.removeprefix("tests/fixtures/"),
            }
            if len(parts) > 3:
                tokens.add(parts[2])
            if PurePosixPath(path).name not in {
                "__init__.py",
                "models.py",
                "main.py",
                "app.py",
                "README.md",
                "index.md",
                "main.ts",
                "main.js",
                "pyproject.toml",
                "package.json",
                "package-lock.json",
            }:
                tokens.add(PurePosixPath(path).name)
            consumers = set()
            for p in all_imports:
                if p.startswith("tests/"):
                    literals = {
                        n.value
                        for n in ast.walk(ast.parse(after.get(p, before.get(p, b""))))
                        if isinstance(n, ast.Constant) and isinstance(n.value, str)
                    }
                    if literals & tokens:
                        consumers.add(module_name(p))
            while True:
                expanded = consumers | {
                    module_name(p)
                    for p, deps in all_imports.items()
                    if p.startswith("tests/") and deps & consumers
                }
                if expanded == consumers:
                    break
                consumers = expanded
            owned = {
                p
                for p in after
                if python_input(p)
                and p.startswith("tests/")
                and Path(p).name.startswith("test_")
                and module_name(p) in consumers
            }
            if owned:
                explicit_tests.update(owned)
                found.add("python")
        if not found:
            unresolved.append(path + ": no trusted contract/test ownership")
        groups.update(found)
        reasons[path] = sorted(found)
    require(not unresolved, "Unresolved selection: " + "; ".join(unresolved[:20]))
    addition = proposal(body, policy["groups"])
    groups.update(addition["groups"])
    explicit_tests.update(addition["tests"])
    # The routing contract is introduced after the base-policy bootstrap.
    # Once present it is mandatory; deleting it still fails the diff review.
    routing_test = "tests/test_pr_ci_workflow.py"
    if "ci-policy" in groups and routing_test in after:
        explicit_tests.add(routing_test)
    lanes: dict[str, set[str]] = {}
    helpers: dict[str, set[str]] = {}
    jobs = {"activation-proof", "wiki-integrity"}
    for name in sorted(groups):
        group = policy["groups"][name]
        jobs.update(group["jobs"])
        for lane in group["lanes"]:
            lanes.setdefault(lane, set()).update(group["tests"])
            helpers.setdefault(lane, set()).update(group["helpers"])
    if explicit_tests:
        lanes.setdefault("ubuntu", set()).update(explicit_tests)
    for lane, tests in lanes.items():
        for test in tests:
            require(
                test.partition("::")[0] in after, "selected test is absent: " + test
            )
    # Exact existing skip declarations become conditional edges in a PR plan,
    # never a claim that this subset is a complete core baseline.
    edges = []
    while True:
        changed = False
        for lane, tests in list(lanes.items()):
            baseline = LANES[lane]["baseline"]
            for entry in allowlist["entries"]:
                if entry["lane"] != baseline or not any(
                    matches(s, entry["node_id"]) for s in tests
                ):
                    continue
                owner = OWNER_LANES.get(entry["owner_lane"])
                require(
                    owner is not None,
                    "unmapped native skip owner: " + entry["owner_lane"],
                )
                edge = {
                    "lane": lane,
                    **{k: entry[k] for k in ("node_id", "reason", "owner_lane")},
                    "producer": owner,
                }
                if edge not in edges:
                    edges.append(edge)
                if owner == "mcp-sdk":
                    jobs.add(owner)
                elif owner == "p0-oci-integration":
                    jobs.add(owner)
                elif owner in LANES:
                    current = lanes.setdefault(owner, set())
                    if not any(matches(s, entry["node_id"]) for s in current):
                        current.add(entry["node_id"])
                        changed = True
                    if owner == "toolchains":
                        helpers.setdefault(owner, set()).update(
                            policy["owners"].get(
                                entry["node_id"].partition("::")[0], []
                            )
                        )
        if not changed:
            break
    for lane in lanes:
        helpers.setdefault(lane, set())
        if lane == "toolchains":
            for test in lanes[lane]:
                helpers[lane].update(policy["owners"].get(test.partition("::")[0], []))
    require(
        all(helpers[lane] <= {"typescript", "go", "rust", "haskell"} for lane in lanes),
        "unknown native helper owner",
    )
    inventory = {
        p
        for p in after
        if python_input(p)
        and p.startswith("tests/")
        and Path(p).name.startswith("test_")
    }
    selected_files = {s.partition("::")[0] for tests in lanes.values() for s in tests}
    require(
        len(inventory) <= 1 or selected_files != inventory,
        "selection expands to the complete test inventory; full testing belongs in release workflows",
    )
    docs_only = groups == {"docs"} and selected_files <= {
        s.partition("::")[0] for s in policy["groups"]["docs"]["tests"]
    }
    profile = (
        "dev" if docs_only else "dev,mcp,tokens" if "mcp-sdk" in jobs else "dev,tokens"
    )
    return {
        "groups": sorted(groups),
        "reasons": reasons,
        "proposal": addition,
        "lanes": {
            lane: {
                **LANES[lane],
                "selectors": compact(tests),
                "helpers": sorted(helpers[lane]),
                "profile": profile,
            }
            for lane, tests in sorted(lanes.items())
            if tests
        },
        "jobs": sorted(jobs),
        "skip_edges": sorted(
            edges, key=lambda e: (e["lane"], e["node_id"], e["reason"])
        ),
        "qualification": False,
    }


def make_plan(
    root: Path,
    directory: Path,
    event: dict,
    candidate: str,
    repository: str,
    run_id: int,
    attempt: int,
) -> dict:
    require(
        SHA.fullmatch(candidate) is not None
        and type(run_id) is int
        and run_id > 0
        and type(attempt) is int
        and attempt > 0,
        "invalid candidate/run identity",
    )
    require(
        event.get("repository", {}).get("full_name") == repository,
        "event repository differs",
    )
    pr = event.get("pull_request")
    if not isinstance(pr, dict) or pr.get("base", {}).get("ref") != "main":
        raise SelectionError("a main pull request is required")
    base, head = pr["base"]["sha"], pr["head"]["sha"]
    require(
        SHA.fullmatch(base) is not None and SHA.fullmatch(head) is not None,
        "invalid PR revisions",
    )
    require(
        git(root, "rev-parse", "HEAD").decode().strip() == candidate,
        "checkout differs from tested candidate",
    )
    for revision in (base, head):
        git(root, "merge-base", "--is-ancestor", revision, candidate)
    require(
        git(root, "show", "-s", "--format=%P", candidate).decode().split()
        == [base, head],
        "PR checks require the exact base/head test merge commit",
    )
    # No candidate fallback, including when this is the first rollout PR.
    for name in POLICY_FILES:
        require(
            git(root, "show", f"{base}:release/{name}")
            == (directory / name).read_bytes(),
            "driver/policy is not from trusted base",
        )
    policy = policy_load(directory)
    before_catalog, after_catalog = tree(root, base), tree(root, candidate)
    rows = changes(root, base, candidate)
    selected = select(
        policy,
        blobs(root, before_catalog),
        blobs(root, after_catalog),
        rows,
        pr.get("body"),
        read_json(directory / "skip-allowlist.json"),
    )
    return {
        "schema": SCHEMA,
        "mode": "pull-request",
        "repository": repository,
        "pull_request": pr["number"],
        "base_sha": base,
        "head_sha": head,
        "candidate_sha": candidate,
        "candidate_tree": git(root, "rev-parse", candidate + "^{tree}")
        .decode()
        .strip(),
        "policy_sha256": policy_identity(directory),
        "run_id": run_id,
        "run_attempt": attempt,
        "changes": rows,
        **selected,
    }


def verify_plan(path: Path, expected: str, root: Path | None = None) -> dict:
    raw = bounded_file(path, MAX_JSON)
    require(digest(raw) == expected, "selection receipt digest differs")
    plan = strict_json(raw)
    require(
        plan.get("schema") == SCHEMA
        and plan.get("mode") in {"pull-request", "main-reuse"}
        and plan.get("qualification") is False,
        "not a nonqualifying selection receipt",
    )
    require(
        plan["policy_sha256"] == policy_identity(path.parent),
        "trusted driver/policy identity differs",
    )
    if root is not None:
        require(
            git(root, "rev-parse", "HEAD").decode().strip() == plan["candidate_sha"],
            "test checkout SHA differs",
        )
        require(
            git(root, "rev-parse", "HEAD^{tree}").decode().strip()
            == plan["candidate_tree"],
            "test checkout tree differs",
        )
        require(
            not git(root, "status", "--porcelain", "--untracked-files=no").strip(),
            "tracked test checkout was modified",
        )
    require(
        plan["repository"] == os.environ.get("GITHUB_REPOSITORY", plan["repository"])
        and str(plan["run_id"]) == os.environ.get("GITHUB_RUN_ID", str(plan["run_id"]))
        and str(plan["run_attempt"])
        == os.environ.get("GITHUB_RUN_ATTEMPT", str(plan["run_attempt"])),
        "selection run identity differs",
    )
    for lane, data in plan["lanes"].items():
        require(
            lane in LANES and all(data[k] == v for k, v in LANES[lane].items()),
            "unknown or changed native lane",
        )
        require(
            data["selectors"] and len(set(data["selectors"])) == len(data["selectors"]),
            "empty or duplicate lane selection",
        )
        require(
            data.get("profile", "dev,mcp,tokens")
            in {"dev", "dev,tokens", "dev,mcp,tokens"},
            "unknown dependency profile",
        )
        for value in data["selectors"]:
            selector(value)
    return plan


def junit_nodes(raw: bytes) -> dict[str, tuple[str, str]]:
    require(
        len(raw) <= MAX_SOURCE and b"<!DOCTYPE" not in raw and b"<!ENTITY" not in raw,
        "unsafe or oversized JUnit",
    )
    parsed = ET.fromstring(raw)
    require(
        not list(parsed.iter("failure")) and not list(parsed.iter("error")),
        "JUnit contains failures or errors",
    )
    result = {}
    for case in parsed.iter("testcase"):
        parts = case.get("classname", "").split(".")
        index = next(
            (i for i, part in enumerate(parts) if part.startswith("test_")), None
        )
        if index is None:
            raise SelectionError("JUnit has no canonical test module")
        node = "::".join(
            [
                "/".join(parts[: index + 1]) + ".py",
                *parts[index + 1 :],
                case.get("name", ""),
            ]
        )
        require(node not in result, "duplicate JUnit node")
        skip = case.find("skipped")
        reason = "" if skip is None else skip.get("message", "")
        if reason.startswith("Skipped: "):
            reason = reason[len("Skipped: ") :]
        result[node] = ("passed", "") if skip is None else ("skipped", reason)
    require(0 < len(result) <= MAX_NODES, "empty or oversized JUnit inventory")
    return result


def verify_lane(
    plan: dict, lane: str, collected: dict, raw: bytes, returncode: int
) -> dict:
    require(returncode == 0, "selected pytest execution did not succeed")
    selection = plan["lanes"][lane]
    nodes = collected.get("collected")
    if (
        not isinstance(nodes, list)
        or not nodes
        or len(nodes) > MAX_NODES
        or len(set(nodes)) != len(nodes)
    ):
        raise SelectionError("invalid collected node inventory")
    require(
        collected.get("deselected") == [] and collected.get("selected") == nodes,
        "selected cases were silently deselected",
    )
    require(
        all(any(matches(s, node) for s in selection["selectors"]) for node in nodes),
        "unexpected collected test",
    )
    require(
        all(any(matches(s, node) for node in nodes) for s in selection["selectors"]),
        "a selected file/node collected nothing",
    )
    outcomes = junit_nodes(raw)
    require(set(outcomes) == set(nodes), "JUnit omits or adds collected nodes")
    expected = {
        (e["node_id"], e["reason"]): e for e in plan["skip_edges"] if e["lane"] == lane
    }
    skips = []
    for node, (state, reason) in outcomes.items():
        if state == "skipped":
            require(
                (node, reason) in expected,
                "unexpected selected-case skip: " + node + ": " + reason,
            )
            skips.append(expected[node, reason])
    return {
        "schema": SCHEMA,
        "kind": "selected-tests",
        "repository": plan["repository"],
        "candidate_sha": plan["candidate_sha"],
        "candidate_tree": plan["candidate_tree"],
        "run_id": plan["run_id"],
        "run_attempt": plan["run_attempt"],
        "lane": lane,
        "policy_sha256": plan["policy_sha256"],
        "selected": len(nodes),
        "passed": len(nodes) - len(skips),
        "skipped": len(skips),
        "skips": skips,
        "passed_nodes": sorted(
            node for node, (state, _) in outcomes.items() if state == "passed"
        ),
        "junit_sha256": digest(raw),
        "runtime": {
            "platform": sys.platform,
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "qualification": False,
    }


def run_lane(args: argparse.Namespace) -> None:
    plan = verify_plan(args.plan, args.expected_sha256, args.root)
    require(
        plan["mode"] == "pull-request" and args.lane in plan["lanes"],
        "lane was not selected",
    )
    lane = plan["lanes"][args.lane]
    require(
        sys.platform == lane["platform"]
        and platform.python_version().startswith(lane["python"] + "."),
        "native runtime differs from plan",
    )
    args.output.mkdir(parents=True, exist_ok=True)
    require(
        not any(args.output.iterdir()), "refuse to overwrite previous lane evidence"
    )
    env = dict(os.environ)
    env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "PR_CI_COLLECTION": str(args.output.absolute() / "collection.json"),
        }
    )
    # The plugin is from the same authenticated base bundle, never a candidate
    # pytest extension. PYTHONPATH does not choose a product installation.
    env["PYTHONPATH"] = str(args.plan.absolute().parent)
    command = [
        sys.executable,
        "-m",
        "pytest",
        *lane["selectors"],
        "-q",
        "-p",
        "pr_ci_pytest",
        "-p",
        "no:cacheprovider",
        "--strict-config",
        "--strict-markers",
        "-W",
        "error",
        "-o",
        "xfail_strict=true",
        "--junitxml=" + str(args.output.absolute() / "junit.xml"),
    ]
    result = subprocess.run(command, cwd=args.root, env=env, check=False)
    evidence = verify_lane(
        plan,
        args.lane,
        read_json(args.output / "collection.json"),
        bounded_file(args.output / "junit.xml", MAX_SOURCE),
        result.returncode,
    )
    write_json(args.output / "result.json", evidence)


def prepare_lane(args: argparse.Namespace) -> None:
    plan = verify_plan(args.plan, args.expected_sha256, args.root)
    require(args.lane in plan["lanes"], "helper lane was not selected")
    languages = plan["lanes"][args.lane]["helpers"]
    if languages:
        command = [
            sys.executable,
            "-m",
            "llm_wiki_cli.cli",
            "prepare-extractors",
            "--src-dir",
            str(args.root),
            "--cache-dir",
            str(args.cache),
        ]
        for language in languages:
            command.extend(["--language", language])
        result = subprocess.run(command, cwd=args.root, check=False)
        require(result.returncode == 0, "selected native helper preparation failed")


def lane_reports(plan: dict, root: Path) -> dict:
    reports = {}
    for path in root.glob("*/result.json"):
        lane = path.parent.name
        if lane.startswith("pr-ci-tests-"):
            suffix = "-" + str(plan["run_attempt"])
            require(lane.endswith(suffix), "test artifact attempt differs")
            lane = lane[len("pr-ci-tests-") : -len(suffix)]
        require(lane in plan["lanes"], "unexpected test evidence directory")
        saved = read_json(path)
        replay = verify_lane(
            plan,
            lane,
            read_json(path.parent / "collection.json"),
            bounded_file(path.parent / "junit.xml", MAX_SOURCE),
            0,
        )
        runtime = saved.get("runtime", {})
        require(
            runtime.get("platform") == plan["lanes"][lane]["platform"]
            and str(runtime.get("python", "")).startswith(
                plan["lanes"][lane]["python"] + "."
            )
            and isinstance(runtime.get("machine"), str)
            and runtime["machine"],
            "native report runtime differs",
        )
        replay["runtime"] = runtime
        require(
            saved == replay, "saved report differs from raw collection/JUnit replay"
        )
        reports[lane] = saved
    return reports


def aggregate(plan: dict, needs: dict, reports: dict[str, dict]) -> dict:
    required = set(plan["jobs"]) | {"plan"}
    if plan["lanes"]:
        required.add("test")
    require(required <= needs.keys(), "missing selected producer")
    require(
        all(
            value.get("result") == "success"
            if name in required
            else value.get("result") == "skipped"
            for name, value in needs.items()
        ),
        "required producer failed, skipped, cancelled or unexpected producer ran",
    )
    require(
        set(reports) == set(plan["lanes"]), "missing or unexpected native test report"
    )
    for lane, report in reports.items():
        require(
            report.get("kind") == "selected-tests"
            and report.get("qualification") is False
            and report.get("lane") == lane
            and type(report.get("selected")) is int
            and report["selected"] > 0
            and type(report.get("passed")) is int
            and report["passed"] >= 0
            and report["selected"] == report["passed"] + report.get("skipped", -1)
            and len(report.get("passed_nodes", [])) == report["passed"],
            "invalid selected test report",
        )
        for key in (
            "repository",
            "candidate_sha",
            "candidate_tree",
            "run_id",
            "run_attempt",
            "policy_sha256",
        ):
            require(
                report.get(key) == plan[key], "lane evidence identity differs: " + key
            )
        for edge in report["skips"]:
            owner = edge["producer"]
            if owner in reports:
                require(
                    edge["node_id"] in reports[owner]["passed_nodes"],
                    "selected skip owner did not actually pass: " + edge["node_id"],
                )
            else:
                require(
                    owner in plan["jobs"]
                    and needs.get(owner, {}).get("result") == "success",
                    "selected external skip owner is incomplete",
                )
    return {
        "schema": SCHEMA,
        "kind": "complete",
        "plan_sha256": digest(canonical(plan) + b"\n"),
        "repository": plan["repository"],
        "candidate_sha": plan["candidate_sha"],
        "candidate_tree": plan["candidate_tree"],
        "head_sha": plan["head_sha"],
        "base_sha": plan["base_sha"],
        "run_id": plan["run_id"],
        "run_attempt": plan["run_attempt"],
        "policy_sha256": plan["policy_sha256"],
        "required_producers": sorted(required),
        "lanes": reports,
        "qualification": False,
        "status": "passed",
    }


def hosted_module(directory: Path):
    spec = importlib.util.spec_from_file_location(
        "pr_ci_hosted", directory / "hosted_evidence.py"
    )
    if spec is None or spec.loader is None:
        raise SelectionError("trusted artifact reader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def api_list(client, path: str, key: str | None = None) -> list:
    rows = []
    for page in range(1, 11):
        data = client.get(
            path + ("&" if "?" in path else "?") + f"per_page=100&page={page}"
        )
        values = data if key is None else data.get(key)
        require(isinstance(values, list), "invalid hosted list")
        rows.extend(values)
        if key is not None:
            require(
                type(data.get("total_count")) is int
                and len(rows) <= data["total_count"],
                "hosted list count differs",
            )
            if len(rows) == data["total_count"]:
                return rows
        elif len(values) < 100:
            return rows
        require(values, "hosted pagination ended prematurely")
    raise SelectionError("hosted list page limit exceeded")


def reuse_main(
    root: Path,
    directory: Path,
    candidate: str,
    repository: str,
    run_id: int,
    attempt: int,
    client=None,
) -> dict:
    """Authenticate an exact-tree merged PR; never run or qualify downloaded code."""
    hosted = hosted_module(directory)
    require(
        SHA.fullmatch(candidate) is not None
        and type(run_id) is int
        and run_id > 0
        and type(attempt) is int
        and attempt > 0,
        "invalid main candidate/run identity",
    )
    require(
        git(root, "rev-parse", "HEAD").decode().strip() == candidate,
        "main checkout differs",
    )
    client = client or hosted.GitHub(repository)
    current_tree = git(root, "rev-parse", candidate + "^{tree}").decode().strip()
    prs = api_list(client, f"/commits/{candidate}/pulls")
    merged = [
        pr
        for pr in prs
        if pr.get("merged_at")
        and pr.get("merge_commit_sha") == candidate
        and pr.get("base", {}).get("ref") == "main"
        and pr.get("base", {}).get("repo", {}).get("full_name") == repository
    ]
    require(
        len(merged) == 1,
        "main needs one authenticated merged PR; direct/unknown pushes cannot reuse evidence",
    )
    pr = merged[0]
    runs = api_list(
        client,
        f"/actions/workflows/ci.yml/runs?event=pull_request&head_sha={pr['head']['sha']}",
        "workflow_runs",
    )
    require(bool(runs), "merged PR has no CI run")
    run = max(runs, key=lambda r: r["id"])
    fresh = client.get(f"/actions/runs/{run['id']}")
    require(
        fresh.get("id") == run["id"]
        and fresh.get("run_attempt") == run.get("run_attempt")
        and fresh.get("status") == "completed"
        and fresh.get("conclusion") == "success"
        and fresh.get("event") == "pull_request"
        and fresh.get("head_sha") == pr["head"]["sha"]
        and fresh.get("path", "").partition("@")[0] == WORKFLOW
        and fresh.get("name") == "CI"
        and fresh.get("repository", {}).get("full_name") == repository,
        "latest PR CI did not succeed or has wrong identity",
    )
    require(
        type(fresh.get("repository", {}).get("id")) is int
        and fresh["repository"]["id"] > 0
        and type(fresh.get("head_repository", {}).get("id")) is int
        and fresh["head_repository"]["id"] > 0,
        "hosted repository identities are unavailable",
    )
    workflow = client.get(f"/actions/workflows/{fresh['workflow_id']}")
    require(
        workflow.get("path") == WORKFLOW and workflow.get("name") == "CI",
        "hosted workflow identity differs",
    )
    jobs = api_list(
        client, f"/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs", "jobs"
    )
    complete = [
        job
        for job in jobs
        if job.get("name") == "CI complete"
        and job.get("conclusion") == "success"
        and job.get("run_id") == run["id"]
    ]
    require(len(complete) == 1, "PR aggregate producer did not succeed uniquely")
    artifacts = api_list(client, f"/actions/runs/{run['id']}/artifacts", "artifacts")
    selected = [
        a
        for a in artifacts
        if a.get("name") == f"pr-ci-complete-{run['run_attempt']}"
        and a.get("expired") is False
    ]
    require(len(selected) == 1, "current-attempt PR receipt is absent or ambiguous")
    artifact = selected[0]
    binding = artifact.get("workflow_run", {})
    require(
        binding.get("id") == run["id"]
        and binding.get("head_sha") == fresh["head_sha"]
        and binding.get("repository_id") == fresh["repository"]["id"]
        and binding.get("head_repository_id")
        == fresh.get("head_repository", {}).get("id"),
        "artifact repository/run binding differs",
    )
    require(
        type(artifact.get("size_in_bytes")) is int
        and 0 < artifact["size_in_bytes"] <= hosted.MAX_ARCHIVE,
        "PR artifact size exceeds existing transport limit",
    )
    require(
        hosted.timestamp(complete[0]["started_at"])
        <= hosted.timestamp(artifact["created_at"])
        <= hosted.timestamp(artifact["updated_at"])
        <= hosted.timestamp(complete[0]["completed_at"]),
        "artifact is not from the current aggregate attempt",
    )
    raw = client.archive(artifact["id"])
    require(
        len(raw) == artifact["size_in_bytes"]
        and "sha256:" + digest(raw) == artifact.get("digest"),
        "PR archive digest/size differs",
    )
    inventory = hosted.zip_inventory(raw)
    require(
        set(inventory) == {"complete.json", "plan.json"},
        "unexpected PR receipt archive members",
    )
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        receipt, old_plan = (
            strict_json(archive.read(name)) for name in ("complete.json", "plan.json")
        )
    require(
        receipt.get("schema") == SCHEMA
        and receipt.get("kind") == "complete"
        and receipt.get("status") == "passed"
        and receipt.get("qualification") is False
        and old_plan.get("mode") == "pull-request"
        and old_plan.get("schema") == SCHEMA
        and old_plan.get("qualification") is False
        and old_plan.get("pull_request") == pr["number"]
        and old_plan.get("policy_sha256") == receipt.get("policy_sha256")
        and old_plan.get("candidate_sha") == receipt.get("candidate_sha"),
        "invalid nonqualifying PR receipt",
    )
    for value in (receipt, old_plan):
        require(
            value.get("repository") == repository
            and value.get("head_sha") == pr["head"]["sha"]
            and value.get("base_sha") == pr["base"]["sha"]
            and value.get("candidate_tree") == current_tree
            and value.get("run_id") == run["id"]
            and value.get("run_attempt") == run["run_attempt"],
            "PR evidence tree/base/head/run differs",
        )
    require(
        receipt["plan_sha256"] == digest(canonical(old_plan) + b"\n"),
        "PR plan digest differs",
    )
    # Recheck current API state so a rerun begun during download invalidates reuse.
    latest = client.get(f"/actions/runs/{run['id']}")
    require(
        latest.get("id") == run["id"]
        and latest.get("run_attempt") == run["run_attempt"]
        and latest.get("status") == "completed"
        and latest.get("conclusion") == "success",
        "PR evidence attempt changed",
    )
    latest_runs = api_list(
        client,
        f"/actions/workflows/ci.yml/runs?event=pull_request&head_sha={pr['head']['sha']}",
        "workflow_runs",
    )
    require(
        bool(latest_runs) and max(r["id"] for r in latest_runs) == run["id"],
        "a newer PR run invalidates receipt reuse",
    )
    return {
        "schema": SCHEMA,
        "mode": "main-reuse",
        "repository": repository,
        "candidate_sha": candidate,
        "candidate_tree": current_tree,
        "head_sha": receipt["head_sha"],
        "base_sha": receipt["base_sha"],
        "policy_sha256": policy_identity(directory),
        "run_id": run_id,
        "run_attempt": attempt,
        "lanes": {},
        "jobs": ["activation-proof", "wiki-integrity"],
        "skip_edges": [],
        "qualification": False,
        "reuse": {
            "run_id": run["id"],
            "run_attempt": run["run_attempt"],
            "artifact_id": artifact["id"],
            "artifact_sha256": digest(raw),
            "candidate_tree": current_tree,
        },
    }


def outputs(plan: dict, plan_path: Path) -> None:
    lock = read_json(plan_path.parent / "toolchain-lock.json")["toolchains"]
    versions = {
        name: lock[name]["version"] for name in ("node", "go", "rust", "haskell")
    }
    require(
        all(
            isinstance(v, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v)
            for v in versions.values()
        ),
        "invalid locked toolchain version",
    )
    data = {
        "plan-sha256": digest(plan_path.read_bytes()),
        "policy-sha256": plan["policy_sha256"],
        "has-tests": str(bool(plan["lanes"])).lower(),
        "matrix": json.dumps(
            {
                "include": [
                    {
                        "lane": lane,
                        "os": row["os"],
                        "python": row["python"],
                        "profile": row.get("profile", "dev,mcp,tokens"),
                        **{
                            name: name in row["helpers"]
                            for name in ("typescript", "go", "rust", "haskell")
                        },
                        "node-version": versions["node"],
                        "go-version": versions["go"],
                    }
                    for lane, row in plan["lanes"].items()
                ]
            },
            separators=(",", ":"),
        ),
    }
    for job in (
        "typecheck",
        "mcp-sdk",
        "p0-oci-integration",
        "action",
        "dependency-controls",
        "package",
        "core-check-inputs",
        "core-check-comparison",
    ):
        data[job] = str(job in plan["jobs"]).lower()
    target = os.environ.get("GITHUB_OUTPUT")
    if target:
        with Path(target).open("a", encoding="utf-8") as stream:
            stream.write("".join(f"{key}={value}\n" for key, value in data.items()))
    print(json.dumps(data))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    plan_parser = subs.add_parser("plan")
    plan_parser.add_argument("--root", type=Path, required=True)
    plan_parser.add_argument("--event", type=Path, required=True)
    plan_parser.add_argument("--candidate", required=True)
    plan_parser.add_argument("--repository", required=True)
    plan_parser.add_argument("--run-id", type=int, required=True)
    plan_parser.add_argument("--attempt", type=int, required=True)
    plan_parser.add_argument("--output", type=Path, required=True)
    preview = subs.add_parser(
        "preview", help="Read-only agent proposal; never CI or release authority"
    )
    preview.add_argument("--root", type=Path, required=True)
    preview.add_argument("--base", required=True)
    preview.add_argument("--head", required=True)
    preview.add_argument("--body", type=Path)
    for name in ("run", "gate", "prepare"):
        command = subs.add_parser(name)
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--expected-sha256", required=True)
        if name != "prepare":
            command.add_argument("--output", type=Path, required=True)
        if name in {"run", "prepare"}:
            command.add_argument("--root", type=Path, required=True)
            command.add_argument("--lane", choices=tuple(LANES), required=True)
            if name == "prepare":
                command.add_argument("--cache", type=Path, required=True)
        else:
            command.add_argument("--needs", type=Path, required=True)
            command.add_argument("--reports", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "preview":
            directory = Path(__file__).resolve().parent
            body = None
            if args.body:
                require(
                    args.body.is_file() and args.body.stat().st_size <= MAX_JSON,
                    "proposal body unavailable or oversized",
                )
                body = args.body.read_text(encoding="utf-8")
            result = select(
                policy_load(directory),
                blobs(args.root, tree(args.root, args.base)),
                blobs(args.root, tree(args.root, args.head)),
                changes(args.root, args.base, args.head),
                body,
                read_json(directory / "skip-allowlist.json"),
            )
            print(
                json.dumps(
                    {
                        "schema": SCHEMA,
                        "mode": "preview",
                        "authority": "proposal-only; trusted base validation remains required",
                        "base_sha": args.base,
                        "head_sha": args.head,
                        **result,
                    },
                    indent=2,
                )
            )
        elif args.command == "plan":
            directory = Path(__file__).resolve().parent
            event = read_json(args.event)
            if "pull_request" in event:
                result = make_plan(
                    args.root,
                    directory,
                    event,
                    args.candidate,
                    args.repository,
                    args.run_id,
                    args.attempt,
                )
            else:
                require(
                    event.get("ref") == "refs/heads/main"
                    and event.get("after") == args.candidate
                    and event.get("repository", {}).get("full_name") == args.repository,
                    "untrusted main push event",
                )
                result = reuse_main(
                    args.root,
                    directory,
                    args.candidate,
                    args.repository,
                    args.run_id,
                    args.attempt,
                )
            write_json(args.output, result)
            outputs(result, args.output)
        elif args.command == "run":
            run_lane(args)
        elif args.command == "prepare":
            prepare_lane(args)
        else:
            plan = verify_plan(args.plan, args.expected_sha256)
            reports = lane_reports(plan, args.reports)
            result = aggregate(plan, read_json(args.needs), reports)
            write_json(args.output, result)
    except (
        SelectionError,
        ValueError,
        OSError,
        KeyError,
        TypeError,
        ET.ParseError,
    ) as exc:
        print("Selective CI refused: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
