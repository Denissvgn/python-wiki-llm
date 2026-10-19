"""Trusted local adapters for maintained release producers; never publication authority.

Receipt arguments are data, not executable commands. Every subprocess command is
constructed here and scratch belongs to one explicitly claimed operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import sys
import subprocess
import time
from typing import Any
import uuid
import zipfile
from pathlib import PurePosixPath

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))

OWNER_SCHEMA = "agent-wiki-local-preflight-work/v1"
ATTEMPT_SCHEMA = "agent-wiki-local-preflight-attempt/v1"
OWNER_FILE = ".preflight-owner.json"
STAGES = (
    "prepare",
    "contracts",
    "static",
    "freeze",
    "host-core",
    "builds",
    "artifacts",
    "rehearsal",
)
INDEPENDENT_CHECKS = {
    "contract-preflight",
    "maintained-static-checks",
    "repository-doctor",
    "wiki-lint",
    "repository-ci",
    "storage-audit",
    "source-archive-budget",
}


class RunnerError(ValueError):
    """Preparation or execution cannot satisfy its declared local contract."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _read_json(path: Path) -> Any:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RunnerError("duplicate scratch metadata key")
            result[key] = value
        return result

    def constant(value):
        raise RunnerError("nonfinite scratch metadata: " + value)

    _safe(path)
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise RunnerError("scratch metadata is missing or oversized")
    return json.loads(
        path.read_bytes(), object_pairs_hook=unique, parse_constant=constant
    )


