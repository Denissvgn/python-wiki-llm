"""Execution contracts for independent, blocking static qualification checks."""

import json
import sys

import pytest

from release import static_checks


def _check(name, code, **kwargs):
    return static_checks.Check(name, (sys.executable, "-c", code), **kwargs)


def test_failure_keeps_later_checks_and_all_evidence(tmp_path):
    checks = [
        _check("pyright", "print('missing import'); raise SystemExit(1)"),
        _check("ruff", "print('checked')"),
        _check("actionlint", "print('workflow error'); raise SystemExit(2)"),
    ]
    result = static_checks.run_checks(checks, tmp_path, tmp_path / "evidence")
    assert not result["passed"]
    assert [item["returncode"] for item in result["checks"]] == [1, 0, 2]
    assert (tmp_path / "evidence/ruff.log").read_text() == "checked\n"
    assert json.loads((tmp_path / "evidence/checks.json").read_text()) == result


@pytest.mark.parametrize("exit_code", [0, 1])
def test_bandit_findings_require_complete_json(tmp_path, exit_code):
    report = tmp_path / "bandit.json"
    payload = json.dumps({"results": [{}], "errors": [], "metrics": {}})
    check = _check(
        "bandit-full",
        f"from pathlib import Path; Path({str(report)!r}).write_text({payload!r}); raise SystemExit({exit_code})",
        accepted_codes=(0, 1),
        report=report,
        report_kind="bandit",
    )
    assert static_checks.run_checks([check], tmp_path, tmp_path / "out")["passed"]


@pytest.mark.parametrize(
    "payload",
    [None, "broken", "{}", '{"results": [], "errors": ["failed"], "metrics": {}}'],
)
def test_bandit_success_cannot_hide_absent_or_failed_report(tmp_path, payload):
    report = tmp_path / "bandit.json"
    code = (
        "pass"
        if payload is None
        else f"from pathlib import Path; Path({str(report)!r}).write_text({payload!r})"
    )
    # A valid old result must never satisfy the current check.
    report.write_text(json.dumps({"results": [], "errors": [], "metrics": {}}))
    check = _check("bandit-full", code, report=report, report_kind="bandit")
    assert not static_checks.run_checks([check], tmp_path, tmp_path / "out")["passed"]


def test_missing_executable_does_not_skip_other_checks(tmp_path):
    checks = [
        static_checks.Check("missing", (str(tmp_path / "absent"),)),
        _check("later", "print('ran')"),
    ]
    result = static_checks.run_checks(checks, tmp_path, tmp_path / "out")
    assert not result["passed"]
    assert result["checks"][0]["error"]
    assert result["checks"][1]["passed"]


def test_default_checks_use_current_interpreter_and_preserve_blocking_scanners(
    tmp_path,
):
    checks = static_checks.default_checks(tmp_path, tmp_path / "out")
    by_name = {check.name: check for check in checks}
    assert set(by_name) == {
        "pip-check",
        "pyright",
        "ruff",
        "bandit-full",
        "bandit-blocking",
        "pip-audit",
        "actionlint",
    }
    assert by_name["pyright"].command[-2:] == ("--pythonpath", sys.executable)
    assert all(
        check.command[0] == sys.executable
        for check in checks
        if check.name != "actionlint"
    )
    assert by_name["bandit-full"].accepted_codes == (0, 1)
    assert by_name["bandit-blocking"].accepted_codes == (0,)
    assert "-lll" in by_name["bandit-blocking"].command
    assert "-iii" in by_name["bandit-blocking"].command
    assert by_name["pip-audit"].report_kind == "pip-audit"
