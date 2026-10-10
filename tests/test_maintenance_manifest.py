"""Explicit maintenance authority survives flat/indexed operational codecs."""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator  # pyright: ignore[reportMissingModuleSource]
import pytest

from llm_wiki_cli.config import EXTRACTOR_REGISTRY
from llm_wiki_cli.services.analysis_capture import capture_analysis
from llm_wiki_cli.services.knowledge_storage import (
    KnowledgeStorageError,
    canonical_bytes,
    digest,
)
from llm_wiki_cli.services.maintenance_state import (
    canonical_hash,
    maintenance_core,
    maintenance_state_hash,
    new_identity,
)
from llm_wiki_cli.services.manifest_storage import (
    ManifestStoreReader,
    build_manifest_store,
    current_manifest_format,
    object_path,
    read_manifest_header,
)
from llm_wiki_cli.services.python_implementation import (
    analysis_identity,
    capture,
    producer,
)
from llm_wiki_cli.services.source_selection import resolve_source_selection
from llm_wiki_cli.services.sync_manifest import (
    MANIFEST_FILENAME,
    MANIFEST_VERSION,
    ManifestEvidenceBaseline,
    ManifestPageSource,
    SyncManifest,
    SyncManifestError,
    prune_manifest_for_source_selection,
)


def _authority(*, acknowledged=False):
    core = maintenance_core()
    guard = {
        "schema_version": "llm-wiki-maintenance-adoption/v1",
        "adoption_id": new_identity(),
        "min_manifest_version": 7,
        "features": {
            "implementation_evidence": 1,
            "maintenance_state": 1,
            "ordinary_acknowledgment": 1,
        },
    }
    text = "class Batch:\n    def cap(self, values):\n        return values[:3]\n"
    analysis = analysis_identity(
        capture_analysis(EXTRACTOR_REGISTRY, languages={"python"})
    )
    assert analysis is not None
    captured = capture(
        ast.parse(text),
        text.encode(),
        "policy.py",
        configured=producer(analysis),
        parsed_source=text,
    )
    evidence = next(
        row["evidence"]
        for row in captured["observations"]
        if row["evidence"]["scope"] == "module"
    )
    target = {
        "canonical_path": "modules/policy.md",
        "section_locator": "llm-wiki://modules/policy#section/Description~1",
        "ownership": "semantic",
    }
    record = new_identity()
    observation = core.observation(
        evidence, digest(b"Retained policy rationale.\n"), target=target
    )
    state = core.initial_state(guard, {record: observation})
    if acknowledged:
        state = core.transition(
            state,
            {
                "schema_version": "llm-wiki-maintenance-event/v1",
                "kind": "acknowledge",
                "record_id": record,
                "expected_state_hash": canonical_hash(state),
                "basis": observation["basis"],
                "actor": {
                    "kind": "agent",
                    "actor_id": "codec-check",
                    "authority": "ordinary-maintenance",
                },
            },
            observation["basis"],
        )
    manifest = SyncManifest(
        sources={"policy.py": {"hash": evidence["source_hash"], "language": "python"}},
        page_source_mappings={
            "modules/policy.md": ManifestPageSource("module", "policy.py")
        },
        evidence_baselines={
            "modules/policy.md": ManifestEvidenceBaseline.unknown(
                "evidence-not-recorded"
            )
        },
    ).with_maintenance_state(state)
    manifest = manifest.with_artifact_hashes(
        surface_index_hash=digest(b"surface fixture"),
        knowledge_index_hash=digest(b"knowledge fixture"),
        evaluated_envelope_hash=digest(b"envelope fixture"),
    )
    return guard, state, manifest, record


def _read(store):
    return SyncManifest.from_payload(
        json.loads(store.root_bytes), object_reader=lambda path, _: store.objects[path]
    )


def _payload(manifest) -> dict[str, Any]:
    return cast(dict[str, Any], manifest.to_payload())


