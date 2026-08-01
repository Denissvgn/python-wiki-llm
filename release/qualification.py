#!/usr/bin/env python3
"""Fail-closed release qualification and promotion helpers.

The module deliberately uses only the Python standard library so that the
promotion verifier can run before any candidate package or third-party tool is
installed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import uuid
import venv
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path, PurePath
from typing import Any, Iterable, Mapping, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - only freeze reads TOML
    tomllib = None  # type: ignore[assignment]


IDENTITY_SCHEMA = "agent-wiki-release-identity/v1"
ALLOWLIST_SCHEMA = "agent-wiki-release-skip-allowlist/v1"
OWNER_LANE_SCHEMA = "agent-wiki-release-owner-lanes/v2"
DECISION_SCHEMA = "agent-wiki-release-decision/v1"
QUALIFICATION_SCHEMA = "agent-wiki-release-qualification/v2"
VERIFICATION_SCHEMA = "agent-wiki-release-verification/v1"
WORKFLOW_VERIFICATION_SCHEMA = "agent-wiki-release-workflow-verification/v1"
PROMOTION_SCHEMA = "agent-wiki-release-promotion/v1"
SMOKE_SCHEMA = "agent-wiki-artifact-smoke/v1"
SMOKE_COMPARISON_SCHEMA = "agent-wiki-artifact-smoke-comparison/v1"
QUALIFICATION_WORKFLOW_PATH = ".github/workflows/release-qualification.yml"
SLSA_PROVENANCE_PREDICATE = "https://slsa.dev/provenance/v1"
SPDX_SBOM_PREDICATE = "https://spdx.dev/Document/v2.3"
GITHUB_ACTIONS_OIDC_ISSUER = "https://token.actions.githubusercontent.com"
ATTESTATION_RECEIPT_COUNT = 2
MAX_ATTESTATION_RECEIPTS_BYTES = 16 * 1024 * 1024
REQUIRED_GATES = tuple(f"RD-{number:02d}" for number in range(14))
QUALIFIED_GATES = REQUIRED_GATES[:-1]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){2}(?:[a-zA-Z0-9.+-]*)$")
EVIDENCE_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
DIST_RE = re.compile(
    r"^agent_wiki_cli-(?P<version>[^/]+?)(?:-py3-none-any\.whl|\.tar\.gz)$"
)
PACKAGE_NAME = "agent-wiki-cli"


class QualificationError(RuntimeError):
    """A release contract is absent, malformed, or inconsistent."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise QualificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise QualificationError(f"non-finite JSON number is forbidden: {value}")


