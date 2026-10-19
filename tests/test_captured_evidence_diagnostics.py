"""Captured failures and fresh observations must never share an implied verdict."""

from dataclasses import replace
import json

import pytest

from llm_wiki_cli import api, cli
from llm_wiki_cli.commands import bootstrap_cmd, sync_cmd
from llm_wiki_cli.services import knowledge_evidence
from llm_wiki_cli.services.documentation_queries import DocumentationGraphQueryService
from llm_wiki_cli.services.evidence_diagnostics import captured_evidence_diagnostic
from llm_wiki_cli.services.knowledge_consumption import build_knowledge_read_view
from llm_wiki_cli.services.knowledge_evidence import ConceptObservationBasis
from llm_wiki_cli.services.knowledge_loader import load_knowledge_state
from llm_wiki_cli.services.knowledge_model import ComputedFreshness, EvidenceState
from llm_wiki_cli.services.sync_manifest import ManifestEvidenceBaseline, SyncManifest
from tests.test_knowledge_freshness import MODULE_LOCATOR, _live_evaluation
from tests.test_knowledge_lint import _loaded_knowledge, _report_for_view
from tests.test_sync_guard_diagnostics import _options, _refusal


def _view(tmp_path, fresh='valid', *, historical=True, source_changed=False, stored_unknown=True, producer_change=None, scope_change=False):
    loaded, knowledge = _loaded_knowledge(tmp_path)
    assert loaded.manifest_basis is not None
    original = next(c for c in knowledge.concepts if c.locator == MODULE_LOCATOR)
    path = original.document.canonical_path
    basis = loaded.manifest_basis.evidence_baselines[path].basis
    assert basis is not None
    live = _live_evaluation(knowledge)
    current = live.concept_bases[MODULE_LOCATOR]
    if producer_change is not None:
        tool = replace(live.producer.tool, configuration_hash=None if producer_change == 'missing' else 'sha256:' + 'd' * 64)
        live = replace(live, producer=replace(live.producer, tool=tool))
    if scope_change:
        current = replace(current, scope='entity')
        live = replace(live, concept_bases={**live.concept_bases, MODULE_LOCATOR: current})
    if source_changed:
        content_hash = 'sha256:' + 'f' * 64
        live = replace(live, source_content_hashes={**live.source_content_hashes, current.source_path: content_hash},
                       concept_bases={k: replace(b, source_content_hash=content_hash) if b.source_path == current.source_path else b for k, b in live.concept_bases.items()})
        current = live.concept_bases[MODULE_LOCATOR]
    if fresh not in {'valid', 'untested'}:
        live = replace(live, concept_bases={**live.concept_bases, MODULE_LOCATOR: replace(current, concept_observation_hash=None, unknown_reason=fresh)})
    if stored_unknown:
        unknown_basis = replace(basis, concept_observation_hash=None, unknown_reason='invalid-inventory-shape')
        unknown = replace(original, facets=replace(original.facets, structure=replace(original.facets.structure, evidence=EvidenceState.UNKNOWN, basis=None)))
        baselines = dict(loaded.manifest_basis.evidence_baselines)
        baselines[path] = ManifestEvidenceBaseline.from_basis(unknown_basis) if historical else ManifestEvidenceBaseline.unknown('evidence-not-recorded')
        loaded = replace(loaded, knowledge=replace(knowledge, concepts=tuple(unknown if c.locator == MODULE_LOCATOR else c for c in knowledge.concepts)), manifest_basis=replace(loaded.manifest_basis, evidence_baselines=baselines))
    view = build_knowledge_read_view(loaded, live_evaluation=None if fresh == 'untested' else live)
    assert view.knowledge is not None
    return view, next(c for c in view.knowledge.concepts if c.locator == MODULE_LOCATOR)


