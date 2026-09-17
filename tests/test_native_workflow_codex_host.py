"""Deterministic host controls; this module never invokes a model or Codex."""

import json
import os
from pathlib import Path
import sys

import pytest

from tests.native_workflow import codex_host as host
from tests.native_workflow.run_trace import AttemptTrace, identity, inspect_attempt
from tests.provider_conformance.model import canonical_json


def observation(events, **updates):
    values = {'returncode': 0, 'stdout': b''.join(json.dumps(e).encode() + b'\n' for e in events),
              'stderr': b'', 'elapsed_ns': 5, 'disposition': 'completed'}
    values.update(updates)
    return host.ProcessObservation(**values)


def events():
    return [{'type': 'thread.started', 'thread_id': 'synthetic'}, {'type': 'turn.started'},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '{"action":"finish","answer":"synthetic"}'}},
            {'type': 'turn.completed', 'usage': {'input_tokens': 100, 'output_tokens': 10, 'cached_input_tokens': 80}}]


def test_host_parsing_keeps_reported_usage_and_observation_scope():
    result = host.parse_response(observation(events()))
    assert result['action'] == {'action': 'finish', 'answer': 'synthetic'}
    assert result['usage'] == {'input_tokens': 100, 'output_tokens': 10, 'cached_input_tokens': 80}
    assert 'not independently observed' in result['scope']


@pytest.mark.parametrize('fault', ['native-tool', 'missing-completion', 'failure', 'duplicate-turn', 'after-completion', 'bad-usage', 'bad-action', 'early-message'])
def test_unexpected_native_actions_and_incomplete_turns_never_become_valid_actions(fault):
    raw = events()
    if fault == 'native-tool':
        raw.insert(2, {'type': 'item.started', 'item': {'type': 'command_execution', 'command': 'forbidden'}})
    elif fault == 'missing-completion':
        raw.pop()
    elif fault == 'failure':
        raw[-1] = {'type': 'turn.failed', 'error': 'synthetic'}
    elif fault == 'duplicate-turn':
        raw.insert(2, {'type': 'turn.started'})
    elif fault == 'after-completion':
        raw.append(raw[2])
    elif fault == 'bad-usage':
        raw[-1]['usage']['input_tokens'] = True
    elif fault == 'early-message':
        raw[1], raw[2] = raw[2], raw[1]
    else:
        raw[2]['item']['text'] = '["not an action"]'
    with pytest.raises(ValueError):
        host.parse_response(observation(raw))


def test_only_the_pinned_pre_turn_disabled_code_mode_notice_is_accepted():
    raw = events()
    notice = {'type': 'item.completed', 'item': {'type': 'error', 'message': host._STARTUP_NOTICE}}
    raw.insert(1, notice)
    assert host.parse_response(observation(raw))['diagnostics'] == [host._STARTUP_NOTICE]
    notice['item']['message'] = 'another startup failure'
    with pytest.raises(host.HostError):
        host.parse_response(observation(raw))


def test_duplicate_json_fields_and_nonfinite_actions_are_rejected():
    duplicate = observation(events())
    duplicate = observation([], stdout=duplicate.stdout.replace(b'"input_tokens": 100', b'"input_tokens": 100, "input_tokens": 0'))
    with pytest.raises(host.HostError, match='Duplicate'):
        host.parse_response(duplicate)
    raw = events()
    raw[2]['item']['text'] = '{"value":NaN}'
    with pytest.raises(ValueError):
        host.parse_response(observation(raw))


@pytest.mark.parametrize('marker', ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'TF_BUILD', 'BUILDKITE', 'JENKINS_URL'])
def test_live_host_calls_are_refused_in_ci_before_any_preparation(tmp_path, monkeypatch, marker):
    monkeypatch.setenv(marker, 'true')
    def forbidden(*args, **kwargs):
        pytest.fail('Live agent boundary was crossed in CI')
    monkeypatch.setattr(host, 'binary_hash', forbidden)
    selected = host.CodexHost(Path('/never-execute'), 'unused', 'synthetic', 'synthetic', 'max')
    with pytest.raises(host.HostError, match='cannot run in CI'):
        selected.call('synthetic', {}, workspace=tmp_path / 'must-not-exist', timeout=1)
    assert not list(tmp_path.iterdir())


