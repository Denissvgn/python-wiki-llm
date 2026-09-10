# reconcile_context_packet

**Entry point:** `reconcile_context_packet` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md), [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), and 30 more

**Complete modules touched:**

- [api](../modules/api.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [context_service](../modules/context_service.md)
- [data_flow](../modules/data_flow.md)
- [dependency_versions](../modules/dependency_versions.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [entrypoints](../modules/entrypoints.md)
- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [imports](../modules/imports.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [plugins](../modules/plugins.md)
- [python_calls](../modules/python_calls.md)
- [python_imports](../modules/python_imports.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as reconcile_context_packet (src/llm_wiki_cli/api.py)
    participant p1 as reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py)
    participant p2 as validate_context_packet
    participant p3 as _coerce_packet_bytes
    participant p4 as isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    participant p5 as bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    participant p6 as TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    participant p7 as ContextPacketMalformedError
    participant p8 as len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    participant p9 as raw.startswith
    participant p10 as raw.endswith
    participant p11 as _strict_json_payload
    participant p12 as raw.decode
    participant p13 as json.loads (src/llm_wiki_cli/services…t.py:_strict_json_payload)
    participant p14 as isinstance (src/llm_wiki_cli/services…t.py:_strict_json_payload)
    participant p15 as _validate_json_tree
    participant p16 as set (src/llm_wiki_cli/services…et.py:_validate_json_tree)
    participant p17 as visit (src/llm_wiki_cli/services…et.py:_validate_json_tree)
    participant p18 as _packet_contract_for_schema
    participant p19 as isinstance (src/llm_wiki_cli/services…acket_contract_for_schema)
    participant p20 as _PACKET_CONTRACT_BY_SCHEMA.get
    p0->>p1: reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py)
    p1->>p2: validate_context_packet
    p2->>p3: _coerce_packet_bytes
    p3-->>p4: isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    p3-->>p4: isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    p3-->>p5: bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    p3-->>p6: TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    p3->>p7: ContextPacketMalformedError
    p3-->>p8: len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)
    p3->>p7: ContextPacketMalformedError
    p3-->>p9: raw.startswith
    p3->>p7: ContextPacketMalformedError
    p3-->>p10: raw.endswith
    p3-->>p10: raw.endswith
    p3->>p7: ContextPacketMalformedError
    p2->>p11: _strict_json_payload
    p11-->>p12: raw.decode
    p11->>p7: ContextPacketMalformedError
    p11-->>p13: json.loads (src/llm_wiki_cli/services…t.py:_strict_json_payload)
    p11->>p7: ContextPacketMalformedError
    p11-->>p14: isinstance (src/llm_wiki_cli/services…t.py:_strict_json_payload)
    p11->>p7: ContextPacketMalformedError
    p11->>p15: _validate_json_tree
    p15-->>p16: set (src/llm_wiki_cli/services…et.py:_validate_json_tree)
    p15-->>p17: visit (src/llm_wiki_cli/services…et.py:_validate_json_tree)
    p2->>p18: _packet_contract_for_schema
    p18-->>p19: isinstance (src/llm_wiki_cli/services…acket_contract_for_schema)
    p18->>p7: ContextPacketMalformedError
    p18-->>p20: _PACKET_CONTRACT_BY_SCHEMA.get
    p18->>p7: ContextPacketMalformedError
```

> Call sequence diagram shows 30 of 2067 interactions; 2037 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. reconcile_context_packet (src/llm_wiki_cli/api.py)"]
    s2["2. reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py)"]
    s3["3. validate_context_packet"]
    s4["4. _coerce_packet_bytes"]
    s5["5. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s6["6. isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s7["7. bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s8["8. TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s9["9. ContextPacketMalformedError"]
    s10["10. len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)"]
    s11["11. ContextPacketMalformedError"]
    s12["12. raw.startswith"]
    s1 -->|"reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py)(…)"| s2
    s2 -->|"validate_context_packet(packet_bytes)"| s3
    s3 -->|"_coerce_packet_bytes(packet_bytes)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, bytes)" .-> s5
    s4 -. "isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value, (...))" .-> s6
    s4 -. "bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(value)" .-> s7
    s4 -. "TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)('packet_bytes must be bytes-like')" .-> s8
    s4 -->|"ContextPacketMalformedError('packet_bytes', 'must not be empty')"| s9
    s4 -. "len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes)(raw)" .-> s10
    s4 -->|"ContextPacketMalformedError('packet_bytes', ...)"| s11
    s4 -. "raw.startswith(b'\xef\xbb\xbf')" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/context_packet.md"
    click s3 "../modules/context_packet.md"
    click s4 "../modules/context_packet.md"
    click s9 "../modules/context_packet.md"
    click s11 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `reconcile_context_packet (src/llm_wiki_cli/api.py)` | `packet_bytes: bytes \| bytearray \| memoryview`, `src_dir: str`, `wiki_dir: str`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `PathValidationError`, `context_packet_service`, `context_packet_service`, `context_packet_service`, `context_packet_service`, `context_cmd` | - | `reconciliation` |
| `reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py)` | `packet_bytes: bytes \| bytearray \| memoryview`, `src_dir: str`, `wiki_dir: str`, `allow_external_src: bool`, `read_only: bool`, `job_request: ExtractionJobRequest \| None`, `plan_reporter: Callable[[ExtractionJobPlan], None] \| None`, `source_selection: str \| Path \| None` | `_RECONCILIATION_FACETS`, `CONTEXT_PACKET_RECONCILIATION_POLICY` | - | `ContextPacketReconciliation._from_official_read(...)` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| reconcile_context_packet (src/llm_wiki_cli/api.py) | reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py) | 1044 | `context_packet_service.reconcile_context_packet(packet_bytes, src_dir, wiki_dir, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection)` |
| reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py) | validate_context_packet | 1577 | `validate_context_packet(packet_bytes)` |
| validate_context_packet | _coerce_packet_bytes | 1488 | `_coerce_packet_bytes(packet_bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2251 | `isinstance(value, bytes)` |
| _coerce_packet_bytes | isinstance (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2253 | `isinstance(value, (...))` |
| _coerce_packet_bytes | bytes (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2254 | `bytes(value)` |
| _coerce_packet_bytes | TypeError (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2256 | `TypeError('packet_bytes must be bytes-like')` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2258 | `ContextPacketMalformedError('packet_bytes', 'must not be empty')` |
| _coerce_packet_bytes | len (src/llm_wiki_cli/services…t.py:_coerce_packet_bytes) | 2259 | `len(raw)` |
| _coerce_packet_bytes | ContextPacketMalformedError | 2260 | `ContextPacketMalformedError('packet_bytes', ...)` |
| _coerce_packet_bytes | raw.startswith | 2264 | `raw.startswith(b'\xef\xbb\xbf')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_coerce_packet_bytes` | `isinstance` | 2251 |
| external_call | `_coerce_packet_bytes` | `isinstance` | 2253 |
| external_call | `_coerce_packet_bytes` | `bytes` | 2254 |
| external_call | `_coerce_packet_bytes` | `TypeError` | 2256 |
| unresolved_call | `_coerce_packet_bytes` | `raw.startswith` | 2264 |
| step_limit | `reconcile_context_packet` | `first 12 steps` | 0 |
| truncated_flow | `reconcile_context_packet` | `depth limit` | 0 |

## Behavior

This flow starts at `reconcile_context_packet` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
