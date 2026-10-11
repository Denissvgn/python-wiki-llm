"""Optional static sync inputs authenticated by the last complete commit."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import json

from ..config import EXTRACTOR_REGISTRY
from .analysis_capture import capture_analysis, capture_operation
from .inventory_cache import InventoryCacheStats, prepare_cache_options
from .io import first_unsafe_path_component, write_json_atomic
from .knowledge_evidence import hash_json
from .knowledge_reuse import implementation_hash, REUSE_INPUT_KEY
from .knowledge_storage_io import read_guarded
from .progress import observed_phase, record_counts
from .runtime_output import warn

SCHEMA = "llm-wiki-sync-analysis/v1"
EXTENSION = "llm-wiki/sync-analysis-v1"
FILENAME = "llm-wiki-sync-analysis.json"
MAX_BYTES = 64 * 1024 * 1024


class SyncAnalysisMutationError(ValueError):
    """A matched static-input snapshot changed before publication."""


@capture_operation
def input_key(options, snapshot, manifest, generation_inputs):
    """Bind source bytes, policy, schema, producer, helpers and generation options."""
    if (manifest.maintenance_state is not None
            or options.initialize_surfaces or options.knowledge_format is not None
            or any((root / ".llm-wiki/plugins.lock.json").exists()
                   for root in (Path.cwd(), snapshot.root))
            or (options.wiki_dir / ".llm-wiki-governance.json").exists()):
        return None
    analysis = capture_analysis(EXTRACTOR_REGISTRY, source_root=snapshot.root,
                                helper_cache_dir=options.helper_cache_dir,
                                languages={k for k, v in snapshot.files_by_language.items() if v})
    active = {"agent-wiki-cli", "llm-wiki/extractor/infrastructure"} | {
        "llm-wiki/extractor/" + k for k, v in snapshot.files_by_language.items() if v
    }
    implementation = implementation_hash()
    if not active <= set(analysis) or implementation is None:
        return None
    inputs = dict(generation_inputs)
    inputs.pop(REUSE_INPUT_KEY, None)
    return {
        "schema_version": SCHEMA, "source_root": str(snapshot.root),
        "source_hashes": dict(snapshot.captured_content_hashes),
        "input_kinds": {k: list(v) for k, v in snapshot.captured_input_kinds.items()},
        "gitignore": snapshot.gitignore_fingerprint,
        "selection": snapshot.source_selection_identity,
        "include_tests": sorted(snapshot.include_tests),
        "surfaces": dict(manifest.surfaces), "generation_inputs": inputs,
        "preserve_semantic": options.preserve_semantic,
        "implementation": implementation, "analysis": analysis,
    }


def cache_path(options):
    cache_options = prepare_cache_options(options.src_dir, options.cache_options)
    destination = cache_options.destination if cache_options is not None else None
    if not options.cache_options.enabled or destination is None or destination.status == "failed" or destination.path is None:
        return None
    return destination.path.with_name(FILENAME)


@observed_phase("sync_analysis_reuse")
def load(options, snapshot, manifest, generation_inputs, state):
    """A cache is advisory; only exact prior committed content authorizes reuse."""
    path = cache_path(options)
    reason = "disabled"
    payload = None
    if options.cache_options.rebuild or options.rebuild_knowledge:
        reason = "rebuild-requested"
    if path is not None and not options.cache_options.rebuild and not options.rebuild_knowledge:
        key = input_key(options, snapshot, manifest, generation_inputs)
        artifacts = state.artifacts
        commitment = artifacts.knowledge.extensions.get(EXTENSION) if artifacts is not None else None
        if key is None:
            reason = "unqualified-inputs"
        elif not isinstance(commitment, Mapping) or commitment.get("schema_version") != SCHEMA:
            reason = "no-committed-analysis"
        elif commitment.get("input_hash") != hash_json(key):
            reason = "inputs-changed"
        else:
            try:
                candidate = json.loads(read_guarded(path, MAX_BYTES).content)
                if (not isinstance(candidate, dict) or candidate.get("schema_version") != SCHEMA
                        or candidate.get("input_key") != key
                        or hash_json(candidate) != commitment.get("payload_hash")):
                    reason = "cache-content-mismatch"
                else:
                    from .knowledge_envelope import hash_inventory, INVENTORY_HASH_EXTENSION
                    assert artifacts is not None
                    if hash_inventory(candidate["inventory"]) != artifacts.knowledge.bundle.snapshot.extensions[INVENTORY_HASH_EXTENSION]:
                        reason = "inventory-commitment-mismatch"
                    else:
                        payload = candidate
                        reason = "committed-inputs-match"
            except (OSError, ValueError, KeyError, TypeError):
                reason = "cache-unavailable-or-corrupt"
        if payload is not None and not generated_sections_match(options.wiki_dir, artifacts):
            payload = None
            reason = "wiki-structure-changed"
    print(f"Sync analysis reuse: {'hit' if payload is not None else 'miss'} ({reason})", flush=True)
    if payload is not None:
        record_counts(reused_source_files=len(payload["inventory"]), reused_graph_observations=1)
    return payload


def build_payload(options, prepared, surface):
    result = prepared.inventory_result
    if (prepared.seed_manifest or prepared.repair_only or result.failed
            or prepared.entrypoint_analysis is None or prepared.contracts is None
            or result.plugin_components or result.producer_plugin_components
            or any(v != EXTRACTOR_REGISTRY.get(k) for k, v in result.extractor_registry.items())):
        return None
    from dataclasses import asdict
    manifest = prepared.manifest.with_generation_state(
        surfaces=prepared.surface_plan.surfaces,
        generation_inputs=prepared.surface_plan.generation_inputs,
    )
    key = input_key(options, prepared.source_snapshot, manifest, prepared.surface_plan.generation_inputs)
    if prepared.analysis_input_key is not None and key != prepared.analysis_input_key:
        raise SyncAnalysisMutationError("analysis inputs changed during cached sync")
    if key is None:
        return None
    maps = prepared.page_maps
    payload = {
        "schema_version": SCHEMA, "input_key": key, "inventory": prepared.inventory,
        "statuses": {k: asdict(v) for k, v in result.statuses.items()},
        "implementation_observations": result.implementation_observations,
        "module_page_map": maps.module_page_map,
        "entity_page_map": [[*k, v] for k, v in sorted(maps.entity_page_cache.items())],
        "entity_occurrence_page_map": [[*k, v] for k, v in sorted(maps.entity_occurrence_page_cache.items())],
        "entrypoint_analysis": asdict(prepared.entrypoint_analysis),
        "contracts": prepared.contracts,
        "graph_observations": asdict(prepared.graph_observations),
    }
    from .knowledge_generation import _graph_concepts
    payload["graph_concepts_hash"] = hash_json([asdict(v) for v in _graph_concepts(
        surface.pages, module_page_map=maps.module_page_map,
        occurrence_page_map=maps.entity_occurrence_page_cache,
    )])
    from .knowledge_evidence import formatted_json_bytes
    if len(formatted_json_bytes(payload)) > MAX_BYTES:
        return None
    return payload


def commitment(payload):
    return {"schema_version": SCHEMA, "input_hash": hash_json(payload["input_key"]),
            "payload_hash": hash_json(payload), "graph_concepts_hash": payload["graph_concepts_hash"]} if payload is not None else None


def generated_sections_match(root, artifacts):
    """Allow prose edits; changing generated structure requires the ordinary path."""
    from .contracts import SECTION_OWNERSHIP_EXTENSION_KEY
    from .section_ownership import observe_page_sections
    prior = {row["page_locator"]: row for row in artifacts.knowledge.extensions[SECTION_OWNERSHIP_EXTENSION_KEY]["pages"]}
    for concept in artifacts.knowledge.concepts:
        path = root / concept.document.canonical_path
        from .knowledge_storage import KnowledgeStorageError
        try:
            content = read_guarded(path, MAX_BYTES).content.decode("utf-8")
        except (OSError, ValueError) as exc:
            if isinstance(exc, KnowledgeStorageError) and exc.code == "storage-mutation":
                raise SyncAnalysisMutationError("wiki changed during analysis reuse") from exc
            return False
        from .knowledge_evidence import sha256_bytes
        if sha256_bytes(content.encode("utf-8")) == concept.facets.semantics.page_hash:
            continue
        kind = concept.document.page_kind
        # Log bodies are append-only authored history, reconciled by the writer.
        if str(getattr(kind, "value", kind)) == "log":
            continue
        current = observe_page_sections(content, concept.locator, kind).to_payload()
        def structural(row):
            return {s["locator"]: s["structural_hash"] for s in row["sections"] if "structural_hash" in s}
        if structural(current) != structural(prior[concept.locator]):
            return False
    return True


def save(options, payload):
    path = cache_path(options)
    if path is None or payload is None or options.dry_run:
        return
    try:
        if first_unsafe_path_component(path) is not None:
            raise OSError("redirected analysis cache destination")
        write_json_atomic(path, payload)
    except (OSError, ValueError) as exc:
        warn(options.cache_options.warning, f"Sync analysis cache was not saved: {exc}")


def inventory_result(payload, snapshot, options):
    from .extraction_service import InventoryResult, ExtractorStatus
    analysis = capture_analysis(EXTRACTOR_REGISTRY, source_root=snapshot.root,
                                helper_cache_dir=options.helper_cache_dir,
                                languages={k for k, v in snapshot.files_by_language.items() if v})
    return InventoryResult(
        inventory=payload["inventory"],
        statuses={k: ExtractorStatus(**v) for k, v in payload["statuses"].items()},
        extractor_registry=dict(EXTRACTOR_REGISTRY), source_snapshot=snapshot,
        analysis_components=analysis,
        implementation_observations=payload["implementation_observations"],
        cache_stats=InventoryCacheStats(enabled=True, status="hit", hits=len(payload["inventory"]),
                                        path=str(cache_path(options))),
    )
