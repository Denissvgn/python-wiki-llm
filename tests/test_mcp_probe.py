"""Failure attribution and bounded transport contracts for artifact MCP probes."""

import ast
from contextlib import contextmanager
from datetime import timedelta
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.mcp_probe import McpProbe
from tests import release_artifact_smoke as smoke
from tests.release_artifact_smoke import SmokeError, _validate_mcp_probe_evidence


@contextmanager
def failing_cleanup():
    try:
        yield
    finally:
        raise RuntimeError("transport cleanup failed")


def test_probe_persists_completed_steps_and_sdk_request_timeout(tmp_path):
    output = tmp_path / "evidence/probe.json"
    probe = McpProbe(output, ["initialize", "packet"])
    assert probe.read_timeout == timedelta(seconds=45)
    request = {"filters": {"module": "app"}}
    with probe.session():
        with probe.step("initialize"):
            current = json.loads(output.read_text())
            assert current["status"] == "running"
            assert current["steps"][-1]["status"] == "running"
        with probe.step("packet", request=request):
            request["filters"]["module"] = "changed"
    result = json.loads(output.read_text())
    assert result["status"] == "pass"
    assert result["steps"][-1]["request"]["filters"]["module"] == "app"
    assert all(step["status"] == "pass" for step in result["steps"])
    assert all(step["elapsed_seconds"] >= 0 for step in result["steps"])
    _validate_mcp_probe_evidence(output)


@pytest.mark.parametrize(
    "error", [TimeoutError("request expired"), AssertionError("packet differs")]
)
def test_probe_preserves_request_failure_before_cleanup_replaces_exception(
    tmp_path, error
):
    output = tmp_path / "probe.json"
    probe = McpProbe(output, ["packet"])
    with pytest.raises(RuntimeError, match="transport cleanup failed"):
        with probe.session(), failing_cleanup():
            with probe.step("packet"):
                raise error
    result = json.loads(output.read_text())
    assert result["status"] == "fail"
    assert result["steps"][0]["status"] == "fail"
    assert result["steps"][0]["error"]["message"] == str(error)
    assert result["steps"][0]["error"]["type"].endswith(type(error).__name__)
    assert result["session_error"]["message"] == "transport cleanup failed"
    with pytest.raises(SmokeError, match="incomplete"):
        _validate_mcp_probe_evidence(output)


def test_probe_does_not_accept_teardown_failure_after_successful_assertions(tmp_path):
    output = tmp_path / "probe.json"
    with pytest.raises(RuntimeError, match="cleanup"):
        probe = McpProbe(output, ["packet"])
        with probe.session(), failing_cleanup():
            with probe.step("packet"):
                pass
    result = json.loads(output.read_text())
    assert result["steps"][0]["status"] == "pass"
    assert result["status"] == "fail"


@pytest.mark.parametrize("steps", [[], ["packet", "packet"]])
def test_probe_rejects_empty_or_duplicate_expectations(tmp_path, steps):
    with pytest.raises(ValueError, match="nonempty and unique"):
        McpProbe(tmp_path / "probe.json", steps)


def test_probe_rejects_missing_steps_and_caught_assertion_failures(tmp_path):
    for name in ("missing", "caught"):
        output = tmp_path / f"{name}.json"
        probe = McpProbe(output, ["packet"])
        with pytest.raises(AssertionError, match="every expected step"):
            with probe.session():
                if name == "caught":
                    with pytest.raises(AssertionError, match="wrong content"):
                        with probe.step("packet"):
                            raise AssertionError("wrong content")
        assert json.loads(output.read_text())["status"] == "fail"


def test_probe_rejects_out_of_order_steps(tmp_path):
    probe = McpProbe(tmp_path / "probe.json", ["initialize", "packet"])
    with pytest.raises(AssertionError, match="Unexpected"):
        with probe.session(), probe.step("packet"):
            pass


def test_probe_captures_expected_and_actual_payloads_outside_consumer(tmp_path):
    consumer = tmp_path / "consumer"
    consumer.mkdir()
    source = consumer / "source.py"
    source.write_bytes(b"unchanged\n")
    probe = McpProbe(tmp_path / "evidence/probe.json", ["packet"])
    payload = {"label": "Café 雪", "packet": {"found": True}}
    probe.capture("packet-expected", payload)
    assert (
        json.loads((tmp_path / "evidence/probe-packet-expected.json").read_text())
        == payload
    )
    assert list(consumer.iterdir()) == [source]
    assert source.read_bytes() == b"unchanged\n"
    with pytest.raises(ValueError, match="simple identifier"):
        probe.capture("../consumer/source", payload)


@pytest.mark.parametrize(
    "value", [0, -1, 46, True, None, "45", float("inf"), float("nan")]
)
def test_probe_keeps_request_deadlines_bounded(tmp_path, value):
    with pytest.raises(ValueError, match="timeout"):
        McpProbe(tmp_path / "probe.json", ["packet"], request_timeout_seconds=value)