def test_bounded_process_stops_at_output_and_deadline_limits(tmp_path):
    # Ordinary deterministic child processes, never a coding host or model.
    output = host.run_bounded([sys.executable, '-I', '-c', 'print("x" * 100000)'],
                              cwd=tmp_path, input_bytes=b'', timeout=5, max_output=1024)
    assert output.disposition == 'output-limit' and len(output.stdout) == 1024
    timed = host.run_bounded([sys.executable, '-I', '-c', 'import time; time.sleep(2)'],
                             cwd=tmp_path, input_bytes=b'', timeout=0.1)
    assert timed.disposition == 'timed-out'


def test_cancel_before_launch_never_creates_a_process(tmp_path, monkeypatch):
    monkeypatch.setattr(host.subprocess, 'Popen', lambda *a, **kw: pytest.fail('cancelled launch'))
    with pytest.raises(host.HostError, match='cancelled'):
        host.run_bounded(['never'], cwd=tmp_path, input_bytes=b'', timeout=1, cancelled=lambda: True)


@pytest.mark.parametrize('raw', [b'not json', b'{}', b'{"type":"item.completed","item":null}',
                               b'{"type":"thread.started","thread_id":"t","bad":NaN}'])
def test_malformed_host_evidence_is_retained_in_the_failure(raw):
    received = observation([], stdout=raw)
    with pytest.raises(host.HostError) as error:
        host.parse_response(received)
    assert error.value.observation is received


def test_multiple_final_actions_cannot_be_silently_replaced():
    raw = events()
    raw.insert(3, raw[2])
    with pytest.raises(host.HostError, match='ambiguous'):
        host.parse_response(observation(raw))


def synthetic_host(monkeypatch):
    for marker in host._CI_MARKERS:
        monkeypatch.delenv(marker, raising=False)
    # Fake the live boundary on every platform; never resolve a real CLI.
    monkeypatch.setattr(host, 'binary_hash', lambda path: 'synthetic-pin')
    monkeypatch.setattr(host, '_NATIVE_WINDOWS', False)
    return host.CodexHost(Path('/never-execute'), 'synthetic-pin', 'synthetic', 'synthetic', 'max')


@pytest.mark.parametrize('fault', ['schema', 'extra-file', 'binary'])
def test_mutated_host_inputs_fail_with_the_raw_observation(tmp_path, monkeypatch, fault):
    selected = synthetic_host(monkeypatch)
    received = observation(events())

    def fake_call(argv, *, cwd, **kwargs):
        if fault == 'schema':
            (cwd / 'output-schema.json').write_bytes(b'{}')
        elif fault == 'extra-file':
            (cwd / 'unreported-edit').write_bytes(b'unreported')
        else:
            monkeypatch.setattr(host, 'binary_hash', lambda path: 'changed')
        return received

    monkeypatch.setattr(host, 'run_bounded', fake_call)
    with pytest.raises(host.HostError, match='changed') as error:
        selected.call('synthetic', {'type': 'object'}, workspace=tmp_path / 'control', timeout=1)
    assert error.value.observation is received


@pytest.mark.parametrize('timeout', [0, 601, float('nan'), float('inf'), True])
def test_invalid_host_limits_fail_before_creating_a_workspace(tmp_path, monkeypatch, timeout):
    selected = synthetic_host(monkeypatch)
    monkeypatch.setattr(host, 'run_bounded', lambda *a, **kw: pytest.fail('invalid launch'))
    with pytest.raises(host.HostError, match='budget'):
        selected.call('synthetic', {}, workspace=tmp_path / 'control', timeout=timeout)
    assert not list(tmp_path.iterdir())


def test_native_windows_live_calls_are_refused_before_preparation(tmp_path, monkeypatch):
    selected = synthetic_host(monkeypatch)
    monkeypatch.setattr(host, '_NATIVE_WINDOWS', True)
    with pytest.raises(host.HostError, match='not qualified on native Windows'):
        selected.call('synthetic', {}, workspace=tmp_path / 'control', timeout=1)
    assert not list(tmp_path.iterdir())