def _safe(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        if (
            stat.S_ISLNK(metadata.st_mode)
            or getattr(metadata, "st_file_attributes", 0) & 0x400
        ):
            raise RunnerError(
                "scratch path traverses a symbolic link or reparse point: "
                + str(current)
            )


def absolute_launcher(path: Path) -> Path:
    """Preserve bin/python symlinks: resolving them selects the base interpreter."""
    return Path(os.path.abspath(path))


def launcher_probe(
    repo: Path, launcher: Path | None = None, *, expected_prefix: Path | None = None
) -> dict:
    launcher = absolute_launcher(launcher or _python(repo / ".venv"))
    prefix = absolute_launcher(expected_prefix or repo / ".venv")
    script = """import importlib.metadata,importlib.util,json,platform,sys
try:
    distribution_version = importlib.metadata.version('agent-wiki-cli')
except importlib.metadata.PackageNotFoundError:
    distribution_version = None
provider = importlib.util.find_spec('llm_wiki_cli')
print(json.dumps({'executable':sys.executable,'prefix':sys.prefix,
    'base_prefix':sys.base_prefix,'python':platform.python_version(),
    'system':platform.system(),'architecture':platform.machine(),
    'distribution_version':distribution_version,
    'provider_origin':provider.origin if provider is not None else None}))
"""
    try:
        child = subprocess.run(
            [str(launcher), "-I", "-c", script],
            cwd=repo,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if child.returncode:
            raise RunnerError(
                "launcher identity probe failed before environment mutation"
            )
        observed = json.loads(child.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise RunnerError(
            "launcher identity unavailable before environment mutation"
        ) from exc
    if (
        not isinstance(observed, dict)
        or absolute_launcher(Path(observed.get("prefix", ""))) != prefix
        or observed.get("prefix") == observed.get("base_prefix")
        or absolute_launcher(Path(observed.get("executable", ""))) != launcher
    ):
        raise RunnerError(
            "launcher/prefix mismatch; no package environment was changed"
        )
    return {"launcher": str(launcher), **observed}


def claim_work(work: Path, binding: dict) -> Path:
    work = Path(os.path.abspath(work))
    _safe(work)
    if not work.parent.is_dir():
        raise RunnerError("work parent must already exist")
    try:
        work.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise RunnerError(
            "work path is occupied; an unowned path cannot be adopted"
        ) from exc
    metadata = work.stat()
    marker = {
        "schema_version": OWNER_SCHEMA,
        "binding": binding,
        "identity": [metadata.st_dev, metadata.st_ino],
        "operation_id": str(uuid.uuid4()),
    }
    with (work / OWNER_FILE).open("xb") as stream:
        stream.write(_canonical(marker) + b"\n")
    return work


def validate_owned_work(work: Path, binding: dict) -> Path:
    work = Path(os.path.abspath(work))
    _safe(work)
    value = _read_json(work / OWNER_FILE)
    metadata = work.stat()
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "binding", "identity", "operation_id"}
        or value["schema_version"] != OWNER_SCHEMA
        or value["binding"] != binding
        or value["identity"] != [metadata.st_dev, metadata.st_ino]
    ):
        raise RunnerError("work owner or plan binding mismatch")
    return work


@dataclass(frozen=True)
class Command:
    name: str
    argv: tuple[str, ...]
    cwd: Path
    timeout: int = 600
    environment: dict[str, str] = field(default_factory=dict)
    # Probe newly created consumers before any pip install; never trust their path spelling alone.
    expected_prefix: Path | None = None


def _python(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _strict_pytest(python: str, junit: Path, *selectors: str) -> tuple[str, ...]:
    return (
        python,
        "-m",
        "pytest",
        *selectors,
        "-q",
        "-p",
        "no:cacheprovider",
        "--strict-config",
        "--strict-markers",
        "-W",
        "error",
        "-o",
        "xfail_strict=true",
        "--junitxml=" + str(junit),
    )


def verify_host_junit(
    *, repo: Path, inventory_path: Path, started_path: Path, junit_path: Path,
    allowlist_path: Path, lane: str, minimum_collected: int = 5322,
    minimum_passed: int = 5070,
) -> dict:
    """Verify a complete local collection without requiring helpers to be absent.

    The hosted lane's exact owned reasons bound any local skips. Passing one of
    those conditional cases locally never satisfies its required hosted owner.
    """
    from release import core_shards as shards, qualification as q

    if any(type(value) is not int or value <= 0 for value in (minimum_collected, minimum_passed)):
        raise RunnerError("host core minimums must be positive integers")
    if lane not in {"core-macos-3.14", "core-windows-3.13", "core-ubuntu-3.10"}:
        raise RunnerError("host core has no maintained baseline lane")
    repo, inventory_path, started_path, junit_path, allowlist_path = (
        Path(os.path.abspath(path)) for path in (repo, inventory_path, started_path, junit_path, allowlist_path)
    )
    try:
        return _host_junit_report(
            repo=repo, inventory_path=inventory_path, started_path=started_path,
            junit_path=junit_path, allowlist_path=allowlist_path, lane=lane,
            minimum_collected=minimum_collected, minimum_passed=minimum_passed,
        )
    except (q.QualificationError, shards.q.QualificationError) as exc:
        raise RunnerError(str(exc)) from exc


def _host_junit_report(
    *, repo: Path, inventory_path: Path, started_path: Path, junit_path: Path,
    allowlist_path: Path, lane: str, minimum_collected: int, minimum_passed: int,
) -> dict:
    from release import core_shards as shards, qualification as q

    for path in (repo, inventory_path, started_path, junit_path, allowlist_path):
        _safe(path)
    nodes = shards.inventory(shards.read(inventory_path))
    if not started_path.is_file() or started_path.stat().st_size:
        raise RunnerError("host collection unexpectedly executed tests")
    with started_path.open("rb") as stream:
        if stream.read(1):
            raise RunnerError("host collection unexpectedly executed tests")
    for name in {shards.file_name(node) for node in nodes}:
        _safe(repo / name)
        if not (repo / name).is_file():
            raise RunnerError("host collection refers to an absent source file")
    entries = [row for row in q._load_skip_allowlist(allowlist_path) if row["lane"] == lane]
    expected = {row["node_id"]: row for row in entries}
    if len(expected) != len(entries) or not set(expected) <= set(nodes):
        raise RunnerError("host collection omits or ambiguously owns baseline conditional cases")
    cases = shards.junit(junit_path)
    if set(cases) != set(nodes):
        raise RunnerError("host JUnit differs from the complete collected inventory")
    counts = {"collected": len(cases), "passed": 0, "skipped": 0, "failed": 0, "errors": 0}
    skips = []
    for node, case in cases.items():
        if case.find("failure") is not None:
            counts["failed"] += 1
        elif case.find("error") is not None:
            counts["errors"] += 1
        elif (skipped := case.find("skipped")) is not None:
            reason = skipped.attrib.get("message") or (skipped.text or "").strip()
            if node not in expected or expected[node]["reason"] != reason:
                raise RunnerError("host core has an unowned skip or changed reason: " + node)
            counts["skipped"] += 1
            skips.append({"node_id": node, "reason": reason, "owner_lane": expected[node]["owner_lane"]})
        else:
            counts["passed"] += 1
    if counts["failed"] or counts["errors"]:
        raise RunnerError("host core has failures/errors")
    if counts["collected"] < minimum_collected or counts["passed"] < minimum_passed:
        raise RunnerError("host core is below the maintained collection/pass minimum")
    return {
        "schema_version": "agent-wiki-local-core-result/v1", "state": "passed",
        "root": str(repo), "baseline_lane": lane, "inventory_complete": True,
        "inventory_sha256": q.sha256_file(inventory_path), "junit_sha256": q.sha256_file(junit_path),
        "counts": counts, "skips": sorted(skips, key=lambda row: row["node_id"]),
        "conditional_passes": sorted(node for node in expected if cases[node].find("skipped") is None),
        "pending_hosted_owners": sorted({row["owner_lane"] for row in entries}),
        "publication_authority": False,
        "qualification": "Local complete-collection verification only; native/hosted owners and policy approval remain independently required",
    }


def _host_report_for_command(command: Command) -> dict:
    # Read only the reconstructed source-owned argv, never receipt-supplied code.
    def value(flag):
        return command.argv[command.argv.index(flag) + 1]

    return verify_host_junit(
        repo=Path(value("--repo")), inventory_path=Path(value("--inventory")),
        started_path=Path(value("--started")), junit_path=Path(value("--junit")),
        allowlist_path=Path(value("--allowlist")), lane=value("--lane"),
        minimum_collected=int(value("--minimum-collected")), minimum_passed=int(value("--minimum-passed")),
    )


def stage_commands(
    stage: str,
    repo: Path,
    scratch: Path,
    *,
    candidate_sha: str,
    version: str,
    repository: str = "Denissvgn/python-wiki-llm",
    launcher: Path | None = None,
) -> list[Command]:
    """Render only source-owned commands, never an argv supplied by a plan/receipt."""
    if stage not in STAGES:
        raise RunnerError("unknown trusted stage: " + stage)
    repo, scratch = Path(os.path.abspath(repo)), Path(os.path.abspath(scratch))
    py = str(absolute_launcher(launcher or _python(repo / ".venv")))
    qualification = str(repo / "release/qualification.py")
    commands: list[Command] = []

    def command(
        name, argv, cwd=repo, timeout=600, environment=None, expected_prefix=None
    ):
        commands.append(
            Command(
                name,
                tuple(str(x) for x in argv),
                cwd,
                timeout,
                environment or {},
                expected_prefix,
            )
        )

    if stage == "prepare":
        if platform.system() not in {"Darwin", "Linux"}:
            raise RunnerError(
                "locked routine toolchain preparation requires its supported native setup host"
            )
        toolchains = repo / ".git/llm-wiki-ci-toolchains"
        command(
            "locked-node-npm",
            (
                py,
                "-I",
                repo / "release/preflight_runner.py",
                "prepare-runtime",
                "--repo",
                repo,
            ),
            timeout=1200,
        )
        active = {
            "PATH": str(toolchains / "node/bin")
            + os.pathsep
            + os.environ.get("PATH", "")
        }
        command(
            "prepared-typescript-owner",
            (
                py,
                "-m",
                "llm_wiki_cli.cli",
                "prepare-extractors",
                "--src-dir",
                repo,
                "--cache-dir",
                repo / ".git",
                "--language",
                "typescript",
            ),
            timeout=1200,
            environment=active,
        )
        command(
            "provider-input-census",
            (
                py,
                "-m",
                "llm_wiki_cli.cli",
                "doctor",
                "--analysis-inputs",
                "--format",
                "json",
            ),
            environment=active,
        )
        command(
            "source-archive-budget",
            (
                py,
                "-I",
                repo / "release/preflight_runner.py",
                "archive-budget",
                "--repo",
                repo,
                "--candidate-sha",
                candidate_sha,
                "--output",
                scratch / "archive-budget",
            ),
            timeout=600,
        )
        source_args = (
            "--src-dir",
            repo,
            "--wiki-dir",
            repo / "docs/llm_wiki",
            "--helper-cache-dir",
            repo / ".git",
            "--jobs",
            "1",
        )
        command(
            "repository-doctor",
            (
                py,
                "-m",
                "llm_wiki_cli.cli",
                "doctor",
                *source_args,
                "--report-schema",
                "v4",
                "--comparison-policy",
                "analysis-v1",
                "--strict",
                "--format",
                "json",
            ),
            environment=active,
            timeout=1800,
        )
        command(
            "wiki-lint",
            (
                py,
                "-m",
                "llm_wiki_cli.cli",
                "lint",
                *source_args,
                "--strict",
                "--no-cache",
            ),
            environment=active,
            timeout=1800,
        )
        command(
            "repository-ci",
            (
                py,
                "-m",
                "llm_wiki_cli.cli",
                "ci-check",
                *source_args,
                "--report-schema",
                "v4",
                "--comparison-policy",
                "analysis-v1",
                "--format",
                "json",
                "--no-report",
                "--no-cache",
            ),
            environment=active,
            timeout=1800,
        )
        command(
            "storage-audit",
            (
                py,
                "-m",
                "llm_wiki_cli.cli",
                "knowledge",
                "storage-check",
                "--wiki-dir",
                repo / "docs/llm_wiki",
                "--full",
                "--format",
                "json",
            ),
            environment=active,
            timeout=1800,
        )
        return commands
    if stage in {"contracts", "rehearsal"}:
        from release.preflight_contracts import contract_groups

        groups = [
            argument for group in contract_groups() for argument in ("--group", group)
        ]
        command(
            "contract-preflight",
            (
                py,
                "-I",
                repo / "release/preflight_contracts.py",
                "groups",
                "--repo",
                repo,
                *groups,
                "--output",
                scratch / "contracts",
                "--python",
                py,
            ),
            timeout=18000,
        )
    if stage in {"static", "rehearsal"}:
        command(
            "maintained-static-checks",
            (
                py,
                "-I",
                repo / "release/static_checks.py",
                "--evidence",
                scratch / "static",
            ),
            timeout=2400,
        )
    if stage in {"contracts", "static"}:
        return commands
    frozen = scratch / "frozen"
    command(
        "freeze-source",
        (
            py,
            "-I",
            qualification,
            "freeze-source",
            "--root",
            repo,
            "--output",
            frozen,
            "--expected-sha",
            candidate_sha,
            "--repository",
            repository,
            "--check-registry",
        ),
    )
    if stage == "freeze":
        return commands
    # Archive hash and epoch are read only after the maintained freeze succeeded.
    # Dynamic arguments are restricted internal references, resolved by _materialize.
    archive = frozen / "candidate-source.tar"

    def extract(name):
        candidate = scratch / name
        command(
            "extract-" + name,
            (
                py,
                "-I",
                qualification,
                "extract-source",
                "--archive",
                archive,
                "--sha256",
                "@archive_sha256",
                "--destination",
                candidate,
            ),
        )
        return candidate

    if stage in {"host-core", "rehearsal"}:
        candidate = extract("host-source")
        environment = scratch / "host-environment"
        env_python = str(_python(environment))
        command(
            "create-host-environment",
            (py, "-I", qualification, "create-venv", "--path", environment),
        )
        command(
            "install-host-source",
            (
                env_python,
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                str(candidate) + "[dev,tokens]",
            ),
            expected_prefix=environment,
            timeout=1200,
        )
        lane = {
            "Darwin": "core-macos-3.14",
            "Windows": "core-windows-3.13",
            "Linux": "core-ubuntu-3.10",
        }.get(platform.system())
        if lane is None or not lane.endswith(
            f"{sys.version_info.major}.{sys.version_info.minor}"
        ):
            raise RunnerError(
                "host OS/Python has no matching maintained native core lane"
            )
        host_environment = {"LLM_WIKI_QUALIFICATION_SOURCE_ARCHIVE": str(archive)}
        command(
            "collect-host-core",
            (env_python, "-I", repo / "release/core_shard_runner.py", "worker",
             "--collect", "--purpose", "shadow", "--output", scratch),
            cwd=candidate, expected_prefix=environment, timeout=600,
            environment=host_environment,
        )
        core_command = _strict_pytest(env_python, scratch / "host-core.xml", "tests")
        if platform.system() == "Linux":
            core_command += (
                "--cov=llm_wiki_cli",
                "--cov-report=xml:" + str(scratch / "coverage-host-core.xml"),
                "--cov-fail-under=87",
            )
        command(
            "strict-host-core",
            core_command,
            cwd=candidate,
            timeout=21600,
            environment=host_environment,
        )
        command(
            "verify-host-junit",
            (
                py,
                "-I",
                repo / "release/preflight_runner.py",
                "verify-host-junit",
                "--repo",
                candidate,
                "--inventory",
                scratch / "collected.json",
                "--started",
                scratch / "started.jsonl",
                "--junit",
                scratch / "host-core.xml",
                "--lane",
                lane,
                "--allowlist",
                candidate / "release/skip-allowlist.json",
                "--minimum-collected",
                "5322",
                "--minimum-passed",
                "5070",
                "--output",
                scratch / "host-result.json",
            ),
        )
    if stage == "host-core":
        return commands
    for copy in ("a", "b"):
        candidate = extract("build-source-" + copy)
        environment = scratch / ("build-environment-" + copy)
        env_python = str(_python(environment))
        command(
            "create-builder-" + copy,
            (py, "-I", qualification, "create-venv", "--path", environment),
        )
        command(
            "bind-build-lock-" + copy,
            (
                env_python,
                "-I",
                repo / "release/dependency_downloads.py",
                "key",
                "--lock",
                candidate / "release/build-requirements.txt",
                "--profile",
                "build",
                "--output",
                scratch / ("build-identity-" + copy + ".json"),
            ),
        )
        command(
            "install-build-lock-" + copy,
            (
                env_python,
                "-I",
                repo / "release/dependency_downloads.py",
                "setup",
                "--lock",
                candidate / "release/build-requirements.txt",
                "--profile",
                "build",
                "--identity",
                scratch / ("build-identity-" + copy + ".json"),
                "--output",
                scratch / ("build-setup-" + copy),
            ),
            expected_prefix=environment,
            timeout=1200,
        )
        command(
            "independent-build-" + copy,
            (
                env_python,
                "-m",
                "build",
                "--no-isolation",
                "--sdist",
                "--wheel",
                "--outdir",
                scratch / ("dist-" + copy),
                candidate,
            ),
            timeout=1200,
            environment={"SOURCE_DATE_EPOCH": "@commit_epoch"},
        )
    command(
        "compare-builds",
        (
            py,
            "-I",
            qualification,
            "compare-builds",
            "--first",
            scratch / "dist-a",
            "--second",
            scratch / "dist-b",
            "--output",
            scratch / "reproducible",
        ),
    )
    validation_environment = scratch / "validation-environment"
    validation_python = str(_python(validation_environment))
    command(
        "create-validation-environment",
        (py, "-I", qualification, "create-venv", "--path", validation_environment),
    )
    command(
        "bind-validation-lock",
        (
            validation_python,
            "-I",
            repo / "release/dependency_downloads.py",
            "key",
            "--lock",
            scratch / "build-source-a/release/validation-requirements.txt",
            "--profile",
            "validation",
            "--output",
            scratch / "validation-identity.json",
        ),
    )
    command(
        "install-validation-lock",
        (
            validation_python,
            "-I",
            repo / "release/dependency_downloads.py",
            "setup",
            "--lock",
            scratch / "build-source-a/release/validation-requirements.txt",
            "--profile",
            "validation",
            "--identity",
            scratch / "validation-identity.json",
            "--output",
            scratch / "validation-setup",
        ),
        expected_prefix=validation_environment,
        timeout=1200,
    )
    command(
        "validate-distribution-metadata",
        (validation_python, "-m", "twine", "check", "@wheel", "@sdist"),
    )
    command(
        "validate-installed-knowledge-schema",
        (
            validation_python,
            scratch / "build-source-a/tests/verify_installed_knowledge_schema.py",
            scratch / "reproducible/dist",
            "--no-build-isolation",
        ),
        cwd=scratch,
        timeout=1200,
    )
    if stage == "builds":
        return commands
    for kind in ("wheel", "sdist"):
        for profile in ("default", "mcp"):
            environment = scratch / (kind + "-" + profile + "-environment")
            command(
                "create-" + kind + "-" + profile,
                (py, "-I", qualification, "create-venv", "--path", environment),
            )
            artifact = "@" + kind + ("[mcp]" if profile == "mcp" else "")
            command(
                "install-" + kind + "-" + profile,
                (
                    _python(environment),
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    artifact,
                ),
                expected_prefix=environment,
                timeout=1200,
            )
        command(
            "complete-artifact-smoke-" + kind,
            (
                py,
                "-I",
                repo / "tests/release_artifact_smoke.py",
                "--artifact",
                "@" + kind,
                "--python",
                _python(scratch / (kind + "-default-environment")),
                "--mcp-python",
                _python(scratch / (kind + "-mcp-environment")),
                "--expected-version",
                version,
                "--work",
                # The harness resets this tree between serial runs. Keep CLI
                # path inputs identical: fixture adoption IDs include argv.
                scratch / "artifact-smoke-work",
                "--output",
                scratch / (kind + "-smoke.json"),
            ),
            cwd=scratch,
            timeout=3600,
        )
    command(
        "compare-artifact-smoke",
        (
            py,
            "-I",
            qualification,
            "compare-smoke",
            "--wheel",
            scratch / "wheel-smoke.json",
            "--sdist",
            scratch / "sdist-smoke.json",
            "--output",
            scratch / "smoke-comparison.json",
        ),
    )
    return commands


def _materialize(value: str, scratch: Path) -> str:
    if not value.startswith("@"):
        return value
    if value in {"@archive_sha256", "@commit_epoch"}:
        identity = _read_json(scratch / "frozen/identity.json")
        key = value[1:]
        result = identity["source"][key]
        if key == "archive_sha256" and not re.fullmatch(r"[0-9a-f]{64}", str(result)):
            raise RunnerError("frozen archive identity is malformed")
        if key == "commit_epoch" and (type(result) is not int or result <= 0):
            raise RunnerError("frozen epoch is malformed")
        return str(result)
    kind = value.removeprefix("@").removesuffix("[mcp]")
    if kind not in {"wheel", "sdist"}:
        raise RunnerError("unrecognized internal command reference")
    pattern = "*.whl" if kind == "wheel" else "*.tar.gz"
    files = list((scratch / "reproducible/dist").glob(pattern))
    if len(files) != 1 or files[0].is_symlink() or not files[0].is_file():
        raise RunnerError("expected exactly one compared " + kind)
    return str(files[0]) + ("[mcp]" if value.endswith("[mcp]") else "")


def execute_stage(
    stage: str,
    *,
    repo: Path,
    work: Path,
    binding: dict,
    candidate_sha: str,
    version: str,
    repository: str = "Denissvgn/python-wiki-llm",
    launcher: Path | None = None,
) -> dict:
    """Run a trusted stage serially, retaining every attempt including failures."""
    repo = Path(os.path.abspath(repo))
    work = validate_owned_work(work, binding)
    observed_launcher = launcher_probe(repo, launcher)
    lock = work / ".execution-lock"
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RunnerError(
            "another stage owns this work root; inspect its retained attempt"
        ) from exc
    os.close(descriptor)
    started = time.time()
    attempt_id = str(uuid.uuid4())
    scratch = work / ("attempt-" + attempt_id)
    try:
        scratch.mkdir(mode=0o700)
    except OSError:
        lock.unlink()
        raise
    result = {
        "schema_version": ATTEMPT_SCHEMA,
        "attempt_id": attempt_id,
        "stage": stage,
        "binding": binding,
        "started": started,
        "status": "blocked",
        "commands": [],
        "publication_authority": False,
        "scratch": str(scratch),
        "candidate_sha": candidate_sha,
        "version": version,
        "repository": repository,
        "launcher_probe": observed_launcher,
        "recovery_actions": [
            "Complete the authorized owning sync, semantic review and re-anchor; preserve authority and authored bytes.",
            "If storage needs cleanup, review the maintained prune preview and byte recovery copies before explicitly authorized apply.",
            "Commit the final source/wiki changes and create a fresh plan; never retarget previous evidence.",
            "Activate the locked .git/llm-wiki-ci-toolchains/node/bin runtime in the operator shell before replanning; preparation does not change that shell.",
        ]
        if stage == "prepare"
        else [],
    }
    try:
        # Exclusive destination probes precede setup; they prove this operation's
        # access only and never authorize mutation of repository wiki authority.
        probe = scratch / ".write-probe"
        with probe.open("xb") as stream:
            stream.write(b"owned-preflight-probe\n")
        probe.unlink()
        commands = stage_commands(
            stage,
            repo,
            scratch,
            candidate_sha=candidate_sha,
            version=version,
            repository=repository,
            launcher=launcher,
        )
        failed = False
        for index, command in enumerate(commands):
            if failed and command.name not in INDEPENDENT_CHECKS:
                break
            validate_owned_work(work, binding)
            _safe(scratch)
            consumer_probe = None
            if command.expected_prefix is not None:
                consumer_probe = launcher_probe(
                    repo, Path(command.argv[0]), expected_prefix=command.expected_prefix
                )
            argv = [_materialize(value, scratch) for value in command.argv]
            environment = {
                key: _materialize(value, scratch)
                for key, value in command.environment.items()
            }
            if command.name.startswith("complete-artifact-smoke-"):
                target = Path(argv[argv.index("--work") + 1])
                _safe(target)
                if target.exists():
                    raise RunnerError(
                        "destructive smoke harness destination is unexpectedly occupied"
                    )
            log = scratch / (f"{index:02d}-" + command.name + ".log")
            elapsed = time.monotonic()
            row = {
                "name": command.name,
                "argv": argv,
                "cwd": str(command.cwd),
                "timeout_seconds": command.timeout,
                "environment": environment,
                "log": str(log),
                "status": "failed",
                "returncode": None,
                "launcher_probe": consumer_probe,
            }
            child_env = dict(os.environ)
            child_env.update(
                {
                    "CI": "1",
                    "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                    "PIP_NO_INPUT": "1",
                    "PYTHONUTF8": "1",
                    "PYTHONIOENCODING": "utf-8",
                    **environment,
                }
            )
            try:
                with log.open("xb") as stream:
                    child = subprocess.run(
                        argv,
                        cwd=command.cwd,
                        stdin=subprocess.DEVNULL,
                        stdout=stream,
                        stderr=subprocess.STDOUT,
                        env=child_env,
                        timeout=command.timeout,
                        check=False,
                    )
                row["returncode"] = child.returncode
                row["status"] = "passed" if child.returncode == 0 else "failed"
                status_report = (
                    scratch / "contracts/results.json"
                    if command.name == "contract-preflight"
                    else scratch / "archive-budget/report.json"
                    if command.name == "source-archive-budget"
                    else None
                )
                if status_report is not None and status_report.is_file():
                    group_state = _read_json(status_report).get("state")
                    if group_state not in {"passed", "failed", "blocked"}:
                        raise RunnerError(
                            "shared contract driver returned an unknown outcome"
                        )
                    if (group_state == "passed") != (child.returncode == 0):
                        raise RunnerError(
                            "shared contract evidence disagrees with its exit status"
                        )
                    row["status"] = group_state
            except (OSError, subprocess.TimeoutExpired) as exc:
                row["error"] = type(exc).__name__ + ": " + str(exc)
            row["seconds"] = time.monotonic() - elapsed
            row["log_sha256"] = (
                hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None
            )
            result["commands"].append(row)
            (scratch / "attempt.json").write_bytes(_canonical(result) + b"\n")
            if row["status"] != "passed":
                failed = True
                # Contract/static groups are independent; retain both failures.
                if command.name not in INDEPENDENT_CHECKS:
                    break
            if failed and command.name not in INDEPENDENT_CHECKS:
                break
        outcomes = {row["status"] for row in result["commands"]}
        result["status"] = (
            "failed"
            if "failed" in outcomes
            else "blocked"
            if "blocked" in outcomes
            else "passed"
        )
    except (RunnerError, OSError, ValueError) as exc:
        result["error"] = str(exc)
        result["status"] = "blocked"
    finally:
        result["seconds"] = time.time() - started
        (scratch / "attempt.json").write_bytes(_canonical(result) + b"\n")
        lock.unlink()
    return result


def verify_attempt(attempt: dict, *, repo: Path, work: Path, binding: dict) -> dict:
    """Rebuild the maintained argv and hash logs without executing receipt commands."""
    work = validate_owned_work(work, binding)
    if not isinstance(attempt, dict) or attempt.get("schema_version") != ATTEMPT_SCHEMA:
        raise RunnerError("unsupported local attempt")
    fields = {
        "schema_version",
        "attempt_id",
        "stage",
        "binding",
        "started",
        "status",
        "commands",
        "publication_authority",
        "scratch",
        "candidate_sha",
        "version",
        "repository",
        "seconds",
        "launcher_probe",
        "recovery_actions",
    }
    if set(attempt) not in (fields, fields | {"error"}):
        raise RunnerError("attempt has missing or unknown fields")
    if (
        attempt.get("binding") != binding
        or attempt.get("publication_authority") is not False
    ):
        raise RunnerError("attempt owner/authority mismatch")
    try:
        identifier = str(uuid.UUID(attempt["attempt_id"]))
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise RunnerError("invalid attempt identity") from exc
    scratch = work / ("attempt-" + identifier)
    if attempt.get("scratch") != str(scratch):
        raise RunnerError("attempt scratch identity mismatch")
    _safe(scratch)
    recorded = _read_json(scratch / "attempt.json")
    if recorded != attempt:
        raise RunnerError("attempt metadata bytes differ from receipt")
    expected = stage_commands(
        attempt["stage"],
        Path(os.path.abspath(repo)),
        scratch,
        candidate_sha=attempt["candidate_sha"],
        version=attempt["version"],
        repository=attempt["repository"],
    )
    rows = attempt.get("commands")
    if not isinstance(rows, list) or len(rows) > len(expected):
        raise RunnerError("unexpected attempt command inventory")
    if attempt.get("status") == "passed" and len(rows) != len(expected):
        raise RunnerError("passing attempt omitted a required command")
    for index, row in enumerate(rows):
        command = expected[index]
        if not isinstance(row, dict):
            raise RunnerError("malformed command result")
        log = scratch / (f"{index:02d}-" + command.name + ".log")
        argv = [_materialize(value, scratch) for value in command.argv]
        environment = {
            key: _materialize(value, scratch)
            for key, value in command.environment.items()
        }
        if (
            row.get("name") != command.name
            or row.get("argv") != argv
            or row.get("cwd") != str(command.cwd)
            or row.get("environment") != environment
            or row.get("timeout_seconds") != command.timeout
            or row.get("log") != str(log)
        ):
            raise RunnerError("recorded command differs from the maintained driver")
        _safe(log)
        if (
            not log.is_file()
            or row.get("log_sha256") != hashlib.sha256(log.read_bytes()).hexdigest()
        ):
            raise RunnerError("retained command log differs")
        if row.get("status") == "passed" and (
            type(row.get("returncode")) is not int or row["returncode"] != 0
        ):
            raise RunnerError("passing command has no successful exit")
        if command.name == "verify-host-junit" and row.get("status") == "passed":
            actual = _host_report_for_command(command)
            report = Path(command.argv[command.argv.index("--output") + 1])
            if _canonical(_read_json(report)) != _canonical(actual):
                raise RunnerError("retained host report differs from collection/JUnit replay")
        if command.name == "source-archive-budget":
            report_path = scratch / "archive-budget/report.json"
            if not report_path.exists():
                if row.get("status") == "passed":
                    raise RunnerError("passing source archive screen has no report")
                # A failed Git/ZIP safety probe can stop before its report.
                # Its original nonpassing command and retained log remain evidence.
                continue
            budget = _read_json(report_path)
            if budget.get("candidate_sha") != attempt["candidate_sha"] or budget.get(
                "state"
            ) != row.get("status"):
                raise RunnerError(
                    "source archive budget differs from its candidate/outcome"
                )
            if budget.get("archive") is not None:
                if budget["archive"] != "candidate-source.zip":
                    raise RunnerError("unexpected source archive budget path")
                observed = inspect_source_zip(
                    scratch / "archive-budget/candidate-source.zip"
                )
                if any(budget.get(key) != value for key, value in observed.items()):
                    raise RunnerError("source archive budget differs from retained ZIP")
            elif row.get("status") != "blocked":
                raise RunnerError("passing source archive screen has no archive")
    if attempt.get("status") == "passed" and any(
        row.get("status") != "passed" for row in rows
    ):
        raise RunnerError("passing attempt includes an unsuccessful command")
    if attempt.get("status") not in {"passed", "failed", "blocked"}:
        raise RunnerError("unknown attempt outcome")
    return {
        "status": "verified",
        "attempt_id": identifier,
        "commands": len(rows),
        "publication_authority": False,
    }


def evidence_paths(attempt: dict) -> list[Path]:
    """Enumerate durable evidence, excluding mutable installed/runtime trees.

    This is an integrity inventory, never authority to execute anything from it.
    Full source bytes are committed by the maintained frozen archive; consumer
    environments are independently observed by the maintained smoke controller.
    """
    scratch = Path(attempt["scratch"])
    _safe(scratch)
    files = {scratch / "attempt.json"}
    for row in attempt["commands"]:
        files.add(Path(row["log"]))
    for name in (
        "host-core.xml",
        "host-result.json",
        "collected.json",
        "started.jsonl",
        "wheel-smoke.json",
        "sdist-smoke.json",
        "smoke-comparison.json",
        "build-identity-a.json",
        "build-identity-b.json",
        "validation-identity.json",
    ):
        path = scratch / name
        if path.exists():
            files.add(path)
    for name in (
        "frozen",
        "reproducible",
        "dist-a",
        "dist-b",
        "contracts",
        "static",
        "build-setup-a",
        "build-setup-b",
        "validation-setup",
        "wheel-smoke-mcp-probes",
        "sdist-smoke-mcp-probes",
        "archive-budget",
    ):
        root = scratch / name
        _safe(root)
        if root.is_dir():
            for path in root.rglob("*"):
                _safe(path)
                if path.is_file() and (
                    name
                    in {"frozen", "reproducible", "dist-a", "dist-b", "archive-budget"}
                    or path.suffix in {".json", ".xml", ".log"}
                ):
                    files.add(path)
    for path in files:
        _safe(path)
        if not path.is_file() or not path.is_relative_to(scratch):
            raise RunnerError("invalid retained evidence path")
    return sorted(files)


def prepare_runtime(repo: Path) -> dict:
    """Reuse a matching runtime or invoke checksum-pinned setup for an absent one.

    Existing mismatched or damaged targets are never removed or overwritten.
    Versions and exact active executable bytes are recorded separately from the
    setup route's download checksums; a version string alone is no attestation.
    """
    repo = Path(os.path.abspath(repo))
    observed_launcher = launcher_probe(repo)
    target = repo / ".git/llm-wiki-ci-toolchains"
    _safe(target)
    node = target / "node/bin/node"
    npm = target / "node/lib/node_modules/npm/bin/npm-cli.js"
    _safe(node)
    _safe(npm)
    lock = _read_json(repo / "release/toolchain-lock.json")
    reused = (target / "node").exists()
    if not reused:
        child = subprocess.run(
            [
                "bash",
                str(repo / ".github/scripts/setup-llm-wiki-ci-toolchains.sh"),
                "--mode",
                "routine",
                "--install-root",
                str(target),
                "--environment-file",
                str(repo / ".git/llm-wiki-ci-toolchains.env"),
                "--python",
                observed_launcher["launcher"],
            ],
            cwd=repo,
            stdin=subprocess.DEVNULL,
            check=False,
            timeout=1200,
        )
        if child.returncode:
            raise RunnerError(
                "locked setup failed; retained existing files were not repaired"
            )
    actual = {}
    for name, argv, artifact in (
        ("node", [str(node), "--version"], node),
        ("npm", [str(node), str(npm), "--version"], npm),
    ):
        _safe(artifact)
        if not artifact.is_file():
            raise RunnerError(
                "locked runtime is incomplete; explicit reviewed repair is required"
            )
        child = subprocess.run(
            argv,
            cwd=repo,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        expected = lock["toolchains"][name]["version_output"]
        if child.returncode or child.stdout.strip() != expected:
            raise RunnerError(
                "existing "
                + name
                + " differs from the lock; explicit reviewed repair is required"
            )
        actual[name] = {
            "version_output": expected,
            "path": str(artifact),
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }
    return {
        "status": "ready",
        "reused": reused,
        "runtime": actual,
        "scope": "local runtime readiness; no hosted or download-provenance attestation",
    }


def _stream_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_source_zip(path: Path) -> dict:
    """Screen local ZIP bytes under unchanged hosted evidence safety budgets."""
    from release import hosted_evidence

    _safe(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RunnerError("source ZIP must be a single-link regular file")
    problems = []
    names = set()
    expanded = 0
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        for member in members:
            name = (
                member.filename.removesuffix("/")
                if member.is_dir()
                else member.filename
            )
            wire = PurePosixPath(name)
            mode = member.external_attr >> 16
            if (
                member.orig_filename != member.filename
                or not name
                or wire.as_posix() != name
                or wire.is_absolute()
                or ".." in wire.parts
                or "\\" in name
                or ":" in name
                or stat.S_ISLNK(mode)
                or stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}
                or name in names
            ):
                raise RunnerError(
                    "source ZIP has unsafe, nonregular or duplicate members"
                )
            names.add(name)
            expanded += member.file_size
        if len(members) > 10000:
            problems.append("source ZIP exceeds hosted member-count limit")
        if expanded > hosted_evidence.MAX_EXPANDED:
            problems.append("source ZIP exceeds hosted expanded-byte limit")
        if info.st_size > hosted_evidence.MAX_ARCHIVE:
            problems.append("source ZIP exceeds hosted compressed-byte limit")
    if not problems:
        # Admit readable contents/CRC with the existing maintained verifier only
        # after its allocation/expansion bounds have independently passed.
        hosted_evidence.zip_inventory(path.read_bytes())
    return {
        "state": "blocked" if problems else "passed",
        "archive_bytes": info.st_size,
        "expanded_bytes": expanded,
        "members": len(members),
        "archive_sha256": _stream_hash(path),
        "limits": {
            "archive_bytes": hosted_evidence.MAX_ARCHIVE,
            "expanded_bytes": hosted_evidence.MAX_EXPANDED,
            "members": 10000,
        },
        "problems": problems,
        "qualification": "Local equivalent-ZIP budget screen only; actual authenticated hosted archive remains independently required",
    }


def archive_budget(repo: Path, output: Path, candidate_sha: str) -> dict:
    """Retain an exact committed HEAD ZIP only below operation-owned scratch."""
    from release import hosted_evidence

    repo, output = Path(os.path.abspath(repo)), Path(os.path.abspath(output))
    _safe(output)
    work = output.parent.parent
    validate_owned_work(
        work, {"repository_root": str(repo), "kind": "local-pre-release-work/v1"}
    )
    try:
        attempt_id = str(uuid.UUID(output.parent.name.removeprefix("attempt-")))
    except ValueError as exc:
        raise RunnerError("archive output must belong to an allocated attempt") from exc
    if output.parent.name != "attempt-" + attempt_id or not output.parent.is_dir():
        raise RunnerError("archive output must belong to an allocated attempt")
    if not re.fullmatch(r"[0-9a-f]{40}", candidate_sha):
        raise RunnerError("archive budget needs an exact full candidate SHA")

    def git(*arguments: str) -> bytes:
        child = subprocess.run(
            ["git", *arguments],
            cwd=repo,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=60,
        )
        if child.returncode:
            raise RunnerError(
                "source archive Git inspection failed: "
                + child.stderr.decode("utf-8", errors="replace")[:1000]
            )
        return child.stdout

    if git("rev-parse", "HEAD").decode("ascii").strip() != candidate_sha:
        raise RunnerError("archive candidate differs from current HEAD")
    tree = git("rev-parse", "HEAD^{tree}").decode("ascii").strip()
    entries = git("ls-tree", "-rltz", candidate_sha).split(b"\0")
    expanded = 0
    for entry in entries:
        if entry:
            header, _ = entry.split(b"\t", 1)
            size = header.split()[-1]
            expanded += 0 if size == b"-" else int(size)
    output.mkdir(mode=0o700)
    report = {
        "schema_version": "agent-wiki-local-source-archive-budget/v1",
        "candidate_sha": candidate_sha,
        "tree": tree,
        "state": "blocked",
        "archive": None,
        "expanded_bytes": expanded,
        "problems": [],
        "qualification": "Local equivalent-ZIP budget screen only; actual authenticated hosted archive remains independently required",
    }
    if len(entries) - 1 > 10000 or expanded > hosted_evidence.MAX_EXPANDED:
        report["problems"] = [
            "source tree exceeds hosted expanded/member budget; archive creation withheld"
        ]
    else:
        archive = output / "candidate-source.zip"
        with archive.open("xb") as stream:
            child = subprocess.run(
                ["git", "archive", "--format=zip", candidate_sha],
                cwd=repo,
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=subprocess.PIPE,
                check=False,
                timeout=600,
            )
        if child.returncode:
            raise RunnerError("source ZIP creation failed; partial bytes retained")
        report.update(inspect_source_zip(archive), archive=archive.name)
    (output / "report.json").write_bytes(_canonical(report) + b"\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare-runtime", "archive-budget", "verify-host-junit"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--candidate-sha")
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--started", type=Path)
    parser.add_argument("--junit", type=Path)
    parser.add_argument("--allowlist", type=Path)
    parser.add_argument("--lane")
    parser.add_argument("--minimum-collected", type=int, default=5322)
    parser.add_argument("--minimum-passed", type=int, default=5070)
    args = parser.parse_args()
    try:
        if args.command == "archive-budget":
            if args.output is None or args.candidate_sha is None:
                raise RunnerError(
                    "archive-budget requires --output and --candidate-sha"
                )
            result = archive_budget(args.repo, args.output, args.candidate_sha)
        elif args.command == "verify-host-junit":
            if any(value is None for value in (
                args.inventory, args.started, args.junit, args.allowlist, args.lane, args.output,
            )):
                raise RunnerError("host verification requires collection, JUnit, baseline and output")
            result = verify_host_junit(
                repo=args.repo, inventory_path=args.inventory, started_path=args.started,
                junit_path=args.junit, allowlist_path=args.allowlist, lane=args.lane,
                minimum_collected=args.minimum_collected, minimum_passed=args.minimum_passed,
            )
            output = Path(os.path.abspath(args.output))
            _safe(output)
            with output.open("xb") as stream:
                stream.write(_canonical(result) + b"\n")
        else:
            result = prepare_runtime(args.repo)
    except (RunnerError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("state", result.get("status")) in {"passed", "ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
