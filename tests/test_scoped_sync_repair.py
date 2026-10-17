"""Scoped repair limits application, while retaining a complete global basis."""

import subprocess

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import knowledge_evidence as ke, scoped_sync_repair as scoped
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import knowledge_index_to_payload
from llm_wiki_cli.services.maintenance_protocol import snapshot_wiki
from llm_wiki_cli.services.maintenance_service import load_recovery_snapshot
from tests.test_sync_guard_diagnostics import _decode_command, _preview_command


def _args(*extra):
    return cli._build_parser().parse_args([
        'sync', '--src-dir', 'src', '--wiki-dir', 'wiki', '--no-cache', '--no-plugins', *extra,
    ])


def _project(tmp_path, monkeypatch, *, count=2, unknown_scope='module'):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'src').mkdir()
    for i in range(count):
        (tmp_path / 'src' / f'f{i:03}.py').write_bytes(
            f'class Item{i}:\n    def value(self):\n        return {i}\n'.encode()
        )
    with monkeypatch.context() as patch:
        def reject(*_):
            raise ke._InventoryNormalizationError('invalid-inventory-shape')
        patch.setattr(ke, f'_normalize_{unknown_scope}_observation', reject)
        bootstrap_cmd.run(cli._build_parser().parse_args([
            'bootstrap', '--src-dir', 'src', '--wiki-dir', 'wiki',
        ]))
        for name in ['modules/f000.md', 'entities/Item0.md']:
            page = tmp_path / 'wiki' / name
            page.write_bytes(page.read_bytes().replace(b'## Description', b'## Description\n\nPreserve this authored explanation.', 1))
        # Anchor prose under the controlled prior rejection, preserving the
        # unknown basis. This is injected evidence, not a released fixture.
        sync_cmd.run(_args())
    return tmp_path / 'wiki'


@pytest.mark.parametrize('unknown_scope', ['module', 'entity'])
@pytest.mark.parametrize('cache', [False, True])
def test_one_source_repair_preserves_other_failures_and_global_facts(tmp_path, monkeypatch, capsys, unknown_scope, cache):
    wiki = _project(tmp_path, monkeypatch, unknown_scope=unknown_scope)
    before = load_knowledge_state(wiki)
    assert before.knowledge is not None and before.manifest_basis is not None
    original = snapshot_wiki(wiki)
    source = {p.name: p.read_bytes() for p in (tmp_path / 'src').iterdir()}
    arguments = ['--repair-evidence', 'f000.py']
    args = _args(*arguments)
    if cache:
        args.no_cache = False
        args.cache_dir = str(tmp_path / 'inventory-cache')
    sync_cmd.run(replace_args(args, dry_run=True))
    preview = capsys.readouterr().out
    assert 'full analysis used 2 inventory file(s)' in preview
    assert '0 new, 0 changed, 0 metadata-only' in preview
    assert 'evidence-refresh-additional=1' in preview
    assert snapshot_wiki(wiki) == original
    sync_cmd.run(args)
    after = load_knowledge_state(wiki)
    assert after.knowledge is not None and after.manifest_basis is not None
    target = 'modules/f000.md' if unknown_scope == 'module' else 'entities/Item0.md'
    other = 'modules/f001.md' if unknown_scope == 'module' else 'entities/Item1.md'
    assert after.manifest_basis.evidence_baselines[target].is_known
    assert after.manifest_basis.evidence_baselines[other] == before.manifest_basis.evidence_baselines[other]
    assert not after.manifest_basis.evidence_baselines[other].is_known
    assert before.manifest_basis.maintenance_state is not None and after.manifest_basis.maintenance_state is not None
    for key, row in before.manifest_basis.maintenance_state['observations'].items():
        if row['coordinate']['source_path'] != 'f000.py':
            assert row == after.manifest_basis.maintenance_state['observations'][key]
            assert before.manifest_basis.maintenance_state['records'][key] == after.manifest_basis.maintenance_state['records'][key]
    left, right = knowledge_index_to_payload(before.knowledge), knowledge_index_to_payload(after.knowledge)
    for old in left['concepts']:
        path = old['document']['canonical_path']
        if path not in {'modules/f000.md', 'entities/Item0.md', 'log.md'}:
            assert old == next(c for c in right['concepts'] if c['locator'] == old['locator'])
    assert left['extensions']['llm-wiki/typed-graph-v1'] == right['extensions']['llm-wiki/typed-graph-v1']
    for page in ['modules/f000.md', 'entities/Item0.md']:
        assert 'Preserve this authored explanation.' in (wiki / page).read_text()
    assert source == {p.name: p.read_bytes() for p in (tmp_path / 'src').iterdir()}
    # Repeat is an active-wiki no-op, even with another pending invalid source.
    stable = snapshot_wiki(wiki)
    sync_cmd.run(args)
    assert snapshot_wiki(wiki) == stable


