# sync_analysis_cache Module

**Path:** `src/llm_wiki_cli/services/sync_analysis_cache.py`

## Description

An optional, bounded cache of static sync inputs authenticated by a validated
complete knowledge commit. Version 2 records its reuse level in both the payload
and committed metadata. Full coverage retains raw graph observations; inventory
coverage retains inventory, page maps, detector inputs, implementation observations
and the complete extraction sidecars, while explicitly omitting graph observations.
Unavailable sidecars remain unavailable rather than becoming complete-empty data.

When input classification or registered implementation files prevent an owned
analysis basis, the cache remains unqualified and emits the bounded analysis
input diagnostic with its review route. That informational record cannot
authorize reuse or synthesize a producer identity.

Valid ordinary-maintenance snapshots bind structural reuse to their canonical
adoption identity. An unavailable identity skips capture before analysis probes.
Mutable review state and actor history remain outside the cache and under current
owner reconciliation. Cache eligibility never authorizes authority repair or
adoption.

Capture first considers full coverage, then inventory coverage when graph data
exceeds the budget. The complete selected payload must fit the unchanged 64 MiB
physical and decoded JSON limit. Compact UTF-8 JSON is uncompressed; bounded
counting does not retain an oversized encoding. Full captures own an independent
graph copy. Older cache schemas use ordinary generation until an eligible owning
commit captures the current version.

Reuse binds exact source bytes, selection/ignore policy, generation configuration,
installed implementation and prepared-helper identities. Generated wiki structure
is checked separately from semantic edits. Partial hits feed their exact sidecars
to the ordinary graph builders and typed materializer; no omitted graph data is
reported as zero or complete. Source, wiki and provider mutations reject matched
reuse. Fixed capture reasons and byte counts expose ineligible contexts and budget
failures. Cache saving follows successful owning publication and remains advisory.

Authenticated captures retain per-path outcomes for qualified empty records.
A retained empty model without its attributable cached outcome triggers narrow
re-extraction. Missing or malformed diagnostic data never becomes a complete
empty result. Full graph shortcuts are abandoned when qualification changes the
cached inventory; ordinary page-map and graph builders receive the rebuilt
module records.

Sync preview separates requested cache eligibility from extraction-cache I/O.
It plans the same analysis commitment as apply for unchanged available inputs,
while resolving the requested destination without probes, directory creation,
cache reads or writes. Explicit cache disabling remains disabled. Publication
and advisory cache saving still require a successful owning apply; preview
does not establish destination writability or durable capture.

Malformed advisory payloads, including runtime recursion exhaustion during JSON
decoding or commitment encoding, are discarded with the bounded corrupt-cache
reason. Ordinary source extraction and publication still perform their normal
authentication and preservation checks. Decoder nesting behavior differs across
Python versions; successful parsing on one runtime cannot make an unauthenticated
payload reusable or make cache availability mandatory.


Ordinary maintenance can reuse qualified structural observations, bound to its immutable adoption identity. Review state and actor history are not cached: every sync reconciles the current guarded owner with current prose. A prose edit reopens its reviewed basis while retaining acknowledgment history. Full snapshot reuse remains separate from this structural optimization.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `EXTRACTOR_REGISTRY` |
| `.analysis_capture` | `capture_analysis`, `capture_operation`, `analysis_diagnostics` |
| `.contracts` | `SECTION_OWNERSHIP_EXTENSION_KEY` |
| `.extraction_service` | `InventoryResult`, `ExtractorStatus` |
| `.inventory_cache` | `InventoryCacheStats`, `prepare_cache_options`, `resolve_inventory_cache_path` |
| `.io` | `first_unsafe_path_component`, `write_bytes_atomic` |
| `.knowledge_envelope` | `hash_inventory`, `INVENTORY_HASH_EXTENSION` |
| `.knowledge_evidence` | `canonical_json_bytes`, `hash_json`, `sha256_bytes` |
| `.knowledge_generation` | `_graph_concepts` |
| `.knowledge_reuse` | `implementation_hash`, `REUSE_INPUT_KEY` |
| `.knowledge_storage` | `KnowledgeStorageError` |
| `.knowledge_storage_io` | `read_guarded` |
| `.maintenance_state` | `MaintenanceError`, `_identity` |
| `.progress` | `observed_phase`, `record_counts` |
| `.runtime_output` | `warn` |
| `.section_ownership` | `observe_page_sections` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `dataclasses` | `asdict`, `fields` |
| `json` | `json` |
| `pathlib` | `Path` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/sync_analysis_cache.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/sync_analysis_cache.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (3) |
| Outbound | `src` (16) |

> All 18 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [SyncAnalysisMutationError](../entities/SyncAnalysisMutationError.md) | 25 | `ValueError` | A matched static-input snapshot changed before publication. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `input_key` | `(options, snapshot, manifest, generation_inputs, *, explain = False)` | `@capture_operation` | Bind source bytes, policy, schema, producer, helpers and generation options. |
| `cache_destination` | `(options, *, capture = False)` | — | Return the bounded eligibility label independently of capture content. |
| `cache_path` | `(options)` | — | — |
| `report_capture` | `(options, status, reason, *, payload_bytes = None, over_budget = False)` | — | Emit fixed vocabulary and counts, never source content or unbounded paths. |
| `payload_size` | `(payload)` | — | Count the exact writer encoding up to the budget, without retaining it. |
| `load` | `(options, snapshot, manifest, generation_inputs, state)` | `@observed_phase('sync_analysis_reuse')` | A cache is advisory; only exact prior committed content authorizes reuse. |
| `build_payload` | `(options, prepared, surface)` | — | — |
| `commitment` | `(payload)` | — | — |
| `generated_sections_match` | `(root, artifacts)` | — | Allow prose edits; changing generated structure requires the ordinary path. |
| `save` | `(options, payload)` | — | — |
| `inventory_result` | `(payload, snapshot, options)` | — | — |