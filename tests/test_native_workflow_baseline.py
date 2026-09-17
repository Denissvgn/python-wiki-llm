"""Baseline preparation preserves original artifacts, visibility and all attempts."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from tests.native_workflow import baseline
from tests.native_workflow.run_trace import AttemptTrace, identity
from tests.provider_conformance.model import canonical_json


@pytest.fixture
def retained(tmp_path):
    corpus_root = tmp_path / 'corpus'
    shutil.copytree(Path(__file__).parent / 'native_workflow' / 'fixtures', corpus_root / 'fixtures')
    corpus_raw = (Path(__file__).parent / 'native_workflow/corpus.json').read_bytes()
    (corpus_root / 'corpus.json').write_bytes(corpus_raw)
    corpus = json.loads(corpus_raw)
    inputs = tmp_path / 'retained'
    inputs.mkdir()
    records = []
    for task in corpus['tasks']:
        destination = inputs / task['id']
        shutil.copytree(corpus_root / 'fixtures' / task['id'], destination)
        (destination / 'native-wiki').mkdir()
        (destination / 'native-wiki/index.md').write_text('# Same knowledge in every arm\n')
        records.append({'task': task['id'], 'preparation': 'unavailable' if task['id'] == 'T07' else 'prepared',
            'reason': 'declared unsupported raw CPP' if task['id'] == 'T07' else None,
            'sha256': {p.relative_to(destination).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in destination.rglob('*') if p.is_file()},
            'source_root': 'project', 'native_wiki_root': 'native-wiki', 'authored_wiki_root': 'project/wiki',
            'visibility': ['project/**', 'native-wiki/**', 'prompt.txt'], 'oracle_visible': False,
            'same_bytes_in_all_arms': True})
    inputs_manifest = inputs / 'manifest.json'
    inputs_manifest.write_bytes(canonical_json({'schema_version': 'native-workflow-baseline-inputs/v1',
        'provider_revision': 'a' * 40, 'model_execution': False, 'records': records}))
    archives = tmp_path / 'archives'
    archives.mkdir()
    hashes = {}
    for name in ('baseline.whl', 'baseline.tar.gz'):
        path = archives / name
        path.write_bytes(b'opaque retained artifact bytes: ' + name.encode())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    artifacts = tmp_path / 'artifacts.json'
    artifacts.write_bytes(canonical_json({'schema_version': 'native-workflow-baseline/v1',
        'source_revision': 'a' * 40, 'artifacts': hashes}))
    protocol = tmp_path / 'protocol.json'
    protocol.write_bytes(canonical_json({'schema_version': 'native-workflow-analysis/v1',
        'manifest_sha256': hashlib.sha256(corpus_raw).hexdigest(), 'seed': 260916, 'repetitions': 3,
        'arm_order': 'Latin square A,B,C; B,C,A; C,A,B by task and repetition',
        'limits': {'seconds_per_run': 600, 'tool_rounds': 24, 'context_tokens': 32000,
                   'workspace_bytes': 67108864, 'concurrent_runs': 1}}))
    return {'corpus_root': corpus_root, 'inputs_manifest': inputs_manifest, 'artifact_manifest': artifacts,
            'artifact_root': archives, 'protocol_path': protocol}


def test_frozen_baseline_keeps_unavailable_cases_and_never_admits_execution(retained):
    before = {p: p.read_bytes() for p in retained['inputs_manifest'].parent.rglob('*') if p.is_file()}
    result = baseline.freeze_baseline(**retained)
    assert result == baseline.freeze_baseline(**retained)
    assert len(result['attempts']) == 72
    assert {r['arm'] for r in result['attempts']} == {'A', 'B'}
    assert len({r['attempt_id'] for r in result['attempts']}) == 72
    assert [(r['task_id'], r['arm']) for r in result['attempts'][:6]] == [
        ('T01', 'A'), ('T01', 'B'), ('T02', 'B'), ('T02', 'A'), ('T03', 'A'), ('T03', 'B')]
    assert len([r for r in result['attempts'] if r['preparation'] == 'unavailable']) == 6
    assert result['execution_allowed'] is False
    assert before == {p: p.read_bytes() for p in retained['inputs_manifest'].parent.rglob('*') if p.is_file()}


@pytest.mark.parametrize('change', ['artifact', 'source', 'extra', 'missing', 'held-out', 'limits', 'revision'])
def test_changed_or_unfair_baseline_inputs_fail_before_any_execution(retained, change):
    task = retained['inputs_manifest'].parent / 'T01'
    if change == 'artifact':
        (retained['artifact_root'] / 'baseline.whl').write_bytes(b'changed')
    elif change == 'source':
        (task / 'project/retry.py').write_bytes(b'changed')
    elif change == 'extra':
        (task / 'project/extra.py').write_bytes(b'unrecorded')
    elif change == 'missing':
        (task / 'prompt.txt').unlink()
    elif change == 'held-out':
        metadata = json.loads(retained['inputs_manifest'].read_text())
        path = task / 'native-wiki/expectations.json'
        path.write_bytes(b'held-out answers')
        metadata['records'][0]['sha256']['native-wiki/expectations.json'] = hashlib.sha256(path.read_bytes()).hexdigest()
        retained['inputs_manifest'].write_bytes(canonical_json(metadata))
    elif change == 'limits':
        metadata = json.loads(retained['protocol_path'].read_text())
        metadata['limits']['tool_rounds'] = True
        retained['protocol_path'].write_bytes(canonical_json(metadata))
    else:
        metadata = json.loads(retained['artifact_manifest'].read_text())
        metadata['source_revision'] = 'b' * 40
        retained['artifact_manifest'].write_bytes(canonical_json(metadata))
    with pytest.raises(ValueError):
        baseline.freeze_baseline(**retained)


def schedule():
    pin = identity(b'pinned input')
    return {f'T01-{arm}-{n}': {'schema_version': 'native-workflow-run-trace/v1',
        'attempt_id': f'T01-{arm}-{n}', 'task_id': 'T01', 'arm': arm, 'repetition': n,
        'execution_kind': 'external-host', 'host': 'synthetic host control', 'model': 'synthetic model',
        'settings': pin, 'admission': pin, 'bindings': {key: pin for key in
        ('task', 'protocol', 'source', 'wiki', 'oracle', 'provider', 'profile', 'original_roots')}}
        for n in range(3) for arm in 'AB'}


def retain_run(path, manifest, clock, duration, *, outcome='passed'):
    with AttemptTrace(path, manifest) as trace:
        pin = trace.blob(b'pinned input')
        trace.record('model-start', {'call_id': 'model', 'request': pin, 'context_ids': []})
        trace.record('model-end', {'call_id': 'model', 'response': pin, 'receipt': pin,
                                  'outcome': 'passed', 'input_tokens': 10, 'output_tokens': 3})
        trace.record('check-start', {'call_id': 'oracle', 'argv': ['owned-oracle'], 'cwd': '.'})
        trace.record('check-end', {'call_id': 'oracle', 'stdout': pin, 'stderr': pin, 'exit_code': 0,
                                  'compilation': 'passed', 'oracle': 'failed'})
        trace.record('cleanup', {'original_before': pin, 'original_after': pin, 'workspace_removed': True, 'receipt': pin})
        clock[0] += duration
        trace.finish(outcome)


@pytest.mark.parametrize('durations,expected', [([100, 100, 100], 3), ([100, 100, 400], 6)])
def test_sizing_uses_complete_baseline_pairs_without_certifying_model_execution(tmp_path, monkeypatch, durations, expected):
    clock = [0]
    monkeypatch.setattr('tests.native_workflow.run_trace.time.monotonic_ns', lambda: clock[0])
    planned = schedule()
    for name, manifest in planned.items():
        retain_run(tmp_path / name, manifest, clock, durations[manifest['repetition']])
    result = baseline.baseline_sampling(tmp_path, planned)
    assert result['denominator'] == 6 and result['outcomes'] == {'passed': 6}
    assert result['tasks']['T01']['complete_pairs'] == 3
    assert result['tasks']['T01']['proposed_repetitions'] == expected
    assert result['amendment_authorized'] is result['model_execution_established'] is False
    assert result['admission_independently_verified'] is False


def test_unplanned_attempt_prevents_a_sampling_proposal_without_reading_its_output(tmp_path, monkeypatch):
    clock = [0]
    monkeypatch.setattr('tests.native_workflow.run_trace.time.monotonic_ns', lambda: clock[0])
    planned = schedule()
    for name, manifest in planned.items():
        retain_run(tmp_path / name, manifest, clock, 100)
    # This can be a replacement attempt or treatment data. It must be counted,
    # but its contents must never enter the baseline-only calculation.
    (tmp_path / 'unplanned').mkdir()
    (tmp_path / 'unplanned' / 'manifest.json').write_bytes(b'not opened')
    result = baseline.baseline_sampling(tmp_path, planned)
    assert result['denominator'] == 7 and result['outcomes']['invalid-evidence'] == 1
    assert result['exact_attempt_inventory'] is result['schedule_complete'] is False
    assert result['tasks']['T01']['proposed_repetitions'] is None


def test_missing_and_failed_pairs_remain_in_the_denominator(tmp_path, monkeypatch):
    clock = [0]
    monkeypatch.setattr('tests.native_workflow.run_trace.time.monotonic_ns', lambda: clock[0])
    planned = schedule()
    for name, manifest in planned.items():
        if name == 'T01-B-2':
            continue
        retain_run(tmp_path / name, manifest, clock, 100, outcome='failed' if name == 'T01-A-1' else 'passed')
    result = baseline.baseline_sampling(tmp_path, planned)
    assert result['denominator'] == 6
    assert result['outcomes'] == {'passed': 4, 'failed': 1, 'missing-evidence': 1}
    assert result['tasks']['T01']['complete_pairs'] == 1
    assert result['tasks']['T01']['proposed_repetitions'] is None
    assert len(result['tasks']['T01']['excluded_pairs']) == 2


@pytest.mark.parametrize('change', ['treatment', 'model', 'protocol', 'source', 'provider', 'duplicate'])
def test_treatment_and_mixed_identities_are_refused_before_reading_traces(tmp_path, monkeypatch, change):
    planned = deepcopy(schedule())
    first = planned['T01-B-0']
    if change == 'treatment':
        first['arm'] = 'C'
    elif change == 'model':
        first['model'] = 'another-model'
    elif change == 'duplicate':
        first['repetition'] = 1
    else:
        first['bindings'][change] = identity(b'changed')
    def forbidden(*args, **kwargs):
        pytest.fail('Invalid baseline schedule reached trace inspection')
    monkeypatch.setattr(baseline, 'inspect_campaign', forbidden)
    with pytest.raises(ValueError):
        baseline.baseline_sampling(tmp_path, planned)
