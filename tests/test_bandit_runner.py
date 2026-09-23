"""Derived Bandit decisions cannot outlive or disagree with their producing scan."""

from dataclasses import replace
import json
import subprocess
import sys

import pytest

from release import static_checks as checks
from tests.bandit_fixtures import report


def configured(tmp_path, monkeypatch, *, blocking=False, missing=False):
    (tmp_path / "source.py").write_text("value = 1\n")
    monkeypatch.setattr(checks, "version", lambda name: checks.PINNED_BANDIT)
    output = tmp_path / "evidence"
    output.mkdir()
    producer, derived = [c for c in checks.default_checks(tmp_path, output) if c.name.startswith("bandit-")]
    payload = report([("HIGH", "HIGH")] if blocking else [])
    code = "pass" if missing else (
        f"from pathlib import Path; Path({str(producer.report)!r}).write_text({json.dumps(payload)!r}); "
        f"raise SystemExit({int(blocking)})")
    producer = replace(producer, command=(sys.executable, "-c", code), source_paths=("source.py",))
    later = checks.Check("later", (sys.executable, "-c", "print('independent check ran')"))
    return output, producer, derived, later


@pytest.mark.parametrize("blocking", [False, True])
def test_one_producer_command_and_an_independent_derived_decision(tmp_path, monkeypatch, blocking):
    output, producer, derived, later = configured(tmp_path, monkeypatch, blocking=blocking)
    called = []
    original = subprocess.run
    def counted(command, **kwargs):
        called.append(command)
        assert kwargs["stdin"] == subprocess.DEVNULL
        return original(command, **kwargs)
    monkeypatch.setattr(checks.subprocess, "run", counted)
    result = checks.run_checks([producer, derived, later], tmp_path, output)
    assert called == [producer.command, later.command]
    assert [r["passed"] for r in result["checks"]] == [True, not blocking, True]
    assert result["passed"] is not blocking and result["complete"]
    assert result["checks"][1]["execution_kind"] == "derived"
    receipt = json.loads((output / "bandit-blocking.json").read_text())
    execution = json.loads((output / "bandit-full-execution.json").read_text())
    assert receipt["run_id"] == execution["run_id"] == result["run_id"]
    assert receipt["execution_sha256"] == checks._sha256(checks._canonical(execution))
    assert execution["elapsed_ns"] > 0 and result["checks"][1]["elapsed_ns"] > 0


@pytest.mark.parametrize("mutation", ["report", "log", "source", "execution"])
def test_changed_producer_evidence_cannot_feed_a_passing_derivation(tmp_path, monkeypatch, mutation):
    output, producer, derived, later = configured(tmp_path, monkeypatch)
    write = checks._write_json
    def corrupt_after_capture(path, payload):
        write(path, payload)
        if path.name == "bandit-full-execution.json":
            if mutation == "source":
                (tmp_path / "source.py").write_text("changed = True\n")
            else:
                target = output / {"report": "bandit-full.json", "log": "bandit-full.log",
                                   "execution": "bandit-full-execution.json"}[mutation]
                target.write_bytes(target.read_bytes() + b"changed")
    monkeypatch.setattr(checks, "_write_json", corrupt_after_capture)
    result = checks.run_checks([producer, derived, later], tmp_path, output)
    assert [r["passed"] for r in result["checks"]] == [True, False, True]
    assert not json.loads((output / "bandit-blocking.json").read_text())["decision"]["passed"]


def test_leftover_reports_and_decisions_cannot_satisfy_a_new_scan(tmp_path, monkeypatch):
    output, producer, derived, later = configured(tmp_path, monkeypatch, missing=True)
    (output / "bandit-full.json").write_text(json.dumps(report([])))
    (output / "bandit-blocking.json").write_text(json.dumps({"decision": {"passed": True}}))
    result = checks.run_checks([producer, derived, later], tmp_path, output)
    assert [r["passed"] for r in result["checks"]] == [False, False, True]
    assert not (output / "bandit-full.json").exists()
    assert json.loads((output / "bandit-blocking.json").read_text())["run_id"] == result["run_id"]


@pytest.mark.parametrize("failure", ["timeout", "launch", "wrong-version"])
def test_scan_execution_failure_preserves_later_checks(tmp_path, monkeypatch, failure):
    output, producer, derived, later = configured(tmp_path, monkeypatch)
    if failure == "wrong-version":
        monkeypatch.setattr(checks, "version", lambda name: "future")
    else:
        run = subprocess.run
        def fail(command, **kwargs):
            if command == producer.command:
                if failure == "timeout":
                    raise subprocess.TimeoutExpired(command, 600)
                raise OSError("owned launch failure")
            return run(command, **kwargs)
        monkeypatch.setattr(checks.subprocess, "run", fail)
    result = checks.run_checks([producer, derived, later], tmp_path, output)
    assert [r["passed"] for r in result["checks"]] == [False, False, True]
    execution = json.loads((output / "bandit-full-execution.json").read_text())
    assert execution["error"] and execution["returncode"] is None


def test_missing_producer_cannot_use_a_disk_receipt(tmp_path, monkeypatch):
    output, _, derived, later = configured(tmp_path, monkeypatch)
    (output / "bandit-full-execution.json").write_text('{}')
    result = checks.run_checks([derived, later], tmp_path, output)
    assert [r["passed"] for r in result["checks"]] == [False, True]


@pytest.mark.parametrize("name", ["bandit-full-execution.json", "bandit-blocking.json"])
def test_unwritable_scan_evidence_fails_closed_without_skipping_other_checks(tmp_path, monkeypatch, name):
    output, producer, derived, later = configured(tmp_path, monkeypatch)
    write = checks._write_json
    def unwritable(path, payload):
        if path.name == name:
            raise OSError("owned evidence write failure")
        return write(path, payload)
    monkeypatch.setattr(checks, "_write_json", unwritable)
    result = checks.run_checks([producer, derived, later], tmp_path, output)
    assert not result["passed"] and result["complete"]
    assert result["checks"][-1]["passed"]
    assert not result["checks"][1]["passed"]
