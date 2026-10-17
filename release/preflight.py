#!/usr/bin/env python3
"""Local release preparation and rehearsal; never qualification or publication."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
from typing import Any
import uuid

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).absolute().parent.parent))
from release import qualification

PLAN_SCHEMA = "agent-wiki-local-preflight-plan/v1"
RECEIPT_SCHEMA = "agent-wiki-local-preflight-receipt/v1"
MAX_DOCUMENT = 16 * 1024 * 1024
MAX_INPUT = 64 * 1024 * 1024
# Retain an over-budget local source diagnostic. This never changes the hosted
# 64 MiB admission limit; only this known operation-owned evidence path may use it.
LOCAL_ARCHIVE_EVIDENCE_LIMIT = 320 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024
STAGES = ("contracts", "static", "freeze", "host-core", "builds", "artifacts")
PLAN_KEYS = {
    "schema_version",
    "root",
    "candidate_sha",
    "binding",
    "readiness",
    "gates",
    "created_at",
    "plan_hash",
}
RECEIPT_KEYS = {
    "schema_version",
    "plan",
    "work",
    "owner",
    "operation",
    "requested_stages",
    "attempts",
    "evidence",
    "status",
    "pending",
    "created_at",
    "receipt_hash",
}


class PreflightError(ValueError):
    """A local preparation binding is missing, stale or unsafe."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sealed(value: dict, key: str) -> dict:
    return {**value, key: _hash(_canonical(value))}


def _check_seal(value: dict, key: str) -> None:
    expected = value.get(key)
    if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
        raise PreflightError(f"Invalid {key}")
    if _hash(_canonical({k: v for k, v in value.items() if k != key})) != expected:
        raise PreflightError(f"Changed {key}")


