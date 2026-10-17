"""Broad-sync diagnosis must explain the owning plan without approving it."""
from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import re
import shlex

import pytest

from llm_wiki_cli import cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services.extraction_service import InventoryResult
from llm_wiki_cli.services.infrastructure_sync import InfrastructureSyncPlan
from llm_wiki_cli.services.knowledge_evidence import normalize_module_observation
from llm_wiki_cli.services.sync_analysis import SyncDiff, compute_sync_diff
from llm_wiki_cli.services.sync_manifest import SourceSelectionPruneResult, SyncManifest


def _infrastructure(**changes):
    return replace(InfrastructureSyncPlan(
        inventory={}, prior_sources={}, current_sources={}, new_sources=(),
        changed_sources=(), unchanged_sources=(), removed_sources=(), moved_sources={},
        unsupported_yaml=(), discovery_roots=(), next_state={}, deselection_only_state={},
        state_changed=False, deselection_state_changed=False,
    ), **changes)


def _options(*args, no_cache=True):
    return sync_cmd._sync_run_options_from_args(cli._build_parser().parse_args([
        'sync', '--src-dir', '.', '--wiki-dir', 'wiki',
        *(['--no-cache'] if no_cache else []), *args,
    ]))


def _files(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def _preview_command(hint):
    return hint.split('): ', 1)[1].splitlines()[0]


def _decode_command(command):
    if not command.startswith('& '):
        return shlex.split(command)
    # Decode literal PowerShell arguments; native backslashes stay literal.
    remaining = command[2:]
    result = []
    while remaining:
        match = re.match(r"'((?:[^']|'')*)'(?: |$)", remaining)
        assert match is not None, remaining
        value = match.group(1)
        for quote in "'‘’‚‛":
            value = value.replace(quote * 2, quote)
        result.append(value)
        remaining = remaining[match.end():]
    return result


def _refusal(options, diff, capsys, *, source_diff=None, count=300, infrastructure=None, **kwargs):
    manifest = SyncManifest(sources={f'src/f{i:03}.py': {} for i in range(count)})
    with pytest.raises(SystemExit) as stopped:
        sync_cmd._exit_if_large_unforced_diff(
            options, diff, manifest, InventoryResult({}, {}),
            infrastructure if infrastructure is not None else _infrastructure(),
            source_diff=source_diff, **kwargs,
        )
    assert stopped.value.code == 1
    return capsys.readouterr().err


def test_released_unknown_fixture_separates_source_diff_from_generator_refresh(tmp_path):
    fixture = json.loads((Path(__file__).parent / 'fixtures/sync_guard_2_5_0.json').read_text())
    assert fixture['producer_version'] == '2.5.0'
    for name, content in fixture['files'].items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode('utf-8'))
    before = _files(tmp_path)
    manifest = SyncManifest.load(tmp_path / 'wiki')
    assert manifest is not None
    assert manifest.evidence_baselines['modules/dyn.md'].unknown_reason == 'invalid-inventory-shape'
    inventory = fixture['fresh_inventory']
    assert normalize_module_observation(inventory['src/dyn.mjs']) is not None
    diff = compute_sync_diff(manifest, inventory, str(tmp_path))
    assert diff.unchanged_files == ['src/dyn.mjs']
    assert not sync_cmd._affected_source_files(diff)
    refreshed = sync_cmd._generator_refresh_diff(diff, inventory)
    assert refreshed.changed_files == ['src/dyn.mjs']
    assert diff.unchanged_files == ['src/dyn.mjs']
    assert _files(tmp_path) == before