@pytest.mark.parametrize("acknowledged", [False, True])
def test_explicit_adoption_flat_and_indexed_roundtrip_preserve_exact_owner(
    acknowledged,
):
    guard, state, manifest, record = _authority(acknowledged=acknowledged)
    payload = _payload(manifest)
    assert MANIFEST_VERSION == 5
    assert payload["version"] == 7
    assert payload["adoption_id"] == guard["adoption_id"]
    assert payload["maintenance_state_hash"] == maintenance_state_hash(state)
    assert state["guard_hash"] == digest(canonical_bytes(guard))
    assert (
        payload["artifact_hashes"]["maintenance_adoption_hash"] == state["guard_hash"]
    )
    flat = SyncManifest.from_payload(payload)
    assert flat.to_payload() == payload and flat.storage_version == 7
    store = build_manifest_store(payload)
    root = json.loads(store.root_bytes)
    assert (root["version"], root["logical_version"]) == (8, 7)
    assert "maintenance_state" in root["catalogs"]
    assert _read(store).to_payload() == payload and _read(store).storage_version == 8
    indexed_state = _read(store).maintenance_state
    assert indexed_state is not None
    assert indexed_state["records"][record] == state["records"][record]
    assert all(len(raw) <= 65_536 for raw in store.objects.values())


def test_legacy_emission_and_indexed_materialization_are_unchanged():
    legacy = SyncManifest(generation_inputs={"example": "legacy policy"})
    payload = legacy.to_payload()
    assert payload["version"] == 5 and "maintenance_state" not in payload
    assert "adoption_id" not in payload and "maintenance_state_hash" not in payload
    store = build_manifest_store(payload)
    assert (
        json.loads(store.root_bytes)["version"],
        json.loads(store.root_bytes)["logical_version"],
    ) == (6, 5)
    assert _read(store).to_payload() == payload
    header = read_manifest_header(store.root_bytes, lambda p, _: store.objects[p])
    assert header.adoption_id is None and header.maintenance_state_hash is None


def test_large_empty_authority_catalogs_keep_root_and_objects_bounded():
    guard = {
        "schema_version": "llm-wiki-maintenance-adoption/v1",
        "adoption_id": new_identity(), "min_manifest_version": 7,
        "features": {"implementation_evidence": 1, "maintenance_state": 1, "ordinary_acknowledgment": 1},
    }
    state = maintenance_core().initial_state(guard, {})
    manifest = SyncManifest(sources={
        f"src/unit_{index}.py": {"language": "python", "hash": digest(b"VALUE=1\n"), "notes": "é" * 60}
        for index in range(10_000)
    }).with_maintenance_state(state).with_artifact_hashes(
        surface_index_hash=digest(b"surface"), knowledge_index_hash=digest(b"knowledge"),
        evaluated_envelope_hash=digest(b"envelope"),
    )
    store = build_manifest_store(manifest.to_payload())
    assert len(store.root_bytes) <= 65_536
    assert len(store.objects) > 2
    assert all(len(raw) <= 65_536 for raw in store.objects.values())
    assert _read(store).to_payload() == manifest.to_payload()
    with pytest.raises(KnowledgeStorageError, match="64 KiB"):
        read_manifest_header(manifest.to_json().encode(), lambda p, _: store.objects[p])


def test_v8_selected_header_is_explicitly_partial_and_does_not_read_state_catalog():
    _, state, manifest, _ = _authority()
    store = build_manifest_store(manifest.to_payload())
    root = json.loads(store.root_bytes)
    state_object = object_path(root["catalogs"]["maintenance_state"]["hash"])
    reads = []

    def read(path, _):
        reads.append(path)
        if path == state_object:
            raise AssertionError(
                "selected policy/header must not silently materialize maintenance history"
            )
        return store.objects[path]

    header = read_manifest_header(store.root_bytes, read)
    assert header.storage_version == 8
    assert header.adoption_id == state["adoption_id"]
    assert header.maintenance_state_hash == maintenance_state_hash(state)
    assert not header.whole_maintenance_state_validated
    assert state_object not in reads