def test_cancellation_during_a_deterministic_child_is_observed(tmp_path):
    checks = []

    def cancel():
        checks.append(True)
        return len(checks) > 1

    result = host.run_bounded([sys.executable, '-I', '-c', 'import time; time.sleep(2)'],
                              cwd=tmp_path, input_bytes=b'', timeout=5, cancelled=cancel)
    assert result.disposition == 'cancelled'


def test_interrupt_reaps_the_child_and_preserves_partial_output(tmp_path):
    marker = tmp_path / 'ready'

    def interrupt():
        if marker.exists():
            raise KeyboardInterrupt
        return False

    script = 'import sys,time; from pathlib import Path; print("partial output",flush=True); Path(sys.argv[1]).touch(); time.sleep(3)'
    with pytest.raises(host.HostCancelled) as error:
        host.run_bounded([sys.executable, '-I', '-c', script, str(marker)], cwd=tmp_path,
                         input_bytes=b'', timeout=5, cancelled=interrupt)
    received = error.value.observation
    assert received is not None and received.disposition == 'cancelled'
    assert received.stdout.strip() == b'partial output'


def test_owned_posix_descendants_are_reaped_even_after_closing_output(tmp_path):
    if os.name == 'nt':
        # Live host calls refuse this platform; the portable root process
        # cancellation contract is covered above on Windows too.
        return
    script = ('import os,time\n'
              'if os.fork() == 0:\n'
              ' os.close(1); os.close(2); time.sleep(2)\n')
    result = host.run_bounded([sys.executable, '-I', '-c', script],
                              cwd=tmp_path, input_bytes=b'', timeout=5)
    assert result.disposition == 'descendants-terminated'


def test_exited_group_is_rechecked_after_a_signal_race(tmp_path, monkeypatch):
    if os.name == 'nt':
        return
    original = host.os.killpg
    denied = []

    def exiting_group(pid, sig):
        if not denied:
            original(pid, sig)
            denied.append(True)
            raise PermissionError('owned group exited during the first signal')
        return original(pid, sig)

    monkeypatch.setattr(host.os, 'killpg', exiting_group)
    result = host.run_bounded([sys.executable, '-I', '-c', 'import time; time.sleep(2)'],
                              cwd=tmp_path, input_bytes=b'', timeout=0.1)
    assert denied and result.disposition == 'timed-out'


def test_persistent_process_group_denial_cannot_claim_cleanup(tmp_path, monkeypatch):
    if os.name == 'nt':
        return

    def denied(*args):
        raise PermissionError('synthetic persistent signal denial')

    monkeypatch.setattr(host.os, 'killpg', denied)
    with pytest.raises(host.HostError, match='cleanup is unavailable') as error:
        host.run_bounded([sys.executable, '-I', '-c', 'import time; time.sleep(2)'],
                         cwd=tmp_path, input_bytes=b'', timeout=0.1)
    received = error.value.observation
    assert received is not None and received.disposition == 'cleanup-failed'


def manifest(selected):
    pin = identity(b'synthetic control only; no execution admission')
    return {'schema_version': 'native-workflow-run-trace/v1', 'attempt_id': 'probe-A-0',
            'task_id': 'probe', 'arm': 'A', 'repetition': 0, 'execution_kind': 'external-host',
            'host': 'synthetic-control', 'model': selected.model,
            'settings': identity(canonical_json(selected.configuration())), 'admission': pin,
            'bindings': {key: pin for key in ('task', 'protocol', 'source', 'wiki', 'oracle',
                                             'provider', 'profile', 'original_roots')}}