def replace_args(args, **changes):
    from argparse import Namespace
    return Namespace(**(vars(args) | changes))


@pytest.mark.parametrize('kind', ['source', 'wiki', 'missing-page', 'producer', 'unowned', 'malformed'])
def test_mixed_or_unqualified_inputs_refuse_without_active_writes(tmp_path, monkeypatch, capsys, kind):
    wiki = _project(tmp_path, monkeypatch)
    path = 'f000.py'
    if kind == 'source':
        (tmp_path / 'src/f001.py').write_bytes(b'class Changed:\n    pass\n')
    elif kind == 'wiki':
        (wiki / 'modules/f001.md').write_bytes((wiki / 'modules/f001.md').read_bytes() + b'\nUser edit\n')
    elif kind == 'missing-page':
        (wiki / 'entities/Item0.md').unlink()
    elif kind == 'producer':
        monkeypatch.setattr(sync_cmd, '__version__', '9.9.9')
    elif kind == 'unowned':
        path = 'not-owned.py'
    elif kind == 'malformed':
        monkeypatch.setattr(ke, '_normalize_module_observation', lambda *_: (_ for _ in ()).throw(ke._InventoryNormalizationError('invalid-inventory-shape')))
    before = snapshot_wiki(wiki)
    capsys.readouterr()
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', path, '--force'))
    assert stopped.value.code == 2
    assert 'Scoped evidence repair' in capsys.readouterr().err
    assert snapshot_wiki(wiki) == before


@pytest.mark.parametrize('path', ['../f000.py', '/tmp/f000.py', r'src\f000.py', './f000.py', 'f000.py\n', 'f000.py\x0a'])
def test_paths_are_canonical_source_coordinates(path):
    with pytest.raises(SystemExit) as stopped:
        sync_cmd._sync_run_options_from_args(_args('--repair-evidence', path))
    assert stopped.value.code == 2


@pytest.mark.parametrize('mutation', ['source', 'wiki', 'selection', 'helper'])
def test_changes_after_isolated_preflight_invalidate_apply(tmp_path, monkeypatch, mutation):
    wiki = _project(tmp_path, monkeypatch)
    original = sync_cmd._run_sync_dry_run
    before = snapshot_wiki(wiki)
    triggered = []
    def race(*args, **kwargs):
        original(*args, **kwargs)
        triggered.append(True)
        if mutation == 'source':
            (tmp_path / 'src/f001.py').write_bytes(b'class Race:\n    pass\n')
        elif mutation == 'wiki':
            (wiki / 'modules/f001.md').write_bytes(before['modules/f001.md'] + b'\nExternal edit\n')
        elif mutation == 'selection':
            (tmp_path / 'src/.gitignore').write_bytes(b'f001.py\n')
        else:
            monkeypatch.setattr(scoped, '_recapture', lambda *a, **kw: {})
    monkeypatch.setattr(sync_cmd, '_run_sync_dry_run', race)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert stopped.value.code == 2
    assert triggered == [True]
    after = snapshot_wiki(wiki)
    if mutation == 'wiki':
        before['modules/f001.md'] += b'\nExternal edit\n'
    assert after == before


def test_out_of_scope_changes_in_staging_are_not_silently_admitted(tmp_path, monkeypatch):
    wiki = _project(tmp_path, monkeypatch)
    before = snapshot_wiki(wiki)
    apply = sync_cmd._apply_prepared_sync
    def tamper(options, prepared):
        result = apply(options, prepared)
        if options.wiki_dir.resolve() != wiki.resolve():
            page = options.wiki_dir / 'modules/f001.md'
            page.write_bytes(page.read_bytes() + b'\nUnexpected global change\n')
        return result
    monkeypatch.setattr(sync_cmd, '_apply_prepared_sync', tamper)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert stopped.value.code == 2
    assert snapshot_wiki(wiki) == before


def test_publication_race_preserves_existing_complete_recovery(tmp_path, monkeypatch):
    wiki = _project(tmp_path, monkeypatch)
    before = snapshot_wiki(wiki)
    apply = sync_cmd._apply_prepared_sync
    triggered = []
    def race(options, prepared):
        result = apply(options, prepared)
        if options.wiki_dir.resolve() == wiki.resolve():
            triggered.append(True)
            (tmp_path / 'src/f001.py').write_bytes(b'class Race:\n    pass\n')
        return result
    monkeypatch.setattr(sync_cmd, '_apply_prepared_sync', race)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert stopped.value.code == 2
    assert triggered == [True]
    assert (wiki / '.llm-wiki-manifest.json').read_bytes() == before['.llm-wiki-manifest.json']
    recovered = []
    for metadata in (tmp_path / '.llm-wiki-maintenance-recovery').rglob('maintenance-recovery.json'):
        _, files, _ = load_recovery_snapshot(metadata.parent, allow_captured_preimage=True)
        recovered.append(files)
    assert before in recovered


