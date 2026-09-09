"""CI runtime outputs and v2 retain check results across persistence failures."""

from __future__ import annotations

import errno
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from llm_wiki_cli.commands import ci_check_cmd
from llm_wiki_cli.services import ci_report, runtime_output
from llm_wiki_cli.services.inventory_cache import InventoryCacheStats
from llm_wiki_cli.services.lint_service import LintIssue, LintReport


def invoke(capsys, **overrides):
    values = dict(
        src_dir=".", wiki_dir="wiki", format="json", report_schema="v2", no_cache=True
    )
    values.update(overrides)
    try:
        ci_check_cmd.run(SimpleNamespace(**values))
    except SystemExit as exc:
        code = exc.code
    else:
        code = 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    ci_report.validate_ci_check_payload(payload, cli_exit=code)
    return code, payload, captured.err


@pytest.fixture
def report_setup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "wiki").mkdir()
    report = LintReport(wiki_dir="wiki", src_dir=".", strict=True)
    compute = Mock(return_value=report)
    monkeypatch.setattr(ci_check_cmd, "build_report", compute)
    monkeypatch.setattr(ci_check_cmd, "record_validation_event", lambda **kw: None)
    return report, compute


@pytest.mark.parametrize("passing", [True, False])
def test_no_report_preserves_check_exit_and_json(
    report_setup, monkeypatch, capsys, passing
):
    report, compute = report_setup
    if not passing:
        report.issues.append(LintIssue("broken_links", "broken"))
    monkeypatch.setattr(
        runtime_output,
        "preflight_output_path",
        lambda *_: pytest.fail("preflighted disabled output"),
    )
    monkeypatch.setattr(
        ci_check_cmd,
        "write_bytes_atomic",
        lambda *a: pytest.fail("wrote disabled output"),
    )
    code, payload, stderr = invoke(capsys, no_report=True)
    assert code == int(not passing)
    assert payload["runtime"]["report"]["status"] == "disabled"
    assert payload["runtime"]["cache"]["status"] == "disabled"
    assert stderr == ""
    assert compute.call_count == 1


@pytest.mark.parametrize("passing", [True, False])
def test_implicit_report_preflight_failure_retains_result(
    report_setup, monkeypatch, capsys, passing
):
    report, compute = report_setup
    if not passing:
        report.issues.append(LintIssue("broken_links", "broken"))
    monkeypatch.setattr(
        runtime_output,
        "preflight_output_path",
        Mock(side_effect=OSError(errno.EROFS, "read-only")),
    )
    code, payload, stderr = invoke(capsys)
    assert code == int(not passing)
    assert payload["runtime"]["report"]["status"] == "failed"
    assert payload["runtime"]["report"]["explicit"] is False
    assert "Implicit report output unavailable" in stderr
    assert compute.call_count == 1


@pytest.mark.parametrize("selected", ["explicit.md", ci_check_cmd.DEFAULT_REPORT])
def test_explicit_report_failure_is_early_even_for_default_spelling(
    report_setup, monkeypatch, selected
):
    _, compute = report_setup
    monkeypatch.setattr(
        runtime_output,
        "preflight_output_path",
        Mock(side_effect=OSError(errno.EROFS, "read-only")),
    )
    with pytest.raises(runtime_output.RuntimeOutputError, match="explicit report"):
        ci_check_cmd.run(
            SimpleNamespace(
                src_dir=".", wiki_dir="wiki", report=selected, no_cache=True
            )
        )
    compute.assert_not_called()


@pytest.mark.parametrize("explicit", [True, False])
@pytest.mark.parametrize("passing", [True, False])
def test_late_report_failure_keeps_findings_and_old_file(
    report_setup, monkeypatch, capsys, explicit, passing
):
    report, _ = report_setup
    if not passing:
        report.issues.append(LintIssue("broken_links", "broken"))
    path = Path("explicit.md" if explicit else ci_check_cmd.DEFAULT_REPORT).absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"previous report\n")
    real_replace = runtime_output.os.replace

    def deny_report_only(source, target):
        if Path(target) == path:
            raise OSError(errno.EROFS, "late report failure")
        return real_replace(source, target)

    monkeypatch.setattr(runtime_output.os, "replace", deny_report_only)
    code, payload, stderr = invoke(
        capsys, **({"report": str(path)} if explicit else {})
    )
    assert code == (2 if explicit else int(not passing))
    assert payload["check_exit_code"] == int(not passing)
    assert payload["ok"] is passing
    assert payload["runtime"]["report"]["status"] == "failed"
    assert path.read_bytes() == b"previous report\n"
    assert not list(path.parent.glob(".*.tmp"))
    assert "not saved" in stderr


def test_written_v2_and_v1_shape_compatibility(report_setup, capsys):
    report, _ = report_setup
    legacy = ci_report.build_ci_check_payload(report)
    code, payload, _ = invoke(capsys, report="report.md")
    assert code == 0
    assert payload["runtime"]["report"]["status"] == "written"
    assert Path("report.md").read_bytes().endswith(b"\n")
    assert {
        key: value
        for key, value in payload.items()
        if key in legacy and key != "schema_version"
    } == {key: value for key, value in legacy.items() if key != "schema_version"}
    _, legacy_result, _ = invoke(capsys, no_report=True, report_schema="v1")
    assert legacy_result == legacy


@pytest.mark.parametrize(
    "path,value",
    [
        (("command_exit_code",), 2),
        (("check_exit_code",), 1),
        (("runtime", "report", "status"), "pending"),
        (("runtime", "report", "error"), "false failure"),
        (("runtime", "cache", "hits"), -1),
        (("runtime", "cache", "failure_stage"), {}),
        (("runtime", "cache", "enabled"), "yes"),
    ],
)
def test_v2_rejects_inconsistent_runtime_data(path, value):
    report = LintReport(wiki_dir="wiki", src_dir=".", strict=True)
    payload = ci_report.build_ci_check_payload(
        report,
        report_schema="v2",
        runtime={
            "cache": InventoryCacheStats().to_dict(),
            "report": {
                "status": "written",
                "path": "report.md",
                "explicit": True,
                "error": None,
            },
        },
    )
    changed = deepcopy(payload)
    target = changed
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    with pytest.raises(ci_report.CiCheckReportError):
        ci_report.validate_ci_check_payload(changed, cli_exit=0)
