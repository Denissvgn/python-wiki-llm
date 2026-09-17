"""Freeze baseline inputs and inspect sample sizing outside the provider runtime.

This tooling never launches a model or a target command and never admits a host.
Structural trace validation is deliberately insufficient for execution approval.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
from typing import Any

from llm_wiki_cli.services.knowledge_storage_io import StorageReadSession, read_guarded, _absolute_path
from llm_wiki_cli.services.validation import is_portable_relative_path
from tests.native_workflow.oracles import verify_corpus
from tests.native_workflow.run_trace import identity, inspect_campaign, validate_manifest
from tests.provider_conformance.model import canonical_json

PLAN_SCHEMA = 'native-workflow-baseline-plan/v1'
MAX_FILES = 10_000
MAX_WORKSPACE_BYTES = 67_108_864
MAX_METADATA_BYTES = 8_388_608
_HIDDEN = {'expectations.json', 'oracle.py', 'oracles.py', 'prior-runs', 'patches', 'sessions'}


class BaselineError(ValueError):
    """A frozen input or baseline-only observation does not meet its contract."""


def _json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = read_guarded(path, MAX_METADATA_BYTES).content

    def unique(pairs):
        result = {}
        for name, value in pairs:
            if name in result:
                raise BaselineError('Duplicate metadata field')
            result[name] = value
        return result

    value = json.loads(raw, object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise BaselineError('Metadata must be an object')
    canonical_json(value)  # Reject nonfinite values before constructing identities.
    return value, raw


def _hash(value: Any) -> str:
    if (not isinstance(value, str) or len(value) != 64
            or any(c not in '0123456789abcdef' for c in value)):
        raise BaselineError('Expected a lowercase SHA-256 digest')
    return value


def _names(root: Path) -> set[str]:
    root = _absolute_path(root)
    pending, names, entries = [root], set(), 0
    while pending:
        with os.scandir(pending.pop()) as children:
            for child in children:
                entries += 1
                if entries > MAX_FILES:
                    raise BaselineError('Input inventory exceeds its entry bound')
                if child.is_symlink() or getattr(child.stat(follow_symlinks=False), 'st_file_attributes', 0) & 0x400:
                    raise BaselineError('Input inventory contains a redirected path')
                if child.is_dir(follow_symlinks=False):
                    pending.append(Path(child.path))
                elif child.is_file(follow_symlinks=False):
                    names.add(Path(child.path).relative_to(root).as_posix())
                else:
                    raise BaselineError('Input inventory contains a special file')
    return names


def _verify_task(root: Path, record: dict, task: dict) -> dict:
    expected = record.get('sha256')
    if (not isinstance(expected, dict) or len(expected) > MAX_FILES
            or record.get('oracle_visible') is not False or record.get('same_bytes_in_all_arms') is not True
            or record.get('source_root') != 'project' or record.get('native_wiki_root') != 'native-wiki'
            or record.get('authored_wiki_root') != 'project/wiki'
            or record.get('visibility') != ['project/**', 'native-wiki/**', 'prompt.txt']
            or record.get('preparation') not in {'prepared', 'unavailable', 'prepared-with-declared-corruption'}):
        raise BaselineError('Invalid prepared task visibility or inventory')
    source_inputs = {}
    for name, digest in expected.items():
        if not isinstance(name, str) or not is_portable_relative_path(name):
            raise BaselineError('Prepared input path must be portable and relative')
        parts = Path(name).parts
        if any(part.casefold() in _HIDDEN for part in parts):
            raise BaselineError('Held-out material cannot enter an arm workspace')
        if name != 'prompt.txt' and parts[0] not in {'project', 'native-wiki'}:
            raise BaselineError('Prepared input is outside the visible namespaces')
        _hash(digest)
        if parts[0] != 'native-wiki':
            source_inputs[name] = digest
    if source_inputs != task['input_sha256']:
        raise BaselineError('Prepared project/prompt differs from the frozen corpus')
    if _names(root) != set(expected):
        raise BaselineError('Prepared task has missing or unrecorded files')
    session = StorageReadSession(root, max_bytes=2 * MAX_WORKSPACE_BYTES)
    total = 0
    with session.phase():
        for name, expected_hash in sorted(expected.items()):
            raw = session.read(name, MAX_WORKSPACE_BYTES - total)
            total += len(raw)
            if hashlib.sha256(raw).hexdigest() != expected_hash:
                raise BaselineError('Prepared task bytes differ from their commitment')
    session.recheck()
    if _names(root) != set(expected):
        raise BaselineError('Prepared task membership changed during validation')
    return {'task_id': task['id'], 'language': task['language'], 'bytes': total,
            'files': dict(sorted(expected.items())), 'inputs_id': identity(canonical_json(expected)),
            'source_id': identity(canonical_json(source_inputs)),
            'wiki_id': identity(canonical_json({n: h for n, h in expected.items() if n.startswith('native-wiki/')})),
            'prompt_id': 'sha256:' + expected['prompt.txt'],
            'preparation': record['preparation'], 'reason': record.get('reason')}


def freeze_baseline(*, corpus_root: Path, inputs_manifest: Path, artifact_manifest: Path,
                    artifact_root: Path, protocol_path: Path) -> dict[str, Any]:
    """Validate retained inputs and emit an A/B schedule, without creating arm workspaces."""
    corpus = verify_corpus(corpus_root)
    corpus_raw = read_guarded(corpus_root / 'corpus.json', MAX_METADATA_BYTES).content
    protocol, protocol_raw = _json(protocol_path)
    inputs, inputs_raw = _json(inputs_manifest)
    artifacts, artifacts_raw = _json(artifact_manifest)
    if (protocol.get('schema_version') != 'native-workflow-analysis/v1'
            or protocol.get('manifest_sha256') != hashlib.sha256(corpus_raw).hexdigest()
            or type(protocol.get('seed')) is not int or not 0 <= protocol['seed'] < 2**32
            or protocol.get('arm_order') != 'Latin square A,B,C; B,C,A; C,A,B by task and repetition'
            or type(protocol.get('repetitions')) is not int or protocol['repetitions'] != 3):
        raise BaselineError('Unsupported or unbound frozen baseline schedule')
    maxima = {'seconds_per_run': 600, 'tool_rounds': 24, 'context_tokens': 32000,
              'workspace_bytes': MAX_WORKSPACE_BYTES, 'concurrent_runs': 1}
    limits = protocol.get('limits')
    if (not isinstance(limits, dict) or set(limits) != set(maxima)
            or any(type(limits[k]) is not int or not 0 < limits[k] <= bound for k, bound in maxima.items())):
        raise BaselineError('Protocol limits must retain the bounded baseline envelope')
    if (inputs.get('schema_version') != 'native-workflow-baseline-inputs/v1'
            or inputs.get('model_execution') is not False
            or artifacts.get('schema_version') != 'native-workflow-baseline/v1'
            or inputs.get('provider_revision') != artifacts.get('source_revision')):
        raise BaselineError('Baseline provider/input provenance differs')
    archive_hashes = artifacts.get('artifacts')
    if not isinstance(archive_hashes, dict) or len(archive_hashes) != 2:
        raise BaselineError('Retain exactly one baseline wheel and source archive')
    kinds = set()
    for name, digest in archive_hashes.items():
        if not isinstance(name, str) or not is_portable_relative_path(name):
            raise BaselineError('Baseline artifact path must be relative')
        kind = 'wheel' if name.endswith('.whl') else 'sdist' if name.endswith('.tar.gz') else None
        if kind is None or kind in kinds:
            raise BaselineError('Baseline wheel/source archive inventory differs')
        kinds.add(kind)
        raw = read_guarded(artifact_root / name, 95 * 1024 * 1024).content
        if hashlib.sha256(raw).hexdigest() != _hash(digest):
            raise BaselineError('Retained baseline artifact changed')
    records = inputs.get('records')
    if (not isinstance(records, list) or len(records) != len(corpus['tasks'])
            or any(not isinstance(r, dict) for r in records)
            or [r.get('task') for r in records] != [t['id'] for t in corpus['tasks']]):
        raise BaselineError('Prepared task inventory differs from the frozen corpus')
    tasks = [_verify_task(inputs_manifest.parent / task['id'], record, task)
             for task, record in zip(corpus['tasks'], records)]
    if any(task['bytes'] > limits['workspace_bytes'] for task in tasks):
        raise BaselineError('Prepared task exceeds the declared workspace limit')
    attempts = []
    for repetition in range(protocol['repetitions']):
        for number, task in enumerate(tasks):
            # Remove C from the predeclared Latin-square row, retaining A/B order.
            row = ('ABC', 'BCA', 'CAB')[(number + repetition) % 3]
            for arm in row.replace('C', ''):
                attempts.append({'attempt_id': f"{task['task_id']}-{arm}-{repetition}",
                                 'task_id': task['task_id'], 'arm': arm, 'repetition': repetition,
                                 'inputs_id': task['inputs_id'], 'preparation': task['preparation']})
    result = {'schema_version': PLAN_SCHEMA, 'source_revision': artifacts['source_revision'],
              'corpus_id': identity(corpus_raw), 'protocol_id': identity(protocol_raw),
              'prepared_inputs_id': identity(inputs_raw), 'artifact_manifest_id': identity(artifacts_raw),
              'artifacts': dict(sorted(archive_hashes.items())), 'tasks': tasks, 'attempts': attempts,
              'limits': limits, 'execution_allowed': False,
              'required_before_execution': ['approved host/model/settings', 'verified runner admission',
                                            'frozen resource and cost authorization'],
              'scope': 'baseline-input-integrity-and-schedule; no execution or admission claim'}
    result['plan_id'] = identity(canonical_json(result))
    return result


def baseline_sampling(directory: Path, schedule: dict[str, dict]) -> dict[str, Any]:
    """Propose sizes from complete A/B trace pairs; never certify host or model evidence.

    The explicit rule uses the larger per-arm population latency coefficient of
    variation. It must be frozen before viewing treatment outcomes.
    """
    if not isinstance(schedule, dict) or not 0 < len(schedule) <= MAX_FILES:
        raise BaselineError('A frozen baseline schedule is required')
    strata: dict[str, dict[tuple[str, int], str]] = {}
    host_basis = set()
    task_bases: dict[str, set[tuple]] = {}
    providers = set()
    for name, raw in schedule.items():
        manifest = validate_manifest(raw)
        if manifest['arm'] not in {'A', 'B'}:
            raise BaselineError('Treatment cannot enter baseline-only sizing')
        if manifest['execution_kind'] != 'external-host':
            raise BaselineError('Replay cannot supply model baseline observations')
        if manifest['repetition'] not in {0, 1, 2}:
            raise BaselineError('Sizing requires the three predeclared baseline repetitions')
        members = strata.setdefault(manifest['task_id'], {})
        key = manifest['arm'], manifest['repetition']
        if key in members:
            raise BaselineError('Duplicate baseline task/arm/repetition')
        members[key] = name
        host_basis.add((manifest['host'], manifest['model'], manifest['settings'], manifest['admission'],
                        manifest['bindings']['protocol']))
        task_bases.setdefault(manifest['task_id'], set()).add(tuple(manifest['bindings'][key]
            for key in ('task', 'source', 'wiki', 'oracle', 'original_roots')))
        if manifest['arm'] == 'B':
            providers.add((manifest['bindings']['provider'], manifest['bindings']['profile']))
    if len(host_basis) != 1:
        raise BaselineError('Baseline host/model/settings/admission strata differ')
    if any(len(bases) != 1 for bases in task_bases.values()) or len(providers) != 1:
        raise BaselineError('Baseline inputs or retained provider differ between pairs')
    required = {(arm, n) for arm in 'AB' for n in range(3)}
    if any(set(members) != required for members in strata.values()):
        raise BaselineError('Schedule must retain every A/B baseline pair')
    report = inspect_campaign(directory, expected_attempts=schedule)
    exact_inventory = report['denominator'] == len(schedule)
    by_id = {r['attempt_id']: r for r in report['attempts']}
    results = {}
    for task, members in sorted(strata.items()):
        latencies: dict[str, list[int]] = {'A': [], 'B': []}
        excluded = []
        for repetition in range(3):
            pair = {arm: by_id.get(schedule[members[(arm, repetition)]]['attempt_id']) for arm in 'AB'}
            bad = {arm: None if value is None else value['outcome'] for arm, value in pair.items()
                   if value is None or value['outcome'] != 'passed'}
            if bad:
                excluded.append({'repetition': repetition, 'outcomes': bad})
                continue
            for arm, value in pair.items():
                assert value is not None
                latencies[arm].append(value['work']['elapsed_ns'])
        cv = {}
        for arm, times in latencies.items():
            mean = statistics.fmean(times) if times else 0
            cv[arm] = statistics.pstdev(times) / mean if mean > 0 and len(times) == 3 else None
        sufficient = exact_inventory and not excluded and all(value is not None and math.isfinite(value) for value in cv.values())
        results[task] = {'complete_pairs': len(latencies['A']), 'excluded_pairs': excluded,
                         'latency_ns': latencies, 'population_latency_cv': cv,
                         'proposed_repetitions': (6 if any(value > 0.25 for value in cv.values()) else 3) if sufficient else None,
                         'disposition': 'proposal-requires-host-verification' if sufficient else 'insufficient-baseline'}
    return {'schema_version': 'native-workflow-baseline-sizing/v1',
            'schedule_id': identity(canonical_json(schedule)), 'rule': 'max-arm-population-latency-cv/v1',
            'denominator': report['denominator'], 'outcomes': dict(Counter(r['outcome'] for r in report['attempts'])),
            'schedule_complete': report['schedule_complete'], 'exact_attempt_inventory': exact_inventory,
            'tasks': results, 'model_execution_established': False, 'admission_independently_verified': False,
            'amendment_authorized': False, 'scope': 'structurally-validated-baseline-observations-only'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prepare = sub.add_parser('freeze')
    for name in ('corpus-root', 'inputs-manifest', 'artifact-manifest', 'artifact-root', 'protocol-path'):
        prepare.add_argument('--' + name, type=Path, required=True)
    sample = sub.add_parser('sample')
    sample.add_argument('--directory', type=Path, required=True)
    sample.add_argument('--schedule', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = vars(parser.parse_args())
    output = args.pop('output')
    action = args.pop('action')
    result = freeze_baseline(**args) if action == 'freeze' else baseline_sampling(args['directory'], _json(args['schedule'])[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(canonical_json(result))


if __name__ == '__main__':
    main()