@pytest.mark.parametrize(
    "filename", ["packet-artifact-parity.py", "native-artifact-consumer.py", "workflow-artifact-consumer.py"]
)
def test_installed_probes_use_sdk_rpc_deadlines_without_outer_session_cancellation(
    filename,
):
    source = Path(__file__).parent / "fixtures" / filename
    tree = ast.parse(source.read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    sessions = [
        node
        for node in calls
        if isinstance(node.func, ast.Name) and node.func.id == "ClientSession"
    ]
    assert sessions
    for session in sessions:
        timeout = next(
            arg.value for arg in session.keywords if arg.arg == "read_timeout_seconds"
        )
        assert isinstance(timeout, ast.Attribute) and timeout.attr == "read_timeout"
    assert not any(
        isinstance(node.func, ast.Attribute) and node.func.attr == "wait_for"
        for node in calls
    )


@pytest.mark.parametrize("payload", [None, {}, {"status": "pass", "steps": []}])
def test_smoke_rejects_missing_or_incomplete_probe_receipts(tmp_path, payload):
    path = tmp_path / "probe.json"
    if payload is not None:
        path.write_text(json.dumps(payload))
    with pytest.raises(SmokeError, match="unavailable|incomplete"):
        _validate_mcp_probe_evidence(path)


def test_workflow_budget_covers_setup_and_both_transports_without_relaxing_other_commands(tmp_path, monkeypatch):
    evidence = tmp_path / 'evidence'
    calls = []

    def windows_paced_run(command, **kwargs):
        mode = command[-3] if len(command) > 3 else 'ordinary'
        # Replay a workload whose individual stages fit the ordinary deadline,
        # but whose setup plus two transports cannot finish within 120 seconds.
        elapsed = {'base': 60, 'mcp': 60 + 71 + 71, 'ordinary': 121}[mode]
        calls.append(mode)
        if elapsed > kwargs['timeout']:
            raise subprocess.TimeoutExpired(command, kwargs['timeout'])
        if mode == 'mcp':
            for transport in ('stdio', 'http'):
                probe = McpProbe(evidence / f'workflow-mcp-{transport}.json', ['verified'])
                with probe.session(), probe.step('verified'):
                    pass
        return subprocess.CompletedProcess(command, 0, json.dumps({
            'sdk': 'verified' if mode == 'mcp' else 'not-used', 'canonical_cli_parity': True,
        }), '')

    monkeypatch.setattr(smoke.subprocess, 'run', windows_paced_run)
    result = smoke._validate_workflow_consumer(Path(sys.executable), Path(sys.executable), tmp_path, evidence)
    assert result == {'canonical_cli_parity': True, 'mcp_transports': ['stdio', 'http']}
    assert calls == ['base', 'mcp']
    records = [json.loads((evidence / f'workflow-{mode}-execution.json').read_text()) for mode in calls]
    assert all(record['status'] == 'pass' and record['elapsed_seconds'] >= 0 for record in records)
    assert records[0]['timeout_seconds'] < 202 <= records[1]['timeout_seconds'] < 900
    with pytest.raises(subprocess.TimeoutExpired):
        smoke._run(['ordinary'], cwd=tmp_path)


@pytest.mark.parametrize('mode', ['base', 'mcp'])
@pytest.mark.parametrize('failure', ['timeout', 'assertion'])
def test_workflow_deadline_still_fails_and_retains_process_diagnostics(tmp_path, monkeypatch, mode, failure):
    evidence = tmp_path / 'evidence'

    def failed_run(command, **kwargs):
        current = command[-3]
        if current != mode:
            return subprocess.CompletedProcess(command, 0, json.dumps({'sdk': 'not-used'}), '')
        record = json.loads((evidence / f'workflow-{current}-execution.json').read_text())
        assert record['status'] == 'running' and record['timeout_seconds'] == kwargs['timeout']
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(command, kwargs['timeout'],
                                            output=b'partial output', stderr='last step: session — started')
        return subprocess.CompletedProcess(command, 1, '', 'assertion failed')

    monkeypatch.setattr(smoke.subprocess, 'run', failed_run)
    expected = f'workflow \\({mode}\\) exceeded its' if failure == 'timeout' else 'command returned 1'
    with pytest.raises(SmokeError, match=expected):
        smoke._validate_workflow_consumer(Path(sys.executable), Path(sys.executable), tmp_path, evidence)
    path = evidence / f'workflow-{mode}-execution.json'
    record = json.loads(path.read_text())
    assert record['status'] == ('timeout' if failure == 'timeout' else 'fail')
    assert record['elapsed_seconds'] >= 0
    if failure == 'timeout':
        assert path.with_suffix('.stdout').read_bytes() == b'partial output'
        assert path.with_suffix('.stderr').read_text(encoding='utf-8') == 'last step: session — started'


def test_smoke_subprocess_enforces_its_explicit_deadline(tmp_path):
    command = smoke._isolated_utf8_python_command(sys.executable, '-c', 'import time; time.sleep(2)')
    with pytest.raises(subprocess.TimeoutExpired):
        smoke._run(command, cwd=tmp_path, timeout=0.1)
