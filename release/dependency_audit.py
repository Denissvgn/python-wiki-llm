"""Audit the installed qualification environment with bounded, evidenced retries.

Only this adapter uses pip-audit's private APIs; its contract is version pinned.
The controller and evidence validator remain standard-library-only.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time
import traceback
import uuid

PINNED_AUDIT = "2.10.1"
OWNED_PROJECT = "agent-wiki-cli"
MAX_BYTES = 64 * 1024 * 1024
DEADLINE_SECONDS = 540
BACKOFF_SECONDS = (5, 15)
TRANSIENT_CATEGORIES = {"http-429", "http-500", "http-502", "http-503", "http-504",
                        "connection-timeout", "connection-unavailable"}
SCHEMA = "agent-wiki-dependency-audit/v1"


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(path: Path) -> bytes:
    if path.is_symlink():
        raise ValueError("audit evidence must not be redirected")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("audit evidence exceeds its byte limit")
    return raw


def strict_json(raw: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate audit field: {key}")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError(f"invalid audit value: {value}")

    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)
    except RecursionError as exc:
        raise ValueError("audit evidence exceeds its nesting bound") from exc


def write(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def normalized_name(name: str) -> str:
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?", name):
        raise ValueError("invalid installed distribution name")
    return re.sub(r"[-_.]+", "-", name).lower()


def installed_packages() -> list[dict]:
    # Inspect everything visible to the isolated interpreter, including tools and
    # optional/example dependencies. No resolver, pip invocation or installation.
    from packaging.version import Version

    packages = {}
    for dist in metadata.distributions():
        name = normalized_name(dist.metadata["Name"])
        if name in packages:
            raise ValueError(f"duplicate installed distribution: {name}")
        packages[name] = {"name": name, "version": str(Version(dist.version)), "installed_version": dist.version}
    if len(packages) < 2:
        raise ValueError("installed dependency inventory is empty or incomplete")
    return [packages[name] for name in sorted(packages)]


def candidate_identity(candidate: Path) -> dict:
    # Reuse the installed release preflight's source/resource identity check.
    # This does not evaluate knowledge, prepare helpers or change health policy.
    from llm_wiki_cli.services.knowledge_maintenance import _installed, project_version

    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib  # type: ignore[reportMissingImports]
    project = tomllib.loads((candidate / "pyproject.toml").read_text("utf-8"))["project"]
    dist = metadata.distribution(OWNED_PROJECT)
    if (project["name"] != OWNED_PROJECT or normalized_name(dist.metadata["Name"]) != OWNED_PROJECT):
        raise ValueError("candidate distribution name does not match the owned project")
    direct_url = dist.read_text("direct_url.json")
    if direct_url is not None and strict_json(direct_url.encode()).get("dir_info", {}).get("editable") is True:
        raise ValueError("dependency audit requires a noneditable candidate installation")
    return _installed(candidate, project_version(candidate), allow_editable=False)


def capture_inventory(candidate: Path) -> dict:
    if metadata.version("pip-audit") != PINNED_AUDIT:
        raise ValueError("pip-audit version differs from the validated adapter contract")
    packages = installed_packages()
    identity = candidate_identity(candidate)
    owned = next((row for row in packages if row["name"] == OWNED_PROJECT), None)
    if owned is None or owned["installed_version"] != identity["version"] or identity["editable"]:
        raise ValueError("candidate exclusion does not match the installed inventory")
    return {
        "schema_version": SCHEMA, "scanner": {"name": "pip-audit", "version": PINNED_AUDIT},
        "environment": {"python": sys.executable, "prefix": sys.prefix,
                        "python_version": platform.python_version(), "platform": platform.platform()},
        "packages": packages,
        "exclusion": {"name": OWNED_PROJECT, "version": owned["version"],
                      "reason": "application-owned candidate; verified against source, not registry-audited",
                      "verification": identity},
    }


def scope(inventory: dict) -> dict[str, str]:
    if (not isinstance(inventory, dict) or inventory.get("schema_version") != SCHEMA
            or inventory.get("scanner") != {"name": "pip-audit", "version": PINNED_AUDIT}):
        raise ValueError("unsupported audit inventory or scanner")
    packages = inventory.get("packages")
    if not isinstance(packages, list) or len(packages) < 2:
        raise ValueError("incomplete audit inventory")
    result = {}
    for row in packages:
        if (not isinstance(row, dict) or set(row) != {"name", "version", "installed_version"}
                or normalized_name(row["name"]) != row["name"] or row["name"] in result
                or not isinstance(row["version"], str) or not row["version"]
                or not isinstance(row["installed_version"], str) or not row["installed_version"]):
            raise ValueError("invalid or duplicate audit inventory entry")
        result[row["name"]] = row["version"]
    if result.get("pip-audit") != PINNED_AUDIT:
        raise ValueError("installed scanner differs from the captured scanner identity")
    excluded = inventory.get("exclusion", {})
    if not isinstance(excluded, dict) or not isinstance(excluded.get("verification"), dict):
        raise ValueError("invalid candidate exclusion")
    verification = excluded.get("verification", {})
    owned = next((row for row in packages if row["name"] == OWNED_PROJECT), {})
    if (excluded.get("name") != OWNED_PROJECT or not result.get(OWNED_PROJECT)
            or excluded.get("version") != result[OWNED_PROJECT] or verification.get("editable") is not False
            or verification.get("version") != owned.get("installed_version")
            or not isinstance(verification.get("implementation_hash"), str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", verification["implementation_hash"])):
        raise ValueError("invalid candidate exclusion identity")
    del result[OWNED_PROJECT]
    return result


def validate_report(raw: bytes, inventory: dict) -> int:
    """Require exact third-party coverage; skipped dependencies are not a pass."""
    data = strict_json(raw)
    if (not isinstance(data, dict) or set(data) != {"dependencies", "fixes"}
            or data["fixes"] != [] or not isinstance(data["dependencies"], list)):
        raise ValueError("malformed dependency audit report")
    expected, observed, findings = scope(inventory), {}, 0
    for row in data["dependencies"]:
        if not isinstance(row, dict):
            raise ValueError("malformed dependency audit entry")
        if "skip_reason" in row:
            raise ValueError(f"unaudited third-party dependency: {row.get('name')}: {row['skip_reason']}")
        if (set(row) != {"name", "version", "vulns"} or not isinstance(row["name"], str)
                or row["name"] in observed or expected.get(row["name"]) != row["version"]
                or not isinstance(row["vulns"], list)):
            raise ValueError("dependency audit entry differs from the captured inventory")
        for vuln in row["vulns"]:
            if (not isinstance(vuln, dict) or set(vuln) != {"id", "fix_versions", "aliases", "description"}
                    or not isinstance(vuln["id"], str) or not vuln["id"]
                    or not isinstance(vuln["description"], str)
                    or any(not isinstance(vuln[k], list) or any(not isinstance(v, str) for v in vuln[k])
                           for k in ("fix_versions", "aliases"))):
                raise ValueError("malformed vulnerability finding")
        observed[row["name"]] = row["version"]
        findings += len(row["vulns"])
    if observed != expected:
        raise ValueError("dependency audit has incomplete inventory coverage")
    return findings


def classify_exception(exc: Exception, exceptions) -> dict:
    chain, current = [], exc
    while current is not None and id(current) not in {id(e) for e in chain}:
        chain.append(current)
        current = current.__cause__ or current.__context__
    result = {"category": "permanent-error", "retryable": False, "retry_after": 0}
    if any(isinstance(e, exceptions.SSLError) for e in chain):
        return {**result, "category": "certificate-error"}
    if any(isinstance(e, exceptions.ProxyError) for e in chain):
        return {**result, "category": "proxy-error"}
    for error in chain:
        if isinstance(error, exceptions.HTTPError) and error.response is not None:
            status = error.response.status_code
            result.update(category=f"http-{status}", retryable=status in {429, 500, 502, 503, 504})
            if status == 429:
                value = error.response.headers.get("Retry-After", "0")
                try:
                    seconds = int(value) if value.isdigit() else (
                        parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds()
                    result["retry_after"] = min(60, max(0, seconds))
                except (TypeError, ValueError, OverflowError):
                    pass
            return result
        if isinstance(error, (exceptions.Timeout, exceptions.ConnectionError)):
            return {**result, "category": "connection-timeout" if isinstance(error, exceptions.Timeout)
                    else "connection-unavailable", "retryable": True}
    return result


def worker(inventory_path: Path, output: Path) -> int:
    """One isolated, read-only attempt using the pinned scanner implementation."""
    report_path = output / "report.json"
    report_path.unlink(missing_ok=True)
    outcome = {"schema_version": SCHEMA, "inventory_sha256": digest(read(inventory_path)),
               "scanner": PINNED_AUDIT, "category": "permanent-error", "retryable": False,
               "retry_after": 0, "error": None, "report_sha256": None, "findings_seen": 0}
    results = {}
    formatter = None
    service = None
    cache = None
    try:
        if metadata.version("pip-audit") != PINNED_AUDIT:
            raise ValueError("pip-audit version differs from the validated adapter contract")
        from packaging.version import Version
        from pip_audit._audit import Auditor
        from pip_audit._dependency_source import DependencySource
        from pip_audit._format.json import JsonFormat
        from pip_audit._service import ResolvedDependency
        from pip_audit._service.pypi import PyPIService

        dependencies = scope(strict_json(read(inventory_path)))

        class CapturedSource(DependencySource):
            def collect(self):
                for name, version in dependencies.items():
                    yield ResolvedDependency(name=name, version=Version(version))

            def fix(self, fix_version):
                raise RuntimeError("release dependency audits are read-only")

        formatter = JsonFormat(output_desc=True, output_aliases=True)
        # Fresh cache per attempt: a previous response cannot qualify a new audit.
        cache = tempfile.TemporaryDirectory(prefix="llm-wiki-audit-")
        service = PyPIService(cache_dir=Path(cache.name), timeout=15)
        for dependency, vulnerabilities in Auditor(service).audit(CapturedSource()):
            results[dependency] = vulnerabilities
            outcome["findings_seen"] += len(vulnerabilities)
        outcome["category"] = "completed"
    except Exception as exc:
        traceback.print_exc()
        outcome["error"] = f"{type(exc).__name__}: {exc}"
        try:
            from requests import exceptions
            outcome.update(classify_exception(exc, exceptions))
        except ImportError:
            pass
        if outcome["findings_seen"]:
            outcome["retryable"] = False
    finally:
        if service is not None:
            service.session.close()
        if cache is not None:
            cache.cleanup()
        if formatter is not None:
            report_path.write_text(formatter.format(results, []) + "\n", encoding="utf-8")
            outcome["report_sha256"] = digest(read(report_path))
        write(output / "outcome.json", outcome)
    return 0 if outcome["category"] == "completed" else 1


def run(candidate: Path, evidence: Path, run_id: str, command: list[str]) -> dict:
    began = time.monotonic()
    evidence.mkdir(parents=True, exist_ok=True)
    final_report = evidence / "pip-audit.json"
    final_report.unlink(missing_ok=True)
    execution_path = evidence / "pip-audit-execution.json"
    execution_path.unlink(missing_ok=True)
    execution = {"schema_version": SCHEMA, "run_id": run_id, "command": command,
                 "status": "incomplete", "error": None, "inventory_sha256": None,
                 "scanner": PINNED_AUDIT, "attempts": [], "report_sha256": None}
    directory = evidence / "pip-audit-attempts" / run_id
    try:
        if not re.fullmatch(r"[0-9a-f]{32}", run_id):
            raise ValueError("invalid audit execution identity")
        directory.mkdir(parents=True, exist_ok=False)
        inventory = capture_inventory(candidate)
        scope(inventory)
        inventory_path = directory / "inventory.json"
        write(inventory_path, inventory)
        inventory_hash = digest(read(inventory_path))
        execution["inventory_sha256"] = inventory_hash
        for number in range(1, 4):
            output = directory / f"attempt-{number}"
            output.mkdir()
            worker_command = [sys.executable, "-I", str(Path(__file__).resolve()), "--worker",
                              "--inventory", str(inventory_path), "--evidence", str(output)]
            attempt = {"number": number, "command": worker_command, "inventory_sha256": inventory_hash,
                       "scanner": PINNED_AUDIT, "started_at": datetime.now(timezone.utc).isoformat(),
                       "elapsed_seconds": 0, "returncode": None, "category": "incomplete",
                       "retryable": False, "retry_after": 0, "error": None, "findings_seen": 0, "files": {}}
            started = time.monotonic()
            try:
                remaining = DEADLINE_SECONDS - (started - began)
                if remaining <= 0:
                    raise TimeoutError("dependency audit deadline exhausted")
                with (output / "output.log").open("wb") as stream:
                    process = subprocess.run(worker_command, stdin=subprocess.DEVNULL, stdout=stream,
                                             stderr=subprocess.STDOUT, timeout=remaining, check=False)
                attempt["returncode"] = process.returncode
                outcome = strict_json(read(output / "outcome.json"))
                if (not isinstance(outcome, dict) or outcome.get("schema_version") != SCHEMA
                        or outcome.get("inventory_sha256") != inventory_hash or outcome.get("scanner") != PINNED_AUDIT
                        or type(outcome.get("retryable")) is not bool
                        or type(outcome.get("retry_after")) not in (int, float)
                        or type(outcome.get("findings_seen")) is not int or outcome["findings_seen"] < 0
                        or not isinstance(outcome.get("category"), str)
                        or outcome.get("error") is not None and not isinstance(outcome["error"], str)
                        or outcome.get("retryable") and outcome.get("category") not in TRANSIENT_CATEGORIES
                        or not 0 <= outcome["retry_after"] <= 60
                        or outcome.get("report_sha256") != digest(read(output / "report.json"))):
                    raise ValueError("missing, stale or mismatched audit attempt evidence")
                for key in ("category", "retryable", "retry_after", "error", "findings_seen"):
                    attempt[key] = outcome[key]
                if attempt["findings_seen"]:
                    attempt["retryable"] = False
                if process.returncode == 0 and outcome["category"] == "completed" and outcome["error"] is None:
                    raw = read(output / "report.json")
                    findings = validate_report(raw, inventory)
                    if capture_inventory(candidate) != inventory:
                        raise ValueError("installed audit inventory or candidate changed during execution")
                    attempt.update(category="vulnerabilities" if findings else "passed", retryable=False)
                    final_report.write_bytes(raw)
                    execution["report_sha256"] = digest(raw)
                    execution["status"] = attempt["category"]
                    execution["error"] = f"dependency audit found {findings} vulnerabilities" if findings else None
                elif process.returncode != 1 or outcome["category"] == "completed":
                    raise ValueError("audit worker exit status disagrees with its evidence")
            except Exception as exc:
                attempt.update(category="incomplete", retryable=False, error=f"{type(exc).__name__}: {exc}")
            finally:
                attempt["elapsed_seconds"] = time.monotonic() - started
                attempt["files"] = {p.name: digest(read(p)) for p in output.iterdir() if p.is_file()}
                execution["attempts"].append(attempt)
                write(execution_path, execution)
            print(f"Dependency audit attempt {number}: {attempt['category']}: {attempt['error'] or ''}", flush=True)
            if execution["status"] != "incomplete":
                break
            execution["error"] = f"dependency audit unavailable/incomplete ({attempt['category']}): {attempt['error']}"
            if attempt["findings_seen"]:
                execution["error"] = f"dependency audit found {attempt['findings_seen']} vulnerabilities; " + execution["error"]
            write(execution_path, execution)
            if not attempt["retryable"] or number == 3:
                break
            delay = max(BACKOFF_SECONDS[number - 1], attempt["retry_after"])
            if time.monotonic() - began + delay >= DEADLINE_SECONDS:
                break
            time.sleep(delay)
    except Exception as exc:
        execution["status"] = "incomplete"
        execution["error"] = f"dependency audit unavailable/incomplete: {type(exc).__name__}: {exc}"
        traceback.print_exc()
    execution["elapsed_seconds"] = time.monotonic() - began
    write(execution_path, execution)
    return execution


def result_error(evidence: Path, run_id: str, command: list[str], returncode: int | None) -> str | None:
    """Bind the static gate to this execution, its inventory and original attempts."""
    try:
        record = strict_json(read(evidence / "pip-audit-execution.json"))
        if (not isinstance(record, dict) or record.get("schema_version") != SCHEMA
                or record.get("run_id") != run_id or record.get("command") != command
                or record.get("scanner") != PINNED_AUDIT):
            raise ValueError("missing, stale or mismatched dependency audit execution")
        if record.get("status") != "passed":
            return record.get("error") or "dependency audit unavailable/incomplete"
        if returncode != 0 or record.get("error") is not None:
            raise ValueError("dependency audit did not exit successfully")
        directory = evidence / "pip-audit-attempts" / run_id
        inventory_raw = read(directory / "inventory.json")
        if digest(inventory_raw) != record["inventory_sha256"]:
            raise ValueError("audit inventory commitment mismatch")
        attempts = record.get("attempts")
        if not isinstance(attempts, list) or not 1 <= len(attempts) <= 3 or attempts[-1]["category"] != "passed":
            raise ValueError("missing successful audit attempt")
        for number, attempt in enumerate(attempts, 1):
            if (attempt["number"] != number or attempt["inventory_sha256"] != record["inventory_sha256"]
                    or attempt["scanner"] != PINNED_AUDIT or not {"report.json", "outcome.json", "output.log"} <= attempt["files"].keys()):
                raise ValueError("invalid audit attempt commitments")
            for name, checksum in attempt["files"].items():
                if name not in {"report.json", "outcome.json", "output.log"} or digest(read(directory / f"attempt-{number}" / name)) != checksum:
                    raise ValueError("changed audit attempt evidence")
            outcome = strict_json(read(directory / f"attempt-{number}" / "outcome.json"))
            if (outcome.get("inventory_sha256") != record["inventory_sha256"] or outcome.get("scanner") != PINNED_AUDIT
                    or outcome.get("schema_version") != SCHEMA
                    or outcome.get("report_sha256") != attempt["files"]["report.json"]):
                raise ValueError("mismatched audit worker outcome")
            if number == len(attempts):
                if (attempt["returncode"] != 0 or outcome.get("category") != "completed"
                        or outcome.get("error") is not None or outcome.get("findings_seen") != 0):
                    raise ValueError("final audit worker did not complete cleanly")
            elif (attempt["returncode"] != 1 or outcome.get("category") not in TRANSIENT_CATEGORIES
                  or outcome.get("retryable") is not True or outcome.get("findings_seen") != 0):
                raise ValueError("audit retried a nontransient or vulnerability failure")
        raw = read(evidence / "pip-audit.json")
        if (digest(raw) != record["report_sha256"] or digest(raw) != attempts[-1]["files"]["report.json"]
                or validate_report(raw, strict_json(inventory_raw))):
            raise ValueError("audit report is mismatched or contains vulnerabilities")
        return None
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        return f"dependency audit unavailable/incomplete: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--inventory", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if args.inventory is None:
            parser.error("worker requires its captured inventory")
        return worker(args.inventory, args.evidence)
    if args.candidate is None:
        parser.error("audit requires the intended candidate source")
    result = run(args.candidate.resolve(), args.evidence.absolute(), args.run_id or uuid.uuid4().hex,
                 [sys.executable, "-I", str(Path(__file__).resolve()), *sys.argv[1:]])
    if result["error"]:
        print(result["error"], file=sys.stderr)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