@pytest.mark.parametrize(('fresh', 'expected'), [
    ('untested', 'Fresh result is untested or unavailable'),
    ('valid', 'Fresh normalization is valid; captured evidence is not repaired'),
    ('invalid-inventory-shape', 'Fresh normalization still rejects'),
    ('unsupported-language', 'Fresh evidence remains unavailable'),
    ('insufficient-inventory-detail', 'Fresh evidence remains unavailable'),
])
def test_diagnosis_distinguishes_results_without_accepting_stored_failure(tmp_path, fresh, expected):
    view, concept = _view(tmp_path, fresh)
    diagnosis = captured_evidence_diagnostic(view, concept)
    assert diagnosis is not None
    description, hint = diagnosis
    assert expected in description
    assert '--read-only' in hint and 'does not commit a repair' in hint
    report = _report_for_view(view)
    issue = next(i for i in report.issues if i.target == MODULE_LOCATOR)
    assert not report.passed and issue.severity == 'error'
    assert issue.reason_code == 'promised-evidence-unknown'
    assert 'Source:' in issue.message and 'Cause: invalid-inventory-shape' in issue.message and 'Extractor:' in issue.message
    assert expected in issue.message
    assert view.freshness is not None
    result = view.freshness.by_locator[MODULE_LOCATOR]
    assert result.state is ComputedFreshness.UNKNOWN
    assert not result.live_comparison_performed
    assert (result.live_basis is not None) == (fresh != 'untested')
    if fresh == 'valid':
        assert 'Captured source bytes: unchanged' in description
        assert '--dry-run' in hint and 'never force automatically' in hint
    else:
        assert 'authorizing --force' not in hint


@pytest.mark.parametrize('historical', [False, True])
def test_absent_provenance_and_changed_bytes_are_not_guessed(tmp_path, historical):
    view, concept = _view(tmp_path, historical=historical, source_changed=True)
    result = captured_evidence_diagnostic(view, concept)
    assert result is not None
    assert ('Captured source bytes: changed' if historical else 'historical source basis not captured') in result[0]
    assert 'do not establish historical artifact identity' in result[0]


def test_fresh_malformed_result_diagnosed_even_with_valid_stored_evidence(tmp_path):
    view, concept = _view(tmp_path, 'invalid-inventory-shape', stored_unknown=False)
    result = captured_evidence_diagnostic(view, concept)
    assert result is not None and 'Captured evidence was present' in result[0]
    assert 'Fresh normalization still rejects' in result[0]
    assert 'do not bypass an invalid-evidence gate' in result[1]


@pytest.mark.parametrize(('change', 'expected'), [('changed', 'metadata: different'), ('missing', 'producer-basis metadata is incomplete')])
def test_same_version_metadata_is_not_artifact_identity(tmp_path, change, expected):
    view, concept = _view(tmp_path, producer_change=change)
    result = captured_evidence_diagnostic(view, concept)
    assert result is not None and expected in result[0]
    assert 'do not establish historical artifact identity' in result[0]
    assert view.freshness is not None and view.freshness.live_producer is not None and view.knowledge is not None
    assert view.freshness.live_producer.tool.version == view.knowledge.bundle.producer.tool.version


def test_coordinate_mismatch_never_establishes_compatible_old_evidence(tmp_path):
    view, concept = _view(tmp_path, scope_change=True)
    result = captured_evidence_diagnostic(view, concept)
    assert result is not None
    assert 'not comparable (source mapping or scope differs)' in result[0]
    assert 'not compatible' in result[0]


def test_untrusted_labels_are_escaped_and_bounded():
    from llm_wiki_cli.services.evidence_diagnostics import _label
    value = 'secret\n\x1b' + '\udc80' + 'x' * 10000
    displayed = _label(value)
    assert len(displayed.encode()) < 1024
    assert '\n' not in displayed and '\x1b' not in displayed and '[truncated]' in displayed


