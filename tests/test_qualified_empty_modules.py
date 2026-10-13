"""Parser-owned empty modules, negative authority, and cache/reader parity."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import json
import os

import pytest

from llm_wiki_cli.commands import sync_cmd
from llm_wiki_cli.services import sync_analysis_cache
from llm_wiki_cli.services.extraction_service import get_inventory_result
from llm_wiki_cli.services.knowledge_storage_diagnostics import storage_report
from llm_wiki_cli.services.lint_service import build_report
from llm_wiki_cli.services.sync_manifest import SyncManifest
from llm_wiki_cli.services.source_snapshot import build_source_snapshot
from tests.test_sync_page_transitions import _bootstrap_project, _draft_source, _sync, _author_description
from tests.test_entity_retirement import _snapshot, _assert_retired

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HELPERS = os.environ.get('LLM_WIKI_CACHE_DIR', str(PROJECT_ROOT / '.git/llm-wiki-extractors'))


@pytest.mark.parametrize('body', ['', '# valid comment only\n', '"""Module description only."""\n'])
def test_parser_owned_python_empty_keeps_module_and_authored_history(tmp_path, monkeypatch, body):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {'model.py': _draft_source('Original draft.')})
    module = wiki / 'modules/model.md'
    _author_description(module, '_Auto-generated from `pkg/model.py`._', 'Authored module purpose.')
    _author_description(wiki / 'entities/Draft.md', 'Original draft.', 'Authored entity history.')
    _sync(wiki)
    prior = SyncManifest.load(wiki)
    owner = prior.page_source_mappings['entities/Draft.md']
    (project / 'pkg/model.py').write_text(body)
    _sync(wiki)
    current = _assert_retired(wiki, 'entities/Draft.md', owner)
    assert current.sources['pkg/model.py']['empty_module'] is True
    assert current.sources['pkg/model.py']['entities'] == []
    basis = current.evidence_baselines['modules/model.md'].basis
    assert basis is not None
    assert basis.source_content_hash == current.sources['pkg/model.py']['hash']
    assert current.tombstones['entities/Draft.md'].last_valid_basis == prior.evidence_baselines['entities/Draft.md'].basis
    assert 'Authored module purpose.' in module.read_text()
    assert 'Authored entity history.' in (wiki / 'entities/Draft.md').read_text()
    assert build_report(str(wiki), '.', strict=True).passed
    assert storage_report(wiki, full=True)['ok']
    stable = _snapshot(wiki)
    _sync(wiki)
    assert _snapshot(wiki) == stable
    _sync(wiki, no_cache=True)
    assert _snapshot(wiki) == stable


@pytest.mark.parametrize('body', ['class Draft(:\n', 'import sys\nfrom pkg import other\nsys.modules[__name__] = other\n'])
def test_parse_failure_and_module_alias_do_not_become_empty(tmp_path, monkeypatch, body):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {'model.py': _draft_source('Original draft.')})
    before = _snapshot(wiki)
    (project / 'pkg/model.py').write_text(body)
    with pytest.raises(SystemExit):
        _sync(wiki)
    assert _snapshot(wiki) == before
    assert not SyncManifest.load(wiki).generation_inputs.get('entity_retirement')


def test_narrow_diagnostic_retry_never_reads_unrequested_source(tmp_path, monkeypatch):
    (tmp_path / 'target.py').write_text('# empty\n')
    (tmp_path / 'outside.py').write_text('class Outside:\n    pass\n')
    snapshot = build_source_snapshot(tmp_path)
    from llm_wiki_cli.extractors.python_extractor import PythonExtractor
    original = PythonExtractor.extract
    seen = []
    def extract(self, *args, **kwargs):
        seen.extend(kwargs['source_files'])
        return original(self, *args, **kwargs)
    monkeypatch.setattr(PythonExtractor, 'extract', extract)
    result = get_inventory_result(str(tmp_path), deep=True, only_files=['target.py'], source_snapshot=snapshot, include_empty=True, capture_path_outcomes=True)
    assert seen == ['target.py']
    assert set(result.inventory) == {'target.py'}
    assert result.path_outcomes['target.py']['retained_empty'] is True


@pytest.mark.parametrize('qualification', [{}, {'extraction_state': 'unavailable', 'reason': 'outcome-not-reported'}, {'extraction_state': 'failed', 'reason': 'syntax-error'}])
def test_unqualified_retry_cannot_promote_a_record(tmp_path, monkeypatch, qualification):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {'model.py': _draft_source('Original draft.')})
    (project / 'pkg/model.py').write_text('# empty\n')
    before = _snapshot(wiki)
    original = sync_cmd.get_inventory_result
    def collect(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs.get('capture_path_outcomes'):
            return replace(result, path_outcomes={'pkg/model.py': qualification})
        return result
    monkeypatch.setattr(sync_cmd, 'get_inventory_result', collect)
    with pytest.raises(SystemExit):
        _sync(wiki)
    assert _snapshot(wiki) == before


@pytest.mark.parametrize('suffix', ['.ts', '.js', '.mjs', '.cjs'])
def test_real_typescript_family_empty_and_partial_syntax_are_distinct(tmp_path, suffix, require_prepared_diagnostics_helper):
    require_prepared_diagnostics_helper('typescript')
    source = tmp_path / ('module' + suffix)
    source.write_text('// empty\n')
    result = get_inventory_result(str(tmp_path), deep=True, include_empty=True, capture_path_outcomes=True, helper_cache_dir=HELPERS)
    assert not result.failed
    assert result.inventory[source.name]['empty_module'] is True
    assert result.path_outcomes[source.name]['retained_empty'] is True
    source.write_text('class Draft {\n')
    failed = get_inventory_result(str(tmp_path), deep=True, include_empty=True, capture_path_outcomes=True, helper_cache_dir=HELPERS)
    assert source.name not in failed.inventory
    assert failed.path_outcomes[source.name]['reason'] == 'syntax-error'


@pytest.mark.parametrize('suffix,valid,invalid', [('.go', 'package pilot\n', 'package\n'), ('.rs', '// valid empty\n', 'pub struct {\n')])
def test_real_go_rust_empty_records_and_unqualified_failure(tmp_path, suffix, valid, invalid, require_prepared_diagnostics_helper):
    require_prepared_diagnostics_helper('go' if suffix == '.go' else 'rust')
    source = tmp_path / ('module' + suffix)
    source.write_text(valid)
    result = get_inventory_result(str(tmp_path), deep=True, capture_path_outcomes=True, helper_cache_dir=HELPERS)
    assert not result.failed
    assert result.inventory[source.name]['classes'] == []
    assert result.inventory[source.name]['functions'] == []
    assert result.path_outcomes[source.name]['extraction_state'] == 'extracted'
    source.write_text(invalid)
    failed = get_inventory_result(str(tmp_path), deep=True, capture_path_outcomes=True, helper_cache_dir=HELPERS)
    assert source.name not in failed.inventory
    assert failed.path_outcomes[source.name]['extraction_state'] in {'failed', 'unavailable'}


def test_haskell_helper_contract_retains_valid_empty_and_missing_coverage(tmp_path):
    from llm_wiki_cli.extractors.haskell_extractor import HaskellExtractor
    from subprocess import CompletedProcess
    source = tmp_path / 'Empty.hs'
    source.write_text('module Empty where\n')
    extractor = HaskellExtractor()
    loaded = extractor._load_inventory(CompletedProcess([], 0, json.dumps({str(source): {'classes': [], 'functions': [], 'imports': [], 'module': 'Empty'}}), ''))
    normalized = extractor._normalize_inventory(str(tmp_path), loaded)
    assert normalized['Empty.hs']['classes'] == []
    assert normalized['Empty.hs']['functions'] == []
    assert normalized['Empty.hs']['language'] == 'haskell'
    unavailable = get_inventory_result(str(tmp_path), deep=True, capture_path_outcomes=True, helper_cache_dir=str(tmp_path / 'unprepared'))
    assert 'Empty.hs' not in unavailable.inventory
    assert unavailable.path_outcomes['Empty.hs']['extraction_state'] in {'failed', 'unavailable'}


def test_committed_analysis_retains_empty_outcome_and_warm_sync_skips_retry(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {'model.py': _draft_source('Original draft.')})
    cache = tmp_path / 'cache'
    _sync(wiki, cache_dir=str(cache))
    (project / 'pkg/model.py').write_text('# empty\n')
    _sync(wiki, cache_dir=str(cache))
    payload = json.loads((cache / sync_analysis_cache.FILENAME).read_text())
    assert payload['inventory']['pkg/model.py']['empty_module'] is True
    assert payload['path_outcomes']['pkg/model.py']['retained_empty'] is True
    stable = _snapshot(wiki)
    def unexpected(*args, **kwargs):
        pytest.fail('qualified warm inventory was parsed again')
    monkeypatch.setattr(sync_cmd, 'get_inventory_result', unexpected)
    _sync(wiki, cache_dir=str(cache))
    assert _snapshot(wiki) == stable


def test_missing_cache_empty_outcomes_are_rebuilt_by_exact_retry(tmp_path, monkeypatch):
    (tmp_path / 'model.py').write_text('# empty\n')
    snapshot = build_source_snapshot(tmp_path)
    result = get_inventory_result(str(tmp_path), deep=True, include_empty=True, capture_path_outcomes=True, source_snapshot=snapshot)
    cached = replace(result, path_outcomes={})
    manifest = SyncManifest.build_from_inventory(cached.inventory, str(tmp_path), {}, {'model.py': 'model'})
    options = SimpleNamespace(src_dir=str(tmp_path), helper_cache_dir=None, include_tests=(), include_plugins=False, parallel_jobs=1)
    observed = []
    original = sync_cmd.get_inventory_result
    def collect(*args, **kwargs):
        observed.append(kwargs['only_files'])
        return original(*args, **kwargs)
    monkeypatch.setattr(sync_cmd, 'get_inventory_result', collect)
    qualified = sync_cmd._qualify_surviving_module_inventory(options, snapshot, manifest, cached)
    assert observed == [['model.py']]
    assert qualified.path_outcomes['model.py']['retained_empty'] is True


@pytest.mark.parametrize('suffix', ['.ts', '.js', '.mjs', '.cjs'])
def test_typescript_empty_owning_transition_and_strict_live_reader(tmp_path, monkeypatch, suffix, require_prepared_diagnostics_helper):
    require_prepared_diagnostics_helper('typescript')
    from llm_wiki_cli import api
    name = 'model' + suffix
    monkeypatch.setenv('LLM_WIKI_CACHE_DIR', HELPERS)
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {name: 'export class Draft {}\n'})
    monkeypatch.delenv('LLM_WIKI_CACHE_DIR')
    owner = SyncManifest.load(wiki).page_source_mappings['entities/Draft.md']
    (project / 'pkg' / name).write_text('// empty\n')
    _sync(wiki, helper_cache_dir=HELPERS)
    manifest = _assert_retired(wiki, 'entities/Draft.md', owner)
    assert manifest.sources['pkg/' + name]['empty_module'] is True
    assert build_report(str(wiki), '.', strict=True, helper_cache_dir=HELPERS).passed
    inspected = api.inspect_concept('modules/model.md', src_dir='.', wiki_dir=str(wiki), live=True, helper_cache_dir=HELPERS)
    assert inspected['concept'] is not None
    stable = _snapshot(wiki)
    _sync(wiki, helper_cache_dir=HELPERS)
    assert _snapshot(wiki) == stable
    (project / 'pkg' / name).write_text('export class Draft {\n')
    with pytest.raises(SystemExit):
        _sync(wiki, helper_cache_dir=HELPERS)
    assert _snapshot(wiki) == stable


def test_manifest_retention_does_not_expand_scope_to_unowned_empty_files(tmp_path, monkeypatch):
    project, wiki = _bootstrap_project(tmp_path, monkeypatch, {'model.py': _draft_source('Original.')})
    (project / 'pkg/model.py').write_text('# tracked empty\n')
    (project / 'pkg/unowned.py').write_text('# new unowned empty\n')
    _sync(wiki)
    manifest = SyncManifest.load(wiki)
    result = get_inventory_result('.', deep=True, retain_empty_paths=('pkg/model.py',))
    assert 'pkg/model.py' in result.inventory
    assert 'pkg/unowned.py' not in result.inventory
    assert 'pkg/unowned.py' not in manifest.sources
    assert build_report(str(wiki), '.', strict=True).passed
