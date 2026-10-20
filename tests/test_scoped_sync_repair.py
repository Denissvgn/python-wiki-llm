"""Scoped repair limits application, while retaining a complete global basis."""

import subprocess
from copy import deepcopy
import json
import base64
from pathlib import Path

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import knowledge_evidence as ke, scoped_sync_repair as scoped
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import knowledge_index_to_payload
from llm_wiki_cli.services.maintenance_protocol import snapshot_wiki
from llm_wiki_cli.services.maintenance_service import load_recovery_snapshot
from tests.test_sync_guard_diagnostics import _decode_command, _preview_command


_ABSENT_EXTENSION = object()


@pytest.mark.parametrize(('before', 'after', 'refused'), [
    pytest.param({'nested': [False]}, {'nested': [0]}, True, id='false-zero'),
    pytest.param({'nested': [True]}, {'nested': [1]}, True, id='true-one'),
    pytest.param({'nested': [0]}, {'nested': [False]}, True, id='zero-false'),
    pytest.param({'nested': [1]}, {'nested': [True]}, True, id='one-true'),
    pytest.param(_ABSENT_EXTENSION, None, True, id='missing-null'),
    pytest.param(None, _ABSENT_EXTENSION, True, id='null-missing'),
    pytest.param({'nested': [False]}, {'nested': [False]}, False, id='same-boolean'),
    pytest.param({'nested': [0]}, {'nested': [0]}, False, id='same-number'),
    pytest.param(None, None, False, id='same-null'),
    pytest.param(_ABSENT_EXTENSION, _ABSENT_EXTENSION, False, id='same-missing'),
])
def test_unselected_json_literals_and_presence_are_preserved(
    tmp_path, monkeypatch, capsys, before, after, refused
):
    wiki = _project(tmp_path, monkeypatch)
    original = snapshot_wiki(wiki)
    serialize = scoped.knowledge_index_to_payload
    calls = []

    def inject(value):
        # Inject only the compared JSON views; native validation, source checks
        # and publication remain real. Opaque JSON must preserve literal types.
        payload = deepcopy(serialize(value))
        candidate = before if len(calls) % 2 == 0 else after
        if candidate is _ABSENT_EXTENSION:
            payload['extensions'].pop('consumer/scoped-json', None)
        else:
            payload['extensions']['consumer/scoped-json'] = candidate
        calls.append(True)
        return payload

    monkeypatch.setattr(scoped, 'knowledge_index_to_payload', inject)
    if refused:
        with pytest.raises(SystemExit) as stopped:
            sync_cmd.run(_args('--repair-evidence', 'f000.py'))
        assert stopped.value.code == 2
        assert snapshot_wiki(wiki) == original
        assert 'global graph, custody or unselected sections changed' in capsys.readouterr().err
    else:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert len(calls) >= 2


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
@pytest.mark.parametrize('transition', [False, True])
def test_one_source_repair_preserves_other_failures_and_global_facts(tmp_path, monkeypatch, capsys, unknown_scope, cache, transition):
    from llm_wiki_cli.services import knowledge_orchestration

    with monkeypatch.context() as capture:
        if transition:
            capture.setattr(sync_cmd, '__version__', '2.5.0')
            capture.setattr(knowledge_orchestration, '__version__', '2.5.0')
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
    if transition:
        assert before.knowledge.bundle.producer.tool.version == '2.5.0'
        assert after.knowledge.bundle.producer.tool.version == knowledge_orchestration.__version__
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