@pytest.mark.parametrize(
    "field", ["adoption_id", "maintenance_state_hash", "maintenance_state"]
)
def test_adopted_flat_root_requires_every_authority_field(field):
    _, _, manifest, _ = _authority()
    payload = _payload(manifest)
    del payload[field]
    with pytest.raises(SyncManifestError):
        SyncManifest.from_payload(payload)


@pytest.mark.parametrize("field", ["adoption_id", "maintenance_state_hash"])
def test_corrupted_root_maintenance_binding_is_rejected_full(field):
    _, _, manifest, _ = _authority()
    payload = _payload(manifest)
    payload[field] = (
        new_identity() if field == "adoption_id" else digest(b"wrong state")
    )
    with pytest.raises(SyncManifestError):
        SyncManifest.from_payload(payload)
    store = build_manifest_store(manifest.to_payload())
    root = json.loads(store.root_bytes)
    root["header"][field] = payload[field]
    with pytest.raises((SyncManifestError, KnowledgeStorageError)):
        SyncManifest.from_payload(root, object_reader=lambda p, _: store.objects[p])


def test_corrupted_indexed_authority_object_cannot_pass_full_validation():
    _, _, manifest, _ = _authority()
    store = build_manifest_store(manifest.to_payload())
    root = json.loads(store.root_bytes)
    corrupt = dict(store.objects)
    corrupt[object_path(root["catalogs"]["maintenance_state"]["hash"])] = b"{}\n"
    # Header deliberately does not claim this unread ledger valid.
    assert not read_manifest_header(
        store.root_bytes, lambda p, _: corrupt[p]
    ).whole_maintenance_state_validated
    with pytest.raises(KnowledgeStorageError, match="commitment"):
        SyncManifest.from_payload(root, object_reader=lambda p, _: corrupt[p])


def test_marker_commitment_and_version_pair_cannot_be_mixed():
    _, _, manifest, _ = _authority()
    payload = _payload(manifest)
    payload["artifact_hashes"]["maintenance_adoption_hash"] = digest(b"other marker")
    with pytest.raises(SyncManifestError, match="guard"):
        SyncManifest.from_payload(payload)
    store = build_manifest_store(manifest.to_payload())
    root = json.loads(store.root_bytes)
    root["logical_version"] = 5
    with pytest.raises(KnowledgeStorageError, match="indexed"):
        ManifestStoreReader(root, lambda p, _: store.objects[p])


@pytest.mark.parametrize("mutation", ["missing-header", "inline-state", "catalog-size", "state-expansion", "missing-marker"])
def test_v8_header_rejects_invalid_ownership_and_catalog_bounds(mutation):
    _, _, manifest, _ = _authority()
    store = build_manifest_store(manifest.to_payload())
    root = json.loads(store.root_bytes)
    if mutation == "missing-header":
        del root["header"]["adoption_id"]
    elif mutation == "inline-state":
        root["header"]["maintenance_state"] = {}
    elif mutation == "catalog-size":
        root["catalogs"]["maintenance_state"]["bytes"] = 65_537
    elif mutation == "state-expansion":
        root["catalogs"]["maintenance_state"]["expanded_bytes"] = 64 * 1024 * 1024 + 1
    else:
        del root["artifact_hashes"]["maintenance_adoption_hash"]
    with pytest.raises((SyncManifestError, KnowledgeStorageError, ValueError)):
        read_manifest_header(canonical_bytes(root), lambda p, _: store.objects[p])


