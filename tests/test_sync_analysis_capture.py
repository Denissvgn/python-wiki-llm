"""Capture diagnostics and resource bounds independently of cache contents."""

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from llm_wiki_cli.services import sync_analysis_cache as cache
from llm_wiki_cli.services.inventory_cache import InventoryCacheOptions
from llm_wiki_cli.services.knowledge_evidence import canonical_json_bytes
from llm_wiki_cli.services.runtime_output import RuntimeDestination


@pytest.fixture
def eligible(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    options = NS(src_dir='src', wiki_dir=tmp_path / 'wiki', helper_cache_dir=None,
                 initialize_surfaces=(), knowledge_format=None, preserve_semantic=True,
                 dry_run=False, cache_options=InventoryCacheOptions(enabled=True,
                     destination=RuntimeDestination(tmp_path / 'inventory.json', status='pending')))
    snapshot = NS(root=tmp_path, files_by_language={}, captured_content_hashes={},
                  captured_input_kinds={}, gitignore_fingerprint='', source_selection_identity=None,
                  include_tests=())
    manifest = NS(maintenance_state=None, surfaces={})
    manifest.with_generation_state = lambda **kw: manifest
    result = NS(failed=[], plugin_components={}, producer_plugin_components={},
                extractor_registry=cache.EXTRACTOR_REGISTRY.copy(), statuses={},
                implementation_observations={}, data_effect_observations=None, import_observations=None)
    @dataclass
    class Graph:
        flows: object = None
    prepared = NS(seed_manifest=False, repair_only=False, inventory_result=result,
                  entrypoint_analysis=Graph(), contracts={}, manifest=manifest,
                  source_snapshot=snapshot, analysis_input_key=None, inventory={},
                  surface_plan=NS(surfaces={}, generation_inputs={}),
                  page_maps=NS(module_page_map={}, entity_page_cache={}, entity_occurrence_page_cache={}),
                  graph_observations=Graph())
    monkeypatch.setattr(cache, 'capture_analysis', lambda *a, **kw: {
        'agent-wiki-cli': {}, 'llm-wiki/extractor/infrastructure': {}})
    monkeypatch.setattr(cache, 'implementation_hash', lambda: 'qualified')
    from llm_wiki_cli.services import knowledge_generation
    monkeypatch.setattr(knowledge_generation, '_graph_concepts', lambda *a, **kw: [])
    return options, prepared, NS(pages=[])


@pytest.mark.parametrize('owner,field,value,reason', [
    ('prepared', 'seed_manifest', True, 'seed-manifest'),
    ('prepared', 'repair_only', True, 'manifest-repair'),
    ('result', 'failed', ['python'], 'inventory-failed'),
    ('prepared', 'entrypoint_analysis', None, 'entrypoints-unavailable'),
    ('prepared', 'contracts', None, 'contracts-unavailable'),
    ('result', 'plugin_components', {'custom': {}}, 'extractor-plugins'),
    ('result', 'producer_plugin_components', {'custom': {}}, 'producer-plugins'),
    ('result', 'extractor_registry', {'python': 'custom'}, 'custom-extractors'),
    ('manifest', 'maintenance_state', {}, 'maintenance-state'),
    ('options', 'initialize_surfaces', ('flows',), 'surface-initialization'),
    ('options', 'knowledge_format', 'v1', 'storage-format-requested'),
])
def test_each_context_exit_is_explained(eligible, capsys, owner, field, value, reason):
    options, prepared, surface = eligible
    target = {'options': options, 'prepared': prepared, 'result': prepared.inventory_result,
              'manifest': prepared.manifest}[owner]
    setattr(target, field, value)
    assert cache.build_payload(options, prepared, surface) is None
    output = capsys.readouterr().out
    assert f'skipped ({reason}); destination=eligible; payload_bytes=unavailable;' in output
    assert len(output) < 250


@pytest.mark.parametrize('reason', ['plugin-lock-present', 'governance-present',
                                  'unqualified-analysis', 'unqualified-implementation'])
def test_qualification_exits_remain_visible(eligible, capsys, monkeypatch, reason):
    options, prepared, surface = eligible
    if reason == 'plugin-lock-present':
        Path('.llm-wiki').mkdir()
        Path('.llm-wiki/plugins.lock.json').write_text('{}')
    elif reason == 'governance-present':
        options.wiki_dir.mkdir()
        (options.wiki_dir / '.llm-wiki-governance.json').write_text('{}')
    elif reason == 'unqualified-analysis':
        monkeypatch.setattr(cache, 'capture_analysis', lambda *a, **kw: {})
    else:
        monkeypatch.setattr(cache, 'implementation_hash', lambda: None)
    assert cache.build_payload(options, prepared, surface) is None
    assert f'skipped ({reason})' in capsys.readouterr().out


@pytest.mark.parametrize('state', ['disabled', 'unconfigured', 'failed', 'redirected'])
def test_destination_exits_do_not_construct_payload(eligible, capsys, monkeypatch, state):
    options, prepared, surface = eligible
    if state == 'redirected':
        Path(cache.FILENAME).symlink_to('elsewhere')
    else:
        options.cache_options = InventoryCacheOptions(enabled=state != 'disabled',
            destination=RuntimeDestination(None, status='failed' if state == 'failed' else 'disabled'))
    monkeypatch.setattr(cache, 'input_key', lambda *a, **kw: pytest.fail('ineligible destination analyzed'))
    assert cache.build_payload(options, prepared, surface) is None
    assert f'skipped (destination-{state}); destination={state};' in capsys.readouterr().out


@pytest.mark.parametrize('payload', [{}, {'é': ['雪', 1, None, True]}, {'nested': {'b': (3, 4)}}])
def test_size_matches_actual_writer_and_exact_boundary(monkeypatch, payload):
    actual = len(canonical_json_bytes(payload)) + 1
    monkeypatch.setattr(cache, 'MAX_BYTES', actual)
    assert cache.payload_size(payload) == actual
    monkeypatch.setattr(cache, 'MAX_BYTES', actual - 1)
    assert cache.payload_size(payload) is None


def test_budget_stops_before_later_values_are_encoded(monkeypatch):
    monkeypatch.setattr(cache, 'MAX_BYTES', 64)
    # The invalid value would raise if encoding continued after the budget.
    assert cache.payload_size({'a': list(range(100)), 'z': object()}) is None


def test_oversized_capture_reports_lower_bound_and_preserves_graph(eligible, capsys, monkeypatch):
    options, prepared, surface = eligible
    original = list(range(1000))
    prepared.graph_observations.flows = original
    monkeypatch.setattr(cache, 'MAX_BYTES', 128)
    assert cache.build_payload(options, prepared, surface) is None
    assert prepared.graph_observations.flows is original
    assert 'skipped (payload-over-budget); destination=eligible; payload_bytes=>128;' in capsys.readouterr().out


@pytest.mark.parametrize('mode,reason', [('dry-run', 'dry-run'), ('no-payload', 'payload-unavailable'),
                                       ('failure', 'cache-write-failed')])
def test_publication_exits_are_explained(eligible, capsys, monkeypatch, mode, reason):
    options, _, _ = eligible
    options.dry_run = mode == 'dry-run'
    def failed(*a):
        raise OSError('unavailable')
    monkeypatch.setattr(cache, 'write_bytes_atomic', failed)
    cache.save(options, None if mode == 'no-payload' else {})
    assert f'skipped ({reason})' in capsys.readouterr().out


def test_capture_mutation_has_explicit_abort_status(eligible, capsys):
    options, prepared, surface = eligible
    prepared.analysis_input_key = {'stale': True}
    with pytest.raises(cache.SyncAnalysisMutationError):
        cache.build_payload(options, prepared, surface)
    assert 'capture: aborted (analysis-inputs-changed)' in capsys.readouterr().out


def test_eligible_capture_owns_graph_copy_and_reports_written_bytes(eligible, capsys):
    options, prepared, surface = eligible
    prepared.graph_observations.flows = [{'qualified': True}]
    payload = cache.build_payload(options, prepared, surface)
    assert payload is not None
    assert payload['graph_observations']['flows'] is not prepared.graph_observations.flows
    size = len(canonical_json_bytes(payload)) + 1
    cache.save(options, payload)
    path = cache.cache_path(options)
    assert path is not None
    assert path.stat().st_size == size
    output = capsys.readouterr().out
    assert f'payload_bytes={size};' in output
    assert 'saved (committed-payload)' in output


def test_partial_capture_retains_unavailable_sidecars(eligible, monkeypatch):
    options, prepared, surface = eligible
    prepared.graph_observations.flows = list(range(10000))
    monkeypatch.setattr(cache, 'MAX_BYTES', 4096)
    payload = cache.build_payload(options, prepared, surface)
    assert payload is not None and payload['coverage'] == 'inventory'
    assert payload['data_effect_observations'] is None
    assert payload['import_observations'] is None
    assert payload['graph_observations'] is None


def test_partial_capture_does_not_discard_over_budget_sidecars(eligible, monkeypatch, capsys):
    options, prepared, surface = eligible
    prepared.graph_observations.flows = list(range(10000))
    prepared.inventory_result.data_effect_observations = {'retained': 'x' * 10000}
    monkeypatch.setattr(cache, 'MAX_BYTES', 4096)
    assert cache.build_payload(options, prepared, surface) is None
    assert 'skipped (payload-over-budget)' in capsys.readouterr().out