def _safe(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    for item in [*reversed(path.parents), path]:
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise PreflightError(f"Redirected path refused: {item}")
    return path


def _read(path: Path, limit: int = MAX_DOCUMENT) -> bytes:
    path = _safe(path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
        raise PreflightError(f"Expected bounded single-link regular file: {path}")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    after = path.lstat()
    if len(raw) > limit or (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise PreflightError(f"File changed during read: {path}")
    return raw


def read_document(path: Path) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PreflightError(f"Duplicate JSON field: {key}")
            result[key] = value
        return result

    def constant(value):
        raise PreflightError(f"Nonfinite JSON value: {value}")

    try:
        value = json.loads(
            _read(path).decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=constant,
        )
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise PreflightError(f"Invalid bounded JSON document: {exc}") from exc
    if not isinstance(value, dict):
        raise PreflightError("Document must be an object")
    return value


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode:
        raise PreflightError(f"Git inspection failed: {result.stderr.strip()[:1000]}")
    return result.stdout


def _destination(root: Path, path: Path) -> Path:
    root, path = _safe(root), _safe(path)
    if not path.is_relative_to(root) or path == root:
        raise PreflightError(
            "Internal output must be inside the project at an ignored destination"
        )
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--", str(path)],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PreflightError(f"Internal output is not ignored: {path}")
    return path


def write_document(path: Path, document: dict, *, root: Path) -> None:
    path = _destination(root, path)
    raw = _canonical(document) + b"\n"
    if len(raw) > MAX_DOCUMENT:
        raise PreflightError("Document exceeds byte bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    _safe(path.parent)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError as exc:
        raise PreflightError(
            "Output is occupied; retain the original document"
        ) from exc


def _version(command: list[str], root: Path) -> dict:
    executable = shutil.which(command[0])
    if executable is None:
        return {"path": None, "version": None, "status": "unavailable"}
    try:
        executable = os.path.abspath(executable)
        result = subprocess.run(
            [executable, *command[1:]],
            cwd=root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        output = (result.stdout or result.stderr).strip()
        if result.returncode or len(output) > 4096:
            return {"path": executable, "version": None, "status": "unavailable"}
        return {
            "path": executable,
            "version": output,
            "status": "observed",
            "sha256": _runtime_hash(Path(executable)),
        }
    except (OSError, subprocess.TimeoutExpired):
        return {"path": executable, "version": None, "status": "unavailable"}


def _runtime_hash(path: Path) -> str:
    # Reading binary identity may follow its normal symlink. Invocation always
    # preserves the original launcher path and virtual-environment prefix.
    digest = hashlib.sha256()
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > 512 * 1024 * 1024:
        raise PreflightError("Runtime binary exceeds inspection bound")
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise PreflightError("Runtime binary changed during inspection")
    return digest.hexdigest()


def _environment(root: Path) -> dict:
    # Launcher spelling is deliberately retained: resolving a venv symlink changes isolation.
    try:
        import llm_wiki_cli as provider

        installed = {
            "version": importlib.metadata.version("agent-wiki-cli"),
            "source_version": provider.__version__,
            "origin": os.path.abspath(provider.__file__),
            "status": "observed",
        }
    except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
        installed = {"status": "unavailable", "reason": str(exc)}
    return {
        "platform": sys.platform,
        "machine": platform.machine().lower(),
        "python": sys.version,
        "executable": os.path.abspath(sys.executable),
        "python_binary_sha256": _runtime_hash(Path(sys.executable)),
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "provider": installed,
        "tools": {
            name: _version(command, root)
            for name, command in {
                "node": ["node", "--version"],
                "npm": ["npm", "--version"],
                "actionlint": ["actionlint", "--version"],
                "go": ["go", "version"],
                "rust": ["rustc", "--version"],
                "haskell": ["ghc", "--numeric-version"],
            }.items()
        },
    }


def _helper(root: Path, environment: dict) -> dict:
    """Inspect the configured prepared helper without setup or arbitrary paths."""
    cache = root / ".git/llm-wiki-extractors/typescript"
    metadata = cache / "current.json"
    if not metadata.exists():
        return {
            "status": "unavailable",
            "reason": "Configured TypeScript helper not prepared",
            "files": {},
        }
    value = read_document(metadata)
    path = _safe(Path(value.get("path", "")))
    prepared = _safe(Path(value.get("root", "")))
    if not path.is_relative_to(cache) or not prepared.is_relative_to(cache):
        raise PreflightError("Helper metadata redirects outside configured cache")
    files = {}
    total = 0
    for file in sorted(path.rglob("*")):
        _safe(file)
        if file.is_dir():
            continue
        raw = _read(file, MAX_INPUT)
        total += len(raw)
        if len(files) > 10000 or total > MAX_TOTAL:
            raise PreflightError("Helper inspection exceeds bound")
        files[file.relative_to(path).as_posix()] = _hash(raw)
    copies = {
        name: _hash(_read(prepared / name))
        for name in ("extract.js", "package.json", "package-lock.json")
    }
    from llm_wiki_cli.services import extractor_helpers as helpers

    active = (
        "node "
        + str(environment["tools"]["node"]["version"])
        + "; npm "
        + str(environment["tools"]["npm"]["version"])
    )
    current = helpers._manifest_current(cache.parent, "typescript")
    ready = current is not None and value.get("toolchain") == active
    return {
        "status": "ready" if ready else "blocked",
        "reason": None
        if ready
        else "Prepared helper/source/platform differs from active Node/npm; explicitly prepare and re-plan",
        "metadata": _hash(_read(metadata)),
        "files": files,
        "copies": copies,
    }


def _capture_binding(root: Path) -> dict:
    from release.preflight_contracts import qualification_contract

    root = _safe(root)
    sha, tree = (
        _git(root, "rev-parse", "HEAD").strip(),
        _git(root, "rev-parse", "HEAD^{tree}").strip(),
    )
    names = _git(
        root, "ls-files", "--cached", "--others", "--exclude-standard", "-z"
    ).split("\0")
    files, total = {}, 0
    if len(names) > 50001:
        raise PreflightError("Source inventory exceeds path bound")
    for name in sorted(set(names) - {""}):
        path = root / name
        if not path.exists():
            files[name] = None
            continue
        raw = _read(path, MAX_INPUT)
        total += len(raw)
        if total > MAX_TOTAL:
            raise PreflightError("Source inspection exceeds byte bound")
        files[name] = {
            "sha256": _hash(raw),
            "bytes": len(raw),
            "executable": bool(path.stat().st_mode & 0o111),
        }
    for name in (".llm-wiki/source-selection.json", ".llm-wiki/team.json"):
        path = root / name
        files[name] = (
            {"sha256": _hash(_read(path)), "bytes": path.stat().st_size}
            if path.exists()
            else None
        )
    environment = _environment(root)
    helper = _helper(root, environment)
    contract = qualification_contract(root)
    return {
        "sha": sha,
        "tree": tree,
        "dirty": _git(root, "status", "--porcelain=v1", "--untracked-files=all"),
        "files": files,
        "contract": contract,
        "environment": environment,
        "helper": helper,
        "maintenance": _maintenance(root),
    }


def _maintenance(root: Path) -> dict:
    from release import knowledge_maintenance as maintenance

    config = root / "release/knowledge-maintenance.json"
    if not config.exists():
        return {"status": "not-configured"}
    try:
        digest = maintenance.composite_policy_digest(
            lambda name: _read(root / name, MAX_INPUT)
        )
        policy = maintenance.policy(_read(config), implementation_hash=digest)
        return {
            "policy": policy["policy"],
            "mode": policy["mode"],
            "implementation": digest,
            "binding": "current",
            "version": maintenance.version_check(root, policy),
            "status": "hosted-proof-required"
            if policy["mode"] == "required"
            else policy["mode"],
        }
    except (ValueError, KeyError, OSError) as exc:
        return {"status": "blocked", "reason": str(exc)[:2000]}


def _eligibility(root: Path, check_registry: bool) -> dict:
    result = qualification.release_eligibility(
        root, check_registry=check_registry, check_remote=check_registry
    )
    return {
        **result,
        "scope": "remote-inspected" if check_registry else "local-only",
        "external": "observed-at-plan-time-recheck-before-publication"
        if check_registry
        else "remote-tag-and-registry-not-inspected",
        "build_residue": [
            name
            for name in ("build", "dist", "src/agent_wiki_cli.egg-info")
            if (root / name).exists()
        ],
    }


def _review(root: Path, path: Path | None, sha: str, version: str) -> dict:
    if path is None:
        return {
            "status": "pending",
            "reason": "Supply a candidate-bound issue snapshot/disposition and SemVer review; no review is inferred",
        }
    path = _destination(root, path)
    value = read_document(path)
    if (
        set(value)
        != {
            "schema_version",
            "candidate_sha",
            "version",
            "observed_at",
            "issues",
            "dispositions",
            "semver",
        }
        or value["schema_version"] != "agent-wiki-local-release-review/v1"
        or value["candidate_sha"] != sha
        or value["version"] != version
        or not isinstance(value["issues"], list)
        or not isinstance(value["dispositions"], list)
        or not isinstance(value["semver"], dict)
    ):
        raise PreflightError("Invalid candidate-bound release review")
    _fresh_time(value["observed_at"])
    issues, decisions = {}, {}
    for item in value["issues"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"number", "title"}
            or type(item["number"]) is not int
            or item["number"] <= 0
            or not isinstance(item["title"], str)
            or item["number"] in issues
        ):
            raise PreflightError("Invalid or duplicate issue snapshot row")
        issues[item["number"]] = item
    for item in value["dispositions"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"number", "decision", "reason"}
            or type(item["number"]) is not int
            or item["number"] in decisions
            or item["decision"] not in {"blocker", "resolved", "deferred", "not-a-bug"}
            or not isinstance(item["reason"], str)
            or not item["reason"].strip()
        ):
            raise PreflightError("Invalid issue disposition")
        decisions[item["number"]] = item
    semver = value["semver"]
    if (
        set(issues) != set(decisions)
        or set(semver) != {"baseline", "target", "reason"}
        or not isinstance(semver["baseline"], str)
        or not re.fullmatch(r"\d+\.\d+\.\d+", semver["baseline"])
        or semver["target"] != version
        or not isinstance(semver["reason"], str)
        or not semver["reason"].strip()
    ):
        raise PreflightError("Release review omits an issue or SemVer decision")
    return {
        "status": "blocked"
        if any(row["decision"] == "blocker" for row in decisions.values())
        else "recorded",
        "path": str(path),
        "sha256": _hash(_read(path)),
        "record": value,
        "qualification": "Caller-supplied local record; not independent approval or authenticated GitHub completeness",
    }


def _fresh_time(value: str) -> None:
    try:
        timestamp = datetime.fromisoformat(value)
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        if timestamp.tzinfo is None or not 0 <= age <= 86400:
            raise ValueError("expired or future observation")
    except (ValueError, TypeError) as exc:
        raise PreflightError(
            "Plan/review timestamp expired or invalid; re-plan mutable external observations"
        ) from exc


def create_plan(
    root: Path,
    candidate_sha: str,
    check_registry: bool = False,
    review_file: Path | None = None,
) -> dict:
    root = _safe(root)
    if not re.fullmatch(r"[a-fA-F0-9]{40}", candidate_sha):
        raise PreflightError("Candidate requires a full Git SHA")
    binding = _capture_binding(root)
    if binding["sha"] != candidate_sha.lower():
        raise PreflightError("Candidate SHA differs from checked out source")
    contract = binding["contract"]
    gates = _gates(contract)
    readiness = _eligibility(root, check_registry)
    readiness["review"] = _review(
        root, review_file, candidate_sha.lower(), readiness["version"]
    )
    return _sealed(
        {
            "schema_version": PLAN_SCHEMA,
            "root": str(root),
            "candidate_sha": candidate_sha.lower(),
            "binding": binding,
            "readiness": readiness,
            "gates": gates,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "plan_hash",
    )


def _gates(contract: dict) -> list[dict]:
    return [
        {
            "id": job["id"],
            "owner": job["owner"],
            "status": "pending",
            "release_pending": bool(job["normal_required"]),
            "environments": job["environments"],
            "reason": "Local results cannot satisfy hosted producer identity",
        }
        for job in contract["jobs"]
    ]


def validate_plan(plan: dict, root: Path) -> None:
    if set(plan) != PLAN_KEYS or plan.get("schema_version") != PLAN_SCHEMA:
        raise PreflightError("Unsupported local plan fields/schema")
    _check_seal(plan, "plan_hash")
    if (
        not isinstance(plan["binding"], dict)
        or not isinstance(plan["readiness"], dict)
        or not isinstance(plan["gates"], list)
        or any(not isinstance(row, dict) for row in plan["gates"])
        or not isinstance(plan["root"], str)
        or not isinstance(plan["candidate_sha"], str)
    ):
        raise PreflightError("Invalid nested local plan fields")
    root = _safe(root)
    if plan["root"] != str(root) or plan["candidate_sha"] != plan["binding"].get("sha"):
        raise PreflightError("Plan belongs to another root/candidate")
    if _capture_binding(root) != plan["binding"]:
        raise PreflightError(
            "Stale plan: source, harness, contract, selection, wiki or environment changed; re-plan final committed candidate"
        )
    if plan["gates"] != _gates(plan["binding"]["contract"]):
        raise PreflightError("Plan omitted or changed required native/hosted gates")
    local = _eligibility(root, False)
    if (
        plan["readiness"].get("version") != local.get("version")
        or plan["readiness"].get("scope") not in {"local-only", "remote-inspected"}
        or plan["readiness"].get("status")
        not in {"eligible", "waiting_release_preparation", "blocked_unavailable"}
        or local.get("status") != "eligible"
        and plan["readiness"].get("status") != local.get("status")
    ):
        raise PreflightError("Readiness does not match current local candidate")
    if plan["readiness"].get("build_residue", []) != local.get("build_residue", []):
        raise PreflightError(
            "Build residue changed; prepare a clean candidate and re-plan"
        )
    _fresh_time(plan["created_at"])
    review = plan["readiness"].get("review")
    if not isinstance(review, dict):
        raise PreflightError("Explicit review disposition missing")
    expected_review = _review(
        root,
        Path(review["path"]) if "path" in review else None,
        plan["candidate_sha"],
        local["version"],
    )
    if review != expected_review:
        raise PreflightError("Release review changed or omitted")


def _owner(root: Path) -> dict:
    return {"repository_root": str(root), "kind": "local-pre-release-work/v1"}


def _manifest(work: Path, attempts: list[dict]) -> dict:
    from release import preflight_runner as runner

    result, total = {}, 0
    paths = [work / runner.OWNER_FILE]
    for attempt in attempts:
        if attempt.get("stage") != "readiness":
            paths.extend(runner.evidence_paths(attempt))
    for path in sorted(set(paths)):
        _safe(path)
        if path.is_dir():
            continue
        name = path.relative_to(work).as_posix()
        if name.startswith("receipts/"):
            continue
        raw = _read(
            path,
            LOCAL_ARCHIVE_EVIDENCE_LIMIT
            if name.endswith("/archive-budget/candidate-source.zip")
            else MAX_INPUT,
        )
        total += len(raw)
        if len(result) >= 50000 or total > MAX_TOTAL:
            raise PreflightError("Evidence inspection exceeds bounds")
        result[name] = {"sha256": _hash(raw), "bytes": len(raw)}
    return result


def _outcome(
    plan: dict, operation: str, requested: list[str], attempts: list[dict]
) -> str:
    statuses = [row.get("status") for row in attempts]
    if "failed" in statuses:
        return "failed"
    if "blocked" in statuses or not statuses:
        return "blocked"
    if (
        operation != "run"
        or requested != list(STAGES)
        or [row.get("stage") for row in attempts] != list(STAGES)
    ):
        return "blocked"
    if (
        plan["binding"]["dirty"]
        or plan["readiness"]["status"] != "eligible"
        or any(x != "passed" for x in statuses)
        or plan["readiness"].get("review", {}).get("status") != "recorded"
        or plan["readiness"].get("build_residue", [])
    ):
        return "blocked"
    return "local-ready-hosted-required"


def _execute(
    plan_path: Path, work: Path, operation: str, stages: tuple[str, ...]
) -> dict:
    from release import preflight_runner as runner

    plan = read_document(plan_path)
    root = _safe(Path(plan["root"]))
    validate_plan(plan, root)
    work = _destination(root, work)
    owner = _owner(root)
    if work.exists():
        runner.validate_owned_work(work, owner)
    else:
        runner.claim_work(work, owner)
    requested = list(stages)
    if (
        not requested
        or len(set(requested)) != len(requested)
        or any(stage not in (*STAGES, "prepare") for stage in requested)
    ):
        raise PreflightError("Unknown or duplicate local stage")
    diagnostic = operation == "run" and stages == ("contracts",)
    attempts = []
    if (
        not diagnostic
        and operation == "run"
        and (
            plan["binding"]["dirty"]
            or plan["readiness"]["status"] != "eligible"
            or plan["readiness"]["review"]["status"] != "recorded"
            or plan["binding"].get("helper", {}).get("status") == "blocked"
            or plan["binding"].get("maintenance", {}).get("status") == "blocked"
            or plan["readiness"].get("build_residue", [])
        )
    ):
        attempts = [
            {
                "stage": "readiness",
                "status": "blocked",
                "reason": "Finish release preparation, commit and create a fresh eligible plan before full rehearsal",
            }
        ]
    else:
        for stage in stages:
            attempt = runner.execute_stage(
                stage,
                repo=root,
                work=work,
                binding=owner,
                candidate_sha=plan["candidate_sha"],
                version=plan["readiness"]["version"],
            )
            attempts.append(attempt)
            if attempt["status"] != "passed":
                break
    if operation == "run":
        validate_plan(
            plan, root
        )  # Guard commands or concurrent edits that changed their inputs.
    pending = [
        *plan["gates"],
        *[
            {
                "id": stage,
                "status": "pending",
                "release_pending": True,
                "reason": "Local mandatory stage not passed",
            }
            for stage in STAGES
            if not any(
                row.get("stage") == stage and row.get("status") == "passed"
                for row in attempts
            )
        ],
    ]
    receipt = _sealed(
        {
            "schema_version": RECEIPT_SCHEMA,
            "plan": plan,
            "work": str(work),
            "owner": owner,
            "operation": operation,
            "requested_stages": requested,
            "attempts": attempts,
            "evidence": _manifest(work, attempts),
            "status": _outcome(plan, operation, requested, attempts),
            "pending": pending,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "receipt_hash",
    )
    output = work / "receipts" / (str(uuid.uuid4()) + ".json")
    write_document(output, receipt, root=root)
    return {**receipt, "receipt_path": str(output)}


def prepare(plan_path: Path, work: Path) -> dict:
    return _execute(plan_path, work, "prepare", ("prepare",))


def run_plan(
    plan_path: Path, work: Path, stages: tuple[str, ...] | None = None
) -> dict:
    return _execute(plan_path, work, "run", stages or STAGES)


def verify_receipt(path: Path) -> dict:
    from release import preflight_runner as runner

    receipt = read_document(path)
    if set(receipt) != RECEIPT_KEYS or receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise PreflightError(
            "Unsupported local receipt fields/schema; no hosted admission"
        )
    _check_seal(receipt, "receipt_hash")
    if (
        not isinstance(receipt["plan"], dict)
        or not isinstance(receipt["work"], str)
        or not isinstance(receipt["owner"], dict)
        or not isinstance(receipt["attempts"], list)
        or any(not isinstance(row, dict) for row in receipt["attempts"])
        or not isinstance(receipt["requested_stages"], list)
        or not receipt["requested_stages"]
        or any(
            not isinstance(stage, str) or stage not in (*STAGES, "prepare")
            for stage in receipt["requested_stages"]
        )
        or len(set(receipt["requested_stages"])) != len(receipt["requested_stages"])
        or not isinstance(receipt["pending"], list)
    ):
        raise PreflightError("Invalid nested local receipt fields")
    plan = receipt["plan"]
    root = _safe(Path(plan["root"]))
    validate_plan(plan, root)
    work = _destination(root, Path(receipt["work"]))
    if receipt["owner"] != _owner(root):
        raise PreflightError("Receipt owner differs")
    runner.validate_owned_work(work, receipt["owner"])
    if receipt["operation"] not in {"prepare", "run"} or not isinstance(
        receipt["attempts"], list
    ):
        raise PreflightError("Invalid local operation/attempts")
    for attempt in receipt["attempts"]:
        if attempt.get("stage") == "readiness":
            if attempt != {
                "stage": "readiness",
                "status": "blocked",
                "reason": "Finish release preparation, commit and create a fresh eligible plan before full rehearsal",
            }:
                raise PreflightError("Invalid readiness refusal")
        else:
            if (
                attempt.get("candidate_sha") != plan["candidate_sha"]
                or attempt.get("version") != plan["readiness"]["version"]
            ):
                raise PreflightError("Attempt differs from candidate/version")
            runner.verify_attempt(
                attempt, repo=root, work=work, binding=receipt["owner"]
            )
    # Evidence is integrity only, never independent hosted execution provenance.
    evidence = receipt["evidence"]
    if not isinstance(evidence, dict) or len(evidence) > 50000:
        raise PreflightError("Invalid evidence inventory")
    for name, commitment in evidence.items():
        if (
            not isinstance(name, str)
            or "\\" in name
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or str(Path(name).as_posix()) != name
        ):
            raise PreflightError("Evidence requires canonical relative paths")
        raw = _read(
            work / name,
            LOCAL_ARCHIVE_EVIDENCE_LIMIT
            if name.endswith("/archive-budget/candidate-source.zip")
            else MAX_INPUT,
        )
        if commitment != {"sha256": _hash(raw), "bytes": len(raw)}:
            raise PreflightError(f"Changed evidence: {name}")
    if _manifest(work, receipt["attempts"]) != evidence:
        raise PreflightError("Evidence inventory changed or omitted required results")
    expected = _outcome(
        plan, receipt["operation"], receipt["requested_stages"], receipt["attempts"]
    )
    if expected != receipt["status"]:
        raise PreflightError("Receipt status does not follow mandatory local stages")
    expected_pending = [
        *plan["gates"],
        *[
            {
                "id": stage,
                "status": "pending",
                "release_pending": True,
                "reason": "Local mandatory stage not passed",
            }
            for stage in STAGES
            if not any(
                row.get("stage") == stage and row.get("status") == "passed"
                for row in receipt["attempts"]
            )
        ],
    ]
    if receipt["pending"] != expected_pending:
        raise PreflightError("Native/hosted or local pending gates omitted")
    return {
        "ok": True,
        "status": expected,
        "qualification": "Local integrity/applicability only; no hosted approval or promotion authority",
        "pending": receipt["pending"],
    }


def status(work: Path) -> dict:
    work = _safe(work)
    rows = []
    paths = sorted((work / "receipts").glob("*.json"))
    if len(paths) > 10000:
        raise PreflightError("Receipt history exceeds bound")
    for path in paths:
        value = read_document(path)
        if set(value) != RECEIPT_KEYS or not isinstance(value.get("plan"), dict):
            raise PreflightError("Malformed recorded receipt")
        _check_seal(value, "receipt_hash")
        rows.append(
            {
                "receipt": str(path),
                "status": value.get("status"),
                "plan_hash": value.get("plan", {}).get("plan_hash"),
                "qualification": "Recorded result; use verify for current applicability",
            }
        )
    return {"receipts": rows, "qualification": "No evidence executed or repaired"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    plan = actions.add_parser("plan")
    plan.add_argument("--root", type=Path, default=Path.cwd())
    plan.add_argument("--candidate-sha", required=True)
    plan.add_argument(
        "--review-file",
        type=Path,
        help="Ignored candidate-bound issue/SemVer review record; never inferred approval",
    )
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument(
        "--check-registry",
        action="store_true",
        help="Explicit read-only remote tag and registry inspection",
    )
    for action in ("prepare", "run"):
        command = actions.add_parser(action)
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--work", type=Path, required=True)
        if action == "run":
            command.add_argument("--stage", action="append", choices=STAGES)
    verify = actions.add_parser("verify")
    verify.add_argument("--receipt", type=Path, required=True)
    view = actions.add_parser("status")
    view.add_argument("--work", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "plan":
            value = create_plan(
                args.root, args.candidate_sha, args.check_registry, args.review_file
            )
            write_document(args.output, value, root=args.root)
        elif args.action == "prepare":
            value = prepare(args.plan, args.work)
        elif args.action == "run":
            value = run_plan(
                args.plan, args.work, tuple(args.stage) if args.stage else None
            )
        elif args.action == "verify":
            value = verify_receipt(args.receipt)
        else:
            value = status(args.work)
        # Plans and receipts can be large; CLI summaries are deliberately bounded.
        summary = {
            key: value[key]
            for key in (
                "schema_version",
                "plan_hash",
                "status",
                "readiness",
                "receipt_path",
                "ok",
                "qualification",
            )
            if key in value
        }
        if "receipts" in value:
            summary.update(
                receipts=value["receipts"][-20:],
                total=len(value["receipts"]),
                truncated=len(value["receipts"]) > 20,
            )
        print(json.dumps(summary, sort_keys=True))
        return 0 if value.get("status") not in {"blocked", "failed"} else 1
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        qualification.QualificationError,
        subprocess.SubprocessError,
        ImportError,
    ) as exc:
        print(
            json.dumps({"ok": False, "error": str(exc)[:2000]}, sort_keys=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
