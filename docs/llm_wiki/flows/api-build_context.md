# build_context

**Entry point:** `build_context` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_context
    participant p1 as _normalise_focus
    participant p2 as isinstance
    participant p3 as list
    participant p4 as _normalize_optional_knowledge_mode
    participant p5 as join
    participant p6 as repr
    participant p7 as InvalidRequestError
    participant p8 as cast
    participant p9 as _validate_protocol_request
    participant p10 as _build_context
    participant p11 as get
    participant p12 as _caused_by
    participant p13 as set
    participant p14 as id
    participant p15 as add
    participant p16 as WorkspaceStateError
    participant p17 as str
    participant p18 as _path_error_field
    participant p19 as PathPolicyError
    participant p20 as _raise_required_knowledge_api_error
    participant p21 as _required_knowledge_failure
    p0->>p1: _normalise_focus
    p1-->>p2: isinstance
    p1-->>p3: list
    p0->>p4: _normalize_optional_knowledge_mode
    p4-->>p2: isinstance
    p4-->>p5: join
    p4-->>p6: repr
    p4->>p7: InvalidRequestError
    p4-->>p8: cast
    p0-->>p9: _validate_protocol_request
    p0-->>p10: _build_context
    p0-->>p11: get
    p0->>p12: _caused_by
    p12-->>p13: set
    p12-->>p14: id
    p12-->>p2: isinstance
    p12-->>p15: add
    p12-->>p14: id
    p0->>p16: WorkspaceStateError
    p0-->>p17: str
    p0->>p18: _path_error_field
    p0-->>p17: str
    p0-->>p19: PathPolicyError
    p0-->>p17: str
    p0->>p18: _path_error_field
    p0-->>p17: str
    p0->>p20: _raise_required_knowledge_api_error
    p20->>p21: _required_knowledge_failure
    p21-->>p13: set
    p21-->>p14: id
```

> Call sequence diagram shows 30 of 61 interactions; 31 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_context"]
    s2["2. _normalise_focus"]
    s3["3. isinstance"]
    s4["4. list"]
    s5["5. _normalize_optional_knowledge_mode"]
    s6["6. isinstance"]
    s7["7. join"]
    s8["8. repr"]
    s9["9. InvalidRequestError"]
    s10["10. cast"]
    s11["11. _validate_protocol_request"]
    s12["12. _build_context"]
    s1 -->|"_normalise_focus(focus)"| s2
    s2 -. "isinstance(focus, str)" .-> s3
    s2 -. "list(focus)" .-> s4
    s1 -->|"_normalize_optional_knowledge_mode(knowledge_mode)"| s5
    s5 -. "isinstance(value, str)" .-> s6
    s5 -. "', '.join(...)" .-> s7
    s5 -. "repr(item)" .-> s8
    s5 -->|"InvalidRequestError(..., code='invalid-request', details={...})"| s9
    s5 -. "cast(KnowledgeMode, value)" .-> s10
    s1 -. "context_cmd._validate_protocol_request(request)" .-> s11
    s1 -. "context_cmd._build_context(src_dir, validated[...], validated[...], validated[...], validated[...], prefer_fresh=validated[...], emit_warnings=False, allow_ext…" .-> s12
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s5 "../modules/api.md"
    click s9 "../modules/api.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_context` | `src_dir: str`, `budget: int`, `format: str`, `focus: str \| list[str]`, `filters: dict[str, Any] \| None`, `wiki_dir: str`, `prefer_fresh: bool`, `allow_external_src: bool` | `context_cmd`, `CONTEXT_KNOWLEDGE_PROTOCOL_VERSION`, `KNOWLEDGE_MODE_REQUEST_FIELD`, `PathValidationError`, `context_cmd`, `context_cmd`, `MarkdownContextResult`, `ContextPayload` | `request[...]`, `result[...]` | `cast(...)`, `cast(...)` |
| `_normalise_focus` | `focus: str \| list[str]` | - | - | `[...]`, `[...]`, `[...]`, `list(...)` |
| `isinstance` | - | - | - | - |
| `list` | - | - | - | - |
| `_normalize_optional_knowledge_mode` | `value: object` | `KNOWLEDGE_MODE_VALUES`, `KNOWLEDGE_MODE_VALUES`, `KNOWLEDGE_MODE_REQUEST_FIELD`, `KnowledgeMode` | - | `None`, `cast(...)` |
| `isinstance` | - | - | - | - |
| `join` | - | - | - | - |
| `repr` | - | - | - | - |
| `InvalidRequestError` | - | - | - | - |
| `cast` | - | - | - | - |
| `_validate_protocol_request` | - | - | - | - |
| `_build_context` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_context | _normalise_focus | 742 | `_normalise_focus(focus)` |
| _normalise_focus | isinstance | 2316 | `isinstance(focus, str)` |
| _normalise_focus | list | 2322 | `list(focus)` |
| build_context | _normalize_optional_knowledge_mode | 743 | `_normalize_optional_knowledge_mode(knowledge_mode)` |
| _normalize_optional_knowledge_mode | isinstance | 360 | `isinstance(value, str)` |
| _normalize_optional_knowledge_mode | join | 361 | `', '.join(...)` |
| _normalize_optional_knowledge_mode | repr | 361 | `repr(item)` |
| _normalize_optional_knowledge_mode | InvalidRequestError | 362 | `InvalidRequestError(..., code='invalid-request', details={...})` |
| _normalize_optional_knowledge_mode | cast | 367 | `cast(KnowledgeMode, value)` |
| build_context | _validate_protocol_request | 759 | `context_cmd._validate_protocol_request(request)` |
| build_context | _build_context | 760 | `context_cmd._build_context(src_dir, validated[...], validated[...], validated[...], validated[...], prefer_fresh=validated[...], emit_warnings=False, allow_external_src=allow_external_src, read_only=read_only, wiki_dir=wiki_dir, source_selection=source_selection, knowledge_mode=validated.get(...), include_plugins=True)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalise_focus` | `isinstance` | 2316 |
| unresolved_call | `_normalize_optional_knowledge_mode` | `isinstance` | 360 |
| unresolved_call | `_normalize_optional_knowledge_mode` | `', '.join` | 361 |
| external_call | `_normalize_optional_knowledge_mode` | `cast` | 367 |
| external_call | `build_context` | `context_cmd._validate_protocol_request` | 759 |
| external_call | `build_context` | `context_cmd._build_context` | 760 |
| step_limit | `build_context` | `first 12 steps` | 0 |

## Behavior

Normalizes focus values, validates the versioned context request, and builds a
token-bounded response from the selected source and wiki. JSON mode returns the
payload with any warnings; Markdown mode returns rendered content alongside the
same payload and warnings. Path, workspace, and request failures remain
separate public API categories, and read-only mode is the default.
