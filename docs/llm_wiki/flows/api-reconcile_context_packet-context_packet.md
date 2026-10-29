# reconcile_context_packet

**Entry point:** `reconcile_context_packet` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [bootstrap_recovery](../modules/bootstrap_recovery.md), and 59 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [bootstrap_recovery](../modules/bootstrap_recovery.md)
- [change_selection](../modules/change_selection.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [dockerfile_parser](../modules/dockerfile_parser.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [go_calls](../modules/go_calls.md)
- [immutable](../modules/immutable.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [packages](../modules/packages.md)
- [packet_field_policy](../modules/packet_field_policy.md)
- [plugins](../modules/plugins.md)
- [python_bindings](../modules/python_bindings.md)
- [python_calls](../modules/python_calls.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_retirement](../modules/source_retirement.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)
- [yaml_formats](../modules/yaml_formats.md)
- [yaml_syntax](../modules/yaml_syntax.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as reconcile_context_packet
    participant p1 as validate_context_packet
    participant p2 as build_qualified_context
    participant p3 as _reconcile_packet_views
    participant p4 as _coerce_packet_bytes
    participant p5 as _normalized_request
    participant p6 as _strict_json_payload
    participant p7 as _packet_contract_for_request
    participant p8 as _packet_contract_for_schema
    participant p9 as capture_context_read
    participant p10 as _reconciliation_facets
    participant p11 as _validate_packet_shape
    participant p12 as _encode_packet_payload
    participant p13 as build_context_from_captured_read
    participant p14 as _protocol_success_payload
    participant p15 as ContextPacketReconciliation._from_official_read
    participant p16 as _packet_id
    participant p17 as _path_policy_receipt
    participant p18 as _fit_knowledge_packet_response
    participant p19 as packet_from_captured_response
    participant p20 as QualifiedContextPacket._from_validated_payload
    participant p21 as _exact_fields
    participant p22 as _candidate_packet_size
    participant p23 as _render_markdown
    participant p24 as _freeze_json
    participant p25 as _validate_reconciliation_contract
    participant p26 as _build_legacy_context_from_captured_read
    participant p27 as _validate_assurance
    participant p28 as _build_knowledge_context_from_captured_read
    participant p29 as len (src/llm_wiki_cli/services…y:validate_context_packet)
    participant p30 as validation.packet.to_payload
    p0->>p1: validate_context_packet
    p0->>p2: build_qualified_context
    p0->>p3: _reconcile_packet_views
    p1->>p4: _coerce_packet_bytes
    p2->>p5: _normalized_request
    p1->>p6: _strict_json_payload
    p2->>p7: _packet_contract_for_request
    p1->>p8: _packet_contract_for_schema
    p2->>p9: capture_context_read
    p3->>p10: _reconciliation_facets
    p1->>p11: _validate_packet_shape
    p1->>p12: _encode_packet_payload
    p2->>p13: build_context_from_captured_read
    p2->>p14: _protocol_success_payload
    p3->>p15: ContextPacketReconciliation._from_official_read
    p1->>p16: _packet_id
    p1->>p17: _path_policy_receipt
    p2->>p18: _fit_knowledge_packet_response
    p2->>p19: packet_from_captured_response
    p1->>p20: QualifiedContextPacket._from_validated_payload
    p11->>p21: _exact_fields
    p18->>p22: _candidate_packet_size
    p14->>p23: _render_markdown
    p20->>p24: _freeze_json
    p15->>p25: _validate_reconciliation_contract
    p13->>p26: _build_legacy_context_from_captured_read
    p11->>p27: _validate_assurance
    p13->>p28: _build_knowledge_context_from_captured_read
    p1-->>p29: len (src/llm_wiki_cli/services…y:validate_context_packet)(raw)
    p0-->>p30: validation.packet.to_payload
```

> Call sequence diagram shows 30 of 4005 interactions; 3975 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1321 (1320 omitted); unresolved 1 of 1326 (1325 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 3 | - | external | 5 |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 3 | [src/llm_wiki_cli/services/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_cli/services/context_packet.py:_coerce_packet_bytes` | 3 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 16 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 16 | [src/llm_wiki_cli/services/context_packet.py](../modules/context_packet.md) | internal | 4 |
| `src/llm_wiki_cli/services/context_packet.py:_strict_json_payload` | 16 | - | external | 2 |
| `src/llm_wiki_cli/services/context_packet.py:_validate_json_tree` | 23 | - | external | 1 |
| `src/llm_wiki_cli/services/context_packet.py:_validate_json_tree` | 23 | - | unresolved | 1 |
> Omission summary shows 8 of 916 groups; 908 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1359; effect analysis evaluated: 964, partial: 0, unavailable: 395. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `reconcile_context_packet` | `available` | `evaluated` | `available` |
| `validate_context_packet` | `available` | `evaluated` | `available` |
| `_coerce_packet_bytes` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ContextPacketMalformedError` | `unavailable` | `unavailable` | `unavailable` |
| `len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ContextPacketMalformedError` | `unavailable` | `unavailable` | `unavailable` |
| `raw.startswith` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ContextPacketMalformedError` | `unavailable` | `unavailable` | `unavailable` |

```mermaid
flowchart LR
    s1["1. reconcile_context_packet"]
    s2["2. validate_context_packet"]
    s3["3. _coerce_packet_bytes"]
    s4["4. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s5["5. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s6["6. bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s7["7. TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s8["8. ContextPacketMalformedError"]
    s9["9. len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s10["10. ContextPacketMalformedError"]
    s11["11. raw.startswith"]
    s12["12. ContextPacketMalformedError"]
    s1 -->|"validate_context_packet(packet_bytes)"| s2
    s2 -->|"_coerce_packet_bytes(packet_bytes)"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, bytes)" .-> s4
    s3 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, (...))" .-> s5
    s3 -. "bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value)" .-> s6
    s3 -. "TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)('packet_bytes must be bytes-like')" .-> s7
    s3 -->|"ContextPacketMalformedError('packet_bytes', 'must not be empty')"| s8
    s3 -. "len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(raw)" .-> s9
    s3 -->|"ContextPacketMalformedError('packet_bytes', ...)"| s10
    s3 -. "raw.startswith(b'\xef\xbb\xbf')" .-> s11
    s3 -->|"ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')"| s12
    click s1 "../modules/context_packet.md"
    click s2 "../modules/context_packet.md"
    click s3 "../modules/context_packet.md"
    click s8 "../modules/context_packet.md"
    click s10 "../modules/context_packet.md"
    click s12 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `reconcile_context_packet` | `packet_bytes: bytes \| bytearray \| memoryview`, `src_dir: str`, `wiki_dir: str`, `allow_external_src: bool`, `read_only: bool`, `job_request: ExtractionJobRequest \| None`, `plan_reporter: Callable[[ExtractionJobPlan], None] \| None`, `source_selection: str \| Path \| None` | - | - | `_reconcile_packet_views(...)` |
| `validate_context_packet` | `packet_bytes: bytes \| bytearray \| memoryview` | - | - | `ContextPacketValidation(...)` |
| `_coerce_packet_bytes` | `value: bytes \| bytearray \| memoryview` | `_MAX_PACKET_BYTES`, `_MAX_PACKET_BYTES` | - | `raw` |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |
| `raw.startswith` | - | - | - | - |
| `ContextPacketMalformedError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| reconcile_context_packet | validate_context_packet | 1860 | `validate_context_packet(packet_bytes)` |
| validate_context_packet | _coerce_packet_bytes | 1771 | `_coerce_packet_bytes(packet_bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2547 | `isinstance(value, bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2549 | `isinstance(value, (...))` |
| _coerce_packet_bytes | bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2550 | `bytes(value)` |
| _coerce_packet_bytes | TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2552 | `TypeError('packet_bytes must be bytes-like')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2554 | `ContextPacketMalformedError('packet_bytes', 'must not be empty')` |
| _coerce_packet_bytes | len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2555 | `len(raw)` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2556 | `ContextPacketMalformedError('packet_bytes', ...)` |
| _coerce_packet_bytes | raw.startswith | 2560 | `raw.startswith(b'\xef\xbb\xbf')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2561 | `ContextPacketMalformedError('packet_bytes', 'must not contain a UTF-8 byte-order mark')` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_coerce_packet_bytes` | `isinstance` | 2547 |
| external_call | `_coerce_packet_bytes` | `isinstance` | 2549 |
| external_call | `_coerce_packet_bytes` | `bytes` | 2550 |
| external_call | `_coerce_packet_bytes` | `TypeError` | 2552 |
| unresolved_call | `_coerce_packet_bytes` | `raw.startswith` | 2560 |
| step_limit | `reconcile_context_packet` | `first 12 steps` | 0 |
| truncated_flow | `reconcile_context_packet` | `depth limit` | 0 |

## Behavior

This flow starts at `reconcile_context_packet` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