def test_codec_authority_is_detached_and_cannot_bypass_shared_state_limit(monkeypatch):
    _, state, manifest, _ = _authority()
    incoming = deepcopy(state)
    updated = manifest.with_maintenance_state(incoming)
    incoming["generation"] += 1
    assert updated.maintenance_state == state
    payload = _payload(updated)
    payload["maintenance_state"]["generation"] += 1
    assert updated.maintenance_state == state
    from llm_wiki_cli.services import maintenance_state
    monkeypatch.setitem(maintenance_state.LIMITS, "state_bytes", len(canonical_bytes(state)) - 1)
    with pytest.raises(SyncManifestError, match="64 MiB"):
        SyncManifest.from_payload(manifest.to_payload())


def test_copy_generation_rebuild_and_source_pruning_preserve_authority(tmp_path):
    _, state, manifest, _ = _authority(acknowledged=True)
    (tmp_path / "other.py").write_text("VALUE=1\n")
    candidates = [
        manifest.without_artifact_hashes(),
        manifest.with_generation_state(surfaces={}, generation_inputs={}),
    ]
    candidates.append(
        SyncManifest.build_from_inventory({}, "", {}, {}, previous_manifest=manifest)
    )
    profile = tmp_path / ".llm-wiki" / "source-selection.json"
    profile.parent.mkdir()
    profile.write_text(
        json.dumps(
            {
                "schema_version": "llm-wiki-source-selection/v1",
                "include": ["other.py"],
                "exclude": [],
            }
        )
    )
    policy = resolve_source_selection(tmp_path, ".llm-wiki/source-selection.json")
    candidates.append(prune_manifest_for_source_selection(manifest, policy).manifest)
    for candidate in candidates:
        assert candidate.maintenance_state == state
        assert candidate.to_payload()["version"] == 7
    indexed = _read(build_manifest_store(manifest.to_payload()))
    assert (
        indexed.with_generation_state(surfaces={}, generation_inputs={}).storage_version
        == 8
    )
    rebuilt = SyncManifest.build_from_inventory({}, "", {}, {}, previous_manifest=indexed)
    assert rebuilt.storage_version == 8 and rebuilt.maintenance_state == state


def test_adopted_authority_cannot_be_removed_or_written_outside_transaction(tmp_path):
    _, _, manifest, _ = _authority()
    with pytest.raises(SyncManifestError, match="removed"):
        replace(manifest, maintenance_state=None, artifact_hashes=None).to_payload()
    with pytest.raises(SyncManifestError, match="manifest-last"):
        manifest.save(tmp_path)
    (tmp_path / MANIFEST_FILENAME).write_text(manifest.to_json())
    with pytest.raises(SyncManifestError, match="legacy"):
        SyncManifest().save(tmp_path)


@pytest.mark.parametrize("content", [None, "invalid json", "legacy"])
def test_marker_with_missing_corrupt_or_legacy_owner_requires_recovery(
    tmp_path, content
):
    guard, _, _, _ = _authority()
    (tmp_path / ".llm-wiki-maintenance-adoption.json").write_bytes(
        canonical_bytes(guard)
    )
    if content is not None:
        (tmp_path / MANIFEST_FILENAME).write_text(
            SyncManifest().to_json() if content == "legacy" else content
        )
    with pytest.raises(KnowledgeStorageError, match="restore"):
        current_manifest_format(tmp_path)


@pytest.mark.parametrize("version", [7, 8])
def test_packaged_version_schema_accepts_typed_codec_and_rejects_missing_bindings(
    version,
):
    _, _, manifest, _ = _authority()
    payload = (
        _payload(manifest)
        if version == 7
        else json.loads(build_manifest_store(manifest.to_payload()).root_bytes)
    )
    path = (
        Path(__file__).parents[1]
        / "src/llm_wiki_cli/schemas"
        / f"llm-wiki-manifest-v{version}.schema.json"
    )
    validator = Draft202012Validator(json.loads(path.read_text()))
    validator.validate(payload)
    invalid = deepcopy(payload)
    del (invalid if version == 7 else invalid["header"])["maintenance_state_hash"]
    assert list(validator.iter_errors(invalid))