def test_mixed_generator_refusal_retains_real_reasons_and_exact_bounds(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    raw = SyncDiff(new_files=['src/new.py'], changed_files=['src/f000.py'],
                   metadata_only_files=['src/f001.py'], removed_files=['src/gone.py'])
    application = sync_cmd._generator_refresh_diff(raw, {f'src/f{i:03}.py': {} for i in range(261)})
    refusal = _refusal(
        _options(), application, capsys, source_diff=raw,
        generator_refresh_required=True, prior_generator_version='2.5.0',
        source_selection_prune=SourceSelectionPruneResult(SyncManifest(), ('outside.py',), ('modules/outside.md',)),
    )
    assert '263 source file(s)' in refusal
    assert 'new=1, changed=1, metadata-only=1, removed=1' in refusal
    assert 'generator-refresh-additional=259' in refusal
    assert 'captured version="2.5.0"' in refusal
    assert f'current version={json.dumps(sync_cmd.__version__)}' in refusal
    assert 'source path sample: 8 shown, 255 omitted' in refusal
    assert '"src/f000.py" [changed]' in refusal
    assert '"src/f001.py" [metadata-only]' in refusal
    assert 'Source-selection pruning: 1 source(s), 1 concept page(s)' in refusal
    assert 'source files are not rewritten' in refusal
    assert '--dry-run' in refusal and 'never applied automatically' in refusal


@pytest.mark.parametrize(('count', 'total', 'blocked'), [(49, 300, False), (50, 300, False), (51, 300, True), (3, 10, False), (4, 10, True)])
def test_diagnosis_does_not_change_count_or_ratio_boundaries(count, total, blocked):
    diff = SyncDiff(changed_files=[f'src/f{i:03}.py' for i in range(count)])
    manifest = SyncManifest(sources={f'src/f{i:03}.py': {} for i in range(total)})
    assert (sync_cmd._large_diff_message(diff, manifest) is not None) is blocked


@pytest.mark.parametrize('category', ['new_files', 'changed_files', 'metadata_only_files', 'removed_files'])
def test_real_source_reasons_do_not_claim_generator_refresh(tmp_path, monkeypatch, capsys, category):
    monkeypatch.chdir(tmp_path)
    diff = SyncDiff()
    setattr(diff, category, [f'src/f{i:03}.py' for i in range(51)])
    refusal = _refusal(_options(), diff, capsys)
    assert '51 source file(s)' in refusal
    assert 'source path sample: 8 shown, 43 omitted' in refusal
    assert '"src/f000.py"' in refusal
    assert 'Generator refresh:' not in refusal
    assert 'generator-refresh-additional=0' in refusal


def test_infrastructure_only_refusal_uses_its_own_guard_and_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    infrastructure = _infrastructure(new_sources=tuple(f'infra/f{i:03}.yaml' for i in range(51)))
    refusal = _refusal(_options(), SyncDiff(), capsys, infrastructure=infrastructure)
    assert '51 infrastructure source(s)' in refusal
    assert 'Affected source inputs: 0' in refusal
    assert 'Infrastructure actions: 51 new' in refusal
    assert 'infrastructure action path sample: 8 shown, 43 omitted' in refusal
    assert '"infra/f000.yaml"' in refusal


def test_force_still_has_no_guard_side_effects(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    sync_cmd._exit_if_large_unforced_diff(
        _options('--force'), SyncDiff(changed_files=[f'f{i}.py' for i in range(51)]),
        SyncManifest(), InventoryResult({}, {}), _infrastructure(),
    )
    assert capsys.readouterr().err == ''
    assert _files(tmp_path) == {}


def test_preview_argv_round_trips_all_planning_bindings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    options = _options(
        '--source-selection', "profiles/selected 'sources'.json", '--helper-cache-dir', 'helper cache',
        '--cache-dir', 'inventory cache', '--openapi-file', 'schema/contracts.yaml',
        '--initialize-surfaces', 'flows,dependencies', '--flow-category', 'http',
        '--exclude-tests', '--include-tests', 'go', '--allow-external-src', '--no-plugins',
        '--no-preserve-semantic', '--rebuild-knowledge', '--rebuild-cache', '--cache-stats', '--jobs', 'auto',
        no_cache=False,
    )
    argv = sync_cmd._sync_preview_argv(options)
    hint = sync_cmd._sync_preview_hint(options)
    command = _preview_command(hint)
    assert _decode_command(command) == argv
    assert '--force' not in argv and '--dry-run' in argv
    restored = sync_cmd._sync_run_options_from_args(cli._build_parser().parse_args(argv[1:]))
    for name in ('src_dir', 'wiki_dir', 'source_selection', 'helper_cache_dir', 'allow_external_src',
                 'include_plugins', 'preserve_semantic', 'rebuild_knowledge', 'initialize_surfaces',
                 'flow_categories', 'exclude_tests', 'include_tests', 'openapi_file', 'clear_openapi_file', 'job_request'):
        assert getattr(restored, name) == getattr(options, name), name
    assert restored.capture_cache_options == options.capture_cache_options


def test_preview_clear_authority_and_explicit_storage_options_are_preserved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    argv = sync_cmd._sync_preview_argv(_options('--clear-openapi-file', '--knowledge-format', 'v1'))
    assert '--clear-openapi-file' in argv
    assert argv[argv.index('--knowledge-format') + 1] == 'v1'
    assert '--openapi-file' not in argv


def test_powershell_hint_uses_existing_literal_argument_renderer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    options = _options('--helper-cache-dir', "cache 'quoted' ‘unicode’")
    with monkeypatch.context() as patch:
        patch.setattr(sync_cmd.os, 'name', 'nt')
        hint = sync_cmd._sync_preview_hint(options)
    assert 'PowerShell): & ' in hint
    assert "'cache ''quoted'' ‘‘unicode’’'" in hint
    assert "'--dry-run'" in hint
    assert _decode_command(_preview_command(hint)) == sync_cmd._sync_preview_argv(options)


def test_hostile_and_large_values_have_bounded_truthful_output(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    paths = [f'src/{i:03}-' + '\U0001f600' * 1000 + '\n\x1b[31m.py' for i in range(261)]
    options = _options('--helper-cache-dir', 'cache-' + 'x' * 6000)
    refusal = _refusal(options, SyncDiff(changed_files=paths), capsys,
                       generator_refresh_required=True, prior_generator_version='old-' + '\U0001f600' * 1000)
    assert len(refusal.encode()) < 8192
    assert '\x1b' not in refusal
    assert '[truncated]' in refusal and '253 omitted' in refusal
    assert 'command display bounded' in refusal
    assert 'Repeat the same sync invocation with --dry-run' in refusal
    assert 'cache-xxx' not in refusal
    assert 'captured version=' in refusal


def test_generator_transition_refusal_and_preview_share_plan_without_active_writes(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'src').mkdir()
    for number in range(61):
        (tmp_path / 'src' / f'f{number:03}.py').write_text(f'class Item{number}:\n    pass\n')
    bootstrap_cmd.run(cli._build_parser().parse_args([
        'bootstrap', '--src-dir', 'src', '--wiki-dir', 'wiki', '--source-adapter',
        '--knowledge-format', 'v1', '--skip-workflows',
    ]))
    capsys.readouterr()
    before = _files(tmp_path)
    prior_version = sync_cmd.__version__
    monkeypatch.setattr(sync_cmd, '__version__', '9.8.7')
    # The version transition is synthetic; all other producing bytes stay current.
    args = ['sync', '--src-dir', 'src', '--wiki-dir', 'wiki', '--jobs', '1', '--no-cache', '--no-plugins']
    with pytest.raises(SystemExit) as stopped:
        sync_cmd.run(cli._build_parser().parse_args(args))
    assert stopped.value.code == 1
    refusal = capsys.readouterr().err
    assert '61 source file(s)' in refusal
    assert f'captured version={json.dumps(prior_version)}, current version="9.8.7"' in refusal
    assert 'generator-refresh-additional=61' in refusal
    assert '8 shown, 53 omitted' in refusal
    assert _files(tmp_path) == before
    shell = 'PowerShell' if os.name == 'nt' else 'POSIX shell'
    command = refusal.split(shell + '): ', 1)[1].splitlines()[0]
    preview_argv = _decode_command(command)
    assert preview_argv[:3] == ['llm-wiki', 'sync', '--dry-run']
    sync_cmd.run(cli._build_parser().parse_args(preview_argv[1:]))
    preview = capsys.readouterr().out
    assert 'generator-refresh-additional=61' in preview
    assert 'generator refresh sources: 61' in preview
    assert 'complete source paths: 61 shown, 0 omitted' in preview
    assert '"f060.py" [generator-refresh-additional]' in preview
    assert 'requires --force: yes' in preview
    assert 'DRY-RUN: no files modified.' in preview
    assert _files(tmp_path) == before


def test_complete_preview_reveals_omitted_paths_and_selection_pruning():
    path = 'src/' + 'long/' * 100 + 'file.py'
    diff = SyncDiff(changed_files=[path])
    lines = sync_cmd._sync_guard_detail_lines(
        diff, diff, _infrastructure(), generator_refresh_required=False,
        prior_generator_version=None, complete_paths=True,
        source_selection_prune=SourceSelectionPruneResult(SyncManifest(), ('outside.py',), ()),
    )
    text = '\n'.join(lines)
    assert json.dumps(path) in text
    assert '[truncated]' not in text
    assert 'complete deselected source paths: 1 shown, 0 omitted' in text
    assert '"outside.py" [source-selection]' in text


def test_unavailable_captured_generator_is_not_invented(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    raw = SyncDiff(unchanged_files=[f'f{i:03}.py' for i in range(51)])
    application = sync_cmd._generator_refresh_diff(raw, {p: {} for p in raw.unchanged_files})
    refusal = _refusal(_options(), application, capsys, source_diff=raw,
                       generator_refresh_required=True, prior_generator_version=None)
    assert 'captured version=unavailable' in refusal
    assert 'generator-refresh-additional=51' in refusal
    assert 'captured version="2.5.0"' not in refusal


@pytest.mark.parametrize('cache', ['cache\nline', 'cache\x1b[31m'])
def test_control_containing_command_uses_repeat_original_guidance(tmp_path, monkeypatch, cache):
    monkeypatch.chdir(tmp_path)
    hint = sync_cmd._sync_preview_hint(_options('--helper-cache-dir', cache))
    assert 'command display bounded' in hint
    assert 'Repeat the same sync invocation with --dry-run' in hint
    assert cache not in hint
