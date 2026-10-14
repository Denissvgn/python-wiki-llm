"""Qualified discovery boundaries preserve selection and recorded authority."""

import errno
import json
import os
from pathlib import Path

import pytest

from llm_wiki_cli import api
from llm_wiki_cli.services import search_service
from llm_wiki_cli.services.knowledge_storage import KnowledgeStorageError
from llm_wiki_cli.services.knowledge_storage_io import StorageReadSession
from llm_wiki_cli.services.knowledge_storage_lifecycle import migrate_knowledge_storage
from llm_wiki_cli.services.maintenance_protocol import ADOPTION_FILENAME
from llm_wiki_cli.services.search_discovery import DiscoveryError
from llm_wiki_cli.services.sync_manifest import SyncManifest


@pytest.fixture
def project(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("src/owner.py").write_text('class Owner:\n    """Describe the cobalt boundary."""\n    def limit(self, values):\n        return values[:3]\n')
    api.bootstrap_wiki("src", "wiki", knowledge_format="v1")
    capsys.readouterr()
    return tmp_path


def search(**options):
    return search_service.search_wiki("cobalt", src_dir="src", wiki_dir="wiki", kinds=["modules", "entities"],
                                    discovery="qualified-v1", **options)


def tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob('*') if path.is_file()}


def test_flat_native_is_explicit_capability_unavailable_but_recorded_owner_survives(project):
    before = tree(project)
    flat = search_service.search_wiki("cobalt", src_dir="src", wiki_dir="wiki", kinds=["modules", "entities"])
    enriched = search()
    assert {k: v for k, v in enriched.items() if k != "discovery"} == flat
    assert enriched["discovery"]["native"]["availability"] == "unavailable"
    assert enriched["discovery"]["native"]["reason"] == "selected-native-layout-unsupported"
    assert len(enriched["discovery"]["members"]) == len(flat["results"])
    for member in enriched["discovery"]["members"]:
        recorded = member["qualification"]["recorded_source"]
        assert recorded["basis"] == "manifest-snapshot" and recorded["source_content_hash"]
        assert not recorded["live_comparison_performed"]
    assert tree(project) == before


@pytest.mark.parametrize("layout", ["sharded-v2", "packed-v3", "packed-v4-deflate"])
def test_one_selected_native_slice_is_scoped_and_exact_without_read_mutation(project, layout):
    migrate_knowledge_storage(Path("wiki"), to=layout, recovery_dir=Path("recovery"))
    before = tree(project)
    result = search()
    native = result["discovery"]["native"]
    assert native["availability"] == "scoped" and not native["whole_store_validated"]
    assert native["validation_scope"].startswith("selected-committed")
    assert not result["discovery"]["live_comparison_performed"]
    assert tree(project) == before


def test_adopted_pending_records_are_snapshot_only_and_real_actor_history_is_not_current(project):
    api.adopt_maintenance("src", "wiki", recovery_dir="maintenance-recovery")
    migrate_knowledge_storage(Path("wiki"), to="sharded-v2", recovery_dir=Path("storage-recovery"))
    before = tree(project)
    result = search()
    reviews = [member["recorded_review"] for member in result["discovery"]["members"]]
    rows = [row for review in reviews for row in review.get("records", [])]
    assert rows and any(row["recorded_status"] == "pending" for row in rows)
    assert all(row.get("effective_status") is None for row in rows)
    assert all(row["qualification"] == "snapshot" and row["governance_effect"] == "none" for row in rows)
    assert all(row["expected_basis"] is None and not row["basis_available"] for row in rows)
    assert all(row["recorded_basis"]["source_hash"] for row in rows)
    assert not {"native_prose_coherent", "requires_sync"} & result["discovery"]["recorded_review"].keys()
    assert tree(project) == before