def load_json(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise QualificationError(f"{path} is not readable strict JSON: {exc}") from exc


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bundle_relative_path(path: PurePath, root: PurePath) -> str:
    """Return a manifest-compatible relative bundle path."""

    return path.relative_to(root).as_posix()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _run(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise QualificationError(
            f"command failed ({completed.returncode}): {' '.join(command)}"
            + (f": {detail}" if detail else "")
        )
    return completed


def _require_object(
    value: object,
    *,
    name: str,
    keys: Iterable[str],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise QualificationError(f"{name} must be an object")
    expected = set(keys)
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise QualificationError(
            f"{name} has invalid fields; missing={missing}, extra={extra}"
        )
    return value


def _require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise QualificationError(f"{name} must be a non-empty string")
    return value


def _require_sha256(value: object, name: str) -> str:
    result = _require_string(value, name)
    if not SHA256_RE.fullmatch(result):
        raise QualificationError(f"{name} must be a lowercase SHA-256 digest")
    return result


def _require_sha(value: object, name: str) -> str:
    result = _require_string(value, name)
    if not SHA_RE.fullmatch(result):
        raise QualificationError(f"{name} must be a full lowercase Git SHA")
    return result


def _project_version(root: Path) -> str:
    global tomllib
    if tomllib is None:  # pragma: no cover - freeze runs on Python 3.13
        try:
            import tomli as tomllib
        except ModuleNotFoundError as exc:
            raise QualificationError(
                "Python 3.10 freeze requires the locked tomli package"
            ) from exc
    with (root / "pyproject.toml").open("rb") as stream:
        payload = tomllib.load(stream)
    try:
        version = payload["project"]["version"]
    except (KeyError, TypeError) as exc:
        raise QualificationError("pyproject.toml has no project.version") from exc
    result = _require_string(version, "project.version")
    if not VERSION_RE.fullmatch(result):
        raise QualificationError(
            "project.version must be a three-component release version"
        )
    return result


def _github_output(values: Mapping[str, object]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with Path(output).open("a", encoding="utf-8") as stream:
        for key, value in values.items():
            stream.write(f"{key}={value}\n")


def _check_registry_unused(version: str) -> None:
    url = f"https://pypi.org/pypi/{PACKAGE_NAME}/{version}/json"
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "agent-wiki-release"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status == 200:
                raise QualificationError(
                    f"{PACKAGE_NAME} {version} already exists on PyPI"
                )
            raise QualificationError(
                f"unexpected PyPI status while checking {version}: {response.status}"
            )
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return
        raise QualificationError(
            f"PyPI preflight failed closed with HTTP {exc.code}"
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise QualificationError(f"PyPI preflight unavailable: {exc}") from exc


def freeze_source(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    expected_sha = args.expected_sha.lower()

    sha = _run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    if sha != expected_sha or not SHA_RE.fullmatch(sha):
        raise QualificationError(
            f"checked-out SHA {sha!r} does not equal candidate {expected_sha!r}"
        )
    tree = _run(["git", "rev-parse", "HEAD^{tree}"], cwd=root).stdout.strip()
    _require_sha(tree, "source.tree")
    epoch_text = _run(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=root).stdout
    try:
        epoch = int(epoch_text.strip())
    except ValueError as exc:
        raise QualificationError("candidate commit timestamp is invalid") from exc

    status = _run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root,
    ).stdout
    if status:
        raise QualificationError(f"candidate worktree is not clean:\n{status}")
    _run(["git", "diff", "--check", "HEAD"], cwd=root)
    unmerged = _run(["git", "ls-files", "--unmerged"], cwd=root).stdout
    if unmerged:
        raise QualificationError("candidate contains unresolved merge entries")

    residue = [
        path
        for path in (root / "dist", root / "build", root / "src" / "agent_wiki_cli.egg-info")
        if path.exists()
    ]
    if residue:
        rendered = ", ".join(str(path.relative_to(root)) for path in residue)
        raise QualificationError(f"stale build residue exists: {rendered}")

    version = _project_version(root)
    tag = f"v{version}"
    candidate_version = tuple(int(component) for component in version.split("."))
    released_versions: list[tuple[int, int, int]] = []
    for existing in _run(["git", "tag", "--list", "v*"], cwd=root).stdout.splitlines():
        match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", existing)
        if match:
            released_versions.append(tuple(int(value) for value in match.groups()))
    if args.mode == "candidate" and released_versions:
        if candidate_version <= max(released_versions):
            raise QualificationError(
                f"candidate version {version} is not newer than the latest release"
            )
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(
        rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$",
        changelog,
        flags=re.MULTILINE,
    )
    if len(headings) != 1:
        raise QualificationError(
            f"CHANGELOG.md must contain exactly one dated {version} heading"
        )
    if "[Unreleased]:" not in changelog or f"compare/{tag}...HEAD" not in changelog:
        raise QualificationError("CHANGELOG.md has no matching Unreleased comparison")
    if f"[{version}]:" not in changelog:
        raise QualificationError(f"CHANGELOG.md has no [{version}] comparison link")

    tag_result = _run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
        cwd=root,
        check=False,
    )
    if tag_result.returncode == 0:
        resolved = _run(["git", "rev-list", "-n", "1", tag], cwd=root).stdout.strip()
        if args.mode == "candidate":
            raise QualificationError(f"candidate tag {tag} already exists locally")
        if resolved != sha:
            raise QualificationError(f"{tag} resolves to {resolved}, not {sha}")
    elif args.mode == "tagged":
        raise QualificationError(f"required release tag {tag} is absent")

    remote_tag = _run(
        [
            "git",
            "ls-remote",
            "--tags",
            "origin",
            f"refs/tags/{tag}",
            f"refs/tags/{tag}^{{}}",
        ],
        cwd=root,
    ).stdout.strip()
    if args.mode == "candidate" and remote_tag:
        raise QualificationError(f"candidate tag {tag} already exists on origin")
    if args.mode == "tagged":
        remote_shas = {
            line.split(maxsplit=1)[0]
            for line in remote_tag.splitlines()
            if line.strip()
        }
        if sha not in remote_shas:
            raise QualificationError(f"origin {tag} does not resolve to {sha}")

    for ancestor in args.required_ancestor:
        completed = _run(
            ["git", "merge-base", "--is-ancestor", ancestor, sha],
            cwd=root,
            check=False,
        )
        if completed.returncode:
            raise QualificationError(
                f"candidate does not contain required ancestor {ancestor}"
            )

    if args.check_registry:
        _check_registry_unused(version)

    archive = output / "candidate-source.tar"
    _run(
        ["git", "archive", "--format=tar", f"--output={archive}", sha],
        cwd=root,
    )
    archive_digest = sha256_file(archive)
    identity = {
        "schema_version": IDENTITY_SCHEMA,
        "repository": args.repository,
        "source": {
            "sha": sha,
            "tree": tree,
            "archive_sha256": archive_digest,
            "commit_epoch": epoch,
        },
        "version": version,
        "tag": tag,
        "mode": args.mode,
    }
    write_json(output / "identity.json", identity)
    (output / "SHA256SUMS").write_text(
        f"{archive_digest}  {archive.name}\n",
        encoding="ascii",
    )
    _github_output(
        {
            "sha": sha,
            "tree": tree,
            "version": version,
            "tag": tag,
            "source-sha256": archive_digest,
            "commit-epoch": epoch,
        }
    )
    return 0


def create_venv(args: argparse.Namespace) -> int:
    destination = args.path.resolve()
    venv.EnvBuilder(with_pip=True, clear=True).create(destination)
    bindir = destination / ("Scripts" if os.name == "nt" else "bin")
    github_path = os.environ.get("GITHUB_PATH")
    if github_path:
        with Path(github_path).open("a", encoding="utf-8") as stream:
            stream.write(str(bindir) + "\n")
    else:
        print(bindir)
    return 0


def extract_source(args: argparse.Namespace) -> int:
    archive = args.archive.resolve()
    expected = args.sha256.lower()
    actual = sha256_file(archive)
    if actual != expected:
        raise QualificationError(
            f"source archive digest mismatch: expected {expected}, got {actual}"
        )
    destination = args.destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:") as stream:
        root = destination
        for member in stream.getmembers():
            target = (root / member.name).resolve()
            if root != target and root not in target.parents:
                raise QualificationError(
                    f"source archive member escapes destination: {member.name}"
                )
        stream.extractall(destination, filter="data")
    return 0


def _junit_testcases(root: ET.Element) -> list[ET.Element]:
    return list(root.iter("testcase"))


def _node_id(testcase: ET.Element) -> str:
    classname = testcase.attrib.get("classname", "")
    name = testcase.attrib.get("name", "")
    parts = classname.split(".")
    module_index = next(
        (index for index, value in enumerate(parts) if value.startswith("test_")),
        None,
    )
    if module_index is None:
        raise QualificationError(f"cannot derive pytest node ID from {classname!r}")
    path = "/".join(parts[: module_index + 1]) + ".py"
    suffix = parts[module_index + 1 :] + [name]
    return "::".join([path, *suffix])


def _skip_tuples(path: Path, lane: str) -> tuple[list[dict[str, str]], dict[str, int]]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise QualificationError(f"invalid JUnit XML {path}: {exc}") from exc
    tuples: list[dict[str, str]] = []
    counts = {"collected": 0, "passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for testcase in _junit_testcases(root):
        counts["collected"] += 1
        failure = testcase.find("failure")
        error = testcase.find("error")
        skipped = testcase.find("skipped")
        if failure is not None:
            counts["failed"] += 1
        elif error is not None:
            counts["errors"] += 1
        elif skipped is not None:
            counts["skipped"] += 1
            reason = skipped.attrib.get("message") or (skipped.text or "").strip()
            tuples.append(
                {
                    "lane": lane,
                    "node_id": _node_id(testcase),
                    "reason": reason,
                }
            )
        else:
            counts["passed"] += 1
    tuples.sort(key=lambda item: (item["lane"], item["node_id"], item["reason"]))
    return tuples, counts


def _load_skip_allowlist(path: Path) -> list[dict[str, str]]:
    allowlist = _require_object(
        load_json(path.resolve()),
        name="skip allowlist",
        keys=("schema_version", "entries"),
    )
    if allowlist["schema_version"] != ALLOWLIST_SCHEMA:
        raise QualificationError("skip allowlist schema_version is unsupported")
    raw_entries = allowlist["entries"]
    if not isinstance(raw_entries, list):
        raise QualificationError("skip allowlist entries must be an array")
    entries: list[dict[str, str]] = []
    for index, item in enumerate(raw_entries):
        entry = _require_object(
            item,
            name=f"skip allowlist entries[{index}]",
            keys=("lane", "node_id", "reason", "owner_lane"),
        )
        result = {
            key: _require_string(
                entry[key],
                f"skip allowlist entries[{index}].{key}",
            )
            for key in ("lane", "node_id", "reason", "owner_lane")
        }
        if result["owner_lane"] == "REVIEW-REQUIRED":
            raise QualificationError(
                "skip allowlist contains an unreviewed owner lane"
            )
        if result["owner_lane"] == result["lane"]:
            raise QualificationError(
                "a skipped test cannot be owned by the lane that skipped it"
            )
        entries.append(result)
    return entries


def verify_junit(args: argparse.Namespace) -> int:
    tuples, counts = _skip_tuples(args.junit.resolve(), args.lane)
    report = {
        "schema_version": "agent-wiki-release-pytest-result/v1",
        "lane": args.lane,
        "counts": counts,
        "skips": tuples,
    }
    write_json(args.output.resolve(), report)
    if counts["failed"] or counts["errors"]:
        raise QualificationError(f"{args.lane} has test failures/errors: {counts}")
    if counts["collected"] < args.minimum_collected:
        raise QualificationError(
            f"{args.lane} collected {counts['collected']} < {args.minimum_collected}"
        )
    if counts["passed"] < args.minimum_passed:
        raise QualificationError(
            f"{args.lane} passed {counts['passed']} < {args.minimum_passed}"
        )
    if args.discovery:
        print(
            f"{args.lane}: discovery-only result has {len(tuples)} skips; "
            "it is not qualifying evidence"
        )
        return 0
    entries = _load_skip_allowlist(args.allowlist)
    expected = [
        item for item in entries if item["lane"] == args.lane
    ]
    expected_tuples = [
        {key: item[key] for key in ("lane", "node_id", "reason")}
        for item in expected
    ]
    expected_tuples.sort(
        key=lambda item: (item["lane"], item["node_id"], item["reason"])
    )
    if tuples != expected_tuples:
        unexpected = [item for item in tuples if item not in expected_tuples]
        missing = [item for item in expected_tuples if item not in tuples]
        raise QualificationError(
            f"{args.lane} skip contract changed; "
            f"unexpected={unexpected}, missing={missing}"
        )
    return 0


def discover_allowlist(args: argparse.Namespace) -> int:
    entries: list[dict[str, str]] = []
    for spec in args.result:
        lane, separator, path_text = spec.partition("=")
        if not separator:
            raise QualificationError("--result must be LANE=JUNIT.xml")
        tuples, _ = _skip_tuples(Path(path_text).resolve(), lane)
        for item in tuples:
            item["owner_lane"] = "REVIEW-REQUIRED"
            entries.append(item)
    entries.sort(key=lambda item: (item["lane"], item["node_id"], item["reason"]))
    write_json(
        args.output.resolve(),
        {"schema_version": ALLOWLIST_SCHEMA, "entries": entries},
    )
    print(
        "Discovery allowlist generated with REVIEW-REQUIRED owner lanes; "
        "it must be reviewed and committed before qualification."
    )
    return 0


def _result_status(result: str) -> str:
    return {
        "success": "PASS",
        "failure": "FAIL",
        "cancelled": "BLOCKED",
        "skipped": "BLOCKED",
        "PASS": "PASS",
        "FAIL": "FAIL",
        "BLOCKED": "BLOCKED",
    }.get(result, "BLOCKED")


def _junit_node_outcomes(path: Path) -> dict[str, str]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        raise QualificationError(f"invalid JUnit XML {path}: {exc}") from exc
    outcomes: dict[str, str] = {}
    for testcase in _junit_testcases(root):
        node_id = _node_id(testcase)
        if node_id in outcomes:
            raise QualificationError(
                f"JUnit XML {path} contains duplicate node ID: {node_id}"
            )
        if testcase.find("failure") is not None:
            outcome = "failed"
        elif testcase.find("error") is not None:
            outcome = "error"
        elif testcase.find("skipped") is not None:
            outcome = "skipped"
        else:
            outcome = "passed"
        outcomes[node_id] = outcome
    return outcomes


def verify_owner_lanes(args: argparse.Namespace) -> int:
    identity_path = args.identity.resolve()
    identity = _validate_identity(load_json(identity_path))
    allowlist_path = args.allowlist.resolve()
    entries = _load_skip_allowlist(allowlist_path)
    statuses: dict[str, str] = {}
    for spec in args.owner_result:
        lane, separator, result = spec.partition("=")
        if not separator or not lane:
            raise QualificationError(f"invalid owner result specification: {spec}")
        if lane in statuses:
            raise QualificationError(f"duplicate owner result specification: {lane}")
        statuses[lane] = _result_status(result)

    junit_paths: dict[str, Path] = {}
    for spec in args.owner_junit:
        lane, separator, path_text = spec.partition("=")
        if not separator or not lane or not path_text:
            raise QualificationError(f"invalid owner JUnit specification: {spec}")
        if lane in junit_paths:
            raise QualificationError(f"duplicate owner JUnit specification: {lane}")
        junit_paths[lane] = Path(path_text).resolve()

    required = sorted({entry["owner_lane"] for entry in entries})
    missing = [lane for lane in required if lane not in statuses]
    if missing:
        raise QualificationError(f"owner lanes have no result: {missing}")
    not_passing = {
        lane: statuses[lane]
        for lane in required
        if statuses[lane] != "PASS"
    }
    if not_passing:
        raise QualificationError(f"owner lanes did not pass: {not_passing}")

    missing_junit = [lane for lane in required if lane not in junit_paths]
    if missing_junit:
        raise QualificationError(
            f"owner lanes have no JUnit evidence: {missing_junit}"
        )

    lane_receipts: dict[str, object] = {}
    for lane in required:
        junit_path = junit_paths[lane]
        outcomes = _junit_node_outcomes(junit_path)
        node_ids = sorted(
            {
                entry["node_id"]
                for entry in entries
                if entry["owner_lane"] == lane
            }
        )
        missing_nodes = [node_id for node_id in node_ids if node_id not in outcomes]
        if missing_nodes:
            raise QualificationError(
                f"{lane} JUnit evidence is missing owned nodes: {missing_nodes}"
            )
        not_passing_nodes = {
            node_id: outcomes[node_id]
            for node_id in node_ids
            if outcomes[node_id] != "passed"
        }
        if not_passing_nodes:
            raise QualificationError(
                f"{lane} owned nodes did not pass: {not_passing_nodes}"
            )
        lane_receipts[lane] = {
            "junit_sha256": sha256_file(junit_path),
            "result": statuses[lane],
            "verified_node_ids": node_ids,
        }

    source = identity["source"]
    write_json(
        args.output.resolve(),
        {
            "schema_version": OWNER_LANE_SCHEMA,
            "identity": {
                "repository": identity["repository"],
                "sha": source["sha"],
                "tree": source["tree"],
                "archive_sha256": source["archive_sha256"],
                "version": identity["version"],
                "tag": identity["tag"],
            },
            "identity_sha256": sha256_file(identity_path),
            "allowlist_sha256": sha256_file(allowlist_path),
            "entries_verified": len(entries),
            "required_owner_lanes": required,
            "owner_results": lane_receipts,
        },
    )
    return 0


def aggregate(args: argparse.Namespace) -> int:
    statuses: dict[str, str] = {}
    for spec in args.gate:
        gate, separator, result = spec.partition("=")
        if not separator or gate not in REQUIRED_GATES:
            raise QualificationError(f"invalid gate specification: {spec}")
        if gate in statuses:
            raise QualificationError(f"duplicate gate specification: {gate}")
        statuses[gate] = _result_status(result)
    for gate in REQUIRED_GATES:
        statuses.setdefault(gate, "BLOCKED")
    failed = sorted(gate for gate, status in statuses.items() if status == "FAIL")
    blocked = sorted(
        gate for gate, status in statuses.items() if status == "BLOCKED"
    )
    if failed:
        decision = "NO-GO"
    elif blocked:
        decision = "BLOCKED"
    else:
        decision = "GO"
    payload = {
        "schema_version": DECISION_SCHEMA,
        "candidate_sha": args.candidate_sha,
        "candidate_version": args.candidate_version,
        "gates": dict(sorted(statuses.items())),
        "failed": failed,
        "blocked": blocked,
        "decision": decision,
    }
    write_json(args.output.resolve(), payload)
    print(decision)
    if decision == "GO" or getattr(args, "allow_non_go_exit_zero", False):
        return 0
    return 1


def compare_smoke(args: argparse.Namespace) -> int:
    wheel = _validate_smoke(load_json(args.wheel.resolve()), "wheel smoke")
    sdist = _validate_smoke(load_json(args.sdist.resolve()), "sdist smoke")
    if wheel["artifact"]["kind"] != "wheel":
        raise QualificationError("wheel smoke artifact kind is not wheel")
    if sdist["artifact"]["kind"] != "sdist":
        raise QualificationError("sdist smoke artifact kind is not sdist")
    if wheel["version"] != sdist["version"]:
        raise QualificationError("wheel and sdist smoke versions differ")
    if wheel["result"] != sdist["result"]:
        raise QualificationError("wheel and sdist installed behavior differs")
    payload = {
        "schema_version": SMOKE_COMPARISON_SCHEMA,
        "version": wheel["version"],
        "wheel_sha256": wheel["artifact"]["sha256"],
        "sdist_sha256": sdist["artifact"]["sha256"],
        "result_sha256": _smoke_result_sha256(wheel["result"]),
        "equal": True,
    }
    write_json(args.output.resolve(), payload)
    _github_output(
        {
            "version": wheel["version"],
            "wheel-sha256": wheel["artifact"]["sha256"],
            "sdist-sha256": sdist["artifact"]["sha256"],
            "result-sha256": payload["result_sha256"],
        }
    )
    return 0


def _validate_identity(value: object) -> Mapping[str, Any]:
    identity = _require_object(
        value,
        name="identity",
        keys=("schema_version", "repository", "source", "version", "tag", "mode"),
    )
    if identity["schema_version"] != IDENTITY_SCHEMA:
        raise QualificationError("identity schema_version is unsupported")
    _require_string(identity["repository"], "identity.repository")
    source = _require_object(
        identity["source"],
        name="identity.source",
        keys=("sha", "tree", "archive_sha256", "commit_epoch"),
    )
    _require_sha(source["sha"], "identity.source.sha")
    _require_sha(source["tree"], "identity.source.tree")
    _require_sha256(source["archive_sha256"], "identity.source.archive_sha256")
    if (
        isinstance(source["commit_epoch"], bool)
        or not isinstance(source["commit_epoch"], int)
        or source["commit_epoch"] <= 0
    ):
        raise QualificationError("identity.source.commit_epoch must be positive")
    version = _require_string(identity["version"], "identity.version")
    if identity["tag"] != f"v{version}":
        raise QualificationError("identity.tag does not match identity.version")
    if identity["mode"] not in {"candidate", "tagged"}:
        raise QualificationError("identity.mode is unsupported")
    return identity


def _validate_smoke(value: object, name: str) -> Mapping[str, Any]:
    smoke = _require_object(
        value,
        name=name,
        keys=("schema_version", "artifact", "version", "result"),
    )
    if smoke["schema_version"] != SMOKE_SCHEMA:
        raise QualificationError(f"{name} schema_version is unsupported")
    artifact = _require_object(
        smoke["artifact"],
        name=f"{name}.artifact",
        keys=("filename", "sha256", "kind"),
    )
    _require_string(artifact["filename"], f"{name}.artifact.filename")
    _require_sha256(artifact["sha256"], f"{name}.artifact.sha256")
    if artifact["kind"] not in {"wheel", "sdist"}:
        raise QualificationError(f"{name}.artifact.kind is unsupported")
    _require_string(smoke["version"], f"{name}.version")
    if not isinstance(smoke["result"], Mapping):
        raise QualificationError(f"{name}.result must be an object")
    return smoke


def _smoke_result_sha256(result: object) -> str:
    return _sha256_bytes(
        json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    )


def _validate_smoke_comparison(value: object) -> Mapping[str, Any]:
    comparison = _require_object(
        value,
        name="smoke comparison",
        keys=(
            "schema_version",
            "version",
            "wheel_sha256",
            "sdist_sha256",
            "result_sha256",
            "equal",
        ),
    )
    if comparison["schema_version"] != SMOKE_COMPARISON_SCHEMA:
        raise QualificationError("smoke comparison schema_version is unsupported")
    _require_string(comparison["version"], "smoke comparison.version")
    _require_sha256(
        comparison["wheel_sha256"],
        "smoke comparison.wheel_sha256",
    )
    _require_sha256(
        comparison["sdist_sha256"],
        "smoke comparison.sdist_sha256",
    )
    _require_sha256(
        comparison["result_sha256"],
        "smoke comparison.result_sha256",
    )
    if comparison["equal"] is not True:
        raise QualificationError("smoke comparison did not establish equality")
    return comparison


def _verify_smoke_consistency(
    wheel_smoke: Mapping[str, Any],
    sdist_smoke: Mapping[str, Any],
    comparison: Mapping[str, Any],
    *,
    wheel: Mapping[str, Any],
    sdist: Mapping[str, Any],
    version: str,
) -> None:
    if wheel_smoke["artifact"] != wheel:
        raise QualificationError("wheel smoke does not bind the qualified wheel")
    if sdist_smoke["artifact"] != sdist:
        raise QualificationError("sdist smoke does not bind the qualified sdist")
    if wheel_smoke["version"] != version:
        raise QualificationError("wheel smoke version does not match qualification")
    if sdist_smoke["version"] != version:
        raise QualificationError("sdist smoke version does not match qualification")
    if wheel_smoke["result"] != sdist_smoke["result"]:
        raise QualificationError("wheel and sdist installed behavior differs")
    if comparison["version"] != version:
        raise QualificationError(
            "smoke comparison version does not match qualification"
        )
    if comparison["wheel_sha256"] != wheel["sha256"]:
        raise QualificationError("smoke comparison wheel digest mismatch")
    if comparison["sdist_sha256"] != sdist["sha256"]:
        raise QualificationError("smoke comparison sdist digest mismatch")
    expected_result_sha256 = _smoke_result_sha256(wheel_smoke["result"])
    if comparison["result_sha256"] != expected_result_sha256:
        raise QualificationError("smoke comparison result digest mismatch")


def _dist_files(dist: Path) -> tuple[Path, Path]:
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise QualificationError("dist must contain exactly one wheel and one sdist")
    return wheels[0], sdists[0]


def _artifact_entry(path: Path, kind: str) -> dict[str, str]:
    return {"filename": path.name, "sha256": sha256_file(path), "kind": kind}


def _subject(artifact: Mapping[str, Any]) -> dict[str, object]:
    return {
        "name": f"dist/{artifact['filename']}",
        "digest": {"sha256": artifact["sha256"]},
    }


def _expected_sbom(
    *,
    repository: str,
    source: Mapping[str, Any],
    version: str,
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    namespace_seed = (
        f"{repository}:{source['sha']}:{artifacts[0]['sha256']}:"
        f"{artifacts[1]['sha256']}"
    )
    namespace = uuid.uuid5(uuid.NAMESPACE_URL, namespace_seed)
    created = datetime.fromtimestamp(
        source["commit_epoch"],
        tz=timezone.utc,
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{PACKAGE_NAME}-{version}",
        "documentNamespace": f"urn:uuid:{namespace}",
        "creationInfo": {
            "created": created,
            "creators": ["Tool: agent-wiki-release-qualification/v1"],
        },
        "packages": [
            {
                "name": artifact["filename"],
                "SPDXID": f"SPDXRef-Package-{index}",
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
                "versionInfo": version,
                "checksums": [
                    {"algorithm": "SHA256", "checksumValue": artifact["sha256"]}
                ],
            }
            for index, artifact in enumerate(artifacts, start=1)
        ],
    }


def _expected_provenance(
    *,
    repository: str,
    source: Mapping[str, Any],
    workflow_run_id: int,
    artifacts: Sequence[Mapping[str, Any]],
    gates: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [_subject(artifact) for artifact in artifacts],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://github.com/Denissvgn/python-wiki-llm/"
                "release-qualification/v1",
                "externalParameters": {
                    "source_sha": source["sha"],
                    "source_tree": source["tree"],
                    "source_archive_sha256": source["archive_sha256"],
                    "gate_evidence_sha256": _sha256_bytes(
                        json.dumps(
                            gates,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=True,
                            allow_nan=False,
                        ).encode("utf-8")
                    ),
                },
                "internalParameters": {},
                "resolvedDependencies": [
                    {
                        "uri": f"git+https://github.com/{repository}@{source['sha']}",
                        "digest": {
                            "gitCommit": source["sha"],
                            "gitTree": source["tree"],
                            "sha256": source["archive_sha256"],
                        },
                    }
                ],
            },
            "runDetails": {
                "builder": {
                    "id": (
                        f"https://github.com/{repository}/"
                        ".github/workflows/release-qualification.yml"
                    )
                },
                "metadata": {
                    "invocationId": (
                        f"https://github.com/{repository}/actions/runs/"
                        f"{workflow_run_id}"
                    ),
                },
            },
        },
    }


def _validate_qualification_decision(
    value: object,
    *,
    identity: Mapping[str, Any],
) -> Mapping[str, str]:
    decision = _require_object(
        value,
        name="qualification gate decision",
        keys=(
            "schema_version",
            "candidate_sha",
            "candidate_version",
            "gates",
            "failed",
            "blocked",
            "decision",
        ),
    )
    if decision["schema_version"] != DECISION_SCHEMA:
        raise QualificationError("qualification gate decision schema is unsupported")
    source = identity["source"]
    if decision["candidate_sha"] != source["sha"]:
        raise QualificationError("gate decision candidate SHA does not match identity")
    if decision["candidate_version"] != identity["version"]:
        raise QualificationError(
            "gate decision candidate version does not match identity"
        )
    gates = _require_object(
        decision["gates"],
        name="qualification gate decision.gates",
        keys=REQUIRED_GATES,
    )
    for gate, status in gates.items():
        if status not in {"PASS", "FAIL", "BLOCKED"}:
            raise QualificationError(f"{gate} has invalid gate status: {status!r}")
    expected = {
        **{gate: "PASS" for gate in QUALIFIED_GATES},
        "RD-13": "BLOCKED",
    }
    if dict(gates) != expected:
        raise QualificationError(
            "qualification requires RD-00 through RD-12 PASS and RD-13 BLOCKED"
        )
    if decision["failed"] != [] or decision["blocked"] != ["RD-13"]:
        raise QualificationError("gate decision failure/block lists are inconsistent")
    if decision["decision"] != "BLOCKED":
        raise QualificationError("pre-promotion gate decision must be BLOCKED")
    return gates


def _copy_gate_evidence(
    specs: Sequence[str],
    *,
    destination: Path,
) -> dict[str, dict[str, object]]:
    by_gate: dict[str, list[dict[str, str]]] = {
        gate: [] for gate in REQUIRED_GATES
    }
    labels: set[tuple[str, str]] = set()
    destinations: set[str] = set()
    for spec in specs:
        binding, separator, source_text = spec.partition("=")
        gate, label_separator, label = binding.partition(":")
        if (
            not separator
            or not label_separator
            or gate not in QUALIFIED_GATES
            or not EVIDENCE_LABEL_RE.fullmatch(label)
            or not source_text
        ):
            raise QualificationError(
                "--evidence must be RD-NN:lowercase-label=FILE_OR_DIRECTORY"
            )
        if (gate, label) in labels:
            raise QualificationError(f"duplicate evidence label: {gate}:{label}")
        labels.add((gate, label))
        source = Path(source_text).resolve()
        if not source.exists() or source.is_symlink():
            raise QualificationError(f"evidence source is absent or a symlink: {source}")
        if source.is_file():
            source_files = [(source, Path(source.name))]
        elif source.is_dir():
            source_files = [
                (path, path.relative_to(source))
                for path in sorted(source.rglob("*"))
                if path.is_file()
            ]
        else:
            raise QualificationError(f"evidence source is not a file/directory: {source}")
        if not source_files:
            raise QualificationError(f"evidence source is empty: {source}")
        for path, relative in source_files:
            if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
                raise QualificationError(f"evidence contains a symlink: {path}")
            target_relative = Path("evidence") / gate / label / relative
            rendered = target_relative.as_posix()
            if rendered in destinations:
                raise QualificationError(f"duplicate evidence destination: {rendered}")
            destinations.add(rendered)
            target = destination / target_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            by_gate[gate].append(
                {"path": rendered, "sha256": sha256_file(target)}
            )
    missing = [gate for gate in QUALIFIED_GATES if not by_gate[gate]]
    if missing:
        raise QualificationError(f"qualification gates have no evidence: {missing}")
    return {
        gate: {
            "status": "PASS" if gate in QUALIFIED_GATES else "BLOCKED",
            "evidence": sorted(
                by_gate[gate],
                key=lambda item: item["path"],
            ),
        }
        for gate in REQUIRED_GATES
    }


def build_bundle(args: argparse.Namespace) -> int:
    identity = _validate_identity(load_json(args.identity.resolve()))
    _validate_qualification_decision(
        load_json(args.gate_decision.resolve()),
        identity=identity,
    )
    wheel_smoke = _validate_smoke(load_json(args.wheel_smoke.resolve()), "wheel")
    sdist_smoke = _validate_smoke(load_json(args.sdist_smoke.resolve()), "sdist")
    comparison = _validate_smoke_comparison(load_json(args.smoke_comparison.resolve()))

    destination = args.output.resolve()
    dist_destination = destination / "dist"
    dist_destination.mkdir(parents=True, exist_ok=False)
    wheel_source, sdist_source = _dist_files(args.dist.resolve())
    wheel = dist_destination / wheel_source.name
    sdist = dist_destination / sdist_source.name
    wheel.write_bytes(wheel_source.read_bytes())
    sdist.write_bytes(sdist_source.read_bytes())
    artifacts = [_artifact_entry(wheel, "wheel"), _artifact_entry(sdist, "sdist")]
    version = _require_string(identity["version"], "identity.version")
    for artifact in artifacts:
        match = DIST_RE.fullmatch(artifact["filename"])
        if not match or match.group("version") != version:
            raise QualificationError(
                f"artifact filename does not identify version {version}: "
                f"{artifact['filename']}"
            )
    _verify_smoke_consistency(
        wheel_smoke,
        sdist_smoke,
        comparison,
        wheel=artifacts[0],
        sdist=artifacts[1],
        version=version,
    )
    gates = _copy_gate_evidence(args.evidence, destination=destination)

    write_json(destination / "smoke-wheel.json", wheel_smoke)
    write_json(destination / "smoke-sdist.json", sdist_smoke)
    write_json(destination / "smoke-comparison.json", comparison)

    source = identity["source"]
    sbom = _expected_sbom(
        repository=identity["repository"],
        source=source,
        version=version,
        artifacts=artifacts,
    )
    write_json(destination / "sbom.spdx.json", sbom)
    provenance = _expected_provenance(
        repository=identity["repository"],
        source=source,
        workflow_run_id=args.workflow_run_id,
        artifacts=artifacts,
        gates=gates,
    )
    write_json(destination / "provenance.intoto.json", provenance)

    sums = "".join(
        f"{artifact['sha256']}  dist/{artifact['filename']}\n"
        for artifact in artifacts
    )
    (destination / "SHA256SUMS").write_text(sums, encoding="ascii")
    support = {
        "sbom.spdx.json": sha256_file(destination / "sbom.spdx.json"),
        "provenance.intoto.json": sha256_file(
            destination / "provenance.intoto.json"
        ),
        "smoke-wheel.json": sha256_file(destination / "smoke-wheel.json"),
        "smoke-sdist.json": sha256_file(destination / "smoke-sdist.json"),
        "smoke-comparison.json": sha256_file(
            destination / "smoke-comparison.json"
        ),
    }
    manifest = {
        "schema_version": QUALIFICATION_SCHEMA,
        "repository": identity["repository"],
        "workflow_run_id": args.workflow_run_id,
        "source": dict(source),
        "version": version,
        "tag": identity["tag"],
        "artifacts": artifacts,
        "supporting_files": support,
        "gates": gates,
    }
    write_json(destination / "qualification-manifest.json", manifest)
    _github_output(
        {
            "version": version,
            "wheel-filename": artifacts[0]["filename"],
            "wheel-sha256": artifacts[0]["sha256"],
            "sdist-filename": artifacts[1]["filename"],
            "sdist-sha256": artifacts[1]["sha256"],
        }
    )
    return 0


def _validate_manifest(value: object) -> Mapping[str, Any]:
    manifest = _require_object(
        value,
        name="qualification manifest",
        keys=(
            "schema_version",
            "repository",
            "workflow_run_id",
            "source",
            "version",
            "tag",
            "artifacts",
            "supporting_files",
            "gates",
        ),
    )
    if manifest["schema_version"] != QUALIFICATION_SCHEMA:
        raise QualificationError("qualification schema_version is unsupported")
    _require_string(manifest["repository"], "manifest.repository")
    if (
        isinstance(manifest["workflow_run_id"], bool)
        or not isinstance(manifest["workflow_run_id"], int)
        or manifest["workflow_run_id"] <= 0
    ):
        raise QualificationError("manifest.workflow_run_id must be positive")
    source = _require_object(
        manifest["source"],
        name="manifest.source",
        keys=("sha", "tree", "archive_sha256", "commit_epoch"),
    )
    _require_sha(source["sha"], "manifest.source.sha")
    _require_sha(source["tree"], "manifest.source.tree")
    _require_sha256(source["archive_sha256"], "manifest.source.archive_sha256")
    if (
        isinstance(source["commit_epoch"], bool)
        or not isinstance(source["commit_epoch"], int)
        or source["commit_epoch"] <= 0
    ):
        raise QualificationError("manifest.source.commit_epoch must be positive")
    version = _require_string(manifest["version"], "manifest.version")
    if not VERSION_RE.fullmatch(version):
        raise QualificationError("manifest.version is not a release version")
    if manifest["tag"] != f"v{version}":
        raise QualificationError("manifest tag/version mismatch")
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) != 2:
        raise QualificationError("manifest must declare exactly two artifacts")
    ordered_kinds: list[str] = []
    for index, value in enumerate(artifacts):
        artifact = _require_object(
            value,
            name=f"manifest.artifacts[{index}]",
            keys=("filename", "sha256", "kind"),
        )
        filename = _require_string(
            artifact["filename"],
            f"manifest.artifacts[{index}].filename",
        )
        _require_sha256(artifact["sha256"], f"manifest.artifacts[{index}].sha256")
        if artifact["kind"] not in {"wheel", "sdist"}:
            raise QualificationError("manifest artifact kind is unsupported")
        match = DIST_RE.fullmatch(filename)
        if not match or match.group("version") != version:
            raise QualificationError(
                f"manifest artifact filename does not identify {version}: {filename}"
            )
        expected_suffix = (
            "-py3-none-any.whl"
            if artifact["kind"] == "wheel"
            else ".tar.gz"
        )
        if not filename.endswith(expected_suffix):
            raise QualificationError(
                f"manifest {artifact['kind']} filename has the wrong format: {filename}"
            )
        ordered_kinds.append(artifact["kind"])
    if ordered_kinds != ["wheel", "sdist"]:
        raise QualificationError(
            "manifest artifacts must be ordered as one wheel then one sdist"
        )
    support = _require_object(
        manifest["supporting_files"],
        name="manifest.supporting_files",
        keys=(
            "sbom.spdx.json",
            "provenance.intoto.json",
            "smoke-wheel.json",
            "smoke-sdist.json",
            "smoke-comparison.json",
        ),
    )
    for filename, digest in support.items():
        _require_sha256(digest, f"manifest.supporting_files[{filename}]")
    gates = _require_object(
        manifest["gates"],
        name="manifest.gates",
        keys=REQUIRED_GATES,
    )
    evidence_paths: set[str] = set()
    for gate, value in gates.items():
        record = _require_object(
            value,
            name=f"manifest.gates[{gate}]",
            keys=("status", "evidence"),
        )
        expected_status = "PASS" if gate in QUALIFIED_GATES else "BLOCKED"
        if record["status"] != expected_status:
            raise QualificationError(
                f"qualification manifest {gate} must be {expected_status}"
            )
        evidence = record["evidence"]
        if not isinstance(evidence, list):
            raise QualificationError(
                f"manifest.gates[{gate}].evidence must be an array"
            )
        if gate in QUALIFIED_GATES and not evidence:
            raise QualificationError(f"qualification manifest {gate} has no evidence")
        if gate == "RD-13" and evidence:
            raise QualificationError("pre-promotion RD-13 evidence must be empty")
        for index, item in enumerate(evidence):
            entry = _require_object(
                item,
                name=f"manifest.gates[{gate}].evidence[{index}]",
                keys=("path", "sha256"),
            )
            path = _require_string(
                entry["path"],
                f"manifest.gates[{gate}].evidence[{index}].path",
            )
            if (
                not path.startswith(f"evidence/{gate}/")
                or Path(path).is_absolute()
                or ".." in Path(path).parts
            ):
                raise QualificationError(f"{gate} evidence path is unsafe: {path}")
            if path in evidence_paths:
                raise QualificationError(f"duplicate gate evidence path: {path}")
            evidence_paths.add(path)
            _require_sha256(
                entry["sha256"],
                f"manifest.gates[{gate}].evidence[{index}].sha256",
            )
    source_archives = [
        entry
        for entry in gates["RD-00"]["evidence"]
        if entry["path"].endswith("/candidate-source.tar")
    ]
    if (
        len(source_archives) != 1
        or source_archives[0]["sha256"] != source["archive_sha256"]
    ):
        raise QualificationError(
            "RD-00 evidence does not bind the frozen source archive"
        )
    return manifest


def _require_mapping_fields(
    value: object,
    *,
    name: str,
    fields: Iterable[str],
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise QualificationError(f"{name} must be an object")
    missing = sorted(set(fields) - set(value))
    if missing:
        raise QualificationError(f"{name} is missing required fields: {missing}")
    return value


def _load_attestation_receipts(path: Path, *, label: str) -> list[list[object]]:
    if path.stat().st_size > MAX_ATTESTATION_RECEIPTS_BYTES:
        raise QualificationError(
            f"{label} attestation receipts exceed "
            f"{MAX_ATTESTATION_RECEIPTS_BYTES} bytes"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise QualificationError(
            f"{label} attestation receipts are not readable UTF-8: {exc}"
        ) from exc
    lines = text.splitlines()
    if (
        len(lines) != ATTESTATION_RECEIPT_COUNT
        or any(not line.strip() for line in lines)
    ):
        raise QualificationError(
            f"{label} must contain exactly {ATTESTATION_RECEIPT_COUNT} "
            "non-empty JSONL receipts"
        )

    receipts: list[list[object]] = []
    for line_number, line in enumerate(lines, start=1):
        try:
            value = json.loads(
                line,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
        except (json.JSONDecodeError, QualificationError) as exc:
            raise QualificationError(
                f"{label} receipt line {line_number} is not strict JSON: {exc}"
            ) from exc
        if not isinstance(value, list) or not value:
            raise QualificationError(
                f"{label} receipt line {line_number} must be a non-empty "
                "GitHub CLI verification-result array"
            )
        receipts.append(value)
    return receipts


def _validate_attestation_receipts(
    path: Path,
    *,
    label: str,
    predicate_type: str,
    manifest: Mapping[str, Any],
    workflow_receipt: Mapping[str, Any],
) -> None:
    receipts = _load_attestation_receipts(path, label=label)
    expected_subjects = {
        artifact["filename"]: artifact["sha256"]
        for artifact in manifest["artifacts"]
    }
    repository = manifest["repository"]
    candidate_sha = manifest["source"]["sha"]
    workflow_path = _require_string(
        workflow_receipt["workflow_path"],
        "workflow receipt path",
    )
    workflow_ref = _require_string(
        workflow_receipt["workflow_ref"],
        "workflow receipt ref",
    )
    if workflow_path != QUALIFICATION_WORKFLOW_PATH:
        raise QualificationError(
            "workflow verification receipt names an unexpected workflow"
        )
    if not re.fullmatch(
        r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]*",
        workflow_ref,
    ):
        raise QualificationError(
            "workflow verification receipt ref is not a full branch ref"
        )

    signer_uri = (
        f"https://github.com/{repository}/{workflow_path}@{workflow_ref}"
    )
    repository_uri = f"https://github.com/{repository}"
    run_uri = (
        f"https://github.com/{repository}/actions/runs/"
        f"{manifest['workflow_run_id']}"
    )
    expected_certificate = {
        "subjectAlternativeName": signer_uri,
        "issuer": GITHUB_ACTIONS_OIDC_ISSUER,
        "buildSignerURI": signer_uri,
        "buildSignerDigest": candidate_sha,
        "runnerEnvironment": "github-hosted",
        "sourceRepositoryURI": repository_uri,
        "sourceRepositoryDigest": candidate_sha,
        "sourceRepositoryRef": workflow_ref,
        "buildConfigURI": signer_uri,
        "buildConfigDigest": candidate_sha,
        "buildTrigger": workflow_receipt["event"],
    }

    covered_subjects: set[tuple[str, str]] = set()
    expected_pairs = set(expected_subjects.items())
    for receipt_number, receipt in enumerate(receipts, start=1):
        receipt_subjects: set[tuple[str, str]] = set()
        for result_number, raw_result in enumerate(receipt, start=1):
            result_name = (
                f"{label} receipt {receipt_number} result {result_number}"
            )
            result = _require_object(
                raw_result,
                name=result_name,
                keys=("attestation", "verificationResult"),
            )
            attestation = result["attestation"]
            if not isinstance(attestation, Mapping) or not attestation:
                raise QualificationError(
                    f"{result_name}.attestation must be a non-empty object"
                )
            verification = _require_mapping_fields(
                result["verificationResult"],
                name=f"{result_name}.verificationResult",
                fields=(
                    "statement",
                    "signature",
                    "verifiedTimestamps",
                ),
            )
            timestamps = verification["verifiedTimestamps"]
            if not isinstance(timestamps, list) or not timestamps:
                raise QualificationError(
                    f"{result_name} has no verified timestamp evidence"
                )
            statement = _require_mapping_fields(
                verification["statement"],
                name=f"{result_name}.statement",
                fields=("subject", "predicateType"),
            )
            if statement["predicateType"] != predicate_type:
                raise QualificationError(
                    f"{result_name} predicate type does not match {label}"
                )
            subjects = statement["subject"]
            if not isinstance(subjects, list) or not subjects:
                raise QualificationError(
                    f"{result_name}.statement.subject must be non-empty"
                )
            result_subjects: set[tuple[str, str]] = set()
            for subject_number, raw_subject in enumerate(subjects, start=1):
                subject = _require_object(
                    raw_subject,
                    name=(
                        f"{result_name}.statement.subject[{subject_number}]"
                    ),
                    keys=("name", "digest"),
                )
                filename = _require_string(
                    subject["name"],
                    f"{result_name} subject name",
                )
                digest = _require_object(
                    subject["digest"],
                    name=f"{result_name} subject digest",
                    keys=("sha256",),
                )
                sha256 = _require_sha256(
                    digest["sha256"],
                    f"{result_name} subject sha256",
                )
                pair = (filename, sha256)
                if pair not in expected_pairs:
                    raise QualificationError(
                        f"{result_name} references an unqualified subject: "
                        f"{filename} sha256:{sha256}"
                    )
                if pair in result_subjects:
                    raise QualificationError(
                        f"{result_name} duplicates qualified subject {filename}"
                    )
                result_subjects.add(pair)
            receipt_subjects.update(result_subjects)

            signature = _require_mapping_fields(
                verification["signature"],
                name=f"{result_name}.signature",
                fields=("certificate",),
            )
            certificate = _require_mapping_fields(
                signature["certificate"],
                name=f"{result_name}.signature.certificate",
                fields=(*expected_certificate, "runInvocationURI"),
            )
            for field, expected in expected_certificate.items():
                actual = _require_string(
                    certificate[field],
                    f"{result_name} certificate {field}",
                )
                if actual != expected:
                    raise QualificationError(
                        f"{result_name} certificate {field} does not match "
                        "qualification identity"
                    )
            invocation = _require_string(
                certificate["runInvocationURI"],
                f"{result_name} certificate runInvocationURI",
            )
            if not re.fullmatch(
                rf"{re.escape(run_uri)}(?:/attempts/[1-9][0-9]*)?",
                invocation,
            ):
                raise QualificationError(
                    f"{result_name} run invocation does not match "
                    "qualification run"
                )
        covered_subjects.update(receipt_subjects)

    if covered_subjects != expected_pairs:
        raise QualificationError(
            f"{label} receipts do not cover exactly both qualified artifacts; "
            f"missing={sorted(expected_pairs - covered_subjects)}, "
            f"extra={sorted(covered_subjects - expected_pairs)}"
        )


def verify_bundle(args: argparse.Namespace) -> int:
    root = args.bundle.resolve()
    manifest = _validate_manifest(load_json(root / "qualification-manifest.json"))
    expected_files = {
        "qualification-manifest.json",
        "SHA256SUMS",
        "sbom.spdx.json",
        "provenance.intoto.json",
        "smoke-wheel.json",
        "smoke-sdist.json",
        "smoke-comparison.json",
        *(f"dist/{item['filename']}" for item in manifest["artifacts"]),
        *(
            item["path"]
            for gate in manifest["gates"].values()
            for item in gate["evidence"]
        ),
    }
    actual_files = {
        _bundle_relative_path(path, root)
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        raise QualificationError(
            "qualified bundle file set differs; "
            f"missing={sorted(expected_files - actual_files)}, "
            f"extra={sorted(actual_files - expected_files)}"
        )
    if manifest["repository"] != args.repository:
        raise QualificationError("qualification repository does not match")
    if manifest["workflow_run_id"] != args.workflow_run_id:
        raise QualificationError("qualification workflow run ID does not match")
    if manifest["source"]["sha"] != args.candidate_sha:
        raise QualificationError("qualification candidate SHA does not match")
    if getattr(args, "verify_repository", False):
        repository_root = args.repository_root.resolve()
        checkout_sha = _run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository_root,
        ).stdout.strip()
        checkout_tree = _run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=repository_root,
        ).stdout.strip()
        if checkout_sha != manifest["source"]["sha"]:
            raise QualificationError(
                "verifier checkout does not match qualification source SHA"
            )
        if checkout_tree != manifest["source"]["tree"]:
            raise QualificationError(
                "verifier checkout tree does not match qualification source tree"
            )
        if _project_version(repository_root) != manifest["version"]:
            raise QualificationError(
                "verifier checkout version does not match qualification"
            )

    artifacts = list(manifest["artifacts"])
    by_kind = {item["kind"]: item for item in artifacts}
    if by_kind["wheel"]["sha256"] != args.wheel_sha256:
        raise QualificationError("supplied wheel digest does not match qualification")
    if by_kind["sdist"]["sha256"] != args.sdist_sha256:
        raise QualificationError("supplied sdist digest does not match qualification")
    for artifact in artifacts:
        path = root / "dist" / artifact["filename"]
        if sha256_file(path) != artifact["sha256"]:
            raise QualificationError(f"artifact digest mismatch: {artifact['filename']}")

    expected_sums = "".join(
        f"{artifact['sha256']}  dist/{artifact['filename']}\n"
        for artifact in artifacts
    )
    if (root / "SHA256SUMS").read_text(encoding="ascii") != expected_sums:
        raise QualificationError("SHA256SUMS is not canonical or is inconsistent")
    for filename, digest in manifest["supporting_files"].items():
        if sha256_file(root / filename) != digest:
            raise QualificationError(f"supporting-file digest mismatch: {filename}")
    for gate, record in manifest["gates"].items():
        for entry in record["evidence"]:
            if sha256_file(root / entry["path"]) != entry["sha256"]:
                raise QualificationError(
                    f"{gate} evidence digest mismatch: {entry['path']}"
                )
    rd00_entries = manifest["gates"]["RD-00"]["evidence"]
    identity_entries = [
        entry for entry in rd00_entries if entry["path"].endswith("/identity.json")
    ]
    source_sum_entries = [
        entry for entry in rd00_entries if entry["path"].endswith("/SHA256SUMS")
    ]
    if len(identity_entries) != 1 or len(source_sum_entries) != 1:
        raise QualificationError("RD-00 identity/checksum evidence is incomplete")
    frozen_identity = _validate_identity(
        load_json(root / identity_entries[0]["path"])
    )
    if (
        frozen_identity["repository"] != manifest["repository"]
        or frozen_identity["source"] != manifest["source"]
        or frozen_identity["version"] != manifest["version"]
        or frozen_identity["tag"] != manifest["tag"]
        or frozen_identity["mode"] != "candidate"
    ):
        raise QualificationError("RD-00 frozen identity differs from qualification")
    expected_source_sum = (
        f"{manifest['source']['archive_sha256']}  candidate-source.tar\n"
    )
    if (
        root / source_sum_entries[0]["path"]
    ).read_text(encoding="ascii") != expected_source_sum:
        raise QualificationError("RD-00 source SHA256SUMS is inconsistent")

    wheel_smoke = _validate_smoke(load_json(root / "smoke-wheel.json"), "wheel")
    sdist_smoke = _validate_smoke(load_json(root / "smoke-sdist.json"), "sdist")
    comparison = _validate_smoke_comparison(load_json(root / "smoke-comparison.json"))
    _verify_smoke_consistency(
        wheel_smoke,
        sdist_smoke,
        comparison,
        wheel=by_kind["wheel"],
        sdist=by_kind["sdist"],
        version=manifest["version"],
    )

    provenance = load_json(root / "provenance.intoto.json")
    expected_provenance = _expected_provenance(
        repository=manifest["repository"],
        source=manifest["source"],
        workflow_run_id=manifest["workflow_run_id"],
        artifacts=artifacts,
        gates=manifest["gates"],
    )
    if provenance != expected_provenance:
        raise QualificationError(
            "provenance does not exactly bind qualification identity and artifacts"
        )
    sbom = load_json(root / "sbom.spdx.json")
    expected_sbom = _expected_sbom(
        repository=manifest["repository"],
        source=manifest["source"],
        version=manifest["version"],
        artifacts=artifacts,
    )
    if sbom != expected_sbom:
        raise QualificationError(
            "SBOM does not exactly bind qualification identity and artifacts"
        )

    if args.require_tag:
        tag = manifest["tag"]
        completed = _run(
            ["git", "rev-list", "-n", "1", tag],
            cwd=args.repository_root.resolve(),
            check=False,
        )
        if completed.returncode or completed.stdout.strip() != args.candidate_sha:
            raise QualificationError(
                f"{tag} does not resolve to qualified SHA {args.candidate_sha}"
            )
    if args.check_registry:
        _check_registry_unused(manifest["version"])
    receipt_output = getattr(args, "output", None)
    if receipt_output is not None:
        write_json(
            receipt_output.resolve(),
            {
                "schema_version": VERIFICATION_SCHEMA,
                "repository": manifest["repository"],
                "workflow_run_id": manifest["workflow_run_id"],
                "candidate_sha": manifest["source"]["sha"],
                "version": manifest["version"],
                "tag": manifest["tag"],
                "manifest_sha256": sha256_file(
                    root / "qualification-manifest.json"
                ),
                "artifacts": artifacts,
                "checks": {
                    "bundle": "PASS",
                    "registry_vacant": bool(args.check_registry),
                    "tag_resolved": bool(args.require_tag),
                },
            },
        )
    _github_output(
        {
            "version": manifest["version"],
            "tag": manifest["tag"],
            "wheel-filename": by_kind["wheel"]["filename"],
            "sdist-filename": by_kind["sdist"]["filename"],
        }
    )
    print(
        f"verified {manifest['tag']} from qualification run "
        f"{manifest['workflow_run_id']}"
    )
    return 0


def finalize_promotion(args: argparse.Namespace) -> int:
    manifest_path = args.manifest.resolve()
    manifest = _validate_manifest(load_json(manifest_path))
    verification = _require_object(
        load_json(args.verification.resolve()),
        name="bundle verification receipt",
        keys=(
            "schema_version",
            "repository",
            "workflow_run_id",
            "candidate_sha",
            "version",
            "tag",
            "manifest_sha256",
            "artifacts",
            "checks",
        ),
    )
    if verification["schema_version"] != VERIFICATION_SCHEMA:
        raise QualificationError("bundle verification receipt schema is unsupported")
    expected_receipt = {
        "repository": manifest["repository"],
        "workflow_run_id": manifest["workflow_run_id"],
        "candidate_sha": manifest["source"]["sha"],
        "version": manifest["version"],
        "tag": manifest["tag"],
        "manifest_sha256": sha256_file(manifest_path),
        "artifacts": manifest["artifacts"],
    }
    for field, expected in expected_receipt.items():
        if verification[field] != expected:
            raise QualificationError(
                f"bundle verification receipt {field} does not match qualification"
            )
    checks = _require_object(
        verification["checks"],
        name="bundle verification receipt.checks",
        keys=("bundle", "registry_vacant", "tag_resolved"),
    )
    if checks["bundle"] != "PASS" or checks["registry_vacant"] is not True:
        raise QualificationError(
            "promotion requires a passing bundle check and registry vacancy"
        )
    if args.require_tag and checks["tag_resolved"] is not True:
        raise QualificationError("publication requires a verified release tag")
    if (
        manifest["repository"] != args.repository
        or manifest["workflow_run_id"] != args.workflow_run_id
        or manifest["source"]["sha"] != args.candidate_sha
    ):
        raise QualificationError("promotion inputs do not match qualification identity")

    evidence: dict[str, dict[str, str]] = {}
    evidence_paths: dict[str, Path] = {}
    for spec in args.rd13_evidence:
        label, separator, path_text = spec.partition("=")
        if (
            not separator
            or not EVIDENCE_LABEL_RE.fullmatch(label)
            or not path_text
            or label in evidence
        ):
            raise QualificationError(
                "--rd13-evidence must be a unique lowercase-label=FILE"
            )
        path = Path(path_text).resolve()
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            raise QualificationError(f"RD-13 evidence is absent or empty: {path}")
        evidence[label] = {
            "filename": path.name,
            "sha256": sha256_file(path),
        }
        evidence_paths[label] = path
    required_evidence = {
        "workflow-run",
        "build-provenance",
        "sbom-attestation",
    }
    if set(evidence) != required_evidence:
        raise QualificationError(
            "RD-13 evidence labels differ; "
            f"missing={sorted(required_evidence - set(evidence))}, "
            f"extra={sorted(set(evidence) - required_evidence)}"
        )
    workflow_receipt = _require_object(
        load_json(evidence_paths["workflow-run"]),
        name="workflow verification receipt",
        keys=(
            "schema_version",
            "repository",
            "workflow_run_id",
            "candidate_sha",
            "workflow_path",
            "workflow_ref",
            "workflow_revision",
            "event",
        ),
    )
    if workflow_receipt["schema_version"] != WORKFLOW_VERIFICATION_SCHEMA:
        raise QualificationError("workflow verification receipt schema is unsupported")
    expected_workflow = {
        "repository": manifest["repository"],
        "workflow_run_id": manifest["workflow_run_id"],
        "candidate_sha": manifest["source"]["sha"],
        "workflow_revision": manifest["source"]["sha"],
        "event": "workflow_dispatch",
    }
    for field, expected in expected_workflow.items():
        if workflow_receipt[field] != expected:
            raise QualificationError(
                f"workflow verification receipt {field} does not match qualification"
            )
    _validate_attestation_receipts(
        evidence_paths["build-provenance"],
        label="build provenance",
        predicate_type=SLSA_PROVENANCE_PREDICATE,
        manifest=manifest,
        workflow_receipt=workflow_receipt,
    )
    _validate_attestation_receipts(
        evidence_paths["sbom-attestation"],
        label="SPDX SBOM",
        predicate_type=SPDX_SBOM_PREDICATE,
        manifest=manifest,
        workflow_receipt=workflow_receipt,
    )

    gates = {
        gate: record["status"]
        for gate, record in manifest["gates"].items()
    }
    gates["RD-13"] = "PASS"
    if any(status != "PASS" for status in gates.values()):
        raise QualificationError("promotion cannot derive GO from non-PASS gates")
    payload = {
        "schema_version": PROMOTION_SCHEMA,
        "repository": manifest["repository"],
        "workflow_run_id": manifest["workflow_run_id"],
        "candidate_sha": manifest["source"]["sha"],
        "candidate_tree": manifest["source"]["tree"],
        "candidate_version": manifest["version"],
        "tag": manifest["tag"],
        "qualification_manifest_sha256": sha256_file(manifest_path),
        "artifacts": manifest["artifacts"],
        "gates": gates,
        "rd13_evidence": dict(sorted(evidence.items())),
        "failed": [],
        "blocked": [],
        "decision": "GO",
    }
    write_json(args.output.resolve(), payload)
    print("GO")
    return 0


def compare_builds(args: argparse.Namespace) -> int:
    first_wheel, first_sdist = _dist_files(args.first.resolve())
    second_wheel, second_sdist = _dist_files(args.second.resolve())
    pairs = ((first_wheel, second_wheel), (first_sdist, second_sdist))
    for first, second in pairs:
        if first.name != second.name:
            raise QualificationError(
                f"independent build filenames differ: {first.name}, {second.name}"
            )
        if sha256_file(first) != sha256_file(second):
            raise QualificationError(
                f"independent build bytes differ: {first.name}"
            )
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    dist = output / "dist"
    dist.mkdir()
    for path in (first_wheel, first_sdist):
        (dist / path.name).write_bytes(path.read_bytes())
    result = {
        "schema_version": "agent-wiki-reproducible-build/v1",
        "artifacts": [
            _artifact_entry(dist / first_wheel.name, "wheel"),
            _artifact_entry(dist / first_sdist.name, "sdist"),
        ],
        "reproducible": True,
    }
    write_json(output / "reproducible-build.json", result)
    return 0


def lock_value(args: argparse.Namespace) -> int:
    value: object = load_json(args.lock.resolve())
    for component in args.key.split("."):
        if not isinstance(value, Mapping) or component not in value:
            raise QualificationError(f"toolchain lock has no {args.key}")
        value = value[component]
    if isinstance(value, (dict, list)) or value is None:
        raise QualificationError(f"toolchain lock value {args.key} is not scalar")
    print(str(value).lower() if isinstance(value, bool) else value)
    return 0


def verify_download(args: argparse.Namespace) -> int:
    value: object = load_json(args.lock.resolve())
    for component in args.key.split("."):
        if not isinstance(value, Mapping) or component not in value:
            raise QualificationError(f"toolchain lock has no {args.key}")
        value = value[component]
    artifact = _require_object(
        value,
        name=f"toolchain lock {args.key}",
        keys=("url", "sha256"),
    )
    url = _require_string(artifact["url"], f"{args.key}.url")
    expected = _require_sha256(artifact["sha256"], f"{args.key}.sha256")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "agent-wiki-release-qualification"},
    )
    destination = args.output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            destination.write_bytes(response.read())
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        raise QualificationError(f"locked download unavailable: {url}: {exc}") from exc
    actual = sha256_file(destination)
    if actual != expected:
        destination.unlink(missing_ok=True)
        raise QualificationError(
            f"locked download digest mismatch for {url}: "
            f"expected {expected}, got {actual}"
        )
    print(actual)
    return 0


def validate_workflow_run(
    payload: object,
    *,
    repository: str,
    workflow_path: str,
    workflow_name: str,
    workflow_ref: str,
    workflow_revision: str,
    event: str,
    candidate_sha: str,
) -> None:
    if not isinstance(payload, Mapping):
        raise QualificationError("GitHub workflow run response must be an object")
    candidate_sha = _require_sha(candidate_sha, "candidate SHA")
    workflow_revision = _require_sha(workflow_revision, "workflow revision")
    if workflow_revision != candidate_sha:
        raise QualificationError(
            "qualification workflow revision must equal the candidate SHA"
        )
    if not re.fullmatch(
        r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]*",
        workflow_ref,
    ):
        raise QualificationError(
            "qualification workflow ref must be a full, safe branch ref"
        )
    ref_components = workflow_ref.removeprefix("refs/heads/").split("/")
    if (
        any(
            not component
            or component.startswith(".")
            or component.endswith((".", ".lock"))
            for component in ref_components
        )
        or ".." in workflow_ref
        or "@{" in workflow_ref
        or "//" in workflow_ref
    ):
        raise QualificationError(
            "qualification workflow ref must be a full, safe branch ref"
        )
    ref_name = workflow_ref.removeprefix("refs/heads/")

    run_repository = payload.get("repository")
    if not isinstance(run_repository, Mapping):
        raise QualificationError("GitHub workflow run has no repository identity")
    head_repository = payload.get("head_repository")
    if not isinstance(head_repository, Mapping):
        raise QualificationError(
            "GitHub workflow run has no head repository identity"
        )
    run_path, separator, run_ref = str(payload.get("path", "")).partition("@")
    expected_run_refs = (ref_name, workflow_ref)
    expected = {
        "repository": (run_repository.get("full_name"), repository),
        "head repository": (head_repository.get("full_name"), repository),
        "workflow path": (run_path, workflow_path),
        "workflow path ref marker": (separator, "@"),
        "workflow ref": (run_ref in expected_run_refs, True),
        "head branch": (payload.get("head_branch"), ref_name),
        "event": (payload.get("event"), event),
        "workflow name": (payload.get("name"), workflow_name),
        "status": (payload.get("status"), "completed"),
        "conclusion": (payload.get("conclusion"), "success"),
        "head SHA": (payload.get("head_sha"), workflow_revision),
    }
    mismatches = [
        f"{field}={actual!r} (expected {wanted!r})"
        for field, (actual, wanted) in expected.items()
        if actual != wanted
    ]
    if mismatches:
        raise QualificationError(
            "qualification workflow run identity mismatch: " + "; ".join(mismatches)
        )


def verify_workflow_run(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise QualificationError("GITHUB_TOKEN is required to verify workflow run")
    url = (
        f"https://api.github.com/repos/{args.repository}/actions/runs/"
        f"{args.workflow_run_id}"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "agent-wiki-release-promotion",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(
                response.read(),
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        urllib.error.URLError,
        TimeoutError,
    ) as exc:
        raise QualificationError(f"GitHub workflow run lookup failed closed: {exc}") from exc
    validate_workflow_run(
        payload,
        repository=args.repository,
        workflow_path=args.workflow_path,
        workflow_name=args.workflow_name,
        workflow_ref=args.workflow_ref,
        workflow_revision=args.workflow_revision,
        event=args.event,
        candidate_sha=args.candidate_sha,
    )
    if getattr(args, "output", None) is not None:
        write_json(
            args.output.resolve(),
            {
                "schema_version": WORKFLOW_VERIFICATION_SCHEMA,
                "repository": args.repository,
                "workflow_run_id": args.workflow_run_id,
                "candidate_sha": args.candidate_sha,
                "workflow_path": args.workflow_path,
                "workflow_ref": args.workflow_ref,
                "workflow_revision": args.workflow_revision,
                "event": args.event,
            },
        )
    print(
        f"verified successful {args.workflow_name} run {args.workflow_run_id} "
        f"for {args.candidate_sha}"
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    freeze = subparsers.add_parser("freeze-source")
    freeze.add_argument("--root", type=Path, default=Path("."))
    freeze.add_argument("--output", type=Path, required=True)
    freeze.add_argument("--expected-sha", required=True)
    freeze.add_argument("--repository", required=True)
    freeze.add_argument("--mode", choices=("candidate", "tagged"), default="candidate")
    freeze.add_argument("--check-registry", action="store_true")
    freeze.add_argument("--required-ancestor", action="append", default=[])
    freeze.set_defaults(function=freeze_source)

    create = subparsers.add_parser("create-venv")
    create.add_argument("--path", type=Path, required=True)
    create.set_defaults(function=create_venv)

    extract = subparsers.add_parser("extract-source")
    extract.add_argument("--archive", type=Path, required=True)
    extract.add_argument("--sha256", required=True)
    extract.add_argument("--destination", type=Path, required=True)
    extract.set_defaults(function=extract_source)

    junit = subparsers.add_parser("verify-junit")
    junit.add_argument("--junit", type=Path, required=True)
    junit.add_argument("--lane", required=True)
    junit.add_argument("--allowlist", type=Path, required=True)
    junit.add_argument("--output", type=Path, required=True)
    junit.add_argument("--minimum-collected", type=int, default=0)
    junit.add_argument("--minimum-passed", type=int, default=0)
    junit.add_argument("--discovery", action="store_true")
    junit.set_defaults(function=verify_junit)

    discover = subparsers.add_parser("discover-allowlist")
    discover.add_argument("--result", action="append", required=True)
    discover.add_argument("--output", type=Path, required=True)
    discover.set_defaults(function=discover_allowlist)

    owners = subparsers.add_parser("verify-owner-lanes")
    owners.add_argument("--identity", type=Path, required=True)
    owners.add_argument("--allowlist", type=Path, required=True)
    owners.add_argument("--owner-result", action="append", required=True)
    owners.add_argument("--owner-junit", action="append", required=True)
    owners.add_argument("--output", type=Path, required=True)
    owners.set_defaults(function=verify_owner_lanes)

    decision = subparsers.add_parser("aggregate")
    decision.add_argument("--candidate-sha", required=True)
    decision.add_argument("--candidate-version", required=True)
    decision.add_argument("--gate", action="append", required=True)
    decision.add_argument("--output", type=Path, required=True)
    decision.add_argument(
        "--allow-non-go-exit-zero",
        action="store_true",
        help=(
            "Preserve a non-GO decision in JSON but return zero for a "
            "pre-promotion diagnostic aggregate"
        ),
    )
    decision.set_defaults(function=aggregate)

    smoke = subparsers.add_parser("compare-smoke")
    smoke.add_argument("--wheel", type=Path, required=True)
    smoke.add_argument("--sdist", type=Path, required=True)
    smoke.add_argument("--output", type=Path, required=True)
    smoke.set_defaults(function=compare_smoke)

    builds = subparsers.add_parser("compare-builds")
    builds.add_argument("--first", type=Path, required=True)
    builds.add_argument("--second", type=Path, required=True)
    builds.add_argument("--output", type=Path, required=True)
    builds.set_defaults(function=compare_builds)

    bundle = subparsers.add_parser("build-bundle")
    bundle.add_argument("--identity", type=Path, required=True)
    bundle.add_argument("--dist", type=Path, required=True)
    bundle.add_argument("--wheel-smoke", type=Path, required=True)
    bundle.add_argument("--sdist-smoke", type=Path, required=True)
    bundle.add_argument("--smoke-comparison", type=Path, required=True)
    bundle.add_argument("--gate-decision", type=Path, required=True)
    bundle.add_argument(
        "--evidence",
        action="append",
        required=True,
        help="Bind gate evidence as RD-NN:label=FILE_OR_DIRECTORY",
    )
    bundle.add_argument("--workflow-run-id", type=int, required=True)
    bundle.add_argument("--output", type=Path, required=True)
    bundle.set_defaults(function=build_bundle)

    verify = subparsers.add_parser("verify-bundle")
    verify.add_argument("--bundle", type=Path, required=True)
    verify.add_argument("--repository", required=True)
    verify.add_argument("--workflow-run-id", type=int, required=True)
    verify.add_argument("--candidate-sha", required=True)
    verify.add_argument("--wheel-sha256", required=True)
    verify.add_argument("--sdist-sha256", required=True)
    verify.add_argument("--repository-root", type=Path, default=Path("."))
    verify.add_argument("--verify-repository", action="store_true")
    verify.add_argument("--require-tag", action="store_true")
    verify.add_argument("--check-registry", action="store_true")
    verify.add_argument("--output", type=Path)
    verify.set_defaults(function=verify_bundle)

    promote = subparsers.add_parser("finalize-promotion")
    promote.add_argument("--manifest", type=Path, required=True)
    promote.add_argument("--verification", type=Path, required=True)
    promote.add_argument("--repository", required=True)
    promote.add_argument("--workflow-run-id", type=int, required=True)
    promote.add_argument("--candidate-sha", required=True)
    promote.add_argument("--rd13-evidence", action="append", required=True)
    promote.add_argument("--require-tag", action="store_true")
    promote.add_argument("--output", type=Path, required=True)
    promote.set_defaults(function=finalize_promotion)

    locked = subparsers.add_parser("lock-value")
    locked.add_argument("--lock", type=Path, required=True)
    locked.add_argument("--key", required=True)
    locked.set_defaults(function=lock_value)

    download = subparsers.add_parser("verify-download")
    download.add_argument("--lock", type=Path, required=True)
    download.add_argument("--key", required=True)
    download.add_argument("--output", type=Path, required=True)
    download.set_defaults(function=verify_download)

    run = subparsers.add_parser("verify-workflow-run")
    run.add_argument("--repository", required=True)
    run.add_argument("--workflow-run-id", type=int, required=True)
    run.add_argument("--candidate-sha", required=True)
    run.add_argument(
        "--workflow-path",
        default=".github/workflows/release-qualification.yml",
    )
    run.add_argument("--workflow-name", default="Release qualification")
    run.add_argument("--workflow-ref", required=True)
    run.add_argument("--workflow-revision", required=True)
    run.add_argument("--event", default="workflow_dispatch")
    run.add_argument("--output", type=Path)
    run.set_defaults(function=verify_workflow_run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        return int(args.function(args))
    except QualificationError as exc:
        print(f"release qualification failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
