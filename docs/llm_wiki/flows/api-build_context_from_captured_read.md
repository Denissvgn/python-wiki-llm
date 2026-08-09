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
    participant p9 as _thaw_json
    participant p10 as str
    participant p11 as items
    participant p12 as _apply_protocol_filters
    participant p13 as _build_protocol_enrichment_from_captured_read
    participant p14 as any
    participant p15 as bool
    participant p16 as set
    participant p17 as _context_query_surface
    participant p18 as DocumentationGraphQueryService
    participant p19 as list
    participant p20 as verification_summaries_for_concepts
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
    p0->>p9: _thaw_json
    p9-->>p1: isinstance
    p9-->>p10: str
    p9->>p9: _thaw_json
    p9-->>p11: items
    p9-->>p1: isinstance
    p9->>p9: _thaw_json
    p0-->>p12: _apply_protocol_filters
    p0->>p13: _build_protocol_enrichment_from_captured_read
    p13-->>p14: any
    p13-->>p15: bool
    p13-->>p16: set
    p13-->>p17: _context_query_surface
    p13->>p18: DocumentationGraphQueryService
    p13-->>p19: list
    p13-->>p19: list
    p13-->>p19: list
    p13->>p9: _thaw_json
    p13-->>p1: isinstance
    p13->>p20: verification_summaries_for_concepts
```

> Call sequence diagram shows 30 of 103 interactions; 73 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
    s12["12. _thaw_json"]
    s1 -. "isinstance(captured, CapturedContextRead)" .-> s2
    s1 -. "TypeError('captured must be a CapturedContextRead')" .-> s3
    s1 -->|"_normalized_request(request)"| s4
    s4 -. "isinstance(request, Mapping)" .-> s5
    s4 -. "context_service.ProtocolRequestError('Request must be a JSON object.', 'request')" .-> s6
    s4 -. "deepcopy(dict(...))" .-> s7
    s4 -. "dict(request)" .-> s8
    s4 -. "candidate.setdefault('protocol', context_service.PROTOCOL_VERSION)" .-> s9
    s4 -. "candidate.setdefault('filters', {...})" .-> s10
    s4 -. "context_service._validate_protocol_request(candidate)" .-> s11
    s1 -->|"_thaw_json(captured.inventory)"| s12
    b0["mutation warnings.append"]
    s1 -. "mutation warnings.append" .-> b0
    b1["mutation warnings.append"]
    s1 -. "mutation warnings.append" .-> b1
    b2["mutation payload.update"]
    s1 -. "mutation payload.update" .-> b2
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
| `build_context_from_captured_read` | `captured: CapturedContextRead`, `request: Mapping[str, Any]` | `CapturedContextRead` | `ranking_policy[...]`, `ranking_policy[...]` | `(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_normalized_request` | `request: Mapping[str, Any]` | `Mapping`, `context_service` | - | `context_service._validate_protocol_request(...)` |
| `isinstance` | - | - | - | - |
| `ProtocolRequestError` | - | - | - | - |
| `deepcopy` | - | - | - | - |
| `dict` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `setdefault` | - | - | - | - |
| `_validate_protocol_request` | - | - | - | - |
| `_thaw_json` | `value: Any` | `Mapping` | - | `...`, `...`, `value` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_context_from_captured_read | isinstance | 701 | `isinstance(captured, CapturedContextRead)` |
| build_context_from_captured_read | TypeError | 702 | `TypeError('captured must be a CapturedContextRead')` |
| build_context_from_captured_read | _normalized_request | 703 | `_normalized_request(request)` |
| _normalized_request | isinstance | 1098 | `isinstance(request, Mapping)` |
| _normalized_request | ProtocolRequestError | 1099 | `context_service.ProtocolRequestError('Request must be a JSON object.', 'request')` |
| _normalized_request | deepcopy | 1103 | `deepcopy(dict(...))` |
| _normalized_request | dict | 1103 | `dict(request)` |
| _normalized_request | setdefault | 1104 | `candidate.setdefault('protocol', context_service.PROTOCOL_VERSION)` |
| _normalized_request | setdefault | 1105 | `candidate.setdefault('filters', {...})` |
| _normalized_request | _validate_protocol_request | 1106 | `context_service._validate_protocol_request(candidate)` |
| build_context_from_captured_read | _thaw_json | 704 | `_thaw_json(captured.inventory)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `warnings.append` | `build_context_from_captured_read` | 727 |
| mutation | `warnings.append` | `build_context_from_captured_read` | 733 |
| mutation | `payload.update` | `build_context_from_captured_read` | 790 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `build_context_from_captured_read` | `isinstance` | 701 |
| unresolved_call | `build_context_from_captured_read` | `TypeError` | 702 |
| unresolved_call | `_normalized_request` | `isinstance` | 1098 |
| external_call | `_normalized_request` | `context_service.ProtocolRequestError` | 1099 |
| external_call | `_normalized_request` | `deepcopy` | 1103 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1104 |
| unresolved_call | `_normalized_request` | `candidate.setdefault` | 1105 |
| external_call | `_normalized_request` | `context_service._validate_protocol_request` | 1106 |
| step_limit | `build_context_from_captured_read` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_context_from_captured_read` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