@pytest.mark.parametrize('fixture_name', ['sync_guard_2_5_0.json', 'scoped_repair_2_5_0_mixed.json'])
def test_released_250_dynamic_import_repairs_after_explicit_upgrade(
    tmp_path, monkeypatch, capsys, require_prepared_diagnostics_helper, fixture_name
):
    from llm_wiki_cli.commands import upgrade_cmd, lint_cmd, ci_check_cmd

    cache = require_prepared_diagnostics_helper('typescript')
    fixture = json.loads((Path(__file__).parent / 'fixtures' / fixture_name).read_text())
    assert fixture['producer_version'] == '2.5.0'
    monkeypatch.chdir(tmp_path)
    for name, content in fixture['files'].items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(content) if fixture.get('encoding') == 'base64' else content.encode('utf-8'))
    parser = cli._build_parser()
    bindings = ['--src-dir', '.', '--wiki-dir', 'wiki',
                '--source-selection', '.llm-wiki/source-selection.json', '--helper-cache-dir', cache]
    # Storage/ownership preparation preserves the actual released evidence.
    # It is not an implicit adoption inside the scoped writer.
    upgrade_cmd.run(parser.parse_args(['upgrade', *bindings]))
    before = load_knowledge_state('wiki')
    assert before.knowledge is not None and before.manifest_basis is not None
    assert before.knowledge.bundle.producer.tool.version == '2.5.0'
    assert before.manifest_basis.evidence_baselines['modules/dyn.md'].unknown_reason == 'invalid-inventory-shape'
    original = snapshot_wiki('wiki')
    source = Path('src/dyn.mjs').read_bytes()
    repair = ['sync', *bindings, '--no-cache', '--no-plugins', '--repair-evidence', 'src/dyn.mjs']
    sync_cmd.run(parser.parse_args([*repair, '--dry-run']))
    assert snapshot_wiki('wiki') == original
    sync_cmd.run(parser.parse_args(repair))
    after = load_knowledge_state('wiki')
    assert after.knowledge is not None and after.manifest_basis is not None
    assert after.manifest_basis.evidence_baselines['modules/dyn.md'].is_known
    assert all(baseline == after.manifest_basis.evidence_baselines[page]
               for page, baseline in before.manifest_basis.evidence_baselines.items() if page != 'modules/dyn.md')
    old_state, new_state = before.manifest_basis.maintenance_state, after.manifest_basis.maintenance_state
    assert old_state is not None and new_state is not None
    assert old_state['records'].keys() == new_state['records'].keys()
    for record_id, record in old_state['records'].items():
        for history in ('acknowledgment_history', 'coordinate_history', 'target_history'):
            assert record[history] == new_state['records'][record_id][history]
        if record['current_acknowledgment_id'] is not None:
            assert new_state['records'][record_id]['status'] == 'pending'
            assert new_state['records'][record_id]['current_acknowledgment_id'] is None
            assert 'producer-incompatible' in new_state['records'][record_id]['reasons']
    assert after.knowledge.bundle.producer.tool.version != '2.5.0'
    assert source == Path('src/dyn.mjs').read_bytes()
    assert all(snapshot_wiki('wiki')[p] == content for p, content in original.items()
               if p.endswith('.md') and p not in {'modules/dyn.md', 'log.md'})
    stable = snapshot_wiki('wiki')
    sync_cmd.run(parser.parse_args(repair))
    assert snapshot_wiki('wiki') == stable
    lint_cmd.run(parser.parse_args(['lint', '--strict', *bindings, '--no-cache']))
    ci_check_cmd.run(parser.parse_args(['ci-check', '--no-report', '--format', 'json', *bindings, '--no-plugins', '--no-cache']))
    capsys.readouterr()


def test_producer_transition_cannot_discard_opaque_annotations(tmp_path, monkeypatch, capsys):
    from dataclasses import replace
    from llm_wiki_cli.services import knowledge_orchestration as orchestration

    tool = orchestration._tool_component

    def annotated(*args, **kwargs):
        component = tool(*args, **kwargs)
        return replace(component, extensions={**component.extensions, 'consumer/annotation': {'flag': False}})

    with monkeypatch.context() as capture:
        capture.setattr(orchestration, '_tool_component', annotated)
        wiki = _project(tmp_path, monkeypatch)
    original = snapshot_wiki(wiki)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py', '--force'))
    assert stopped.value.code == 2
    assert 'producer annotations or component selection changed' in capsys.readouterr().err
    assert snapshot_wiki(wiki) == original


@pytest.mark.parametrize(('before', 'after'), [(False, 0), (True, 1)])
def test_candidate_producer_json_types_match_checked_analysis(tmp_path, monkeypatch, capsys, before, after):
    from dataclasses import replace
    from llm_wiki_cli.services import knowledge_orchestration as orchestration

    tool = orchestration._tool_component

    def annotated(*args, **kwargs):
        component = tool(*args, **kwargs)
        return replace(component, extensions={**component.extensions, 'consumer/flag': before})

    monkeypatch.setattr(orchestration, '_tool_component', annotated)
    wiki = _project(tmp_path, monkeypatch)
    original = snapshot_wiki(wiki)
    validate = scoped.validate_knowledge_artifacts

    def changed(**kwargs):
        checked = validate(**kwargs)
        producer = checked.knowledge.bundle.producer
        altered = replace(producer.tool, extensions={**producer.tool.extensions, 'consumer/flag': after})
        return replace(checked, knowledge=replace(checked.knowledge, bundle=replace(
            checked.knowledge.bundle, producer=replace(producer, tool=altered))))

    monkeypatch.setattr(scoped, 'validate_knowledge_artifacts', changed)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert stopped.value.code == 2
    assert 'candidate producer differs from the checked current analysis' in capsys.readouterr().err
    assert snapshot_wiki(wiki) == original


