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
    participant p4 as _validate_protocol_request
    participant p5 as _build_context
    participant p6 as _caused_by
    participant p7 as set
    participant p8 as id
    participant p9 as add
    participant p10 as WorkspaceStateError
    participant p11 as str
    participant p12 as PathPolicyError
    participant p13 as InvalidRequestError
    participant p14 as cast
    participant p15 as _render_markdown
    participant p16 as dict
    p0->>p1: _normalise_focus
    p1-->>p2: isinstance
    p1-->>p3: list
    p0-->>p4: _validate_protocol_request
    p0-->>p5: _build_context
    p0->>p6: _caused_by
    p6-->>p7: set
    p6-->>p8: id
    p6-->>p2: isinstance
    p6-->>p9: add
    p6-->>p8: id
    p0->>p10: WorkspaceStateError
    p0-->>p11: str
    p0-->>p12: PathPolicyError
    p0-->>p11: str
    p0-->>p12: PathPolicyError
    p0-->>p11: str
    p0->>p10: WorkspaceStateError
    p0-->>p11: str
    p0->>p13: InvalidRequestError
    p0-->>p11: str
    p0-->>p14: cast
    p0-->>p15: _render_markdown
    p0-->>p16: dict
    p0-->>p14: cast
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_context"]
    s2["2. _normalise_focus"]
    s3["3. isinstance"]
    s4["4. list"]
    s5["5. _validate_protocol_request"]
    s6["6. _build_context"]
    s7["7. _caused_by"]
    s8["8. set"]
    s9["9. id"]
    s10["10. isinstance"]
    s11["11. add"]
    s12["12. id"]
    s1 -->|"_normalise_focus(focus)"| s2
    s2 -. "isinstance(focus, str)" .-> s3
    s2 -. "list(focus)" .-> s4
    s1 -. "context_cmd._validate_protocol_request(request)" .-> s5
    s1 -. "context_cmd._build_context(src_dir, validated[...], validated[...], validated[...], validated[...], prefer_fresh=validated[...], emit_warnings=False, allow_ext…" .-> s6
    s1 -->|"_caused_by(exc, OSError)"| s7
    s7 -. "set(data not statically known)" .-> s8
    s7 -. "id(current)" .-> s9
    s7 -. "isinstance(current, expected)" .-> s10
    s7 -. "seen.add(id(...))" .-> s11
    s7 -. "id(current)" .-> s12
    b0["mutation seen.add"]
    s7 -. "mutation seen.add" .-> b0
    click s1 "../modules/api.md"
    click s2 "../modules/api.md"
    click s7 "../modules/api.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_context` | `src_dir: str`, `budget: int`, `format: str`, `focus: str \| list[str]`, `filters: dict[str, Any] \| None`, `wiki_dir: str`, `prefer_fresh: bool`, `allow_external_src: bool` | `context_cmd`, `PathValidationError`, `context_cmd`, `MarkdownContextResult`, `ContextPayload` | `result[...]` | `cast(...)`, `cast(...)` |
| `_normalise_focus` | `focus: str \| list[str]` | - | - | `[...]`, `[...]`, `[...]`, `list(...)` |
| `isinstance` | - | - | - | - |
| `list` | - | - | - | - |
| `_validate_protocol_request` | - | - | - | - |
| `_build_context` | - | - | - | - |
| `_caused_by` | `exc: BaseException`, `expected: type[BaseException]` | - | - | `True`, `False` |
| `set` | - | - | - | - |
| `id` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `add` | - | - | - | - |
| `id` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_context | _normalise_focus | 633 | `_normalise_focus(focus)` |
| _normalise_focus | isinstance | 1238 | `isinstance(focus, str)` |
| _normalise_focus | list | 1244 | `list(focus)` |
| build_context | _validate_protocol_request | 643 | `context_cmd._validate_protocol_request(request)` |
| build_context | _build_context | 644 | `context_cmd._build_context(src_dir, validated[...], validated[...], validated[...], validated[...], prefer_fresh=validated[...], emit_warnings=False, allow_external_src=allow_external_src, read_only=read_only, wiki_dir=wiki_dir, source_selection=source_selection)` |
| build_context | _caused_by | 658 | `_caused_by(exc, OSError)` |
| _caused_by | set | 382 | `set(data not statically known)` |
| _caused_by | id | 383 | `id(current)` |
| _caused_by | isinstance | 384 | `isinstance(current, expected)` |
| _caused_by | add | 386 | `seen.add(id(...))` |
| _caused_by | id | 386 | `id(current)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `_caused_by` | 386 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_normalise_focus` | `isinstance` | 1238 |
| external_call | `build_context` | `context_cmd._validate_protocol_request` | 643 |
| external_call | `build_context` | `context_cmd._build_context` | 644 |
| unresolved_call | `_caused_by` | `id` | 383 |
| unresolved_call | `_caused_by` | `isinstance` | 384 |
| step_limit | `build_context` | `first 12 steps` | 0 |

## Behavior

Normalizes focus values, validates the versioned context request, and builds a
token-bounded response from the selected source and wiki. JSON mode returns the
payload with any warnings; Markdown mode returns rendered content alongside the
same payload and warnings. Path, workspace, and request failures remain
separate public API categories, and read-only mode is the default.
