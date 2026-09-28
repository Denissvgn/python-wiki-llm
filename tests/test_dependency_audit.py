"""Fail-closed audit scope, outage recovery and evidence binding contracts."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from release import dependency_audit as audit
from release import static_checks


RUN_ID = "a" * 32
COMMAND = [sys.executable, "-I", str(Path(audit.__file__).resolve())]


def inventory():
    return {
        "schema_version": audit.SCHEMA,
        "scanner": {"name": "pip-audit", "version": audit.PINNED_AUDIT},
        "packages": [
            {"name": name, "version": version, "installed_version": version}
            for name, version in ((audit.OWNED_PROJECT, "2.3.0"), ("pip-audit", audit.PINNED_AUDIT), ("runtime-extra", "1.0"))
        ],
        "exclusion": {"name": audit.OWNED_PROJECT, "version": "2.3.0", "verification": {
            "version": "2.3.0", "editable": False, "implementation_hash": "sha256:" + "b" * 64,
        }},
    }


def report():
    return {"dependencies": [{"name": name, "version": version, "vulns": []}
                             for name, version in audit.scope(inventory()).items()], "fixes": []}


def configure(monkeypatch, tmp_path, outcomes):
    """Simulate the worker process, retaining real controller files and bindings."""
    calls, sleeps = [], []
    monkeypatch.setattr(audit, "capture_inventory", lambda candidate: inventory())
    monkeypatch.setattr(audit, "time", SimpleNamespace(monotonic=audit.time.monotonic, sleep=sleeps.append))

    def worker(command, **kwargs):
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert 0 < kwargs["timeout"] <= audit.DEADLINE_SECONDS
        assert command[:2] == [sys.executable, "-I"] and "--worker" in command
        calls.append(command)
        action = outcomes[min(len(calls) - 1, len(outcomes) - 1)]
        if isinstance(action, Exception):
            raise action
        output = Path(command[command.index("--evidence") + 1])
        inventory_path = Path(command[command.index("--inventory") + 1])
        kwargs["stdout"].write(b"original scanner output\n")
        payload = action.get("report", report())
        if isinstance(payload, bytes):
            (output / "report.json").write_bytes(payload)
        elif payload is not None:
            audit.write(output / "report.json", payload)
        row = {"schema_version": audit.SCHEMA, "inventory_sha256": audit.digest(audit.read(inventory_path)),
               "scanner": audit.PINNED_AUDIT, "category": action.get("category", "completed"),
               "retryable": action.get("retryable", False), "retry_after": action.get("retry_after", 0),
               "error": action.get("error"), "report_sha256": audit.digest(audit.read(output / "report.json")) if payload is not None else None,
               "findings_seen": 0}
        row.update(action.get("overrides", {}))
        audit.write(output / "outcome.json", row)
        return SimpleNamespace(returncode=action.get("returncode", int(row["category"] != "completed")))

    monkeypatch.setattr(audit.subprocess, "run", worker)
    return tmp_path / "evidence", calls, sleeps


TRANSIENT = {"category": "http-503", "retryable": True, "error": "ServiceError: original outage"}


def test_transient_then_success_preserves_attempts_and_complete_scope(tmp_path, monkeypatch):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [TRANSIENT, {}])
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "passed" and result["error"] is None
    assert len(calls) == 2 and sleeps == [5]
    assert [a["category"] for a in result["attempts"]] == ["http-503", "passed"]
    assert result["attempts"][0]["error"] == TRANSIENT["error"]
    assert audit.result_error(evidence, RUN_ID, COMMAND, 0) is None
    assert json.loads((evidence / "pip-audit.json").read_text()) == report()
    assert audit.OWNED_PROJECT not in audit.scope(inventory())
    assert "runtime-extra" in audit.scope(inventory())


@pytest.mark.parametrize("transient", [TRANSIENT, {**TRANSIENT, "category": "connection-timeout"},
                                     {**TRANSIENT, "category": "http-429", "retry_after": 60}])
def test_exhausted_retries_stay_incomplete(tmp_path, monkeypatch, transient):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [transient])
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "incomplete" and len(calls) == 3
    assert sleeps == ([60, 60] if transient["category"] == "http-429" else [5, 15])
    assert not (evidence / "pip-audit.json").exists()
    assert "unavailable/incomplete" in (audit.result_error(evidence, RUN_ID, COMMAND, 1) or "")
    assert all((evidence / "pip-audit-attempts" / RUN_ID / f"attempt-{i}" / "output.log").exists() for i in (1, 2, 3))


@pytest.mark.parametrize("action", [
    {"category": "http-401", "error": "auth"}, {"category": "certificate-error", "error": "TLS"},
    {"category": "permanent-error", "error": "unknown"}, {"returncode": 1},
    {"report": b"invalid"}, {"report": b'{"dependencies":[],"dependencies":[],"fixes":[]}'},
    {"report": b'{"dependencies":NaN,"fixes":[]}'}, {"report": None},
    {"report": {"dependencies": [], "fixes": []}}, {"overrides": {"inventory_sha256": "stale"}},
    {"overrides": {"scanner": "future"}}, {"overrides": {"retry_after": 999}},
    OSError("launch error"), subprocess.TimeoutExpired(COMMAND, 540),
])
def test_permanent_incomplete_or_missing_evidence_is_not_retried(tmp_path, monkeypatch, action):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [action])
    evidence.mkdir()
    audit.write(evidence / "pip-audit.json", report())
    audit.write(evidence / "pip-audit-execution.json", {"status": "passed"})
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "incomplete" and len(calls) == 1 and not sleeps
    assert not (evidence / "pip-audit.json").exists()
    assert audit.result_error(evidence, RUN_ID, COMMAND, 1)


def test_vulnerabilities_block_without_retry_and_retain_full_report(tmp_path, monkeypatch):
    value = report()
    value["dependencies"][0]["vulns"] = [{"id": "GHSA-example", "aliases": [], "fix_versions": ["99"], "description": "finding"}]
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [{"report": value}])
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "vulnerabilities" and len(calls) == 1 and not sleeps
    assert "found 1 vulnerabilities" in (audit.result_error(evidence, RUN_ID, COMMAND, 1) or "")
    assert json.loads((evidence / "pip-audit.json").read_text()) == value


def test_observed_finding_before_outage_is_not_retried(tmp_path, monkeypatch):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [{**TRANSIENT, "overrides": {"findings_seen": 1}}])
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "incomplete" and len(calls) == 1 and not sleeps
    assert "found 1 vulnerabilities" in result["error"]


@pytest.mark.parametrize("mutation", ["partial", "duplicate", "wrong-version", "extra", "skip", "malformed-vuln"])
def test_coverage_validation_fails_closed(mutation):
    value = report()
    if mutation == "partial":
        value["dependencies"].pop()
    elif mutation == "duplicate":
        value["dependencies"].append(deepcopy(value["dependencies"][0]))
    elif mutation == "wrong-version":
        value["dependencies"][0]["version"] = "9"
    elif mutation == "extra":
        value["dependencies"].append({"name": audit.OWNED_PROJECT, "version": "2.3.0", "vulns": []})
    elif mutation == "skip":
        value["dependencies"][0] = {"name": "pip-audit", "skip_reason": "404"}
    else:
        value["dependencies"][0]["vulns"] = [{"id": "unknown"}]
    with pytest.raises(ValueError):
        audit.validate_report(audit.canonical(value), inventory())


@pytest.mark.parametrize("mutation", ["run-id", "command", "inventory", "report", "output", "outcome", "returncode", "execution"])
def test_stale_or_changed_success_cannot_pass(tmp_path, monkeypatch, mutation):
    evidence, _, _ = configure(monkeypatch, tmp_path, [{}])
    audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    if mutation in {"inventory", "report", "output", "outcome"}:
        target = {"inventory": evidence / "pip-audit-attempts" / RUN_ID / "inventory.json",
                  "report": evidence / "pip-audit.json",
                  "output": evidence / "pip-audit-attempts" / RUN_ID / "attempt-1/output.log",
                  "outcome": evidence / "pip-audit-attempts" / RUN_ID / "attempt-1/outcome.json"}[mutation]
        target.write_bytes(target.read_bytes() + b"changed")
    elif mutation == "execution":
        (evidence / "pip-audit-execution.json").unlink()
    assert audit.result_error(evidence, "b" * 32 if mutation == "run-id" else RUN_ID,
                              [] if mutation == "command" else COMMAND, 1 if mutation == "returncode" else 0)


def test_environment_change_invalidates_completed_audit(tmp_path, monkeypatch):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [{}])
    captures = iter([inventory(), {**inventory(), "environment": "changed"}])
    monkeypatch.setattr(audit, "capture_inventory", lambda candidate: next(captures))
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "incomplete" and len(calls) == 1 and not sleeps
    assert "changed during execution" in result["error"]


@pytest.mark.parametrize("failure", ["report", "execution"])
def test_evidence_publication_failure_cannot_return_success(tmp_path, monkeypatch, failure):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [{}])
    if failure == "report":
        original_bytes = Path.write_bytes

        def fail_report(path, raw):
            if path == evidence / "pip-audit.json":
                raise OSError("cannot publish report")
            return original_bytes(path, raw)

        monkeypatch.setattr(Path, "write_bytes", fail_report)
    else:
        original_write = audit.write

        def fail_receipt(path, payload):
            if path == evidence / "pip-audit-execution.json" and payload["status"] == "passed":
                raise OSError("cannot publish execution")
            return original_write(path, payload)

        monkeypatch.setattr(audit, "write", fail_receipt)
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "incomplete" and len(calls) == 1 and not sleeps
    assert "cannot publish" in result["error"]
    assert audit.result_error(evidence, RUN_ID, COMMAND, 1)


def test_deadline_stops_before_backoff_and_does_not_relaunch(tmp_path, monkeypatch):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [TRANSIENT])
    ticks = iter([0, 0, 538, 539, 540])
    monkeypatch.setattr(audit.time, "monotonic", lambda: next(ticks))
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert result["status"] == "incomplete" and len(calls) == 1 and not sleeps
    assert result["elapsed_seconds"] == 540


def test_candidate_or_tool_mismatch_prevents_any_query(tmp_path, monkeypatch):
    evidence, calls, sleeps = configure(monkeypatch, tmp_path, [{}])

    def mismatch(candidate):
        raise ValueError("candidate installation mismatch")

    monkeypatch.setattr(audit, "capture_inventory", mismatch)
    result = audit.run(tmp_path, evidence, RUN_ID, COMMAND)
    assert not calls and not sleeps and result["status"] == "incomplete"
    assert "candidate installation mismatch" in (audit.result_error(evidence, RUN_ID, COMMAND, 1) or "")


def test_capture_uses_all_installed_packages_and_verifies_only_owned_exclusion(tmp_path, monkeypatch):
    monkeypatch.setattr(audit.metadata, "version", lambda name: audit.PINNED_AUDIT)
    monkeypatch.setattr(audit, "installed_packages", lambda: inventory()["packages"])
    monkeypatch.setattr(audit, "candidate_identity", lambda candidate: inventory()["exclusion"]["verification"])
    captured = audit.capture_inventory(tmp_path)
    assert captured["packages"] == inventory()["packages"]
    assert audit.scope(captured) == audit.scope(inventory())
    monkeypatch.setattr(audit.metadata, "version", lambda name: "unverified")
    with pytest.raises(ValueError, match="version differs"):
        audit.capture_inventory(tmp_path)


def test_installed_inventory_rejects_duplicates_and_invalid_versions(monkeypatch):
    dist = SimpleNamespace(metadata={"Name": "Some_Package"}, version="1.0")
    monkeypatch.setattr(audit.metadata, "distributions", lambda: [dist, dist])
    with pytest.raises(ValueError, match="duplicate"):
        audit.installed_packages()
    dist.version = "invalid version!"
    with pytest.raises(ValueError):
        audit.installed_packages()


@pytest.mark.parametrize("mismatch", ["name", "installed-name", "editable", "version", "source"])
def test_candidate_identity_verification_cannot_be_bypassed(tmp_path, monkeypatch, mismatch):
    from llm_wiki_cli.services import knowledge_maintenance as maintenance

    (tmp_path / "pyproject.toml").write_text('[project]\nname="agent-wiki-cli"\nversion="2.3.0"\n')
    dist = SimpleNamespace(metadata={"Name": audit.OWNED_PROJECT},
                           read_text=lambda name: json.dumps({"dir_info": {"editable": mismatch == "editable"}}))
    monkeypatch.setattr(audit.metadata, "distribution", lambda name: dist)
    calls = []

    def installed(candidate, version, *, allow_editable):
        calls.append((candidate, version, allow_editable))
        raise ValueError(f"installed {mismatch} mismatch")

    monkeypatch.setattr(maintenance, "_installed", installed)
    if mismatch == "name":
        (tmp_path / "pyproject.toml").write_text('[project]\nname="different"\nversion="2.3.0"\n')
    if mismatch == "installed-name":
        dist.metadata["Name"] = "different"
    with pytest.raises(ValueError):
        audit.candidate_identity(tmp_path)
    assert calls == ([(tmp_path, "2.3.0", False)] if mismatch in {"version", "source"} else [])


@pytest.mark.parametrize("mutation", ["name", "version", "editable", "hash", "second-exclusion"])
def test_unverified_exclusion_is_rejected(mutation):
    value = inventory()
    if mutation == "name":
        value["exclusion"]["name"] = "runtime-extra"
    elif mutation == "version":
        value["exclusion"]["verification"]["version"] = "2.2.0"
    elif mutation == "editable":
        value["exclusion"]["verification"]["editable"] = True
    elif mutation == "hash":
        value["exclusion"]["verification"]["implementation_hash"] = "unknown"
    else:
        value["packages"].append(deepcopy(value["packages"][0]))
    with pytest.raises(ValueError):
        audit.scope(value)


class ConnectionFailure(Exception):
    pass


class CertificateFailure(ConnectionFailure):
    pass


class ProxyFailure(ConnectionFailure):
    pass


class TimeoutFailure(Exception):
    pass


class HTTPFailure(Exception):
    def __init__(self, status, retry_after="0"):
        self.response = SimpleNamespace(status_code=status, headers={"Retry-After": retry_after})


EXCEPTIONS = SimpleNamespace(SSLError=CertificateFailure, ProxyError=ProxyFailure, ConnectionError=ConnectionFailure,
                             Timeout=TimeoutFailure, HTTPError=HTTPFailure)


@pytest.mark.parametrize("status,retry", [(429, True), (500, True), (502, True), (503, True), (504, True),
                                         (400, False), (401, False), (403, False), (404, False), (501, False)])
def test_http_errors_are_classified_by_structured_cause(status, retry):
    error = RuntimeError("same text, independent of retry status")
    error.__cause__ = HTTPFailure(status)
    result = audit.classify_exception(error, EXCEPTIONS)
    assert result["category"] == f"http-{status}" and result["retryable"] is retry


@pytest.mark.parametrize("error,retry", [(ConnectionFailure(), True), (TimeoutFailure(), True),
                                        (CertificateFailure(), False), (ProxyFailure(), False), (ValueError("503 Timeout"), False)])
def test_network_classification_does_not_match_error_text(error, retry):
    wrapped = RuntimeError("scanner failure")
    wrapped.__context__ = error
    assert audit.classify_exception(wrapped, EXCEPTIONS)["retryable"] is retry


@pytest.mark.parametrize("header,expected", [("999999", 60), ("invalid", 0), ("10", 10)])
def test_retry_after_is_bounded(header, expected):
    assert audit.classify_exception(HTTPFailure(429, header), EXCEPTIONS)["retry_after"] == expected


def test_retry_after_accepts_http_date():
    header = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=30), usegmt=True)
    assert 28 <= audit.classify_exception(HTTPFailure(429, header), EXCEPTIONS)["retry_after"] <= 30


def test_pin_matches_release_locks_and_default_runner_uses_isolation(tmp_path):
    root = Path(__file__).parents[1]
    for name in ("requirements.in", "requirements.txt"):
        assert f"pip-audit=={audit.PINNED_AUDIT}" in (root / "release" / name).read_text()
    check = next(c for c in static_checks.default_checks(root, tmp_path) if c.name == "pip-audit")
    assert check.command == (sys.executable, "-I", str(root / "release/dependency_audit.py"),
                             "--candidate", str(root), "--evidence", str(tmp_path))


@pytest.mark.parametrize("outcomes,passed", [([TRANSIENT, {}], True), ([TRANSIENT], False)])
def test_audit_retries_do_not_repeat_bandit_or_prevent_later_checks(tmp_path, monkeypatch, outcomes, passed):
    from tests.test_bandit_runner import configured

    original = subprocess.run
    evidence, producer, derived, later = configured(tmp_path, monkeypatch)
    _, worker_calls, sleeps = configure(monkeypatch, tmp_path, outcomes)
    simulated_worker = audit.subprocess.run
    checks = static_checks.default_checks(tmp_path, evidence)
    audit_check = next(check for check in checks if check.name == "pip-audit")
    launched = []

    def launch(command, **kwargs):
        if "--worker" in command:
            return simulated_worker(command, **kwargs)
        launched.append(command)
        if command[:len(audit_check.command)] == audit_check.command:
            result = audit.run(tmp_path, evidence, command[-1], list(command))
            return SimpleNamespace(returncode=0 if result["status"] == "passed" else 1)
        return original(command, **kwargs)

    monkeypatch.setattr(audit.subprocess, "run", launch)
    result = static_checks.run_checks([producer, derived, audit_check, later], tmp_path, evidence)
    assert [row["passed"] for row in result["checks"]] == [True, True, passed, True]
    assert result["passed"] is passed and result["complete"]
    assert launched.count(producer.command) == 1 and len(launched) == 3
    assert len(worker_calls) == (2 if passed else 3)
    assert sleeps == ([5] if passed else [5, 15])
    if not passed:
        assert "http-503" in result["checks"][2]["error"]
