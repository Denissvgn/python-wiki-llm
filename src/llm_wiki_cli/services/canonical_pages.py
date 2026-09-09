"""Canonical generated page names and explicitly retained removal history."""

from __future__ import annotations

from collections.abc import Mapping

from .infrastructure_sync import (
    build_infrastructure_page_map,
    infrastructure_evidence_by_page,
)
from .sync_manifest import SyncManifest, TOMBSTONE_SOURCE_MISSING


def canonical_generated_pages(
    inventory: dict,
    infrastructure_inventory: Mapping[str, object],
    *,
    manifest: SyncManifest | None = None,
) -> dict[str, set[str]]:
    """Use the generator's mappers; only known removal records extend live names."""
    from .bootstrap_runtime import (
        build_entity_occurrence_page_map,
        build_module_page_map,
    )

    modules = build_module_page_map(inventory)
    entities = build_entity_occurrence_page_map(inventory, modules)
    allowed = {
        "modules": {f"modules/{name}.md" for name in modules.values()},
        "entities": {f"entities/{name}.md" for name in entities.values()},
        "infrastructure": set(
            build_infrastructure_page_map(infrastructure_inventory).values()
        ),
    }
    if manifest is None:
        return allowed
    # Also validate manually supplied manifests, not just those loaded from disk.
    manifest.to_payload()
    for path, tombstone in manifest.tombstones.items():
        if tombstone.reason == TOMBSTONE_SOURCE_MISSING:
            # Manifest validation proves a known last basis and matching page mapping.
            allowed[path.split("/", 1)[0]].add(path)
    evidence = infrastructure_evidence_by_page(manifest.generation_inputs)
    state = manifest.generation_inputs.get("infrastructure", {})
    if isinstance(state, Mapping):
        for record in (state.get("tombstones") or {}).values():
            if record["reason"] == "source-removed" and record["page_path"] in evidence:
                allowed["infrastructure"].add(record["page_path"])
    return allowed
