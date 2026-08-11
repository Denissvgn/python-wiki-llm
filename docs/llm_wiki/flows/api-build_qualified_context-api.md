# build_qualified_context

**Entry point:** `build_qualified_context` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_qualified_context
    participant p1 as _normalize_optional_knowledge_mode
    participant p2 as isinstance
    participant p3 as join
    participant p4 as repr
    participant p5 as InvalidRequestError
    participant p6 as cast
    participant p7 as get
    participant p8 as _caused_by
    participant p9 as set
    participant p10 as id
    participant p11 as add
    participant p12 as WorkspaceStateError
    participant p13 as str
    participant p14 as _path_error_field
    participant p15 as PathPolicyError
    participant p16 as getattr
    participant p17 as _raise_required_knowledge_api_error
    participant p18 as _required_knowledge_failure
    p0->>p1: _normalize_optional_knowledge_mode
    p1-->>p2: isinstance
    p1-->>p3: join
    p1-->>p4: repr
    p1->>p5: InvalidRequestError
    p1-->>p6: cast
    p0->>p5: InvalidRequestError
    p0-->>p7: get
    p0-->>p2: isinstance
    p0->>p5: InvalidRequestError
    p0-->>p0: build_qualified_context
    p0->>p8: _caused_by
    p8-->>p9: set
    p8-->>p10: id
    p8-->>p2: isinstance
    p8-->>p11: add
    p8-->>p10: id
    p0->>p12: WorkspaceStateError
    p0-->>p13: str
    p0->>p14: _path_error_field
    p0-->>p13: str
    p0-->>p15: PathPolicyError
    p0-->>p13: str
    p0->>p14: _path_error_field
    p0-->>p13: str
    p0-->>p15: PathPolicyError
    p0-->>p13: str
    p0-->>p16: getattr
    p0->>p17: _raise_required_knowledge_api_error
    p17->>p18: _required_knowledge_failure
```

> Call sequence diagram shows 30 of 66 interactions; 36 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_qualified_context"]
    s2["2. _normalize_optional_knowledge_mode"]
    s3["3. isinstance"]
    s4["4. join"]
    s5["5. repr"]
    s6["6. InvalidRequestError"]
    s7["7. cast"]
    s8["8. InvalidRequestError"]
    s9["9. get"]
    s10["10. isinstance"]
    s11["11. InvalidRequestError"]
    s12["12. build_qualified_context"]
    s1 -->|"_normalize_optional_knowledge_mode(knowledge_mode)"| s2
    s2 -. "isinstance(value, str)" .-> s3
    s2 -. "', '.join(...)" .-> s4
    s2 -. "repr(item)" .-> s5
    s2 -->|"InvalidRequestError(..., code='invalid-request', details={...})"| s6
    s2 -. "cast(KnowledgeMode, value)" .-> s7
    s1 -->|"InvalidRequestError('knowledge_mode cannot be supplied both as an API parameter and in the packet request', code='invalid-request', details={...})"| s8
    s1 -. "request.get('protocol')" .-> s9
    s1 -. "isinstance(supplied_protocol, str)" .-> s10
    s1 -->|"InvalidRequestError('protocol is not supported', code='invalid-request', details={...})"| s11
    s1 -. "context_packet_service.build_qualified_context(src_dir, wiki_dir, packet_request, allow_external_src=allow_external_src, read_only=read_only, source_selection=…" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s6 "../modules/api.md"
    click s8 "../modules/api.md"
    click s11 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_qualified_context` | `src_dir: str`, `wiki_dir: str`, `request: Mapping[str, Any] \| None`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None`, `knowledge_mode: KnowledgeMode \| None` | `KNOWLEDGE_MODE_REQUEST_FIELD`, `KNOWLEDGE_MODE_REQUEST_FIELD`, `context_cmd`, `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `KNOWLEDGE_MODE_REQUEST_FIELD`, `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `KNOWLEDGE_MODE_REQUEST_FIELD`, `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION` | - | `packet` |
| `_normalize_optional_knowledge_mode` | `value: object` | `KNOWLEDGE_MODE_VALUES`, `KNOWLEDGE_MODE_VALUES`, `KNOWLEDGE_MODE_REQUEST_FIELD`, `KnowledgeMode` | - | `None`, `cast(...)` |
| `isinstance` | - | - | - | - |
| `join` | - | - | - | - |
| `repr` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `cast` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `build_qualified_context` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_qualified_context | _normalize_optional_knowledge_mode | 835 | `_normalize_optional_knowledge_mode(knowledge_mode)` |
| _normalize_optional_knowledge_mode | isinstance | 360 | `isinstance(value, str)` |
| _normalize_optional_knowledge_mode | join | 361 | `', '.join(...)` |
| _normalize_optional_knowledge_mode | repr | 361 | `repr(item)` |
| _normalize_optional_knowledge_mode | InvalidRequestError | 362 | `InvalidRequestError(..., code='invalid-request', details={...})` |
| _normalize_optional_knowledge_mode | cast | 367 | `cast(KnowledgeMode, value)` |
| build_qualified_context | InvalidRequestError | 839 | `InvalidRequestError('knowledge_mode cannot be supplied both as an API parameter and in the packet request', code='invalid-request', details={...})` |
| build_qualified_context | get | 845 | `request.get('protocol')` |
| build_qualified_context | isinstance | 847 | `isinstance(supplied_protocol, str)` |
| build_qualified_context | InvalidRequestError | 854 | `InvalidRequestError('protocol is not supported', code='invalid-request', details={...})` |
| build_qualified_context | build_qualified_context | 877 | `context_packet_service.build_qualified_context(src_dir, wiki_dir, packet_request, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalize_optional_knowledge_mode` | `isinstance` | 360 |
| unresolved_call | `_normalize_optional_knowledge_mode` | `', '.join` | 361 |
| external_call | `_normalize_optional_knowledge_mode` | `cast` | 367 |
| unresolved_call | `build_qualified_context` | `request.get` | 845 |
| unresolved_call | `build_qualified_context` | `isinstance` | 847 |
| external_call | `build_qualified_context` | `context_packet_service.build_qualified_context` | 877 |
| step_limit | `build_qualified_context` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_qualified_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
