# build_qualified_context

**Entry point:** `build_qualified_context` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [change_selection](../modules/change_selection.md), [common](../modules/common.md), and 62 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [change_selection](../modules/change_selection.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
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
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [maintenance_status](../modules/maintenance_status.md)
- [manifest_storage](../modules/manifest_storage.md)
- [packet_field_policy](../modules/packet_field_policy.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [python_bindings](../modules/python_bindings.md)
- [python_calls](../modules/python_calls.md)
- [python_implementation](../modules/python_implementation.md)
- [python_imports](../modules/python_imports.md)
- [section_ownership](../modules/section_ownership.md)
- [services_dependencies](../modules/services_dependencies.md)
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
    participant p0 as build_qualified_context
    participant p1 as _normalized_request
    participant p2 as _packet_contract_for_request
    participant p3 as capture_context_read
    participant p4 as build_context_from_captured_read
    participant p5 as _protocol_success_payload
    participant p6 as _fit_knowledge_packet_response
    participant p7 as packet_from_captured_response
    participant p8 as _candidate_packet_size
    participant p9 as _render_markdown
    participant p10 as _build_legacy_context_from_captured_read
    participant p11 as _build_knowledge_context_from_captured_read
    participant p12 as _assert_selection_unchanged
    participant p13 as _validate_protocol_request
    participant p14 as validate_context_packet
    participant p15 as validate_source_root
    participant p16 as resolve_source_selection
    participant p17 as capture_source_selection_inputs
    participant p18 as validate_live_query_source_selection
    participant p19 as build_source_snapshot
    participant p20 as _guard_windows_inputs
    participant p21 as _assert_source_unchanged
    participant p22 as _assert_source_inputs_unchanged
    participant p23 as _wiki_anchor
    participant p24 as get_entry_points
    participant p25 as read_console_scripts
    participant p26 as resolve_call_edges
    participant p27 as build_flow
    participant p28 as build_data_flow_context
    participant p29 as bool (src/llm_wiki_cli/services…y:build_qualified_context)
    participant p30 as normalized.get (src/llm_wiki_cli/services…y:build_qualified_context)
    p0->>p1: _normalized_request
    p0->>p2: _packet_contract_for_request
    p0->>p3: capture_context_read
    p0->>p4: build_context_from_captured_read
    p0->>p5: _protocol_success_payload
    p0->>p6: _fit_knowledge_packet_response
    p0->>p7: packet_from_captured_response
    p6->>p8: _candidate_packet_size
    p5->>p9: _render_markdown
    p4->>p10: _build_legacy_context_from_captured_read
    p4->>p11: _build_knowledge_context_from_captured_read
    p7->>p12: _assert_selection_unchanged
    p1->>p13: _validate_protocol_request
    p7->>p14: validate_context_packet
    p3->>p15: validate_source_root
    p3->>p16: resolve_source_selection
    p3->>p17: capture_source_selection_inputs
    p3->>p18: validate_live_query_source_selection
    p3->>p19: build_source_snapshot
    p3->>p20: _guard_windows_inputs
    p3->>p21: _assert_source_unchanged
    p3->>p22: _assert_source_inputs_unchanged
    p3->>p23: _wiki_anchor
    p3->>p24: get_entry_points
    p3->>p25: read_console_scripts
    p3->>p26: resolve_call_edges
    p3->>p27: build_flow
    p3->>p28: build_data_flow_context
    p0-->>p29: bool (src/llm_wiki_cli/services…y:build_qualified_context)(...)
    p0-->>p30: normalized.get (src/llm_wiki_cli/services…y:build_qualified_context)('knowledge_mode')
```

> Call sequence diagram shows 30 of 5489 interactions; 5459 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1724 (1723 omitted); unresolved 1 of 1879 (1878 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/context_packet.py:_normalized_request` | 2 | - | external | 3 |
| `src/llm_wiki_cli/services/context_packet.py:_normalized_request` | 2 | [src/llm_wiki_cli/services/context_service.py](../modules/context_service.md) | internal | 1 |
| `src/llm_wiki_cli/services/context_packet.py:_normalized_request` | 2 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/context_service.py:_validate_protocol_request` | 9 | - | external | 2 |
| `src/llm_wiki_cli/services/context_service.py:_validate_protocol_request` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/context_service.py:_validate_protocol_request` | 9 | [src/llm_wiki_cli/services/context_service.py](../modules/context_service.md) | internal | 1 |
| `src/llm_wiki_cli/services/context_service.py:_validate_protocol_request_impl` | 12 | - | external | 11 |
| `src/llm_wiki_cli/services/context_service.py:_validate_protocol_request_impl` | 12 | [src/llm_wiki_cli/services/context_service.py](../modules/context_service.md) | internal | 12 |
> Omission summary shows 8 of 1293 groups; 1285 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_qualified_context"]
    s2["2. _normalized_request"]
    s3["3. isinstance (src/llm_wiki_cli/services…et.py:_normalized_request)"]
    s4["4. ProtocolRequestError"]
    s5["5. deepcopy (src/llm_wiki_cli/services…et.py:_normalized_request)"]
    s6["6. dict (src/llm_wiki_cli/services…et.py:_normalized_request)"]
    s7["7. candidate.setdefault"]
    s8["8. candidate.setdefault"]
    s9["9. _validate_protocol_request"]
    s10["10. isinstance (src/llm_wiki_cli/services…validate_protocol_request)"]
    s11["11. data.get (src/llm_wiki_cli/services…validate_protocol_request)"]
    s12["12. _validate_protocol_request_impl"]
    s1 -->|"_normalized_request(...)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…et.py:_normalized_request)(request, Mapping)" .-> s3
    s2 -->|"ProtocolRequestError('Request must be a JSON object.', 'request')"| s4
    s2 -. "deepcopy (src/llm_wiki_cli/services…et.py:_normalized_request)(dict(...))" .-> s5
    s2 -. "dict (src/llm_wiki_cli/services…et.py:_normalized_request)(request)" .-> s6
    s2 -. "candidate.setdefault('protocol', ...)" .-> s7
    s2 -. "candidate.setdefault('filters', {...})" .-> s8
    s2 -->|"_validate_protocol_request(candidate)"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…validate_protocol_request)(data, dict)" .-> s10
    s9 -. "data.get (src/llm_wiki_cli/services…validate_protocol_request)('protocol')" .-> s11
    s9 -->|"_validate_protocol_request_impl(data)"| s12
    click s1 "../modules/context_packet.md"
    click s2 "../modules/context_packet.md"
    click s4 "../modules/context_service.md"
    click s9 "../modules/context_service.md"
    click s12 "../modules/context_service.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_qualified_context` | `src_dir: str`, `wiki_dir: str`, `request: Mapping[str, Any] \| None`, `allow_external_src: bool`, `read_only: bool`, `job_request: ExtractionJobRequest \| None`, `plan_reporter: Callable[[ExtractionJobPlan], None] \| None`, `source_selection: str \| Path \| None` | `_KNOWLEDGE_PACKET_CONTRACT`, `_KNOWLEDGE_PACKET_CONTRACT`, `context_service`, `_KNOWLEDGE_PACKET_CONTRACT` | `response[...]` | `packet_from_captured_response(...)` |
| `_normalized_request` | `request: Mapping[str, Any]` | `Mapping`, `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `context_service` | - | `context_service._validate_protocol_request(...)` |
| `isinstance (src/llm_wiki_cli/services…et.py:_normalized_request)` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `deepcopy (src/llm_wiki_cli/services…et.py:_normalized_request)` | - | - | - | - |
| `dict (src/llm_wiki_cli/services…et.py:_normalized_request)` | - | - | - | - |
| `candidate.setdefault` | - | - | - | - |
| `candidate.setdefault` | - | - | - | - |
| `_validate_protocol_request` | `data: object` | `PROTOCOL_VERSION`, `ProtocolRequestError`, `PROTOCOL_VERSION`, `KNOWLEDGE_PROTOCOL_VERSION` | `exc.protocol` | `_validate_protocol_request_impl(...)` |
| `isinstance (src/llm_wiki_cli/services…validate_protocol_request)` | - | - | - | - |
| `data.get (src/llm_wiki_cli/services…validate_protocol_request)` | - | - | - | - |
| `_validate_protocol_request_impl` | `data: object` | `PROTOCOL_VERSION`, `_V1_REQUEST_KEYS`, `KNOWLEDGE_PROTOCOL_VERSION`, `_V2_REQUEST_KEYS`, `PROTOCOL_VERSION`, `KNOWLEDGE_PROTOCOL_VERSION`, `_FORMATS`, `KNOWLEDGE_PROTOCOL_VERSION` | `normalized[...]` | `validate_request(...)`, `normalized` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_qualified_context | _normalized_request | 1431 | `_normalized_request(...)` |
| _normalized_request | isinstance (src/llm_wiki_cli/services…et.py:_normalized_request) | 1961 | `isinstance(request, Mapping)` |
| _normalized_request | ProtocolRequestError | 1962 | `context_service.ProtocolRequestError('Request must be a JSON object.', 'request')` |
| _normalized_request | deepcopy (src/llm_wiki_cli/services…et.py:_normalized_request) | 1966 | `deepcopy(dict(...))` |
| _normalized_request | dict (src/llm_wiki_cli/services…et.py:_normalized_request) | 1966 | `dict(request)` |
| _normalized_request | candidate.setdefault | 1967 | `candidate.setdefault('protocol', ...)` |
| _normalized_request | candidate.setdefault | 1975 | `candidate.setdefault('filters', {...})` |
| _normalized_request | _validate_protocol_request | 1976 | `context_service._validate_protocol_request(candidate)` |
| _validate_protocol_request | isinstance (src/llm_wiki_cli/services…validate_protocol_request) | 1104 | `isinstance(data, dict)` |
| _validate_protocol_request | data.get (src/llm_wiki_cli/services…validate_protocol_request) | 1104 | `data.get('protocol')` |
| _validate_protocol_request | _validate_protocol_request_impl | 1106 | `_validate_protocol_request_impl(data)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_normalized_request` | `isinstance` | 1961 |
| external_call | `_normalized_request` | `deepcopy` | 1966 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1967 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1975 |
| external_call | `_validate_protocol_request` | `isinstance` | 1104 |
| unresolved_call | `_validate_protocol_request` | `data.get` | 1104 |
| step_limit | `build_qualified_context` | `first 12 steps` | 0 |
| truncated_flow | `build_qualified_context` | `depth limit` | 0 |

## Behavior

This flow starts at `build_qualified_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