@pytest.mark.parametrize(('count', 'selected'), [(51, 51), (10, 4)])
def test_scoped_evidence_inputs_keep_count_and_ratio_review(tmp_path, monkeypatch, capsys, count, selected):
    wiki = _project(tmp_path, monkeypatch, count=count)
    before = snapshot_wiki(wiki)
    capsys.readouterr()
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', *(f'f{i:03}.py' for i in range(selected))))
    assert stopped.value.code == 1
    diagnostic = capsys.readouterr().err
    assert f'evidence-refresh-additional={selected}' in diagnostic
    assert '--repair-evidence' in diagnostic
    assert snapshot_wiki(wiki) == before


def test_helper_mutation_at_publication_checkpoint_is_refused(tmp_path, monkeypatch):
    from llm_wiki_cli.services.knowledge_artifacts import CommitStage

    wiki = _project(tmp_path, monkeypatch)
    before = snapshot_wiki(wiki)
    finalize = sync_cmd.finalize_runtime_knowledge
    triggered = []
    def checked(inputs, *, dry_run=False):
        def mutation(stage):
            if stage is CommitStage.KNOWLEDGE_OBJECTS_WRITTEN:
                triggered.append(True)
                monkeypatch.setattr(scoped, '_recapture', lambda *a, **kw: {})
        return finalize(inputs, dry_run=dry_run, fault_injector=None if dry_run else mutation)
    monkeypatch.setattr(sync_cmd, 'finalize_runtime_knowledge', checked)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert stopped.value.code == 2 and triggered == [True]
    assert (wiki / '.llm-wiki-manifest.json').read_bytes() == before['.llm-wiki-manifest.json']


def test_preview_command_retains_scope_and_caller_bindings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    arguments = _args('--repair-evidence=-a.py', '--repair-evidence', 'dir/a space.py', 'b.py', '--cache-dir', 'cache')
    arguments.no_cache = False
    options = sync_cmd._sync_run_options_from_args(arguments)
    hint = sync_cmd._sync_preview_hint(options)
    argv = _decode_command(_preview_command(hint))
    decoded = sync_cmd._sync_run_options_from_args(cli._build_parser().parse_args(argv[1:]))
    assert decoded.repair_paths == options.repair_paths
    assert decoded.source_selection == options.source_selection
    assert decoded.src_dir == options.src_dir and decoded.helper_cache_dir == options.helper_cache_dir
    assert not decoded.force and decoded.dry_run


def test_new_git_revision_keeps_source_and_repository_identity(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True)
    git('init', '-q')
    git('config', 'user.name', 'Scoped fixture')
    git('config', 'user.email', 'fixture@example.invalid')
    git('commit', '--allow-empty', '-qm', 'Initial fixture')
    wiki = _project(tmp_path, monkeypatch)
    before = load_knowledge_state(wiki)
    git('commit', '--allow-empty', '-qm', 'Unrelated revision')
    sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    after = load_knowledge_state(wiki)
    assert before.knowledge is not None and after.knowledge is not None
    assert after.knowledge.bundle.repository.identity == before.knowledge.bundle.repository.identity
    assert after.knowledge.bundle.repository.evaluated_revision != before.knowledge.bundle.repository.evaluated_revision
    assert after.manifest_basis is not None
    assert after.manifest_basis.evidence_baselines['modules/f000.md'].is_known


@pytest.mark.parametrize('missing', ['.llm-wiki-manifest.json', '.llm-wiki-knowledge.json'])
def test_missing_authority_never_bootstraps_scoped_repair(tmp_path, monkeypatch, missing):
    wiki = _project(tmp_path, monkeypatch)
    (wiki / missing).unlink()
    before = snapshot_wiki(wiki)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py', '--force'))
    assert stopped.value.code != 0
    assert snapshot_wiki(wiki) == before


def test_symlinked_requested_source_cannot_escape_selection(tmp_path, monkeypatch):
    wiki = _project(tmp_path, monkeypatch)
    (tmp_path / 'outside.py').write_bytes((tmp_path / 'src/f000.py').read_bytes())
    (tmp_path / 'src/f000.py').unlink()
    (tmp_path / 'src/f000.py').symlink_to(tmp_path / 'outside.py')
    before = snapshot_wiki(wiki)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py', '--force'))
    assert stopped.value.code != 0
    assert snapshot_wiki(wiki) == before
