"""Focused contract tests for sync manifest v5 operational state."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from llm_wiki_cli.services import io, sync_manifest
from llm_wiki_cli.services.knowledge_evidence import (
    ENTITY_OBSERVATION_SCOPE,
    MODULE_OBSERVATION_SCOPE,
    ConceptObservationBasis,
    hash_file,
    sha256_bytes,
)
from llm_wiki_cli.services.sync_manifest import (
    EVIDENCE_NOT_RECORDED,
    LEGACY_EVIDENCE_UNAVAILABLE,
    MANIFEST_FILENAME,
    MANIFEST_STATE_UNAVAILABLE,
    MANIFEST_VERSION,
    SOURCE_MAPPING_CHANGED,
    TOMBSTONE_SOURCE_MISSING,
    TOMBSTONE_UNKNOWN_PROVENANCE,
    ManifestArtifactHashes,
    ManifestEvidenceBaseline,
    ManifestPageSource,
    ManifestTombstone,
    SyncManifest,
    SyncManifestError,
)

EXTRACTOR_REF = "python-ast"
CONCEPT_HASH = sha256_bytes(b"concept observation")
SECOND_CONCEPT_HASH = sha256_bytes(b"second concept observation")
SURFACE_HASH = sha256_bytes(b"surface index")
KNOWLEDGE_HASH = sha256_bytes(b"knowledge index")
ENVELOPE_HASH = sha256_bytes(b"evaluated envelope")


def _reverse_mapping_order(value):
    if isinstance(value, dict):
        return {
            key: _reverse_mapping_order(item)
            for key, item in reversed(list(value.items()))
        }
    if isinstance(value, list):
        return [_reverse_mapping_order(item) for item in value]
    return value


def _write_duplicate_source(root: Path, content: str | None = None) -> str:
    source_path = "pkg/models.py"
    path = root / source_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        content or ("class User:\n    first: str\n\nclass User:\n    second: str\n"),
        encoding="utf-8",
    )
    return source_path


def _duplicate_inventory() -> dict[str, dict]:
    return {
        "pkg/models.py": {
            "language": "python",
            "imports": [],
            "functions": [],
            "classes": [
                {
                    "name": "User",
                    "attributes": [{"name": "first", "type": "str"}],
                    "methods": [],
                },
                {
                    "name": "User",
                    "attributes": [{"name": "second", "type": "str"}],
                    "methods": [],
                },
            ],
        }
    }


def _page_maps():
    return (
        {("User", "pkg/models.py"): "User_1"},
        {"pkg/models.py": "models"},
        {
            ("User", "pkg/models.py", 1): "User_1",
            ("User", "pkg/models.py", 2): "User_2",
        },
    )


def _basis(
    *,
    scope: str,
    source_hash: str,
    concept_hash: str | None = CONCEPT_HASH,
    reason: str | None = None,
    source_path: str = "pkg/models.py",
) -> ConceptObservationBasis:
    return ConceptObservationBasis(
        scope=scope,
        source_path=source_path,
        extractor_ref=EXTRACTOR_REF,
        source_content_hash=source_hash,
        concept_observation_hash=concept_hash,
        unknown_reason=reason,
    )


def _build_duplicate_manifest(
    root: Path,
    *,
    previous_manifest: SyncManifest | None = None,
    evidence_baselines=None,
    retained_page_paths=None,
) -> SyncManifest:
    entity_pages, module_pages, occurrence_pages = _page_maps()
    return SyncManifest.build_from_inventory(
        _duplicate_inventory(),
        str(root),
        entity_pages,
        module_pages,
        entity_occurrence_page_cache=occurrence_pages,
        previous_manifest=previous_manifest,
        evidence_baselines=evidence_baselines,
        retained_page_paths=retained_page_paths,
    )


def _empty_rebuild(
    root: Path,
    previous_manifest: SyncManifest | None = None,
    *,
    retained_page_paths=None,
) -> SyncManifest:
    return SyncManifest.build_from_inventory(
        {},
        str(root),
        {},
        {},
        previous_manifest=previous_manifest,
        retained_page_paths=retained_page_paths,
    )


def _valid_v5_payload() -> dict:
    source_hash = sha256_bytes(b"class App: pass\n")
    return {
        "version": MANIFEST_VERSION,
        "sources": {
            "src/app.py": {
                "hash": source_hash,
                "semantic_hash": sha256_bytes(b"semantic"),
                "language": "python",
                "entities": [],
                "entity_pages": {},
                "entity_page_occurrences": [],
                "module_page": "app",
            }
        },
        "surfaces": {},
        "generation_inputs": {},
        "page_source_mappings": {
            "modules/app.md": {
                "scope": MODULE_OBSERVATION_SCOPE,
                "source_path": "src/app.py",
            }
        },
        "evidence_baselines": {
            "modules/app.md": {
                "state": "known",
                "basis": {
                    "scope": MODULE_OBSERVATION_SCOPE,
                    "source_path": "src/app.py",
                    "extractor_ref": EXTRACTOR_REF,
                    "source_content_hash": source_hash,
                    "concept_observation_hash": CONCEPT_HASH,
                },
            }
        },
        "tombstones": {},
    }


def test_v4_migration_preserves_values_and_recovers_duplicate_occurrences():
    legacy = {
        "version": 4,
        "sources": {
            "pkg/models.py": {
                "hash": sha256_bytes(b"source"),
                "semantic_hash": sha256_bytes(b"semantic"),
                "generated_semantics": {"module": {"description": "café"}},
                "language": "python",
                "entities": ["User", "User"],
                "entity_pages": {"User": "User_1"},
                "entity_page_occurrences": [
                    {"name": "User", "page": "User_1", "occurrence": 1},
                    {"name": "User", "page": "User_2", "occurrence": 2},
                ],
                "module_page": "models",
                "legacy_extension": {"preserve": [2, 1]},
            }
        },
        "surfaces": {"flows": {"enabled": True, "categories": ["write", "read"]}},
        "generation_inputs": {
            "openapi_file": "api/openapi.json",
            "options": {"include_tests": False},
        },
    }
    original = deepcopy(legacy)

    migrated = SyncManifest.from_payload(legacy)
    reordered = SyncManifest.from_payload(_reverse_mapping_order(legacy))

    assert legacy == original
    assert migrated.sources == original["sources"]
    assert migrated.surfaces == original["surfaces"]
    assert migrated.generation_inputs == original["generation_inputs"]
    assert migrated.page_source_mappings == {
        "modules/models.md": ManifestPageSource(
            scope=MODULE_OBSERVATION_SCOPE,
            source_path="pkg/models.py",
        ),
        "entities/User_1.md": ManifestPageSource(
            scope=ENTITY_OBSERVATION_SCOPE,
            source_path="pkg/models.py",
            entity_name="User",
            occurrence=1,
        ),
        "entities/User_2.md": ManifestPageSource(
            scope=ENTITY_OBSERVATION_SCOPE,
            source_path="pkg/models.py",
            entity_name="User",
            occurrence=2,
        ),
    }
    assert set(migrated.evidence_baselines) == set(migrated.page_source_mappings)
    assert all(
        baseline == ManifestEvidenceBaseline.unknown(LEGACY_EVIDENCE_UNAVAILABLE)
        for baseline in migrated.evidence_baselines.values()
    )
    assert migrated.tombstones == {}
    assert migrated.artifact_hashes is None
    assert migrated.to_payload()["version"] == MANIFEST_VERSION
    assert migrated.to_json() == reordered.to_json()
    assert SyncManifest.from_payload(migrated.to_payload()).to_payload() == (
        migrated.to_payload()
    )


def test_v4_collapsed_duplicate_mapping_does_not_guess_later_occurrences():
    legacy = {
        "version": 4,
        "sources": {
            "pkg/models.py": {
                "language": "python",
                "entities": ["User", "User"],
                "entity_pages": {"User": "User"},
                "module_page": "models",
            }
        },
        "surfaces": {},
        "generation_inputs": {},
    }

    migrated = SyncManifest.from_payload(legacy)

    assert migrated.page_source_mappings == {
        "modules/models.md": ManifestPageSource(
            scope=MODULE_OBSERVATION_SCOPE,
            source_path="pkg/models.py",
        ),
        "entities/User.md": ManifestPageSource(
            scope=ENTITY_OBSERVATION_SCOPE,
            source_path="pkg/models.py",
            entity_name="User",
            occurrence=1,
        ),
    }
    assert "entities/User_2.md" not in migrated.evidence_baselines


def test_v4_migration_drops_ambiguous_page_mappings_independent_of_source_order():
    source_records = [
        (
            "pkg/a.py",
            {
                "language": "python",
                "entities": ["User"],
                "entity_pages": {"User": "User"},
                "module_page": "shared",
            },
        ),
        (
            "pkg/b.py",
            {
                "language": "python",
                "entities": ["User"],
                "entity_pages": {"User": "User"},
                "module_page": "shared",
            },
        ),
    ]

    def migrate(records):
        return SyncManifest.from_payload(
            {
                "version": 4,
                "sources": dict(records),
                "surfaces": {},
                "generation_inputs": {},
            }
        )

    forward = migrate(source_records)
    reverse = migrate(reversed(source_records))

    assert forward.page_source_mappings == {}
    assert forward.evidence_baselines == {}
    assert forward.to_json() == reverse.to_json()


def test_v4_migration_rejects_state_that_cannot_be_reloaded_as_v5():
    with pytest.raises(SyncManifestError) as source_exc:
        SyncManifest.from_payload(
            {
                "version": 4,
                "sources": {"../outside.py": {"module_page": "outside"}},
                "surfaces": {},
                "generation_inputs": {},
            }
        )
    assert source_exc.value.field == "sources.../outside.py"

    with pytest.raises(SyncManifestError) as surface_exc:
        SyncManifest.from_payload(
            {
                "version": 4,
                "sources": {},
                "surfaces": {"future": True},
                "generation_inputs": {},
            }
        )
    assert surface_exc.value.field == "surfaces.future"

    with pytest.raises(SyncManifestError) as inputs_exc:
        SyncManifest.from_payload(
            {
                "version": 4,
                "sources": {},
                "surfaces": {},
                "generation_inputs": [],
            }
        )
    assert inputs_exc.value.field == "generation_inputs"


def test_inventory_build_records_known_partial_unknown_and_duplicate_coordinates(
    tmp_path,
):
    source_path = _write_duplicate_source(tmp_path)
    source_hash = hash_file(tmp_path / source_path)
    module_basis = _basis(
        scope=MODULE_OBSERVATION_SCOPE,
        source_hash=source_hash,
    )
    first_basis = _basis(
        scope=ENTITY_OBSERVATION_SCOPE,
        source_hash=source_hash,
    )
    second_basis = _basis(
        scope=ENTITY_OBSERVATION_SCOPE,
        source_hash=source_hash,
        concept_hash=None,
        reason="insufficient-inventory-detail",
    )

    manifest = _build_duplicate_manifest(
        tmp_path,
        evidence_baselines={
            "modules/models.md": module_basis,
            "entities/User_1.md": first_basis,
            "entities/User_2.md": second_basis,
        },
    )

    assert manifest.page_source_mappings["entities/User_1.md"] == (
        ManifestPageSource(
            scope=ENTITY_OBSERVATION_SCOPE,
            source_path=source_path,
            entity_name="User",
            occurrence=1,
        )
    )
    assert manifest.page_source_mappings["entities/User_2.md"] == (
        ManifestPageSource(
            scope=ENTITY_OBSERVATION_SCOPE,
            source_path=source_path,
            entity_name="User",
            occurrence=2,
        )
    )
    assert manifest.evidence_baselines["modules/models.md"].is_known
    assert manifest.evidence_baselines["entities/User_1.md"].is_known
    second = manifest.evidence_baselines["entities/User_2.md"]
    assert not second.is_known
    assert second.basis == second_basis
    assert second.unknown_reason == "insufficient-inventory-detail"
    assert second.to_payload() == {
        "state": "unknown",
        "basis": second_basis.to_evidence_payload(),
        "unknown_reason": "insufficient-inventory-detail",
    }


def test_inventory_build_without_evidence_records_explicit_unknowns(tmp_path):
    _write_duplicate_source(tmp_path)

    manifest = _build_duplicate_manifest(tmp_path)

    assert set(manifest.evidence_baselines) == set(manifest.page_source_mappings)
    assert all(
        baseline == ManifestEvidenceBaseline.unknown(EVIDENCE_NOT_RECORDED)
        for baseline in manifest.evidence_baselines.values()
    )


def test_removal_retains_known_and_unknown_state_as_distinct_tombstones(
    tmp_path,
):
    source_path = _write_duplicate_source(tmp_path)
    source_hash = hash_file(tmp_path / source_path)
    known = _basis(
        scope=MODULE_OBSERVATION_SCOPE,
        source_hash=source_hash,
    )
    previous = _build_duplicate_manifest(
        tmp_path,
        evidence_baselines={
            "modules/models.md": known,
            "entities/User_1.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
            "entities/User_2.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
        },
    )

    removed = _empty_rebuild(
        tmp_path,
        previous,
        retained_page_paths={
            "modules/models.md",
            "entities/User_1.md",
            "entities/User_2.md",
        },
    )

    assert removed.evidence_baselines == {}
    assert removed.tombstones["modules/models.md"] == ManifestTombstone(
        reason=TOMBSTONE_SOURCE_MISSING,
        last_valid_basis=known,
    )
    assert removed.tombstones["entities/User_1.md"] == ManifestTombstone(
        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
        unknown_reason="inspection-unavailable",
    )
    assert removed.tombstones["entities/User_2.md"] == ManifestTombstone(
        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
        unknown_reason="inspection-unavailable",
    )
    assert set(removed.page_source_mappings) == set(removed.tombstones)


def test_page_coordinate_remap_never_claims_that_live_source_is_missing(tmp_path):
    source_path = _write_duplicate_source(tmp_path)
    source_hash = hash_file(tmp_path / source_path)
    previous = _build_duplicate_manifest(
        tmp_path,
        evidence_baselines={
            "modules/models.md": _basis(
                scope=MODULE_OBSERVATION_SCOPE,
                source_hash=source_hash,
            ),
            "entities/User_1.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
            "entities/User_2.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
        },
    )
    remapped = SyncManifest.build_from_inventory(
        _duplicate_inventory(),
        str(tmp_path),
        {("User", source_path): "RenamedUser"},
        {source_path: "renamed_models"},
        entity_occurrence_page_cache={
            ("User", source_path, 1): "RenamedUser",
            ("User", source_path, 2): "RenamedUser_2",
        },
        previous_manifest=previous,
        retained_page_paths={
            *previous.page_source_mappings,
            "modules/renamed_models.md",
            "entities/RenamedUser.md",
            "entities/RenamedUser_2.md",
        },
    )

    assert remapped.tombstones["modules/models.md"] == ManifestTombstone(
        reason=TOMBSTONE_UNKNOWN_PROVENANCE,
        unknown_reason=SOURCE_MAPPING_CHANGED,
    )
    assert all(
        tombstone.reason != TOMBSTONE_SOURCE_MISSING
        for tombstone in remapped.tombstones.values()
    )


def test_reseed_retained_page_without_manifest_state_is_unknown_provenance(
    tmp_path,
):
    wiki = tmp_path / "wiki"
    (wiki / "modules").mkdir(parents=True)
    (wiki / "modules" / "orphan.md").write_text(
        "# Content must not become evidence\n",
        encoding="utf-8",
    )

    reseeded = _empty_rebuild(
        tmp_path,
        retained_page_paths={"modules/orphan.md"},
    )

    assert reseeded.page_source_mappings == {}
    assert reseeded.evidence_baselines == {}
    assert reseeded.tombstones == {
        "modules/orphan.md": ManifestTombstone(
            reason=TOMBSTONE_UNKNOWN_PROVENANCE,
            unknown_reason=MANIFEST_STATE_UNAVAILABLE,
        )
    }


def test_unretained_removed_page_drops_mapping_and_tombstone(tmp_path):
    source_path = _write_duplicate_source(tmp_path)
    source_hash = hash_file(tmp_path / source_path)
    previous = _build_duplicate_manifest(
        tmp_path,
        evidence_baselines={
            "modules/models.md": _basis(
                scope=MODULE_OBSERVATION_SCOPE,
                source_hash=source_hash,
            ),
            "entities/User_1.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
            "entities/User_2.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
        },
    )

    removed = _empty_rebuild(
        tmp_path,
        previous,
        retained_page_paths=set(),
    )

    assert removed.page_source_mappings == {}
    assert removed.evidence_baselines == {}
    assert removed.tombstones == {}


def test_reappearance_restores_matching_known_basis_and_clears_tombstone(
    tmp_path,
):
    source_path = _write_duplicate_source(tmp_path)
    source_hash = hash_file(tmp_path / source_path)
    known = _basis(
        scope=MODULE_OBSERVATION_SCOPE,
        source_hash=source_hash,
    )
    previous = _build_duplicate_manifest(
        tmp_path,
        evidence_baselines={
            "modules/models.md": known,
            "entities/User_1.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
            "entities/User_2.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
        },
    )
    removed = _empty_rebuild(
        tmp_path,
        previous,
        retained_page_paths=set(previous.page_source_mappings),
    )

    reappeared = _build_duplicate_manifest(
        tmp_path,
        previous_manifest=removed,
    )

    assert reappeared.tombstones == {}
    assert reappeared.evidence_baselines["modules/models.md"] == (
        ManifestEvidenceBaseline.from_basis(known)
    )
    assert reappeared.evidence_baselines["entities/User_1.md"] == (
        ManifestEvidenceBaseline.unknown("inspection-unavailable")
    )


def test_reappearance_with_changed_source_does_not_restore_known_basis(
    tmp_path,
):
    source_path = _write_duplicate_source(tmp_path)
    source_hash = hash_file(tmp_path / source_path)
    known = _basis(
        scope=MODULE_OBSERVATION_SCOPE,
        source_hash=source_hash,
    )
    previous = _build_duplicate_manifest(
        tmp_path,
        evidence_baselines={
            "modules/models.md": known,
            "entities/User_1.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
            "entities/User_2.md": ManifestEvidenceBaseline.unknown(
                "inspection-unavailable"
            ),
        },
    )
    removed = _empty_rebuild(
        tmp_path,
        previous,
        retained_page_paths=set(previous.page_source_mappings),
    )
    _write_duplicate_source(
        tmp_path,
        "class User:\n    changed: bool\n\nclass User:\n    second: str\n",
    )

    reappeared = _build_duplicate_manifest(
        tmp_path,
        previous_manifest=removed,
    )

    assert reappeared.tombstones == {}
    module_baseline = reappeared.evidence_baselines["modules/models.md"]
    assert module_baseline == ManifestEvidenceBaseline.unknown(EVIDENCE_NOT_RECORDED)
    assert module_baseline.basis is None


def test_artifact_hashes_are_complete_optional_and_round_trip(tmp_path):
    manifest = SyncManifest().with_artifact_hashes(
        surface_index_hash=SURFACE_HASH,
        knowledge_index_hash=KNOWLEDGE_HASH,
        evaluated_envelope_hash=ENVELOPE_HASH,
    )

    assert manifest.artifact_hashes == ManifestArtifactHashes(
        surface_index_hash=SURFACE_HASH,
        knowledge_index_hash=KNOWLEDGE_HASH,
        evaluated_envelope_hash=ENVELOPE_HASH,
    )
    assert SyncManifest.from_payload(manifest.to_payload()) == manifest

    wiki = tmp_path / "wiki"
    manifest.save(wiki)
    assert SyncManifest.load(wiki) == manifest
    assert SyncManifest.load(wiki).to_json() == manifest.to_json()
    assert "artifact_hashes" not in manifest.without_artifact_hashes().to_payload()


@pytest.mark.parametrize(
    "missing_field",
    [
        "surface_index_hash",
        "knowledge_index_hash",
        "evaluated_envelope_hash",
    ],
)
def test_partial_artifact_hash_commitment_is_rejected(missing_field):
    payload = (
        SyncManifest()
        .with_artifact_hashes(
            surface_index_hash=SURFACE_HASH,
            knowledge_index_hash=KNOWLEDGE_HASH,
            evaluated_envelope_hash=ENVELOPE_HASH,
        )
        .to_payload()
    )
    del payload["artifact_hashes"][missing_field]

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == f"artifact_hashes.{missing_field}"


@pytest.mark.parametrize(
    "invalid_hash",
    [
        "sha256:abc",
        "sha256:" + "A" * 64,
        "0" * 64,
        None,
    ],
)
def test_malformed_artifact_hash_is_rejected(invalid_hash):
    payload = (
        SyncManifest()
        .with_artifact_hashes(
            surface_index_hash=SURFACE_HASH,
            knowledge_index_hash=KNOWLEDGE_HASH,
            evaluated_envelope_hash=ENVELOPE_HASH,
        )
        .to_payload()
    )
    payload["artifact_hashes"]["knowledge_index_hash"] = invalid_hash

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "artifact_hashes.knowledge_index_hash"


def test_rebuild_and_generation_state_changes_clear_artifact_commitment(
    tmp_path,
):
    committed = SyncManifest().with_artifact_hashes(
        surface_index_hash=SURFACE_HASH,
        knowledge_index_hash=KNOWLEDGE_HASH,
        evaluated_envelope_hash=ENVELOPE_HASH,
    )

    assert (
        committed.with_generation_state(
            surfaces={"flows": {"enabled": True}},
            generation_inputs={"include_tests": False},
        ).artifact_hashes
        is None
    )
    assert _empty_rebuild(tmp_path, committed).artifact_hashes is None


@pytest.mark.parametrize(
    ("version", "message"),
    [
        (True, "must be an integer"),
        (0, "must be positive"),
        (MANIFEST_VERSION + 1, "unsupported future manifest version"),
    ],
)
def test_manifest_version_validation_is_field_specific(version, message):
    payload = _valid_v5_payload()
    payload["version"] = version

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "version"
    assert message in exc_info.value.message


@pytest.mark.parametrize(
    "page_path",
    [
        "/modules/app.md",
        "modules/../app.md",
        "modules\\app.md",
        "module/app.md",
        "modules/app.txt",
        "modules/nested/app.md",
        "modules/app.md ",
    ],
)
def test_manifest_rejects_noncanonical_page_paths(page_path):
    payload = _valid_v5_payload()
    mapping = payload["page_source_mappings"].pop("modules/app.md")
    payload["page_source_mappings"][page_path] = mapping

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == f"page_source_mappings.{page_path}"


@pytest.mark.parametrize(
    ("source_path", "expected_field"),
    [
        ("/src/app.py", "page_source_mappings.modules/app.md.source_path"),
        ("D:src/app.py", "page_source_mappings.modules/app.md.source_path"),
        ("src/../app.py", "page_source_mappings.modules/app.md.source_path"),
        ("src\\app.py", "page_source_mappings.modules/app.md.source_path"),
        ("src/app.py ", "page_source_mappings.modules/app.md.source_path"),
    ],
)
def test_manifest_rejects_noncanonical_mapping_source_paths(
    source_path, expected_field
):
    payload = _valid_v5_payload()
    payload["page_source_mappings"]["modules/app.md"]["source_path"] = source_path

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == expected_field


@pytest.mark.parametrize("source_path", ["/src/app.py", "D:src/app.py"])
def test_manifest_rejects_noncanonical_v5_source_record_path(source_path):
    payload = _valid_v5_payload()
    payload["sources"][source_path] = payload["sources"].pop("src/app.py")

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == f"sources.{source_path}"


def test_inventory_build_rejects_drive_relative_source_before_hashing(
    tmp_path, monkeypatch
):
    def unexpected_source_read(_path):
        raise AssertionError("unsafe source path reached the filesystem")

    monkeypatch.setattr(sync_manifest, "hash_file", unexpected_source_read)

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.build_from_inventory(
            {"D:secret.py": {"language": "python", "classes": []}},
            str(tmp_path),
            {},
            {"D:secret.py": "secret"},
        )

    assert exc_info.value.field == "page_source_mappings.source_path"


def test_inventory_build_reuses_exact_source_hashes_without_reading(
    tmp_path, monkeypatch
):
    source_hash = sha256_bytes(b"class App: pass\n")
    inventory = {
        "src/app.py": {
            "language": "python",
            "classes": [],
            "functions": [],
        }
    }

    def unexpected_source_read(_path):
        raise AssertionError("build_from_inventory reread a captured source")

    monkeypatch.setattr(sync_manifest, "hash_file", unexpected_source_read)

    manifest = SyncManifest.build_from_inventory(
        inventory,
        str(tmp_path),
        {},
        {"src/app.py": "app"},
        source_content_hashes={"src/app.py": source_hash},
    )

    assert manifest.sources["src/app.py"]["hash"] == source_hash


@pytest.mark.parametrize(
    ("source_hashes", "field"),
    [
        ({}, "source_content_hashes.src/app.py"),
        (
            {
                "src/app.py": sha256_bytes(b"class App: pass\n"),
                "src/extra.py": sha256_bytes(b"pass\n"),
            },
            "source_content_hashes.src/extra.py",
        ),
        (
            {"src/app.py": "sha256:bad"},
            "source_content_hashes.src/app.py",
        ),
        (
            {"/tmp/app.py": sha256_bytes(b"class App: pass\n")},
            "source_content_hashes./tmp/app.py",
        ),
    ],
)
def test_inventory_build_rejects_invalid_captured_source_hashes(
    tmp_path, source_hashes, field
):
    inventory = {
        "src/app.py": {
            "language": "python",
            "classes": [],
            "functions": [],
        }
    }

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.build_from_inventory(
            inventory,
            str(tmp_path),
            {},
            {"src/app.py": "app"},
            source_content_hashes=source_hashes,
        )

    assert exc_info.value.field == field


def test_inventory_build_keeps_file_hash_compatibility_path(tmp_path, monkeypatch):
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_text("class App: pass\n", encoding="utf-8")
    inventory = {
        "src/app.py": {
            "language": "python",
            "classes": [],
            "functions": [],
        }
    }
    real_hash_file = sync_manifest.hash_file
    calls: list[Path] = []

    def tracking_hash_file(path):
        calls.append(path)
        return real_hash_file(path)

    monkeypatch.setattr(sync_manifest, "hash_file", tracking_hash_file)

    manifest = SyncManifest.build_from_inventory(
        inventory,
        str(tmp_path),
        {},
        {"src/app.py": "app"},
    )

    assert calls == [source]
    assert manifest.sources["src/app.py"]["hash"] == sha256_bytes(b"class App: pass\n")


def test_manifest_rejects_page_scope_mismatch():
    payload = _valid_v5_payload()
    payload["page_source_mappings"]["entities/app.md"] = payload[
        "page_source_mappings"
    ].pop("modules/app.md")
    payload["evidence_baselines"]["entities/app.md"] = payload[
        "evidence_baselines"
    ].pop("modules/app.md")

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "page_source_mappings.entities/app.md.scope"


def test_manifest_rejects_mapping_without_evidence_state():
    payload = _valid_v5_payload()
    payload["evidence_baselines"] = {}

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "page_source_mappings.modules/app.md"


def test_manifest_rejects_baseline_without_mapping():
    payload = _valid_v5_payload()
    payload["page_source_mappings"] = {}

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "evidence_baselines.modules/app.md"


def test_manifest_rejects_baseline_tombstone_overlap():
    payload = _valid_v5_payload()
    payload["tombstones"]["modules/app.md"] = {
        "reason": TOMBSTONE_UNKNOWN_PROVENANCE,
        "unknown_reason": "inspection-unavailable",
    }

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "evidence_baselines.modules/app.md"


@pytest.mark.parametrize(
    ("basis_field", "value"),
    [
        ("scope", ENTITY_OBSERVATION_SCOPE),
        ("source_path", "src/other.py"),
    ],
)
def test_manifest_rejects_basis_mapping_coordinate_mismatch(basis_field, value):
    payload = _valid_v5_payload()
    payload["evidence_baselines"]["modules/app.md"]["basis"][basis_field] = value

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == (
        f"evidence_baselines.modules/app.md.basis.{basis_field}"
    )


def test_manifest_rejects_active_mapping_to_absent_source_record():
    payload = _valid_v5_payload()
    payload["sources"] = {}

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == ("page_source_mappings.modules/app.md.source_path")


def test_manifest_rejects_active_basis_hash_mismatching_source_record():
    payload = _valid_v5_payload()
    payload["evidence_baselines"]["modules/app.md"]["basis"]["source_content_hash"] = (
        sha256_bytes(b"different source")
    )

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == (
        "evidence_baselines.modules/app.md.basis.source_content_hash"
    )


def test_manifest_rejects_known_tombstone_without_source_mapping():
    payload = _valid_v5_payload()
    basis = payload["evidence_baselines"]["modules/app.md"]["basis"]
    payload["page_source_mappings"] = {}
    payload["evidence_baselines"] = {}
    payload["tombstones"] = {
        "modules/app.md": {
            "reason": TOMBSTONE_SOURCE_MISSING,
            "last_valid_basis": basis,
        }
    }

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "tombstones.modules/app.md"


def test_manifest_rejects_unknown_entity_mapping_without_occurrence():
    payload = _valid_v5_payload()
    payload["page_source_mappings"] = {
        "entities/App.md": {
            "scope": ENTITY_OBSERVATION_SCOPE,
            "source_path": "src/app.py",
            "entity_name": "App",
        }
    }
    payload["evidence_baselines"] = {
        "entities/App.md": {
            "state": "unknown",
            "unknown_reason": "inspection-unavailable",
        }
    }

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "page_source_mappings.entities/App.md.occurrence"


def test_manifest_v5_rejects_unknown_top_level_fields():
    payload = _valid_v5_payload()
    payload["unexpected"] = True

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.from_payload(payload)

    assert exc_info.value.field == "manifest.unexpected"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (
            '{"version":5,"version":5}\n',
            "contains duplicate JSON key 'version'",
        ),
        (
            '{"version":5,"sources":{"src/app.py":{},"src/app.py":{}}}\n',
            "contains duplicate JSON key 'src/app.py'",
        ),
        ('{"version":NaN}\n', "contains non-finite JSON number 'NaN'"),
        ('{"version":Infinity}\n', "contains non-finite JSON number 'Infinity'"),
        ('{"version":-Infinity}\n', "contains non-finite JSON number '-Infinity'"),
    ],
)
def test_manifest_load_strictly_rejects_duplicate_keys_and_nonfinite_numbers(
    tmp_path,
    content,
    message,
):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / MANIFEST_FILENAME).write_text(content, encoding="utf-8")

    with pytest.raises(SyncManifestError) as exc_info:
        SyncManifest.load(wiki)

    assert exc_info.value.field == "manifest"
    assert exc_info.value.message == message


def test_manifest_save_cleans_temp_and_preserves_marker_on_replace_failure(
    tmp_path, monkeypatch
):
    wiki = tmp_path / "wiki"
    original = SyncManifest()
    original.save(wiki)
    marker = wiki / MANIFEST_FILENAME
    original_bytes = marker.read_bytes()
    replacement = SyncManifest(
        surfaces={"flows": {"enabled": True}},
        generation_inputs={"include_tests": False},
    )

    def fail_replace(source, destination):
        assert Path(source).parent == wiki
        assert Path(destination) == marker
        raise OSError("manifest marker replace failed")

    monkeypatch.setattr(io.os, "replace", fail_replace)

    with pytest.raises(OSError, match="manifest marker replace failed"):
        replacement.save(wiki)

    assert marker.read_bytes() == original_bytes
    assert not list(wiki.glob(f".{MANIFEST_FILENAME}.*.tmp"))


@pytest.mark.parametrize(
    "invalid_value",
    [
        float("nan"),
        float("inf"),
        object(),
        "\ud800",
    ],
)
def test_manifest_save_serialization_failure_creates_no_temp(tmp_path, invalid_value):
    wiki = tmp_path / "wiki"
    original = SyncManifest()
    original.save(wiki)
    marker = wiki / MANIFEST_FILENAME
    original_bytes = marker.read_bytes()
    invalid = SyncManifest(
        generation_inputs={"invalid": invalid_value},
    )

    with pytest.raises((TypeError, ValueError, UnicodeEncodeError)):
        invalid.save(wiki)

    assert marker.read_bytes() == original_bytes
    assert not list(wiki.glob(f".{MANIFEST_FILENAME}.*.tmp"))