@pytest.mark.parametrize('changed', ['syntax', 'issuer'])
def test_unselected_executable_facts_and_current_issuer_are_protected(tmp_path, monkeypatch, capsys, changed):
    from llm_wiki_cli.services.implementation_evidence import IMPLEMENTATION_KEY

    wiki = _project(tmp_path, monkeypatch)
    original = snapshot_wiki(wiki)
    serialize = scoped.knowledge_index_to_payload
    calls = []

    def altered(knowledge):
        payload = deepcopy(serialize(knowledge))
        if calls:
            concept = next(c for c in payload['concepts'] if c['locator'] == 'llm-wiki://entities/Item1')
            evidence = concept['extensions'][IMPLEMENTATION_KEY]
            if changed == 'syntax':
                evidence['executable_hash'] = 'sha256:' + '0' * 64
            else:
                evidence['producer']['analysis_compatibility_hash'] = 'sha256:' + '0' * 64
        calls.append(True)
        return payload

    monkeypatch.setattr(scoped, 'knowledge_index_to_payload', altered)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py', '--force'))
    assert stopped.value.code == 2
    expected = 'unselected concept facts changed' if changed == 'syntax' else 'candidate executable issuer differs'
    assert expected in capsys.readouterr().err
    assert snapshot_wiki(wiki) == original


@pytest.mark.parametrize('source', ['f000.py', 'f001.py'])
def test_changed_known_observation_cannot_inherit_current_producer(tmp_path, monkeypatch, capsys, source):
    from dataclasses import replace

    wiki = _project(tmp_path, monkeypatch)
    original = snapshot_wiki(wiki)
    from llm_wiki_cli.services import knowledge_orchestration as evaluate
    build = evaluate.build_runtime_live_evaluation

    def changed(inputs):
        live = build(inputs)
        bases = dict(live.concept_bases)
        for locator, basis in bases.items():
            if basis.scope == 'entity' and basis.source_path == source:
                bases[locator] = replace(basis, concept_observation_hash='sha256:' + '0' * 64)
        return replace(live, concept_bases=bases)

    monkeypatch.setattr(evaluate, 'build_runtime_live_evaluation', changed)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py', '--force'))
    assert stopped.value.code == 2
    assert 'known observation changed despite unchanged source' in capsys.readouterr().err
    assert snapshot_wiki(wiki) == original


@pytest.mark.parametrize('kind', ['source', 'wiki', 'missing-page', 'unowned', 'malformed'])
def test_mixed_or_unqualified_inputs_refuse_without_active_writes(tmp_path, monkeypatch, capsys, kind):
    wiki = _project(tmp_path, monkeypatch)
    path = 'f000.py'
    if kind == 'source':
        (tmp_path / 'src/f001.py').write_bytes(b'class Changed:\n    pass\n')
    elif kind == 'wiki':
        (wiki / 'modules/f001.md').write_bytes((wiki / 'modules/f001.md').read_bytes() + b'\nUser edit\n')
    elif kind == 'missing-page':
        (wiki / 'entities/Item0.md').unlink()
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
@pytest.mark.parametrize('transition', [False, True])
def test_scoped_evidence_inputs_keep_count_and_ratio_review(tmp_path, monkeypatch, capsys, count, selected, transition):
    from llm_wiki_cli.services import knowledge_orchestration

    with monkeypatch.context() as capture:
        if transition:
            capture.setattr(sync_cmd, '__version__', '2.5.0')
            capture.setattr(knowledge_orchestration, '__version__', '2.5.0')
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


@pytest.mark.parametrize('page', ['modules/f000.md', 'modules/f001.md', 'log.md'])
def test_markdown_mutation_at_publication_checkpoint_is_refused(tmp_path, monkeypatch, page):
    from llm_wiki_cli.services.knowledge_artifacts import CommitStage

    wiki = _project(tmp_path, monkeypatch)
    before = snapshot_wiki(wiki)
    finalize = sync_cmd.finalize_runtime_knowledge
    triggered = []
    def checked(inputs, *, dry_run=False):
        def mutation(stage):
            if stage is CommitStage.KNOWLEDGE_OBJECTS_WRITTEN:
                triggered.append(True)
                target = wiki / page
                target.write_bytes(target.read_bytes() + b'\nExternal publication edit\n')
        return finalize(inputs, dry_run=dry_run, fault_injector=None if dry_run else mutation)
    monkeypatch.setattr(sync_cmd, 'finalize_runtime_knowledge', checked)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert stopped.value.code == 2 and triggered == [True]
    assert (wiki / '.llm-wiki-manifest.json').read_bytes() == before['.llm-wiki-manifest.json']


def test_selected_markdown_after_render_must_match_isolated_preflight(tmp_path, monkeypatch):
    wiki = _project(tmp_path, monkeypatch)
    before = snapshot_wiki(wiki)
    apply = sync_cmd._apply_prepared_sync
    triggered = []
    def race(options, prepared):
        result = apply(options, prepared)
        if options.wiki_dir.resolve() == wiki.resolve():
            triggered.append(True)
            page = wiki / 'modules/f000.md'
            page.write_bytes(page.read_bytes().replace(b'Preserve this authored explanation.', b'External selected edit.'))
        return result
    monkeypatch.setattr(sync_cmd, '_apply_prepared_sync', race)
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(_args('--repair-evidence', 'f000.py'))
    assert stopped.value.code == 2 and triggered == [True]
    assert (wiki / '.llm-wiki-manifest.json').read_bytes() == before['.llm-wiki-manifest.json']