@pytest.mark.parametrize("damage", ["root", "unknown-schema", "missing-owner", "marker"])
def test_corrupt_or_mixed_authority_cannot_hide_as_native_unavailable(project, damage):
    if damage in {"missing-owner", "marker"}:
        api.adopt_maintenance("src", "wiki", recovery_dir="recovery")
        if damage == "missing-owner":
            Path("wiki/.llm-wiki-manifest.json").unlink()
        else:
            Path("wiki", ADOPTION_FILENAME).write_text('{}')
    else:
        root = Path("wiki/.llm-wiki-knowledge.json")
        data = json.loads(root.read_text())
        data["schema_version"] = "llm-wiki-knowledge/v999" if damage == "unknown-schema" else data["schema_version"]
        data["unexpected"] = True
        root.write_text(json.dumps(data))
    before = tree(project)
    with pytest.raises(ValueError):
        search()
    assert tree(project) == before


def test_plain_wiki_absence_remains_discoverable_with_page_only_unknown_native(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("src").mkdir()
    Path("wiki/guides").mkdir(parents=True)
    Path("wiki/guides/intro.md").write_text('# Guide\n\nCobalt orientation narrative.\n')
    before = tree(tmp_path)
    result = search_service.search_wiki("cobalt", src_dir="src", wiki_dir="wiki", discovery="qualified-v1")
    assert result["results"] and result["discovery"]["native"]["reason"] == "native-absent"
    assert tree(tmp_path) == before


@pytest.fixture
def selected(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    root = Path("project")
    (root / "selected").mkdir(parents=True)
    (root / "selected/owner.py").write_text('def owner():\n    """Cobalt selected ownership."""\n    return 1\n')
    (root / "selected/keeper.py").write_text('def keeper():\n    return 1\n')
    (root / "outside.py").write_text('def hidden():\n    """Secret unselected cobalt payload."""\n    return 2\n')
    (root / ".llm-wiki").mkdir()
    profile = root / ".llm-wiki/source-selection.json"
    profile.write_text(json.dumps({"schema_version": "llm-wiki-source-selection/v1", "include": ["selected"], "exclude": []}))
    api.bootstrap_wiki("project", "wiki", knowledge_format="v1")
    capsys.readouterr()
    manifest = SyncManifest.load(Path("wiki"))
    module = next(path for path, owner in manifest.page_source_mappings.items() if owner.source_path == 'selected/owner.py')
    return profile.relative_to(root), module


@pytest.mark.parametrize("mode", ["ranked", "ranked-v1", "substring"])
def test_active_selection_filters_before_content_reads_even_without_discovery(selected, monkeypatch, mode):
    profile, module = selected
    Path("wiki/modules/stray.md").write_text('# Stray\nSecret stray cobalt.\n')
    original = StorageReadSession.read
    def observe(self, relative, maximum):
        assert relative != 'modules/stray.md', 'unmapped source content read'
        return original(self, relative, maximum)
    monkeypatch.setattr(StorageReadSession, 'read', observe)
    result = search_service.search_wiki('cobalt', src_dir='project', wiki_dir='wiki', source_selection=profile,
                                      kinds=['modules'], mode=mode)
    assert any(row['path'] == module for row in result['results'])
    assert all(row['path'] != 'modules/stray.md' for row in result['results'])
    assert 'Secret stray' not in json.dumps(result)


def test_effectively_selected_missing_source_is_retained_without_live_claim(selected):
    profile, module = selected
    Path('project/selected/owner.py').unlink()
    result = search_service.search_wiki('cobalt', src_dir='project', wiki_dir='wiki', source_selection=profile,
                                      kinds=['modules'], discovery='qualified-v1')
    assert any(row['path'] == module for row in result['results'])
    assert all(not member['qualification']['recorded_source']['live_comparison_performed']
               for member in result['discovery']['members'])


@pytest.mark.parametrize("mutation", ["page", "source", "membership", "marker"])
def test_mutation_during_serialization_is_rejected_by_final_guards(project, monkeypatch, mutation):
    from llm_wiki_cli.services import workflow_profile
    original = workflow_profile.canonical_json
    before = tree(project)
    changed = False
    def serialize(value):
        nonlocal changed
        encoded = original(value)
        if not changed and isinstance(value, dict) and value.get('schema_version') == 'llm-wiki-discovery/v1':
            changed = True
            if mutation == 'source':
                Path('src/owner.py').write_text(Path('src/owner.py').read_text() + '\n# concurrent\n')
            elif mutation == 'membership':
                Path('wiki/modules').mkdir(exist_ok=True)
                Path('wiki/modules/added.md').write_text('# Added\nCobalt.\n')
            elif mutation == 'marker':
                Path('wiki', ADOPTION_FILENAME).write_text('{}')
            else:
                Path('wiki/modules/owner.md').write_text('# Replaced\nCobalt.\n')
        return encoded
    monkeypatch.setattr(workflow_profile, 'canonical_json', serialize)
    if os.name == 'nt' and mutation == 'page':
        with pytest.raises(PermissionError) as denied:
            search()
        assert denied.value.errno == errno.EACCES
        assert denied.value.filename == str(Path('wiki/modules/owner.md'))
        assert tree(project) == before
    else:
        with pytest.raises(ValueError):
            search()
    assert changed


def test_complete_boundary_metadata_cap_fails_with_stable_discovery_error(project, monkeypatch):
    from llm_wiki_cli.services import workflow_profile
    original = workflow_profile.canonical_json
    def serialize(value):
        if isinstance(value, dict) and 'capture_work' in value:
            return b'x' * 262145
        return original(value)
    monkeypatch.setattr(workflow_profile, 'canonical_json', serialize)
    with pytest.raises(DiscoveryError) as failed:
        search()
    assert failed.value.code == 'discovery-output-limit' and failed.value.required_bytes == 262145


def test_invalid_discovery_refuses_before_any_source_or_wiki_access(monkeypatch):
    monkeypatch.setattr(search_service, 'validate_source_root', lambda *a, **kw: pytest.fail('source accessed'))
    with pytest.raises(ValueError, match='discovery'):
        search_service.search_wiki('query', discovery=True)


def test_declared_native_root_disappearance_is_integrity_failure(project):
    Path('wiki/.llm-wiki-knowledge.json').unlink()
    with pytest.raises(KnowledgeStorageError, match='Declared committed'):
        search()


@pytest.mark.parametrize('mode', ['ranked', 'ranked-v1', 'ranked-v2', 'substring'])
@pytest.mark.parametrize('reason', ['unselected', 'ignored'])
def test_historical_mapped_ineligible_owner_never_enters_reader_or_results(selected, monkeypatch, mode, reason):
    from hashlib import sha256
    from llm_wiki_cli.services.sync_manifest import (
        ManifestPageSource, ManifestTombstone, TOMBSTONE_UNKNOWN_PROVENANCE, MANIFEST_STATE_UNAVAILABLE,
    )
    profile, _ = selected
    owner = 'outside.py' if reason == 'unselected' else 'selected/ignored.py'
    if reason == 'ignored':
        Path('project/selected/ignored.py').write_text('def hidden():\n    return 2\n')
        Path('project/.gitignore').write_text('selected/ignored.py\n')
        # Establish the actual ignored policy before the same owning refresh.
        import sys
        from llm_wiki_cli import cli
        monkeypatch.setattr(sys, 'argv', ['llm-wiki', 'sync', '--src-dir', 'project', '--wiki-dir', 'wiki', '--jobs', '1'])
        cli.main()
    manifest = SyncManifest.load(Path('wiki'))
    path = 'modules/retained_hidden.md'
    manifest.page_source_mappings[path] = ManifestPageSource(source_path=owner, scope='module')
    manifest.tombstones[path] = ManifestTombstone(reason=TOMBSTONE_UNKNOWN_PROVENANCE, unknown_reason=MANIFEST_STATE_UNAVAILABLE)
    manifest.sources[owner] = {'hash': 'sha256:' + sha256(Path('project', owner).read_bytes()).hexdigest()}
    manifest.save(Path('wiki'))
    Path('wiki', path).write_text('# Hidden\nCobalt secret forbidden owner content.\n')
    original = StorageReadSession.read
    def observe(self, relative, maximum):
        assert relative != path, 'mapped ineligible body was read'
        return original(self, relative, maximum)
    monkeypatch.setattr(StorageReadSession, 'read', observe)
    result = search_service.search_wiki('cobalt', src_dir='project', wiki_dir='wiki', source_selection=profile,
                                      kinds=['modules'], mode=mode, discovery='qualified-v1')
    serialized = json.dumps(result)
    assert path not in serialized and owner not in serialized and 'forbidden owner content' not in serialized
    assert result['discovery']['selection']['excluded_source_pages'] == 1


def test_empty_result_root_replacement_during_enrichment_cannot_publish(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('src').mkdir()
    Path('wiki').mkdir()
    from llm_wiki_cli.services import search_discovery
    original = search_discovery.enrich_search
    attempted = False
    def replace_root(*args, **kwargs):
        nonlocal attempted
        result = original(*args, **kwargs)
        attempted = True
        Path('wiki').rename('prior-wiki')
        Path('wiki').mkdir()
        return result
    monkeypatch.setattr(search_discovery, 'enrich_search', replace_root)
    if os.name == 'nt':
        with pytest.raises(PermissionError) as denied:
            search_service.search_wiki('absent', src_dir='src', wiki_dir='wiki', discovery='qualified-v1')
        assert denied.value.errno == errno.EACCES
        assert denied.value.winerror == 32
        assert denied.value.filename == 'wiki' and denied.value.filename2 == 'prior-wiki'
        assert Path('wiki').is_dir() and not Path('prior-wiki').exists()
        assert not list(Path('wiki').iterdir())
    else:
        with pytest.raises(ValueError, match='changed'):
            search_service.search_wiki('absent', src_dir='src', wiki_dir='wiki', discovery='qualified-v1')
        assert Path('prior-wiki').is_dir()
    assert attempted


def test_absent_captured_authority_never_reopens_an_uncaptured_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('src').mkdir()
    Path('wiki/guides').mkdir(parents=True)
    Path('wiki/guides/intro.md').write_text('# Intro\nCobalt.\n')
    monkeypatch.setattr(SyncManifest, 'load', lambda *a, **kw: pytest.fail('uncaptured owner reopen'))
    result = search_service.search_wiki('cobalt', src_dir='src', wiki_dir='wiki', discovery='qualified-v1')
    assert result['discovery']['native']['reason'] == 'native-absent'


def test_legacy_selected_wiki_read_does_not_inherit_optional_source_capture_limit(selected):
    profile, module = selected
    Path('project/selected/owner.py').write_bytes(b'# ' + b'x' * 16_777_217)
    result = search_service.search_wiki('cobalt', src_dir='project', wiki_dir='wiki', source_selection=profile,
                                      kinds=['modules'], mode='substring')
    assert any(row['path'] == module for row in result['results'])
    with pytest.raises(ValueError):
        search_service.search_wiki('cobalt', src_dir='project', wiki_dir='wiki', source_selection=profile,
                                  kinds=['modules'], discovery='qualified-v1')


def test_declared_qualified_capture_limits_are_separate_from_lexical_scan_limits(project):
    result = search()
    limits = result['discovery']['limits']
    assert limits['source_snapshot_bytes'] == 16_777_216 and limits['source_snapshot_files'] == 10000
    assert limits['native_read_bytes'] == 8_388_608 and limits['native_selectors'] == 100
    assert limits['native_records'] == 1000 and limits['native_expanded_bytes'] == 16_777_216


def test_source_indexing_preserves_pre_read_exclusion_of_unowned_and_missing_derived_pages(project, monkeypatch):
    manifest = SyncManifest.load(Path('wiki'))
    blocked = {'modules/unowned.md', *manifest.page_source_mappings}
    Path('wiki/modules/unowned.md').write_text('# Unowned\nCobalt hidden.\n')
    Path('src/owner.py').unlink()
    original = StorageReadSession.read
    def observe(self, relative, maximum):
        assert relative not in blocked, 'excluded source-index body read'
        return original(self, relative, maximum)
    monkeypatch.setattr(StorageReadSession, 'read', observe)
    result = search_service.search_wiki('cobalt', src_dir='src', wiki_dir='wiki',
        kinds=['modules', 'entities'], mode='ranked-v2', include_source=True)
    assert result['results'] == []
