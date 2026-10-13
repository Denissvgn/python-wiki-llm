"""Optional static sync inputs authenticated by the last complete commit."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import json

from ..config import EXTRACTOR_REGISTRY
from .analysis_capture import capture_analysis, capture_operation, analysis_diagnostics
from .inventory_cache import InventoryCacheStats, prepare_cache_options, resolve_inventory_cache_path
from .io import first_unsafe_path_component, write_bytes_atomic
from .knowledge_evidence import canonical_json_bytes, hash_json
from .knowledge_reuse import implementation_hash, REUSE_INPUT_KEY
from .knowledge_storage_io import read_guarded
from .progress import observed_phase, record_counts
from .runtime_output import warn

SCHEMA = "llm-wiki-sync-analysis/v2"
EXTENSION = "llm-wiki/sync-analysis-v2"
FILENAME = "llm-wiki-sync-analysis.json"
MAX_BYTES = 64 * 1024 * 1024


class SyncAnalysisMutationError(ValueError):
    """A matched static-input snapshot changed before publication."""


@capture_operation
def input_key(options, snapshot, manifest, generation_inputs, *, explain=False):
    """Bind source bytes, policy, schema, producer, helpers and generation options."""
    def skipped(reason):
        if explain:
            report_capture(options, "skipped", reason)
        return None

    for excluded, reason in (
        (manifest.maintenance_state is not None, "maintenance-state"),
        (bool(options.initialize_surfaces), "surface-initialization"),
        (options.knowledge_format is not None, "storage-format-requested"),
        (any((root / ".llm-wiki/plugins.lock.json").exists()
             for root in (Path.cwd(), snapshot.root)), "plugin-lock-present"),
        ((options.wiki_dir / ".llm-wiki-governance.json").exists(), "governance-present"),
    ):
        if excluded:
            return skipped(reason)
    analysis = capture_analysis(EXTRACTOR_REGISTRY, source_root=snapshot.root,
                                helper_cache_dir=options.helper_cache_dir,
                                languages={k for k, v in snapshot.files_by_language.items() if v})
    active = {"agent-wiki-cli", "llm-wiki/extractor/infrastructure"} | {
        "llm-wiki/extractor/" + k for k, v in snapshot.files_by_language.items() if v
    }
    implementation = implementation_hash()
    if not active <= set(analysis):
        diagnostic = analysis_diagnostics(analysis)
        if diagnostic is not None:
            print("Analysis input preflight: " + json.dumps(diagnostic, ensure_ascii=True, sort_keys=True), flush=True)
        return skipped("unqualified-analysis")
    if implementation is None:
        return skipped("unqualified-implementation")
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


def cache_destination(options, *, capture=False):
    """Return the bounded eligibility label independently of capture content."""
    # Preview disables extraction cache I/O, but plans the same commitment as
    # apply. This selection only resolves eligibility; saving remains gated by
    # the owning command's successful non-preview publication.
    requested = (getattr(options, "capture_cache_options", None) if capture else None) or options.cache_options
    if not requested.enabled:
        return None, "disabled"
    if capture and not options.cache_options.enabled:
        # No destination probes, directories or cache reads during preview.
        try:
            path = resolve_inventory_cache_path(options.src_dir, requested.cache_dir)
        except (OSError, ValueError, RuntimeError):
            return None, "failed"
        if path is None:
            return None, "unconfigured"
        path = path.with_name(FILENAME)
        return (None, "redirected") if first_unsafe_path_component(path) is not None else (path, "eligible")
    cache_options = prepare_cache_options(options.src_dir, requested)
    destination = cache_options.destination if cache_options is not None else None
    if destination is None or destination.path is None:
        return None, "failed" if destination is not None and destination.status == "failed" else "unconfigured"
    if destination.status == "failed":
        return None, "failed"
    path = destination.path.with_name(FILENAME)
    if first_unsafe_path_component(path) is not None:
        return None, "redirected"
    return path, "eligible"


def cache_path(options):
    return cache_destination(options)[0]


def report_capture(options, status, reason, *, payload_bytes=None, over_budget=False):
    """Emit fixed vocabulary and counts, never source content or unbounded paths."""
    destination = cache_destination(options, capture=True)[1]
    size = "unavailable" if payload_bytes is None else str(payload_bytes)
    if over_budget:
        size = f">{MAX_BYTES}"
    print(f"Sync analysis capture: {status} ({reason}); destination={destination}; "
          f"payload_bytes={size}; limit_bytes={MAX_BYTES}", flush=True)


def payload_size(payload):
    """Count the exact writer encoding up to the budget, without retaining it."""
    encoder = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False)
    size = 1  # The writer's trailing newline.
    for chunk in encoder.iterencode(payload):
        if len(chunk) > MAX_BYTES - size:
            return None
        size += len(chunk.encode("utf-8"))
        if size > MAX_BYTES:
            return None
    return size


@observed_phase("sync_analysis_reuse")
def load(options, snapshot, manifest, generation_inputs, state):
    """A cache is advisory; only exact prior committed content authorizes reuse."""
    path, destination = cache_destination(options)
    reason = "disabled" if destination == "disabled" else "destination-" + destination
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
                        or candidate.get("coverage") not in {"full", "inventory"}
                        or candidate.get("coverage") != commitment.get("coverage")
                        or not {"data_effect_observations", "import_observations"} <= candidate.keys()
                        or (candidate.get("coverage") == "full") != isinstance(candidate.get("graph_observations"), dict)
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
            except (OSError, ValueError, KeyError, TypeError, RecursionError):
                reason = "cache-unavailable-or-corrupt"
        if payload is not None and not generated_sections_match(options.wiki_dir, artifacts):
            payload = None
            reason = "wiki-structure-changed"
    coverage = f"; coverage={payload['coverage']}" if payload is not None else ""
    print(f"Sync analysis reuse: {'hit' if payload is not None else 'miss'} ({reason}){coverage}", flush=True)
    if payload is not None:
        record_counts(reused_source_files=len(payload["inventory"]), reused_graph_observations=int(payload["coverage"] == "full"))
    return payload


def build_payload(options, prepared, surface):
    result = prepared.inventory_result
    destination = cache_destination(options, capture=True)[1]
    if destination != "eligible":
        report_capture(options, "skipped", "destination-" + destination)
        return None
    for excluded, reason in (
        (prepared.seed_manifest, "seed-manifest"),
        (prepared.repair_only, "manifest-repair"),
        (result.failed, "inventory-failed"),
        (prepared.entrypoint_analysis is None, "entrypoints-unavailable"),
        (prepared.contracts is None, "contracts-unavailable"),
        (bool(result.plugin_components), "extractor-plugins"),
        (bool(result.producer_plugin_components), "producer-plugins"),
        (any(v != EXTRACTOR_REGISTRY.get(k) for k, v in result.extractor_registry.items()), "custom-extractors"),
    ):
        if excluded:
            report_capture(options, "skipped", reason)
            return None
    from dataclasses import asdict, fields
    manifest = prepared.manifest.with_generation_state(
        surfaces=prepared.surface_plan.surfaces,
        generation_inputs=prepared.surface_plan.generation_inputs,
    )
    key = input_key(options, prepared.source_snapshot, manifest, prepared.surface_plan.generation_inputs, explain=True)
    if prepared.analysis_input_key is not None and key != prepared.analysis_input_key:
        report_capture(options, "aborted", "analysis-inputs-changed")
        raise SyncAnalysisMutationError("analysis inputs changed during cached sync")
    if key is None:
        return None
    maps = prepared.page_maps
    payload = {
        "schema_version": SCHEMA, "coverage": "full", "input_key": key, "inventory": prepared.inventory,
        "statuses": {k: asdict(v) for k, v in result.statuses.items()},
        "implementation_observations": result.implementation_observations,
        "path_outcomes": getattr(result, "path_outcomes", {}),
        "data_effect_observations": result.data_effect_observations,
        "import_observations": result.import_observations,
        "module_page_map": maps.module_page_map,
        "entity_page_map": [[*k, v] for k, v in sorted(maps.entity_page_cache.items())],
        "entity_occurrence_page_map": [[*k, v] for k, v in sorted(maps.entity_occurrence_page_cache.items())],
        "entrypoint_analysis": asdict(prepared.entrypoint_analysis),
        "contracts": prepared.contracts,
        "graph_observations": {field.name: getattr(prepared.graph_observations, field.name)
                               for field in fields(prepared.graph_observations)},
    }
    from .knowledge_generation import _graph_concepts
    payload["graph_concepts_hash"] = hash_json([asdict(v) for v in _graph_concepts(
        surface.pages, module_page_map=maps.module_page_map,
        occurrence_page_map=maps.entity_occurrence_page_cache,
    )])
    size = payload_size(payload)
    if size is None:
        # This is qualified partial reuse, not a truncated graph projection.
        # The ordinary graph builders receive the exact extraction sidecars.
        payload["coverage"] = "inventory"
        payload["graph_observations"] = None
        size = payload_size(payload)
    if size is None:
        report_capture(options, "skipped", "payload-over-budget", over_budget=True)
        return None
    if payload["coverage"] == "full":
        payload["graph_observations"] = asdict(prepared.graph_observations)
    report_capture(options, "ready", "qualified-" + payload["coverage"], payload_bytes=size)
    return payload


def commitment(payload):
    return {"schema_version": SCHEMA, "coverage": payload["coverage"],
            "input_hash": hash_json(payload["input_key"]),
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
    if path is None:
        report_capture(options, "skipped", "destination-" + cache_destination(options)[1])
        return
    if payload is None:
        report_capture(options, "skipped", "payload-unavailable")
        return
    if options.dry_run:
        report_capture(options, "skipped", "dry-run")
        return
    try:
        if first_unsafe_path_component(path) is not None:
            raise OSError("redirected analysis cache destination")
        content = canonical_json_bytes(payload) + b"\n"
        if len(content) > MAX_BYTES:
            report_capture(options, "skipped", "payload-over-budget", over_budget=True)
            return
        write_bytes_atomic(path, content)
        report_capture(options, "saved", "committed-payload")
    except (OSError, ValueError) as exc:
        report_capture(options, "skipped", "cache-write-failed")
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
        path_outcomes=dict(payload["path_outcomes"]) if isinstance(payload.get("path_outcomes"), Mapping) else {},
        data_effect_observations=payload["data_effect_observations"],
        import_observations=payload["import_observations"],
        cache_stats=InventoryCacheStats(enabled=True, status="hit", hits=len(payload["inventory"]),
                                        path=str(cache_path(options))),
    )
