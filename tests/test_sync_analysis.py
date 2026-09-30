"""Ownership contracts for entity renames inferred from prior manifests."""

import pytest

from llm_wiki_cli.services.bootstrap_runtime import (
    build_entity_page_map,
    build_module_page_map,
)
from llm_wiki_cli.services.knowledge_evidence import semantic_hash_for_file
from llm_wiki_cli.services.sync_analysis import SyncOwnershipError, compute_sync_diff
from llm_wiki_cli.services.sync_manifest import (
    ManifestPageSource,
    ManifestTombstone,
    SyncManifest,
    TOMBSTONE_UNKNOWN_PROVENANCE,
)


def _inventory(**modules):
    return {
        f"pkg/{module}.py": {
            "language": "python",
            "classes": [{"name": name, "line": index + 1} for index, name in enumerate(names)],
            "functions": [],
            "imports": [],
        }
        for module, names in modules.items()
    }


def _hashes(inventory):
    return {path: semantic_hash_for_file(data) for path, data in inventory.items()}


def _manifest(inventory):
    return SyncManifest.build_from_inventory(
        inventory,
        ".",
        build_entity_page_map(inventory),
        build_module_page_map(inventory),
        source_content_hashes=_hashes(inventory),
    )


def _diff(manifest, inventory):
    return compute_sync_diff(manifest, inventory, ".", source_content_hashes=_hashes(inventory))


@pytest.mark.parametrize("reverse_sources", [False, True])
@pytest.mark.parametrize("reverse_inventory", [False, True])
def test_only_the_original_source_can_rename_its_page(reverse_sources, reverse_inventory):
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    current = _inventory(alpha=["Draft"], beta=["Other", "Draft"])
    if reverse_sources:
        manifest.sources = dict(reversed(list(manifest.sources.items())))
    if reverse_inventory:
        current = dict(reversed(list(current.items())))
    before = manifest.to_json()

    diff = _diff(manifest, current)

    assert diff.renamed_entity_pages == {("Draft", "pkg/alpha.py"): ("Draft", "alpha_Draft")}
    assert manifest.to_json() == before
    assert diff.changed_files == ["pkg/beta.py"]
    assert diff.moved_entities == {}


@pytest.mark.parametrize("version", [1, 2, 3, 4])
def test_unique_legacy_member_can_use_an_unqualified_fallback(version):
    old = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    for info in old.sources.values():
        info.pop("entity_pages")
        info.pop("entity_page_occurrences")
    legacy = SyncManifest.from_payload({"version": version, "sources": old.sources})

    diff = _diff(legacy, _inventory(alpha=["Draft"], beta=["Other", "Draft"]))

    assert diff.renamed_entity_pages == {("Draft", "pkg/alpha.py"): ("Draft", "alpha_Draft")}


@pytest.mark.parametrize("record_kind", ["coordinate", "occurrence"])
def test_recorded_page_is_used_when_legacy_projection_is_absent(record_kind):
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Draft"]))
    for info in manifest.sources.values():
        info.pop("entity_pages")
        if record_kind == "coordinate":
            info.pop("entity_page_occurrences")
    if record_kind == "occurrence":
        manifest.page_source_mappings = {}

    diff = _diff(manifest, _inventory(alpha=["Draft"], beta=["Other"]))

    assert diff.renamed_entity_pages == {("Draft", "pkg/alpha.py"): ("alpha_Draft", "Draft")}


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("private", [False, True])
def test_ambiguous_legacy_fallback_never_claims_shared_page(reverse, private):
    old = _manifest(_inventory(alpha=["Draft"], beta=["_Draft" if private else "Draft"]))
    for info in old.sources.values():
        info.pop("entity_pages")
        info.pop("entity_page_occurrences")
    sources = dict(reversed(list(old.sources.items()))) if reverse else old.sources
    legacy = SyncManifest.from_payload({"version": 4, "sources": sources})

    with pytest.raises(SyncOwnershipError, match="claimed by multiple source coordinates"):
        _diff(legacy, _inventory(alpha=["Draft"], beta=["_Draft" if private else "Draft"]))


@pytest.mark.parametrize("reverse", [False, True])
def test_legacy_ambiguous_explicit_mappings_remain_conflicts_after_migration(reverse):
    old = _manifest(_inventory(alpha=["Draft"], beta=["Draft"]))
    for info in old.sources.values():
        info["entity_pages"]["Draft"] = "Draft"
        info.pop("entity_page_occurrences")
    sources = dict(reversed(list(old.sources.items()))) if reverse else old.sources
    legacy = SyncManifest.from_payload({"version": 4, "sources": sources})
    assert "entities/Draft.md" not in legacy.page_source_mappings

    with pytest.raises(SyncOwnershipError, match="claimed by multiple source coordinates"):
        _diff(legacy, _inventory(alpha=["Draft"], beta=["Draft"]))


