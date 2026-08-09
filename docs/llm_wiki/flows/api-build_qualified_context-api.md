# build_qualified_context

**Entry point:** `build_qualified_context` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_qualified_context
    participant p1 as _caused_by
    participant p2 as set
    participant p3 as id
    participant p4 as isinstance
    participant p5 as add
    participant p6 as WorkspaceStateError
    participant p7 as str
    participant p8 as PathPolicyError
    participant p9 as InvalidRequestError
    p0-->>p0: build_qualified_context
    p0->>p1: _caused_by
    p1-->>p2: set
    p1-->>p3: id
    p1-->>p4: isinstance
    p1-->>p5: add
    p1-->>p3: id
    p0->>p6: WorkspaceStateError
    p0-->>p7: str
    p0-->>p8: PathPolicyError
    p0-->>p7: str
    p0-->>p8: PathPolicyError
    p0-->>p7: str
    p0->>p6: WorkspaceStateError
    p0-->>p7: str
    p0-->>p8: PathPolicyError
    p0-->>p7: str
    p0->>p6: WorkspaceStateError
    p0-->>p7: str
    p0->>p9: InvalidRequestError
    p0-->>p7: str
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_qualified_context"]
    s2["2. build_qualified_context"]
    s3["3. _caused_by"]
    s4["4. set"]
    s5["5. id"]
    s6["6. isinstance"]
    s7["7. add"]
    s8["8. id"]
    s9["9. WorkspaceStateError"]
    s10["10. str"]
    s11["11. PathPolicyError"]
    s12["12. str"]
    s1 -. "context_packet_service.build_qualified_context(src_dir, wiki_dir, request, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_…" .-> s2
    s1 -->|"_caused_by(exc, OSError)"| s3
    s3 -. "set(data not statically known)" .-> s4
    s3 -. "id(current)" .-> s5
    s3 -. "isinstance(current, expected)" .-> s6
    s3 -. "seen.add(id(...))" .-> s7
    s3 -. "id(current)" .-> s8
    s1 -->|"WorkspaceStateError(str(...))"| s9
    s1 -. "str(exc)" .-> s10
    s1 -. "PathPolicyError(str(...))" .-> s11
    s1 -. "str(exc)" .-> s12
    b0["mutation seen.add"]
    s3 -. "mutation seen.add" .-> b0
    click s1 "../modules/api.md"
    click s3 "../modules/api.md"
    click s9 "../modules/api.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_qualified_context` | `src_dir: str`, `wiki_dir: str`, `request: Mapping[str, Any] \| None`, `allow_external_src: bool`, `read_only: bool`, `source_selection: str \| Path \| None` | `PathValidationError`, `context_packet_service`, `context_packet_service`, `context_packet_service`, `context_cmd` | - | `packet` |
| `build_qualified_context` | - | - | - | - |
| `_caused_by` | `exc: BaseException`, `expected: type[BaseException]` | - | - | `True`, `False` |
| `set` | - | - | - | - |
| `id` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `add` | - | - | - | - |
| `id` | - | - | - | - |
| `WorkspaceStateError` | - | - | - | - |
| `str` | - | - | - | - |
| `PathPolicyError` | - | - | - | - |
| `str` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_qualified_context | build_qualified_context | 697 | `context_packet_service.build_qualified_context(src_dir, wiki_dir, request, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection)` |
| build_qualified_context | _caused_by | 706 | `_caused_by(exc, OSError)` |
| _caused_by | set | 382 | `set(data not statically known)` |
| _caused_by | id | 383 | `id(current)` |
| _caused_by | isinstance | 384 | `isinstance(current, expected)` |
| _caused_by | add | 386 | `seen.add(id(...))` |
| _caused_by | id | 386 | `id(current)` |
| build_qualified_context | WorkspaceStateError | 707 | `WorkspaceStateError(str(...))` |
| build_qualified_context | str | 707 | `str(exc)` |
| build_qualified_context | PathPolicyError | 708 | `PathPolicyError(str(...))` |
| build_qualified_context | str | 708 | `str(exc)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `_caused_by` | 386 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_qualified_context` | `context_packet_service.build_qualified_context` | 697 |
| unresolved_call | `_caused_by` | `id` | 383 |
| unresolved_call | `_caused_by` | `isinstance` | 384 |
| unresolved_call | `build_qualified_context` | `PathPolicyError` | 708 |
| step_limit | `build_qualified_context` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_qualified_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
