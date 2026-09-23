"""Run all independent static qualification checks and retain their evidence."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
from importlib.metadata import version
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import time
import uuid

PINNED_BANDIT = "1.9.4"
BANDIT_RANKS = ("UNDEFINED", "LOW", "MEDIUM", "HIGH")
MAX_REPORT_BYTES = 64 * 1024 * 1024
METRIC_KEYS = {"loc", "nosec", "skipped_tests"} | {
    f"{kind}.{rank}" for kind in ("SEVERITY", "CONFIDENCE") for rank in BANDIT_RANKS
}
ISSUE_KEYS = {"code", "filename", "issue_confidence", "issue_severity", "issue_cwe", "issue_text",
              "line_number", "line_range", "col_offset", "end_col_offset", "more_info", "test_id", "test_name"}


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _bounded_read(path: Path) -> bytes:
    if path.is_symlink():
        raise ValueError("scanner evidence must not be a symbolic link")
    with path.open("rb") as stream:
        raw = stream.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("scanner evidence exceeds its byte limit")
    return raw


def _strict_json(raw: bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate report field: {key}")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"non-finite report value: {value}")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid)
    except RecursionError as exc:
        raise ValueError("scanner report exceeds its nesting bound") from exc


def _report_path(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("invalid scanner filename")
    value = value.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or path.as_posix() != value or ":" in value:
        raise ValueError("scanner filename must be a relative source path")
    return value


def source_manifest(root: Path, paths: tuple[str, ...]) -> dict:
    if not paths:
        raise ValueError("Bandit requires an explicit source scope")
    files = {}
    for relative in paths:
        path = root / _report_path(relative)
        if path.is_symlink() or not path.exists():
            raise ValueError("scanner source scope is missing or redirected")
        selected = [path] if path.is_file() else sorted(path.rglob("*.py"))
        for file in selected:
            if "__pycache__" in file.parts:
                continue
            if file.is_symlink():
                raise ValueError("scanner source files must not be redirected")
            files[file.relative_to(root).as_posix()] = _sha256(_bounded_read(file))
    if not files:
        raise ValueError("scanner source scope is empty")
    return {"paths": list(paths), "files": files, "sha256": _sha256(_canonical(files))}


def validate_bandit_report(raw: bytes) -> dict:
    """Validate the complete, unfiltered JSON schema emitted by pinned Bandit."""
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("Bandit report exceeds its byte limit")
    data = _strict_json(raw)
    if not isinstance(data, dict) or set(data) != {"errors", "generated_at", "metrics", "results"}:
        raise ValueError("incomplete or unsupported Bandit report")
    if data["errors"] != []:
        raise ValueError("Bandit report records analysis errors")
    if not isinstance(data["generated_at"], str):
        raise ValueError("invalid Bandit generation timestamp")
    datetime.strptime(data["generated_at"], "%Y-%m-%dT%H:%M:%SZ")
    metrics, findings = data["metrics"], data["results"]
    if not isinstance(metrics, dict) or not isinstance(findings, list) or "_totals" not in metrics:
        raise ValueError("missing Bandit inventory")
    by_file = {}
    for name, row in metrics.items():
        if (not isinstance(row, dict) or set(row) != METRIC_KEYS
                or any(type(count) is not int or count < 0 for count in row.values())):
            raise ValueError("invalid Bandit metrics")
        if name != "_totals":
            name = _report_path(name)
            if name in by_file:
                raise ValueError("duplicate normalized Bandit filename")
            by_file[name] = row
    totals = metrics["_totals"]
    if not by_file or totals["loc"] <= 0 or any(totals[key] != sum(row[key] for row in by_file.values()) for key in METRIC_KEYS):
        raise ValueError("Bandit report has incomplete aggregate metrics")
    counts = {name: {key: 0 for key in METRIC_KEYS if "." in key} for name in by_file}
    for row in findings:
        if not isinstance(row, dict) or set(row) != ISSUE_KEYS:
            raise ValueError("incomplete or unsupported Bandit finding")
        name = _report_path(row["filename"])
        if name not in by_file:
            raise ValueError("finding has no scanned-file metrics")
        if row["issue_severity"] not in BANDIT_RANKS or row["issue_confidence"] not in BANDIT_RANKS:
            raise ValueError("unknown Bandit ranking")
        if (not all(isinstance(row[k], str) for k in ("code", "issue_text", "more_info", "test_id", "test_name"))
                or not re.fullmatch(r"B\d{3}", row["test_id"]) or not row["test_name"]
                or type(row["line_number"]) is not int or row["line_number"] < 1
                or not isinstance(row["line_range"], list) or not row["line_range"]
                or any(type(line) is not int or line < 1 for line in row["line_range"])
                or any(row[k] is not None and (type(row[k]) is not int or row[k] < -1) for k in ("col_offset", "end_col_offset"))):
            raise ValueError("invalid Bandit finding location or identity")
        cwe = row["issue_cwe"]
        if (not isinstance(cwe, dict) or cwe != {} and (set(cwe) != {"id", "link"}
                or type(cwe["id"]) is not int or cwe["id"] < 0 or not isinstance(cwe["link"], str))):
            raise ValueError("invalid Bandit CWE")
        counts[name]["SEVERITY." + row["issue_severity"]] += 1
        counts[name]["CONFIDENCE." + row["issue_confidence"]] += 1
    if any(by_file[name][key] != count for name, row in counts.items() for key, count in row.items()):
        raise ValueError("Bandit findings disagree with unfiltered metrics")
    return data


def evaluate_bandit(raw: bytes, log: bytes, observation: dict, *, run_id: str,
                    command: tuple[str, ...], source: dict) -> dict:
    """Derive HIGH/HIGH policy only from this runner's completed scan receipt."""
    keys = {"schema_version", "run_id", "command", "tool", "error", "returncode", "source",
            "report_sha256", "report_bytes", "log_sha256", "started_at", "finished_at", "elapsed_ns"}
    if (set(observation) != keys or not re.fullmatch(r"[0-9a-f]{32}", run_id)
            or observation.get("schema_version") != "agent-wiki-bandit-execution/v1"
            or observation.get("run_id") != run_id or observation.get("command") != list(command)
            or observation.get("tool") != {"name": "bandit", "version": PINNED_BANDIT, "python": sys.executable}
            or observation.get("error") is not None or type(observation.get("returncode")) is not int
            or observation["returncode"] not in (0, 1) or observation.get("source") != source
            or type(observation.get("elapsed_ns")) is not int or observation["elapsed_ns"] < 0
            or observation.get("report_sha256") != _sha256(raw) or type(observation.get("report_bytes")) is not int
            or observation.get("report_bytes") != len(raw)
            or observation.get("log_sha256") != _sha256(log)):
        raise ValueError("Bandit scan observation is absent, failed, stale, or mismatched")
    for field in ("started_at", "finished_at"):
        if not isinstance(observation[field], str) or datetime.fromisoformat(observation[field].replace("Z", "+00:00")).tzinfo is None:
            raise ValueError("invalid scan observation timestamp")
    # Plugin exceptions can produce exit 0 and an empty report.errors array.
    # The unmodified pinned CLI logs these failures rather than propagating them.
    if re.search(rb"(?m)^(?:\[[^\]]+\]\s+(?:ERROR|CRITICAL)\s|Bandit internal error running:)", log):
        raise ValueError("Bandit scanner log records an analysis failure")
    data = validate_bandit_report(raw)
    if {_report_path(name) for name in data["metrics"] if name != "_totals"} != set(source["files"]):
        raise ValueError("Bandit did not analyze the complete source scope")
    if observation["returncode"] != int(bool(data["results"])):
        raise ValueError("Bandit exit status disagrees with the complete report")
    findings = sorted(data["results"], key=_canonical)
    blocking = [row for row in findings if row["issue_severity"] == row["issue_confidence"] == "HIGH"]
    return {
        "schema_version": "agent-wiki-bandit-decision/v1", "run_id": run_id,
        "report_sha256": _sha256(raw), "log_sha256": _sha256(log),
        "execution_sha256": _sha256(_canonical(observation)), "source_sha256": source["sha256"],
        "tool": observation["tool"],
        "decision": {"threshold": {"severity": "HIGH", "confidence": "HIGH", "operator": "and"},
                     "passed": not blocking, "reason": "blocking-findings" if blocking else "no-blocking-findings",
                     "findings": len(findings), "blocking_findings": len(blocking),
                     "findings_sha256": _sha256(_canonical(findings)),
                     "blocking": [{key: row[key] for key in ("filename", "line_number", "test_id", "issue_severity", "issue_confidence")}
                                  for row in blocking]},
    }


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    accepted_codes: tuple[int, ...] = (0,)
    report: Path | None = None
    report_kind: str | None = None
    source_paths: tuple[str, ...] = ()
    derived_from: str | None = None


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _report_error(check: Check) -> str | None:
    if check.report is None:
        return None
    try:
        data = json.loads(check.report.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"Required report is unreadable: {exc}"
    if check.report_kind == "bandit":
        try:
            validate_bandit_report(_bounded_read(check.report))
        except (OSError, ValueError) as exc:
            return str(exc)
        valid = True
    elif check.report_kind == "pip-audit":
        valid = (
            isinstance(data, dict)
            and isinstance(data.get("dependencies"), list)
            and bool(data["dependencies"])
        )
    else:
        valid = False
    return None if valid else "Required report is incomplete or records analysis errors"


def default_checks(root: Path, evidence: Path) -> list[Check]:
    def module(name: str, *args: str) -> tuple[str, ...]:
        return (sys.executable, "-m", name, *args)

    bandit_report = evidence / "bandit-full.json"
    audit_report = evidence / "pip-audit.json"
    return [
        Check("pip-check", module("pip", "check")),
        Check("pyright", module("pyright", "--pythonpath", sys.executable)),
        Check(
            "ruff",
            module(
                "ruff",
                "check",
                "src",
                "tests",
                "examples",
                "integrations/github-action/render_summary.py",
            ),
        ),
        Check(
            "bandit-full",
            (sys.executable, "-I", "-m", "bandit",
                "-r",
                "src/llm_wiki_cli",
                "-f",
                "json",
                "-o",
                str(bandit_report),
            ),
            accepted_codes=(0, 1),
            report=bandit_report,
            report_kind="bandit",
            source_paths=("src/llm_wiki_cli",),
        ),
        Check(
            "bandit-blocking",
            (),
            report=evidence / "bandit-blocking.json",
            report_kind="bandit-decision",
            derived_from="bandit-full",
        ),
        Check(
            "pip-audit",
            module(
                "pip_audit",
                "--local",
                "--format",
                "json",
                "--output",
                str(audit_report),
            ),
            report=audit_report,
            report_kind="pip-audit",
        ),
        Check(
            "actionlint",
            (
                "actionlint",
                *(
                    str(path)
                    for path in sorted((root / ".github/workflows").glob("*.yml"))
                ),
            ),
        ),
    ]


def run_checks(checks: list[Check], root: Path, evidence: Path) -> dict:
    root, evidence = root.resolve(), evidence.absolute()
    evidence.mkdir(parents=True, exist_ok=True)
    if len({check.name for check in checks}) != len(checks) or any(
        not re.fullmatch(r"[a-z0-9][a-z0-9-]*", check.name) for check in checks
    ):
        raise ValueError("check names must be safe and unique")
    run_id = uuid.uuid4().hex
    results = []
    observations = {}
    definitions = {check.name: check for check in checks}
    _write_json(evidence / "checks.json", {"passed": False, "complete": False, "run_id": run_id, "checks": []})
    for check in checks:
        began = time.perf_counter_ns()
        error = None
        returncode = None
        log = evidence / f"{check.name}.log"
        observation: dict | None = None
        scan_started = None
        try:
            log.write_bytes(b"")
            if check.report is not None:
                check.report.unlink(missing_ok=True)
            if check.derived_from is not None:
                if check.command or check.report_kind != "bandit-decision" or check.report is None:
                    raise ValueError("invalid derived Bandit check")
                producer = definitions.get(check.derived_from)
                if (producer is None or producer.report_kind != "bandit" or producer.report is None
                        or producer.name not in observations or not any(
                            r["name"] == producer.name and r["passed"] for r in results)):
                    raise ValueError("current full Bandit producer did not complete successfully")
                retained = _strict_json(_bounded_read(evidence / f"{producer.name}-execution.json"))
                if retained != observations[producer.name]:
                    raise ValueError("retained Bandit execution record changed")
                decision = evaluate_bandit(
                    _bounded_read(producer.report), _bounded_read(evidence / f"{producer.name}.log"),
                    observations[producer.name], run_id=run_id, command=producer.command,
                    source=source_manifest(root, producer.source_paths),
                )
                _write_json(check.report, decision)
                log.write_text(json.dumps(decision["decision"], sort_keys=True) + "\n", encoding="utf-8")
                returncode = 0 if decision["decision"]["passed"] else 1
            else:
                if check.report_kind == "bandit":
                    (evidence / f"{check.name}-execution.json").unlink(missing_ok=True)
                    observation = {"schema_version": "agent-wiki-bandit-execution/v1", "run_id": run_id,
                        "command": list(check.command), "tool": {"name": "bandit", "version": None, "python": sys.executable},
                        "error": None, "returncode": None, "source": None, "report_sha256": None,
                        "report_bytes": None, "log_sha256": None, "started_at": None, "finished_at": None, "elapsed_ns": 0}
                    observation["tool"]["version"] = version("bandit")
                    if observation["tool"]["version"] != PINNED_BANDIT:
                        raise ValueError("Bandit version differs from the validated report contract")
                    observation["source"] = source_manifest(root, check.source_paths)
                    observation["started_at"] = datetime.now(timezone.utc).isoformat()
                    scan_started = time.perf_counter_ns()
                with log.open("wb") as stream:
                    result = subprocess.run(
                        check.command, cwd=root, stdin=subprocess.DEVNULL,
                        stdout=stream, stderr=subprocess.STDOUT, check=False, timeout=600,
                    )
                returncode = result.returncode
                if observation is not None:
                    assert scan_started is not None
                    observation["finished_at"] = datetime.now(timezone.utc).isoformat()
                    observation["elapsed_ns"] = time.perf_counter_ns() - scan_started
                    observation["returncode"] = returncode
                    if check.report is None:
                        raise ValueError("Bandit report path is missing")
                    raw, log_raw = _bounded_read(check.report), _bounded_read(log)
                    observation.update(report_sha256=_sha256(raw), report_bytes=len(raw), log_sha256=_sha256(log_raw))
                    evaluate_bandit(raw, log_raw, observation, run_id=run_id, command=check.command,
                                    source=source_manifest(root, check.source_paths))
                else:
                    error = _report_error(check)
        except (OSError, ValueError, ImportError, subprocess.TimeoutExpired) as exc:
            error = str(exc)
            try:
                if log.exists():
                    with log.open("ab") as stream:
                        stream.write(("\nCheck failed: " + error + "\n").encode("utf-8"))
            except OSError as log_error:
                error += f"; diagnostic log unavailable: {log_error}"
            if check.derived_from is not None and check.report is not None:
                try:
                    _write_json(check.report, {"schema_version": "agent-wiki-bandit-decision/v1", "run_id": run_id,
                                              "decision": {"passed": False, "reason": "invalid-scan-evidence"}, "error": error})
                except OSError as report_error:
                    error += f"; decision report unavailable: {report_error}"
        if observation is not None:
            observation["error"] = error
            observation["returncode"] = returncode
            if observation["finished_at"] is None:
                observation["finished_at"] = datetime.now(timezone.utc).isoformat()
                observation["elapsed_ns"] = time.perf_counter_ns() - scan_started if scan_started is not None else 0
            try:
                observation["log_sha256"] = _sha256(_bounded_read(log))
            except (OSError, ValueError):
                observation["log_sha256"] = None
            observations[check.name] = observation
            try:
                _write_json(evidence / f"{check.name}-execution.json", observation)
            except OSError as record_error:
                error = f"{error + '; ' if error else ''}execution record unavailable: {record_error}"
                observation["error"] = error
        passed = returncode in check.accepted_codes and error is None
        results.append(
            {
                "name": check.name,
                "command": list(check.command),
                "returncode": returncode,
                "error": error,
                "passed": passed,
                "log": log.name,
                "execution_kind": "derived" if check.derived_from is not None else "command",
                "derived_from": check.derived_from,
                "elapsed_ns": time.perf_counter_ns() - began,
            }
        )
        _write_json(evidence / "checks.json", {"passed": False, "complete": False, "run_id": run_id, "checks": results})
        print(
            f"{check.name}: {'PASS' if passed else 'FAIL'} (exit {returncode})",
            flush=True,
        )
        if not passed:
            try:
                diagnostic = log.read_text(encoding="utf-8", errors="replace") if log.exists() else error
            except OSError:
                diagnostic = error
            print(diagnostic or error, flush=True)
    payload = {
        "passed": bool(results) and all(item["passed"] for item in results),
        "complete": True,
        "run_id": run_id,
        "checks": results,
    }
    _write_json(evidence / "checks.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence.absolute()
    evidence.mkdir(parents=True, exist_ok=True)
    environment = {"executable": sys.executable, "prefix": sys.prefix, "versions": {}}
    try:
        importlib.import_module("tokenizers")
        environment["versions"] = {
            name: version(name)
            for name in (
                "agent-wiki-cli",
                "tokenizers",
                "mcp",
                "pyright",
                "ruff",
                "bandit",
                "pip-audit",
            )
        }
    except (ImportError, ValueError) as exc:
        environment["error"] = str(exc)
        _write_json(evidence / "environment.json", environment)
        _write_json(
            evidence / "checks.json", {"passed": False, "checks": [], "error": str(exc)}
        )
        print(f"Qualification environment preflight failed: {exc}", file=sys.stderr)
        return 1
    _write_json(evidence / "environment.json", environment)
    return (
        0
        if run_checks(default_checks(Path.cwd(), evidence), Path.cwd(), evidence)[
            "passed"
        ]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