@pytest.mark.parametrize("record_kind", ["projection", "occurrence", "coordinate"])
def test_contradictory_recorded_names_cannot_rename_a_page(record_kind):
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    if record_kind == "projection":
        manifest.sources["pkg/alpha.py"]["entity_pages"]["Draft"] = "Wrong"
    elif record_kind == "occurrence":
        manifest.sources["pkg/alpha.py"]["entity_page_occurrences"][0]["page"] = "Wrong"
    else:
        manifest.page_source_mappings["entities/Wrong.md"] = (
            manifest.page_source_mappings["entities/Draft.md"]
        )

    with pytest.raises(SyncOwnershipError, match="contradictory recorded pages"):
        _diff(manifest, _inventory(alpha=["Draft"], beta=["Other", "Draft"]))


def test_portable_alias_cannot_hide_another_source_owner():
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    manifest.page_source_mappings["entities/draft.md"] = ManifestPageSource(
        scope="entity", source_path="pkg/beta.py", entity_name="Other", occurrence=1
    )
    with pytest.raises(SyncOwnershipError, match="claimed by multiple source coordinates"):
        _diff(manifest, _inventory(alpha=["Draft"], beta=["Other", "Draft"]))


def test_retained_page_owner_is_not_ignored_when_its_source_is_absent():
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    manifest.page_source_mappings["entities/draft.md"] = ManifestPageSource(
        scope="entity", source_path="pkg/removed.py", entity_name="Draft", occurrence=1
    )
    with pytest.raises(SyncOwnershipError, match="claimed by multiple source coordinates"):
        _diff(manifest, _inventory(alpha=["Draft"], beta=["Other", "Draft"]))


@pytest.mark.parametrize("legacy", [False, True])
def test_unchanged_duplicate_declarations_do_not_reuse_the_first_occurrence(legacy):
    inventory = _inventory(alpha=["Draft", "Draft"])
    manifest = _manifest(inventory)
    if legacy:
        manifest.sources["pkg/alpha.py"].pop("entity_page_occurrences")
        manifest = SyncManifest.from_payload({"version": 4, "sources": manifest.sources})

    assert _diff(manifest, inventory).renamed_entity_pages == {}


def test_new_occurrence_has_no_claim_on_the_first_declarations_old_page():
    manifest = _manifest(_inventory(alpha=["Draft"]))
    diff = _diff(manifest, _inventory(alpha=["Draft", "Draft"]))
    assert diff.renamed_entity_pages == {}


def test_repeated_declarations_requiring_separate_renames_fail_conservatively():
    manifest = _manifest(_inventory(alpha=["Draft", "Draft"]))
    with pytest.raises(SyncOwnershipError, match="occurrence-specific moves"):
        _diff(manifest, _inventory(alpha=["Draft", "Draft"], beta=["Draft"]))


def test_unique_source_move_keeps_existing_diff_contract():
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    diff = _diff(manifest, _inventory(beta=["Other", "Draft"]))
    assert diff.moved_entities == {"Draft": ("pkg/alpha.py", "pkg/beta.py")}
    assert diff.renamed_entity_pages == {}


def test_repeated_declarations_do_not_prove_a_unique_source_move():
    manifest = _manifest(_inventory(alpha=["Draft", "Draft"]))
    with pytest.raises(SyncOwnershipError, match="source move ambiguous"):
        _diff(manifest, _inventory(beta=["Draft"]))


def test_retained_alias_does_not_compete_with_the_current_page_for_the_same_owner():
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    manifest.page_source_mappings["entities/Historical.md"] = (
        manifest.page_source_mappings["entities/Draft.md"]
    )
    manifest.tombstones["entities/Historical.md"] = ManifestTombstone(
        reason=TOMBSTONE_UNKNOWN_PROVENANCE, unknown_reason="legacy-manifest-no-evidence"
    )
    diff = _diff(manifest, _inventory(alpha=["Draft"], beta=["Other", "Draft"]))
    assert diff.renamed_entity_pages == {("Draft", "pkg/alpha.py"): ("Draft", "alpha_Draft")}


@pytest.mark.parametrize("record_kind", ["projection", "occurrence", "coordinate"])
def test_recorded_coordinate_cannot_disagree_with_prior_membership(record_kind):
    manifest = _manifest(_inventory(alpha=["Draft"], beta=["Other"]))
    source = manifest.sources["pkg/alpha.py"]
    if record_kind == "projection":
        source["entity_pages"]["Ghost"] = "Ghost"
    elif record_kind == "occurrence":
        source["entity_page_occurrences"].append(
            {"name": "Draft", "occurrence": 2, "page": "Draft_2"}
        )
    else:
        manifest.page_source_mappings["entities/Ghost.md"] = ManifestPageSource(
            scope="entity", source_path="pkg/alpha.py", entity_name="Ghost", occurrence=1
        )
    with pytest.raises(SyncOwnershipError, match="prior source membership"):
        _diff(manifest, _inventory(alpha=["Draft"], beta=["Other", "Draft"]))