def test_trace_bridge_retains_actual_request_receipt_usage_and_unknown_framing(tmp_path, monkeypatch):
    selected = synthetic_host(monkeypatch)
    received = observation(events())
    monkeypatch.setattr(host.CodexHost, 'call', lambda *a, **kw: received)
    directory = tmp_path / 'trace'
    with AttemptTrace(directory, manifest(selected)) as trace:
        result = host.trace_call(trace, selected, 'observed prompt', {}, call_id='call-0',
                                 workspace=tmp_path / 'control', timeout=1)
        assert result['action']['action'] == 'finish'
        # This control verifies model recording only. It cannot establish
        # successful arm execution without the missing admission and cleanup.
        trace.finish('integration-failed')
    report = inspect_attempt(directory)
    assert report['work']['model_usage'] == {'input_tokens': 100, 'output_tokens': 10}
    assert report['observations']['context'] == report['observations']['model-end'] == 1
    assert report['work']['contexts'][0]['host_framing_tokens'] is None
    assert report['model_execution_established'] is False
    records = [json.loads(line) for line in (directory / 'events.jsonl').read_bytes().splitlines()]
    end = next(item['data'] for item in records if item['kind'] == 'model-end')
    receipt = json.loads((directory / 'blobs' / end['receipt'][7:]).read_bytes())
    assert (directory / 'blobs' / receipt['host_process']['stdout'][7:]).read_bytes() == received.stdout
    request = next(item['data']['request'] for item in records if item['kind'] == 'model-start')
    actual = json.loads((directory / 'blobs' / request[7:]).read_bytes())
    assert actual['prompt'] == 'observed prompt' and actual['schema'] == {}
    assert actual['argv'][-1] == '-'


@pytest.mark.parametrize('disposition,expected', [('timed-out', 'timed-out'), ('cancelled', 'cancelled'),
                                                ('output-limit', 'integration-failed'), ('completed', 'integration-failed')])
def test_trace_bridge_preserves_failed_and_malformed_responses(tmp_path, monkeypatch, disposition, expected):
    selected = synthetic_host(monkeypatch)
    received = observation([], disposition=disposition, stdout=b'malformed partial output')
    monkeypatch.setattr(host.CodexHost, 'call', lambda *a, **kw: received)
    directory = tmp_path / 'trace'
    with AttemptTrace(directory, manifest(selected)) as trace:
        with pytest.raises(host.HostError):
            host.trace_call(trace, selected, 'synthetic', {}, call_id='call-0',
                            workspace=tmp_path / 'control', timeout=1)
        trace.finish(expected)
    report = inspect_attempt(directory)
    assert report['outcome'] == expected and not report['pending_calls']
    assert report['work']['model_usage'] == {'input_tokens': None, 'output_tokens': None}
    assert (directory / 'blobs' / identity(received.stdout)[7:]).read_bytes() == received.stdout


def test_trace_bridge_refuses_configuration_substitution_before_a_call(tmp_path, monkeypatch):
    selected = synthetic_host(monkeypatch)
    wrong = manifest(selected)
    wrong['model'] = 'another model'
    monkeypatch.setattr(host.CodexHost, 'call', lambda *a, **kw: pytest.fail('substituted model'))
    with AttemptTrace(tmp_path / 'trace', wrong) as trace:
        with pytest.raises(host.HostError, match='configuration'):
            host.trace_call(trace, selected, 'synthetic', {}, call_id='call-0',
                            workspace=tmp_path / 'control', timeout=1)
        trace.finish('integration-failed')


def test_trace_bridge_retains_preparation_cancellation_without_inventing_a_process(tmp_path, monkeypatch):
    selected = synthetic_host(monkeypatch)
    monkeypatch.setattr(host, 'run_bounded', lambda *a, **kw: pytest.fail('cancelled launch'))
    directory = tmp_path / 'trace'
    with AttemptTrace(directory, manifest(selected)) as trace:
        with pytest.raises(host.HostCancelled):
            host.trace_call(trace, selected, 'synthetic', {}, call_id='call-0',
                            workspace=tmp_path / 'control', timeout=1, cancelled=lambda: True)
        trace.finish('cancelled')
    report = inspect_attempt(directory)
    assert report['outcome'] == 'cancelled' and not report['pending_calls']
    assert not (tmp_path / 'control').exists()
    records = [json.loads(line) for line in (directory / 'events.jsonl').read_bytes().splitlines()]
    end = next(item['data'] for item in records if item['kind'] == 'model-end')
    assert end['outcome'] == 'cancelled'
    receipt = json.loads((directory / 'blobs' / end['receipt'][7:]).read_bytes())
    assert receipt['host_process'] is None
