# build_qualified_context

**Entry point:** `build_qualified_context` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [common](../modules/common.md), [config](../modules/config.md), [context_packet](../modules/context_packet.md), [dependency_versions](../modules/dependency_versions.md), and 16 more

**Complete modules touched:**

- [common](../modules/common.md)
- [config](../modules/config.md)
- [context_packet](../modules/context_packet.md)
- [dependency_versions](../modules/dependency_versions.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [imports](../modules/imports.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_observability](../modules/knowledge_observability.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [paths](../modules/paths.md)
- [plugins](../modules/plugins.md)
- [services_dependencies](../modules/services_dependencies.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_qualified_context
    participant p1 as _normalized_request
    participant p2 as isinstance
    participant p3 as ProtocolRequestError
    participant p4 as deepcopy
    participant p5 as dict
    participant p6 as setdefault
    participant p7 as _validate_protocol_request
    participant p8 as _packet_contract_for_request
    participant p9 as get
    participant p10 as capture_context_read
    participant p11 as TypeError
    participant p12 as callable
    participant p13 as validate_source_root
    participant p14 as validate_path
    participant p15 as PathValidationError
    participant p16 as resolve
    participant p17 as cwd
    participant p18 as relative_to
    participant p19 as resolve_source_selection
    p0->>p1: _normalized_request
    p1-->>p2: isinstance
    p1-->>p3: ProtocolRequestError
    p1-->>p4: deepcopy
    p1-->>p5: dict
    p1-->>p6: setdefault
    p1-->>p6: setdefault
    p1-->>p7: _validate_protocol_request
    p0->>p8: _packet_contract_for_request
    p8-->>p9: get
    p8-->>p3: ProtocolRequestError
    p0->>p10: capture_context_read
    p10-->>p2: isinstance
    p10-->>p11: TypeError
    p10-->>p12: callable
    p10-->>p11: TypeError
    p10-->>p2: isinstance
    p10-->>p11: TypeError
    p10-->>p2: isinstance
    p10-->>p11: TypeError
    p10-->>p13: validate_source_root
    p10->>p14: validate_path
    p14->>p15: PathValidationError
    p14-->>p16: resolve
    p14-->>p17: cwd
    p14-->>p16: resolve
    p14-->>p17: cwd
    p14-->>p18: relative_to
    p14->>p15: PathValidationError
    p10-->>p19: resolve_source_selection
```

> Call sequence diagram shows 30 of 2082 interactions; 2052 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_qualified_context"]
    s2["2. _normalized_request"]
    s3["3. isinstance"]
    s4["4. ProtocolRequestError"]
    s5["5. deepcopy"]
    s6["6. dict"]
    s7["7. setdefault"]
    s8["8. setdefault"]
    s9["9. _validate_protocol_request"]
    s10["10. _packet_contract_for_request"]
    s11["11. get"]
    s12["12. ProtocolRequestError"]
    s1 -->|"_normalized_request(...)"| s2
    s2 -. "isinstance(request, Mapping)" .-> s3
    s2 -. "context_service.ProtocolRequestError('Request must be a JSON object.', 'request')" .-> s4
    s2 -. "deepcopy(dict(...))" .-> s5
    s2 -. "dict(request)" .-> s6
    s2 -. "candidate.setdefault('protocol', ...)" .-> s7
    s2 -. "candidate.setdefault('filters', {...})" .-> s8
    s2 -. "context_service._validate_protocol_request(candidate)" .-> s9
    s1 -->|"_packet_contract_for_request(normalized)"| s10
    s10 -. "request.get('protocol')" .-> s11
    s10 -. "context_service.ProtocolRequestError(..., 'protocol')" .-> s12
    click s1 "../modules/context_packet.md"
    click s2 "../modules/context_packet.md"
    click s10 "../modules/context_packet.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_qualified_context` | `src_dir: str`, `wiki_dir: str`, `request: Mapping[str, Any] \| None`, `allow_external_src: bool`, `read_only: bool`, `job_request: ExtractionJobRequest \| None`, `plan_reporter: Callable[[ExtractionJobPlan], None] \| None`, `source_selection: str \| Path \| None` | `_KNOWLEDGE_PACKET_CONTRACT`, `_KNOWLEDGE_PACKET_CONTRACT`, `_KNOWLEDGE_PACKET_CONTRACT` | `response[...]` | `validated.packet` |
| `_normalized_request` | `request: Mapping[str, Any]` | `Mapping`, `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `context_service` | - | `context_service._validate_protocol_request(...)` |
| `isinstance` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `_validate_protocol_request` | - | - | - | - |
| `_packet_contract_for_request` | `request: Mapping[str, Any]` | `_LEGACY_PACKET_CONTRACT`, `_LEGACY_PACKET_CONTRACT`, `_KNOWLEDGE_PACKET_CONTRACT`, `_KNOWLEDGE_PACKET_CONTRACT` | - | `_LEGACY_PACKET_CONTRACT`, `_KNOWLEDGE_PACKET_CONTRACT` |
| `get` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_qualified_context | _normalized_request | 1231 | `_normalized_request(...)` |
| _normalized_request | isinstance | 1726 | `isinstance(request, Mapping)` |
| _normalized_request | ProtocolRequestError | 1727 | `context_service.ProtocolRequestError('Request must be a JSON object.', 'request')` |
| _normalized_request | deepcopy | 1731 | `deepcopy(dict(...))` |
| _normalized_request | dict | 1731 | `dict(request)` |
| _normalized_request | setdefault | 1732 | `candidate.setdefault('protocol', ...)` |
| _normalized_request | setdefault | 1740 | `candidate.setdefault('filters', {...})` |
| _normalized_request | _validate_protocol_request | 1741 | `context_service._validate_protocol_request(candidate)` |
| build_qualified_context | _packet_contract_for_request | 1241 | `_packet_contract_for_request(normalized)` |
| _packet_contract_for_request | get | 289 | `request.get('protocol')` |
| _packet_contract_for_request | ProtocolRequestError | 294 | `context_service.ProtocolRequestError(..., 'protocol')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalized_request` | `isinstance` | 1726 |
| external_call | `_normalized_request` | `context_service.ProtocolRequestError` | 1727 |
| external_call | `_normalized_request` | `deepcopy` | 1731 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1732 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1740 |
| external_call | `_normalized_request` | `context_service._validate_protocol_request` | 1741 |
| unresolved_call | `_packet_contract_for_request` | `request.get` | 289 |
| external_call | `_packet_contract_for_request` | `context_service.ProtocolRequestError` | 294 |
| step_limit | `build_qualified_context` | `first 12 steps` | 0 |
| truncated_flow | `build_qualified_context` | `depth limit` | 0 |

## Behavior

This flow starts at `build_qualified_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
