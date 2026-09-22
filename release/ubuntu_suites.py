"""Collected Ubuntu suite execution and fail-closed, nonqualifying comparison.

Validation uses only the standard library. Pytest is imported only in the worker
process inside the installed candidate's virtual environment.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any
import xml.etree.ElementTree as ET

# Load the sibling from the verified harness, including when invoked with -I.
_spec = importlib.util.spec_from_file_location(
    "_ubuntu_qualification", Path(__file__).with_name("qualification.py")
)
assert _spec is not None and _spec.loader is not None
q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q)

LANES = ("slow", "determinism", "security-ubuntu-24.04", "product-ubuntu-24.04")
PROFILE = {
    "os": "ubuntu-24.04",
    "python": "3.13",
    "extras": ["dev"],
    "install": "noneditable",
}
FLAGS = [
    "-q",
    "-p",
    "no:cacheprovider",
    "--strict-config",
    "--strict-markers",
    "-W",
    "error",
    "-o",
    "xfail_strict=true",
]
SCHEMA = "agent-wiki-ubuntu-execution/v1"
INVENTORY_SCHEMA = "agent-wiki-ubuntu-inventory/v1"
TIMEOUT = 1800


def require(condition: bool, message: str) -> None:
    if not condition:
        raise q.QualificationError(message)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def registry(path: Path) -> dict[str, Any]:
    value = q.load_json(path)
    require(
        isinstance(value, dict)
        and set(value) == {"schema_version", "profile", "pytest_flags", "gates"},
        "invalid suite registry fields",
    )
    require(
        value["schema_version"] == "agent-wiki-ubuntu-suites/v1"
        and value["profile"] == PROFILE
        and value["pytest_flags"] == FLAGS,
        "unsupported suite profile/flags",
    )
    require(
        isinstance(value["gates"], dict) and set(value["gates"]) == set(LANES),
        "suite gate membership differs",
    )
    for lane, selectors in value["gates"].items():
        require(
            isinstance(selectors, list)
            and bool(selectors)
            and all(isinstance(s, str) for s in selectors),
            f"invalid selectors for {lane}",
        )
        require(len(selectors) == len(set(selectors)), f"duplicate selector in {lane}")
        for selector in selectors:
            q._canonical_junit_selector(selector)
    return value


def resolve(nodes: list[str], contract: dict[str, Any]) -> dict[str, Any]:
    require(
        isinstance(nodes, list)
        and bool(nodes)
        and all(isinstance(node, str) for node in nodes)
        and len(nodes) == len(set(nodes)),
        "empty or duplicate canonical collected node IDs",
    )
    for node in nodes:
        q._canonical_junit_selector(node)
        require("::" in node, f"not a collected node: {node}")
    gates: dict[str, list[str]] = {}
    for lane, selectors in contract["gates"].items():
        selected: set[str] = set()
        for selector in selectors:
            matches = {node for node in nodes if q._selector_matches(selector, node)}
            require(bool(matches), f"selector matched no collected tests: {selector}")
            selected.update(matches)
        gates[lane] = sorted(selected)
    union = sorted({node for selected in gates.values() for node in selected})
    return {
        "schema_version": INVENTORY_SCHEMA,
        "collected": sorted(nodes),
        "gates": gates,
        "union": union,
        "membership": {
            node: sorted(lane for lane in gates if node in gates[lane])
            for node in union
        },
    }


def files_for(root: Path, selectors: list[str]) -> list[str]:
    result: set[str] = set()
    for selector in selectors:
        q._canonical_junit_selector(selector)
        pattern = selector.partition("::")[0]
        matches = sorted(root.glob(pattern))
        require(bool(matches), f"selector matched no files: {selector}")
        for path in matches:
            require(
                path.is_file()
                and not path.is_symlink()
                and root.resolve() in path.resolve().parents,
                f"unsafe suite file: {path}",
            )
            result.add(path.relative_to(root).as_posix())
    return sorted(result)


def environment(root: Path | None = None) -> dict[str, Any]:
    require(
        sys.prefix != sys.base_prefix,
        "suite execution requires a fresh virtual environment",
    )
    require(
        platform.system() == "Linux" and sys.version_info[:2] == (3, 13),
        "suite profile requires Linux/Python 3.13",
    )
    # freedesktop_os_release exists on every supported execution interpreter.
    distro = platform.freedesktop_os_release()
    require(
        distro.get("ID") == "ubuntu" and distro.get("VERSION_ID") == "24.04",
        "suite profile requires Ubuntu 24.04",
    )
    packages: dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"].lower().replace("_", "-")
        require(name not in packages, f"duplicate installed distribution: {name}")
        packages[name] = dist.version
    require(
        not {"tokenizers", "mcp"}.intersection(packages),
        "tokens/MCP extras cannot enter the Ubuntu dev profile",
    )
    provider = importlib.metadata.distribution("agent-wiki-cli")
    direct = json.loads(provider.read_text("direct_url.json") or "{}")
    require(
        direct.get("dir_info", {}).get("editable") is not True,
        "candidate must be installed noneditably",
    )
    if root is not None:
        require(
            direct.get("url") == root.resolve().as_uri(),
            "installed candidate source differs from execution root",
        )
    require(
        Path(sys.prefix).resolve()
        in Path(str(provider.locate_file(""))).resolve().parents,
        "candidate installation is outside the virtual environment",
    )
    return {
        "profile": PROFILE,
        "python": platform.python_version(),
        "machine": platform.machine(),
        "runner_image": os.environ.get("ImageVersion", "unreported"),
        "packages": dict(sorted(packages.items())),
    }


def validate_environment(value: Any) -> None:
    require(
        isinstance(value, dict)
        and set(value) == {"profile", "python", "machine", "runner_image", "packages"},
        "invalid environment receipt",
    )
    for field in ("machine", "runner_image"):
        require(
            isinstance(value[field], str) and bool(value[field].strip()),
            f"environment {field} must be a non-empty string",
        )
    require(
        value["profile"] == PROFILE
        and isinstance(value["python"], str)
        and value["python"].startswith("3.13."),
        "environment profile differs",
    )
    packages = value["packages"]
    require(
        isinstance(packages, dict)
        and {"agent-wiki-cli", "pytest", "pytest-cov"} <= packages.keys()
        and not {"tokenizers", "mcp"}.intersection(packages),
        "environment package profile differs",
    )
    require(
        all(
            isinstance(k, str) and isinstance(v, str) and v for k, v in packages.items()
        ),
        "invalid distribution versions",
    )


def frozen_inputs(args: argparse.Namespace) -> dict[str, Any]:
    identity = q._validate_identity(q.load_json(args.identity))
    require(
        q.sha256_file(args.harness) == args.harness_sha256, "harness digest mismatch"
    )
    with tarfile.open(args.harness) as archive:
        require(
            archive.pax_headers.get("comment") == identity["source"]["sha"],
            "harness/source candidate mismatch",
        )
        for name in (
            "qualification.py",
            "ubuntu_suites.py",
            "ubuntu_shadow.py",
            "ubuntu-suites.json",
        ):
            member = archive.extractfile("release/" + name)
            require(member is not None, f"harness input missing: {name}")
            assert member is not None
            require(
                member.read() == Path(__file__).with_name(name).read_bytes(),
                f"harness input differs: {name}",
            )
    require(
        args.registry.read_bytes()
        == Path(__file__).with_name("ubuntu-suites.json").read_bytes(),
        "registry differs from frozen harness",
    )
    return {
        "identity": identity,
        "identity_sha256": q.sha256_file(args.identity),
        "harness_sha256": args.harness_sha256,
        "registry_sha256": q.sha256_file(args.registry),
    }


def context(args: argparse.Namespace) -> dict[str, Any]:
    return {**frozen_inputs(args), "environment": environment(args.root)}


def outcomes(path: Path) -> dict[str, dict[str, str]]:
    statuses = q._junit_node_outcomes(path)
    require(bool(statuses), f"empty JUnit: {path}")
    result = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        node = q._node_id(case)
        skip = case.find("skipped")
        result[node] = {
            "outcome": statuses[node],
            "reason": ""
            if skip is None
            else skip.get("message") or (skip.text or "").strip(),
        }
    return dict(sorted(result.items()))


def worker(args: argparse.Namespace) -> int:
    import pytest

    contract = registry(args.registry)
    selectors = [s for lane in LANES for s in contract["gates"][lane]]
    files = files_for(Path.cwd(), selectors)
    started: list[str] = []
    collected: list[str] = []
    expected = None if args.collect else q.load_json(args.inventory)

    class InventoryPlugin:
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            collected.extend(item.nodeid for item in items)
            observed = resolve(collected, contract)
            if expected is not None:
                require(
                    observed == expected,
                    "execution collection differs from frozen inventory",
                )
                chosen = set(expected["union"])
                rejected = [item for item in items if item.nodeid not in chosen]
                items[:] = [item for item in items if item.nodeid in chosen]
                config.hook.pytest_deselected(items=rejected)
            q.write_json(args.observed, observed)

        def pytest_runtest_logstart(self, nodeid, location):
            started.append(nodeid)

    flags = FLAGS + files
    flags += ["--collect-only"] if args.collect else [f"--junitxml={args.junit}"]
    code = int(pytest.main(flags, plugins=[InventoryPlugin()]))
    if not args.collect:
        q.write_json(args.started, started)
    return code


def invoke(command: list[str], root: Path, log: Path) -> dict[str, Any]:
    start = time.monotonic()
    with log.open("wb") as output:
        try:
            code = subprocess.run(
                command,
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            code = 124
    return {"exit_code": code, "seconds": time.monotonic() - start}


def projection(
    root: Path,
    lane: str,
    identity: Path,
    inventory: dict[str, Any],
    execution: dict[str, Any],
) -> None:
    q.project_junit(
        argparse.Namespace(
            identity=identity,
            source_junit=root / "union.xml",
            source_lane="ubuntu-union",
            target_lane=lane,
            selector=inventory["gates"][lane],
            projected_junit=root / f"{lane}.xml",
            receipt=root / f"{lane}-projection.json",
        )
    )
    receipt = q.load_json(root / f"{lane}-projection.json")
    receipt["lineage"] = {
        "harness_sha256": execution["harness_sha256"],
        "registry_sha256": execution["registry_sha256"],
        "environment_sha256": digest(execution["environment"]),
        "inventory_sha256": q.sha256_file(root / "inventory.json"),
        "execution_sha256": q.sha256_file(root / "execution.json"),
    }
    q.write_json(root / f"{lane}-projection.json", receipt)


def execute(args: argparse.Namespace) -> int:
    root, output = args.root.resolve(), args.output.resolve()
    require(
        not output.exists(),
        "execution output must be new (stale evidence is forbidden)",
    )
    output.mkdir(parents=True)
    start = time.monotonic()
    execution: dict[str, Any] = {
        "schema_version": SCHEMA,
        "mode": args.mode,
        "complete": False,
        "runs": {},
    }
    q.write_json(output / "execution.json", execution)
    execution.update(context(args))
    contract = registry(args.registry)
    q.write_json(output / "registry.json", contract)
    q.write_json(output / "identity.json", execution["identity"])
    # Record setup separately from test execution without claiming runner billing.
    execution["setup_seconds"] = max(0.0, time.time() - args.setup_started)
    if args.mode == "union":
        worker_command = [
            sys.executable,
            "-I",
            str(Path(__file__).resolve()),
            "worker",
            "--registry",
            str(args.registry.resolve()),
        ]
        collection = invoke(
            worker_command
            + ["--collect", "--observed", str(output / "inventory.json")],
            root,
            output / "collection.log",
        )
        execution["runs"]["collection"] = collection
        if collection["exit_code"] == 0:
            execution["runs"]["union"] = invoke(
                worker_command
                + [
                    "--inventory",
                    str(output / "inventory.json"),
                    "--observed",
                    str(output / "observed.json"),
                    "--started",
                    str(output / "started.json"),
                    "--junit",
                    str(output / "union.xml"),
                ],
                root,
                output / "union.log",
            )
        expected = {"collection", "union"}
    else:
        require(
            bool(args.lane)
            and len(args.lane) == len(set(args.lane))
            and set(args.lane) <= set(LANES),
            "invalid legacy lanes",
        )
        for lane in args.lane:
            expanded: list[str] = []
            for selector in contract["gates"][lane]:
                expanded.extend(
                    [selector] if "::" in selector else files_for(root, [selector])
                )
            execution["runs"][lane] = invoke(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    *FLAGS,
                    *expanded,
                    f"--junitxml={output / (lane + '.xml')}",
                ],
                root,
                output / f"{lane}.log",
            )
        expected = set(args.lane)
    execution["execution_seconds"] = time.monotonic() - start
    execution["complete"] = set(execution["runs"]) == expected and all(
        row["exit_code"] == 0 for row in execution["runs"].values()
    )
    execution["files"] = {
        p.name: q.sha256_file(p)
        for p in sorted(output.iterdir())
        if p.suffix in {".xml", ".json"} and p.name != "execution.json"
    }
    q.write_json(output / "execution.json", execution)
    if not execution["complete"]:
        return 1
    if args.mode == "union":
        validation_started = time.monotonic()
        validate_execution(
            output,
            execution["identity"],
            args.harness_sha256,
            args.registry,
            projections=False,
        )
        validation_seconds = time.monotonic() - validation_started
        projection_start = time.monotonic()
        inventory = q.load_json(output / "inventory.json")
        for lane in LANES:
            projection(output, lane, output / "identity.json", inventory, execution)
        projection_seconds = time.monotonic() - projection_start
        q.write_json(output / "projection-timing.json", {"seconds": projection_seconds})
        validation_started = time.monotonic()
        validate_execution(
            output, execution["identity"], args.harness_sha256, args.registry
        )
        q.write_json(
            output / "postprocessing.json",
            {
                "qualifying": False,
                "execution_sha256": q.sha256_file(output / "execution.json"),
                "projection_seconds": projection_seconds,
                "validation_seconds": validation_seconds
                + time.monotonic()
                - validation_started,
                "total_seconds": time.monotonic() - start,
            },
        )
    return 0


def validate_execution(
    root: Path,
    identity: Any,
    harness: str,
    registry_path: Path,
    *,
    projections: bool = True,
) -> dict[str, Any]:
    execution = q.load_json(root / "execution.json")
    require(
        isinstance(execution, dict)
        and set(execution)
        == {
            "schema_version",
            "mode",
            "complete",
            "runs",
            "identity",
            "identity_sha256",
            "harness_sha256",
            "registry_sha256",
            "environment",
            "setup_seconds",
            "execution_seconds",
            "files",
        }
        and execution.get("schema_version") == SCHEMA
        and execution.get("mode") in {"union", "legacy"}
        and execution.get("complete") is True,
        "incomplete Ubuntu execution",
    )
    require(
        execution.get("identity") == identity
        and q.load_json(root / "identity.json") == identity,
        "Ubuntu candidate identity differs",
    )
    require(
        execution.get("identity_sha256") == q.sha256_file(root / "identity.json"),
        "Ubuntu identity digest differs",
    )
    require(
        q.SHA256_RE.fullmatch(harness) is not None
        and execution.get("harness_sha256") == harness,
        "Ubuntu harness identity differs",
    )
    contract = registry(registry_path)
    require(
        execution.get("registry_sha256") == q.sha256_file(registry_path)
        and q.load_json(root / "registry.json") == contract,
        "Ubuntu selector contract differs",
    )
    validate_environment(execution.get("environment"))
    require(
        execution["environment"]["packages"]["agent-wiki-cli"] == identity["version"],
        "installed candidate version differs",
    )
    runs = execution.get("runs")
    require(
        isinstance(runs, dict)
        and bool(runs)
        and all(
            isinstance(row, dict)
            and set(row) == {"exit_code", "seconds"}
            and type(row.get("exit_code")) is int
            and row["exit_code"] == 0
            for row in runs.values()
        ),
        "Ubuntu source process did not succeed",
    )
    assert isinstance(runs, dict)  # Narrow the shape already checked above.
    timings = [
        execution.get("setup_seconds"),
        execution.get("execution_seconds"),
        *(row.get("seconds") for row in runs.values()),
    ]
    require(
        all(
            type(value) in (float, int) and math.isfinite(value) and value >= 0
            for value in timings
        ),
        "invalid execution timing",
    )
    union = execution["mode"] == "union"
    require(
        set(runs) == {"collection", "union"} if union else set(runs) <= set(LANES),
        "unexpected Ubuntu execution runs",
    )
    expected_files = {"identity.json", "registry.json"} | (
        {"inventory.json", "observed.json", "started.json", "union.xml"}
        if union
        else {lane + ".xml" for lane in runs}
    )
    require(
        set(execution.get("files", {})) == expected_files,
        "execution evidence membership differs",
    )
    for name in expected_files:
        require(
            q.sha256_file(root / name) == execution["files"][name],
            f"altered execution evidence: {name}",
        )
    if not union:
        for lane in runs:
            require(
                all(
                    v["outcome"] in {"passed", "skipped"}
                    for v in outcomes(root / f"{lane}.xml").values()
                ),
                "legacy failures cannot qualify",
            )
        return execution
    inventory = q.load_json(root / "inventory.json")
    require(
        inventory == resolve(inventory["collected"], contract),
        "inventory does not resolve the suite contract",
    )
    require(
        q.load_json(root / "observed.json") == inventory, "observed inventory differs"
    )
    started = q.load_json(root / "started.json")
    require(
        isinstance(started, list)
        and all(isinstance(node, str) for node in started)
        and Counter(started) == Counter(inventory["union"]),
        "each union node must execute exactly once",
    )
    raw = outcomes(root / "union.xml")
    require(
        sorted(raw) == inventory["union"]
        and all(v["outcome"] in {"passed", "skipped"} for v in raw.values()),
        "union JUnit has missing, extra or failing nodes",
    )
    if projections:
        # Reproduce projection bytes and receipts rather than trusting declared
        # counts or hashes from an artifact submitted by a producer.
        with tempfile.TemporaryDirectory() as temporary:
            scratch = Path(temporary)
            for name in expected_files | {"execution.json"}:
                (scratch / name).write_bytes((root / name).read_bytes())
            for lane in LANES:
                projection(
                    scratch, lane, scratch / "identity.json", inventory, execution
                )
                for name in (f"{lane}.xml", f"{lane}-projection.json"):
                    require(
                        (scratch / name).read_bytes() == (root / name).read_bytes(),
                        f"projection lineage differs: {name}",
                    )
    return execution


def _compare(args: argparse.Namespace, diagnostic: dict[str, Any]) -> int:
    diagnostic["stage"] = "identity"
    identity = q._validate_identity(q.load_json(args.identity))
    diagnostic["identity"] = identity
    diagnostic["stage"] = "union-validation"
    union = validate_execution(args.union, identity, args.harness_sha256, args.registry)
    require(union["mode"] == "union", "comparison requires union execution")
    legacy: dict[str, dict[str, dict[str, str]]] = {}
    timings = {}
    diagnostic["stage"] = "legacy-validation"
    for directory in args.legacy:
        item = validate_execution(
            directory, identity, args.harness_sha256, args.registry
        )
        require(item["mode"] == "legacy", "comparison requires legacy execution")
        differences = {
            key: {"union": union["environment"].get(key), "legacy": value}
            for key, value in item["environment"].items()
            if value != union["environment"].get(key)
        }
        if differences:
            diagnostic["environment_differences"][directory.name] = differences
        for lane in item["runs"]:
            require(lane not in legacy, f"duplicate legacy lane: {lane}")
            legacy[lane] = outcomes(directory / f"{lane}.xml")
            timings[lane] = item["runs"][lane]["seconds"]
    require(set(legacy) == set(LANES), "missing legacy suite")
    diagnostic["stage"] = "environment-comparison"
    require(
        not diagnostic["environment_differences"],
        "legacy/union execution environments differ",
    )
    diagnostic["stage"] = "outcome-comparison"
    for lane in LANES:
        require(
            legacy[lane] == outcomes(args.union / f"{lane}.xml"),
            f"legacy/union nodes, outcomes or skip reasons differ: {lane}",
        )
    diagnostic["stage"] = "skip-ownership"
    inventory = q.load_json(args.union / "inventory.json")
    allowlist = q._load_skip_allowlist(args.allowlist)
    obligations = [item for item in allowlist if item["owner_lane"] in LANES]
    for item in obligations:
        row = legacy[item["owner_lane"]].get(item["node_id"])
        require(
            row is not None and row["outcome"] == "passed",
            f"Ubuntu skip owner did not pass: {item}",
        )
    q.write_json(
        args.output,
        {
            **diagnostic,
            "passed": True,
            "complete": True,
            "stage": "complete",
            "identity": identity,
            "harness_sha256": args.harness_sha256,
            "registry_sha256": q.sha256_file(args.registry),
            "allowlist_sha256": q.sha256_file(args.allowlist),
            "owner_obligations": obligations,
            "union_execution_sha256": q.sha256_file(args.union / "execution.json"),
            "legacy_execution_sha256": [
                q.sha256_file(p / "execution.json") for p in args.legacy
            ],
            "unique_nodes": len(inventory["union"]),
            "legacy_executions": sum(map(len, legacy.values())),
            "timing": {
                "legacy_tests_seconds": timings,
                "union": union["runs"],
                "projection": q.load_json(args.union / "projection-timing.json"),
                "legacy_setup_seconds": [
                    q.load_json(p / "execution.json")["setup_seconds"]
                    for p in args.legacy
                ],
                "union_setup_seconds": union["setup_seconds"],
                "confidence": "one comparison; step wall time only, not hosted billing or a speed SLO",
            },
        },
    )
    return 0


SHADOW_PRODUCERS = ("legacy-slow", "legacy-security", "legacy-product", "union")


def comparison_diagnostic(stage: str) -> dict[str, Any]:
    return {
        "schema_version": "agent-wiki-ubuntu-shadow/v1",
        "qualifying": False,
        "passed": False,
        "complete": False,
        "stage": stage,
        "producer_results": {},
        "environment_differences": {},
        "errors": [],
    }


def compare(args: argparse.Namespace) -> int:
    # Never replace an input receipt while initializing an output diagnostic.
    output = args.output.resolve()
    protected = [
        args.identity.resolve(),
        args.registry.resolve(),
        args.allowlist.resolve(),
    ]
    roots = [args.union.resolve(), *(path.resolve() for path in args.legacy)]
    require(
        output not in protected
        and not any(output == root or root in output.parents for root in roots),
        "comparison output must be separate from input evidence",
    )
    diagnostic = comparison_diagnostic("producer-status")
    q.write_json(output, diagnostic)
    started = time.monotonic()
    try:
        for spec in getattr(args, "producer_result", []):
            name, separator, status = spec.partition("=")
            require(
                bool(separator)
                and name in SHADOW_PRODUCERS
                and name not in diagnostic["producer_results"],
                f"invalid or duplicate producer result: {spec}",
            )
            diagnostic["producer_results"][name] = status
        if getattr(args, "producer_result", []):
            require(
                set(diagnostic["producer_results"]) == set(SHADOW_PRODUCERS)
                and all(
                    value == "success"
                    for value in diagnostic["producer_results"].values()
                ),
                "shadow producers did not all succeed",
            )
        result = _compare(args, diagnostic)
    except (q.QualificationError, OSError, ValueError, KeyError, TypeError) as exc:
        diagnostic["errors"].append({"type": type(exc).__name__, "message": str(exc)})
        diagnostic["validation_seconds"] = time.monotonic() - started
        q.write_json(output, diagnostic)
        raise
    payload = q.load_json(output)
    payload["validation_seconds"] = time.monotonic() - started
    q.write_json(output, payload)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--mode", choices=("union", "legacy"), required=True)
    run.add_argument("--lane", action="append", default=[])
    run.add_argument("--root", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--harness", type=Path, required=True)
    run.add_argument("--setup-started", type=float, required=True)
    run.set_defaults(func=execute)
    comparison = commands.add_parser("compare")
    comparison.add_argument("--union", type=Path, required=True)
    comparison.add_argument("--legacy", type=Path, action="append", required=True)
    comparison.add_argument("--allowlist", type=Path, required=True)
    comparison.add_argument("--output", type=Path, required=True)
    comparison.add_argument("--producer-result", action="append", default=[])
    comparison.set_defaults(func=compare)
    for command in (run, comparison):
        command.add_argument("--identity", type=Path, required=True)
        command.add_argument("--harness-sha256", required=True)
        command.add_argument("--registry", type=Path, required=True)
    description = commands.add_parser("environment")
    description.add_argument("--root", type=Path, required=True)
    description.add_argument("--output", type=Path, required=True)
    description.set_defaults(
        func=lambda a: q.write_json(a.output, environment(a.root)) or 0
    )
    work = commands.add_parser("worker")
    work.add_argument("--registry", type=Path, required=True)
    work.add_argument("--collect", action="store_true")
    work.add_argument("--inventory", type=Path)
    work.add_argument("--observed", type=Path, required=True)
    work.add_argument("--started", type=Path)
    work.add_argument("--junit", type=Path)
    work.set_defaults(func=worker)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (q.QualificationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Ubuntu suites refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