@pytest.mark.parametrize('surface', ['service', 'api', 'mcp'])
def test_existing_explanation_shape_retains_current_basis_and_strict_unknown(tmp_path, monkeypatch, surface):
    view, _ = _view(tmp_path)
    service = DocumentationGraphQueryService({}, knowledge_view=view)
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    if surface == 'api':
        result = api.explain_evidence(MODULE_LOCATOR, service=service)
    elif surface == 'mcp':
        from llm_wiki_cli.services import mcp_server
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(mcp_server, 'build_documentation_query_service', lambda *a, **kw: service)
        result = mcp_server.McpWikiService(src_dir='.', wiki_dir='.').explain_evidence(MODULE_LOCATOR)
    else:
        result = service.explain_evidence(MODULE_LOCATOR)
    evidence = result['evidence']
    assert evidence is not None
    assert evidence['structure']['evidence'] == 'unknown'
    freshness = evidence['freshness']
    assert set(freshness) == {'state', 'reason', 'description', 'live_comparison_performed', 'recorded_basis', 'live_basis', 'hint'}
    assert freshness['state'] == 'unknown' and not freshness['live_comparison_performed']
    assert freshness['recorded_basis'] is None
    assert freshness['live_basis']['concept_observation_hash'].startswith('sha256:')
    assert 'Fresh normalization is valid' in freshness['description']
    assert result['bounds']['raw_evidence_bytes']['returned'] == len(json.dumps(result['evidence'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
    assert {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()} == before


@pytest.mark.parametrize('scope', ['module', 'entity'])
def test_same_version_invalid_basis_refreshes_without_edit_and_stays_stable(tmp_path, monkeypatch, capsys, scope):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'src').mkdir()
    source = tmp_path / 'src/app.py'
    source.write_bytes(b'class Thing:\n    def value(self):\n        return 1\n')
    with monkeypatch.context() as patch:
        def reject(*args):
            raise knowledge_evidence._InventoryNormalizationError('invalid-inventory-shape')
        patch.setattr(knowledge_evidence, f'_normalize_{scope}_observation', reject)
        bootstrap_cmd.run(cli._build_parser().parse_args(['bootstrap', '--src-dir', 'src', '--wiki-dir', 'wiki', '--source-adapter', '--knowledge-format', 'v1', '--skip-workflows', '--skip-flows']))
    wiki = tmp_path / 'wiki'
    manifest = SyncManifest.load(wiki)
    assert manifest is not None
    page_path = 'modules/app.md' if scope == 'module' else 'entities/Thing.md'
    assert manifest.evidence_baselines[page_path].unknown_reason == 'invalid-inventory-shape'
    page = wiki / page_path
    page.write_bytes(page.read_bytes().replace(b'## Description', b'## Description\n\nKeep this authored explanation.', 1))
    source_bytes = source.read_bytes()
    args = ['sync', '--src-dir', 'src', '--wiki-dir', 'wiki', '--no-cache', '--no-plugins']
    before = {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob('*') if p.is_file()}
    capsys.readouterr()
    sync_cmd.run(cli._build_parser().parse_args([*args, '--dry-run']))
    preview = capsys.readouterr().out
    assert '0 new, 0 changed, 0 metadata-only' in preview
    assert 'evidence-refresh-additional=1' in preview
    assert 'generator-refresh-additional=0' in preview
    assert {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob('*') if p.is_file()} == before
    sync_cmd.run(cli._build_parser().parse_args(args))
    after = load_knowledge_state(wiki)
    assert after.manifest_basis is not None
    assert all(b.is_known for b in after.manifest_basis.evidence_baselines.values())
    assert source.read_bytes() == source_bytes and 'Keep this authored explanation.' in page.read_text()
    snapshot = {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob('*') if p.is_file()}
    sync_cmd.run(cli._build_parser().parse_args(args))
    assert {p.relative_to(wiki).as_posix(): p.read_bytes() for p in wiki.rglob('*') if p.is_file()} == snapshot


def test_evidence_refresh_keeps_broad_guard_and_truthful_reason(tmp_path, monkeypatch, capsys):
    from llm_wiki_cli.services.sync_analysis import SyncDiff

    monkeypatch.chdir(tmp_path)
    paths = tuple(f'f{i}.py' for i in range(51))
    raw = SyncDiff(unchanged_files=list(paths))
    applied = SyncDiff(changed_files=list(paths))
    refusal = _refusal(_options(), applied, capsys, source_diff=raw, evidence_refresh_sources=paths)
    assert '51 source file(s)' in refusal and 'changed=0' in refusal
    assert 'evidence-refresh-additional=51' in refusal and 'generator-refresh-additional=0' in refusal


def test_still_malformed_inventory_is_not_scheduled_as_repaired():
    from llm_wiki_cli.services.sync_analysis import SyncDiff
    from llm_wiki_cli.services.sync_manifest import ManifestPageSource

    basis = ConceptObservationBasis('module', 'app.py', 'python', 'sha256:' + 'a' * 64, None, 'invalid-inventory-shape')
    manifest = SyncManifest(evidence_baselines={'modules/app.md': ManifestEvidenceBaseline.from_basis(basis)}, page_source_mappings={'modules/app.md': ManifestPageSource('module', 'app.py')})
    assert sync_cmd._recoverable_evidence_refresh_sources(manifest, {'app.py': {'language': 'python'}}, SyncDiff(unchanged_files=['app.py'])) == ()
