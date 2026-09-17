"""Measure explicit layout tradeoffs in a fresh disposable Git repository."""

from __future__ import annotations

import argparse
from copy import deepcopy
import gc
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

from llm_wiki_cli.services.knowledge_packs import build_storage, open_knowledge_store


def variants(original):
    yield 'baseline', original
    def changed(*numbers):
        value = deepcopy(original)
        for number in numbers:
            key = f'storage-scale/record-{number:06d}'
            text = value['extensions'][key]
            value['extensions'][key] = ('0' if text[0] != '0' else '1') + text[1:]
        return value
    yield 'tiny-edit', changed(5)
    source = deepcopy(original)
    source['concepts'][0]['title'] += ' updated'
    yield 'one-source-projection', source
    broad = changed(5)
    del broad['extensions']['storage-scale/record-000010']
    broad['extensions']['storage-scale/inserted'] = 'new record ' * 1000
    for number in range(20, 30):
        key = f'storage-scale/record-{number:06d}'
        broad['extensions'][key] = broad['extensions'][key][::-1]
    yield 'broad-with-boundaries', broad
    inserted = deepcopy(original)
    inserted['extensions']['storage-scale/inserted'] = 'inserted record' * 10000
    yield 'insertion', inserted
    deleted = deepcopy(original)
    del deleted['extensions']['storage-scale/record-000010']
    yield 'deletion', deleted
    yield 'merged-independent-edits', changed(5, 777)
    for length in range(1, 4):
        repeated = changed(5)
        key = 'storage-scale/record-000005'
        repeated['extensions'][key] = 'f' * length + repeated['extensions'][key][length:]
        yield f'repeated-{length}', repeated


def qualify(work: Path, original, fmt, *, git_history=True):
    work.mkdir(parents=True)
    command = ['git', '-C', str(work), '-c', 'user.name=Locality Fixture',
               '-c', 'user.email=locality@example.invalid', '-c', 'commit.gpgSign=false',
               '-c', 'core.hooksPath=/dev/null', '-c', 'gc.auto=0']
    def git(*args, **kwargs):
        return subprocess.run([*command, *args], check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, **kwargs).stdout
    if git_history:
        git('init', '--initial-branch=fixture')
        assert not git('for-each-ref', '--format=%(upstream:short)', 'refs/heads/fixture').strip()
        (work / '.gitattributes').write_text('* text=auto eol=lf\n')
    previous, baseline = set(), {}
    rows = []
    for label, payload in variants(original):
        gc.collect()
        started = time.process_time_ns()
        plan = build_storage(payload, fmt)
        cpu = time.process_time_ns() - started
        files = {'.llm-wiki-knowledge.json': plan.root_bytes, **plan.objects}
        hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
        if not baseline:
            baseline = hashes
        changed = [name for name in files if hashes[name] != baseline.get(name)]
        reader = open_knowledge_store(plan.root_bytes, lambda name, _, objects=plan.objects: objects[name])
        assert reader.materialize() == payload
        del reader
        row = {'case': label, 'build_cpu_ns': cpu, 'files': len(files),
               'physical_bytes': sum(map(len, files.values())), 'changed_files': len(changed),
               'changed_bytes': sum(len(files[name]) for name in changed),
               'largest_file_bytes': max(map(len, files.values())), 'full_rebuild_equivalent': True,
               'retired_bytes': sum((work / name).stat().st_size for name in previous - files.keys())}
        for name in previous - files.keys():
            (work / name).unlink()
        for name, raw in files.items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if git_history:
            git('add', '--all')
            git('commit', '-q', '-m', label)
            with tempfile.TemporaryFile() as stream:
                subprocess.run([*command, '-c', 'pack.threads=1', 'pack-objects', '--stdout', '--revs', '--window=10', '--depth=50'],
                               input=b'HEAD\n', stdout=stream, stderr=subprocess.PIPE, check=True)
                row['git_history_pack_bytes'] = stream.tell()
        rows.append(row)
        (work.parent / (fmt + '.json')).write_text(json.dumps(rows, indent=2) + '\n')
        print(fmt, label, row['changed_bytes'], row['files'], flush=True)
        previous = set(files)
        del files, plan
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--legacy', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--formats', nargs='+', default=['packed-v3', 'packed-v4', 'packed-v3-deflate', 'packed-v4-deflate'])
    args = parser.parse_args()
    if args.work.exists():
        parser.error('work directory must be new')
    raw = args.legacy.read_bytes()
    original = json.loads(raw)
    identity = hashlib.sha256(raw).hexdigest()
    del raw
    output = {'legacy_sha256': identity, 'formats': {}}
    for fmt in args.formats:
        output['formats'][fmt] = qualify(args.work / fmt, original, fmt)
        (args.work / 'summary.json').write_text(json.dumps(output, indent=2) + '\n')


if __name__ == '__main__':
    main()
