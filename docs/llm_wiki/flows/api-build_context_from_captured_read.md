# build_context_from_captured_read

**Entry point:** `build_context_from_captured_read` (`api`)
**Source:** [context_packet](../modules/context_packet.md)
**Modules touched:** [context_packet](../modules/context_packet.md), [documentation_queries](../modules/documentation_queries.md), [knowledge_verification](../modules/knowledge_verification.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_context_from_captured_read
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _normalized_request
    participant p4 as ProtocolRequestError
    participant p5 as deepcopy
    participant p6 as dict
    participant p7 as setdefault
    participant p8 as _validate_protocol_request
    participant p9 as _build_legacy_context_from_captured_read
    participant p10 as _thaw_json
    participant p11 as str
    participant p12 as items
    participant p13 as _apply_protocol_filters
    participant p14 as _build_protocol_enrichment_from_captured_read
    participant p15 as any
    participant p16 as bool
    participant p17 as set
    participant p18 as _context_query_surface
    participant p19 as DocumentationGraphQueryService
    participant p20 as list
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: _normalized_request
    p3-->>p1: isinstance
    p3-->>p4: ProtocolRequestError
    p3-->>p5: deepcopy
    p3-->>p6: dict
    p3-->>p7: setdefault
    p3-->>p7: setdefault
    p3-->>p8: _validate_protocol_request
    p0->>p9: _build_legacy_context_from_captured_read
    p9->>p10: _thaw_json
    p10-->>p1: isinstance
    p10-->>p11: str
    p10->>p10: _thaw_json
    p10-->>p12: items
    p10-->>p1: isinstance
    p10->>p10: _thaw_json
    p9-->>p13: _apply_protocol_filters
    p9->>p14: _build_protocol_enrichment_from_captured_read
    p14-->>p15: any
    p14-->>p16: bool
    p14-->>p17: set
    p14-->>p18: _context_query_surface
    p14->>p19: DocumentationGraphQueryService
    p14-->>p20: list
    p14-->>p20: list
    p14-->>p20: list
    p14->>p10: _thaw_json
    p14-->>p1: isinstance
```

> Call sequence diagram shows 30 of 162 interactions; 132 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_context_from_captured_read"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. _normalized_request"]
    s5["5. isinstance"]
    s6["6. ProtocolRequestError"]
    s7["7. deepcopy"]
    s8["8. dict"]
    s9["9. setdefault"]
    s10["10. setdefault"]
    s11["11. _validate_protocol_request"]
    s12["12. _build_legacy_context_from_captured_read"]
    s1 -. "isinstance(captured, CapturedContextRead)" .-> s2
    s1 -. "TypeError('captured must be a CapturedContextRead')" .-> s3
    s1 -->|"_normalized_request(request)"| s4
    s4 -. "isinstance(request, Mapping)" .-> s5
    s4 -. "context_service.ProtocolRequestError('Request must be a JSON object.', 'request')" .-> s6
    s4 -. "deepcopy(dict(...))" .-> s7
    s4 -. "dict(request)" .-> s8
    s4 -. "candidate.setdefault('protocol', ...)" .-> s9
    s4 -. "candidate.setdefault('filters', {...})" .-> s10
    s4 -. "context_service._validate_protocol_request(candidate)" .-> s11
    s1 -->|"_build_legacy_context_from_captured_read(captured, normalized)"| s12
    b0["mutation warnings.append"]
    s12 -. "mutation warnings.append" .-> b0
    b1["mutation warnings.append"]
    s12 -. "mutation warnings.append" .-> b1
    b2["mutation payload.update"]
    s12 -. "mutation payload.update" .-> b2
    click s1 "../modules/context_packet.md"
    click s4 "../modules/context_packet.md"
    click s12 "../modules/context_packet.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_context_from_captured_read` | `captured: CapturedContextRead`, `request: Mapping[str, Any]` | `CapturedContextRead`, `context_service` | - | `_build_legacy_context_from_captured_read(...)`, `_build_knowledge_context_from_captured_read(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_normalized_request` | `request: Mapping[str, Any]` | `Mapping`, `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `context_service` | - | `context_service._validate_protocol_request(...)` |
| `isinstance` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `_validate_protocol_request` | - | - | - | - |
| `_build_legacy_context_from_captured_read` | `captured: CapturedContextRead`, `normalized: Mapping[str, Any]` | - | `ranking_policy[...]`, `ranking_policy[...]` | `(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_context_from_captured_read | isinstance | 859 | `isinstance(captured, CapturedContextRead)` |
| build_context_from_captured_read | TypeError | 860 | `TypeError('captured must be a CapturedContextRead')` |
| build_context_from_captured_read | _normalized_request | 861 | `_normalized_request(request)` |
| _normalized_request | isinstance | 1726 | `isinstance(request, Mapping)` |
| _normalized_request | ProtocolRequestError | 1727 | `context_service.ProtocolRequestError('Request must be a JSON object.', 'request')` |
| _normalized_request | deepcopy | 1731 | `deepcopy(dict(...))` |
| _normalized_request | dict | 1731 | `dict(request)` |
| _normalized_request | setdefault | 1732 | `candidate.setdefault('protocol', ...)` |
| _normalized_request | setdefault | 1740 | `candidate.setdefault('filters', {...})` |
| _normalized_request | _validate_protocol_request | 1741 | `context_service._validate_protocol_request(candidate)` |
| build_context_from_captured_read | _build_legacy_context_from_captured_read | 863 | `_build_legacy_context_from_captured_read(captured, normalized)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `warnings.append` | `_build_legacy_context_from_captured_read` | 896 |
| mutation | `warnings.append` | `_build_legacy_context_from_captured_read` | 902 |
| mutation | `payload.update` | `_build_legacy_context_from_captured_read` | 959 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_context_from_captured_read` | `isinstance` | 859 |
| unresolved_call | `build_context_from_captured_read` | `TypeError` | 860 |
| unresolved_call | `_normalized_request` | `isinstance` | 1726 |
| external_call | `_normalized_request` | `context_service.ProtocolRequestError` | 1727 |
| external_call | `_normalized_request` | `deepcopy` | 1731 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1732 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1740 |
| external_call | `_normalized_request` | `context_service._validate_protocol_request` | 1741 |
| step_limit | `build_context_from_captured_read` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_context_from_captured_read` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
