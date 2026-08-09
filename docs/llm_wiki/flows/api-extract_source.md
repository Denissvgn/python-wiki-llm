# extract_source

**Entry point:** `extract_source` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [api](../modules/api.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as extract_source
    participant p1 as build_extract_payload
    participant p2 as _caused_by
    participant p3 as set
    participant p4 as id
    participant p5 as isinstance
    participant p6 as add
    participant p7 as WorkspaceStateError
    participant p8 as str
    participant p9 as PathPolicyError
    participant p10 as InvalidRequestError
    participant p11 as cast
    p0-->>p1: build_extract_payload
    p0->>p2: _caused_by
    p2-->>p3: set
    p2-->>p4: id
    p2-->>p5: isinstance
    p2-->>p6: add
    p2-->>p4: id
    p0->>p7: WorkspaceStateError
    p0-->>p8: str
    p0-->>p9: PathPolicyError
    p0-->>p8: str
    p0->>p7: WorkspaceStateError
    p0-->>p8: str
    p0->>p10: InvalidRequestError
    p0-->>p8: str
    p0-->>p11: cast
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. extract_source"]
    s2["2. build_extract_payload"]
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
    s1 -. "extract_cmd.build_extract_payload(src_dir, changed=changed, summary=summary, deep=deep, paths=paths, package_filter=package, include_empty=include_empty, allow…" .-> s2
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
| `extract_source` | `src_dir: str`, `changed: bool`, `summary: bool`, `deep: bool`, `paths: list[str] \| None`, `package: str \| None`, `include_empty: bool`, `allow_external_src: bool` | `PathValidationError`, `extract_cmd`, `ExtractSourceResult` | - | `cast(...)` |
| `build_extract_payload` | - | - | - | - |
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
| extract_source | build_extract_payload | 595 | `extract_cmd.build_extract_payload(src_dir, changed=changed, summary=summary, deep=deep, paths=paths, package_filter=package, include_empty=include_empty, allow_external_src=allow_external_src, read_only=read_only, source_selection=source_selection)` |
| extract_source | _caused_by | 608 | `_caused_by(exc, OSError)` |
| _caused_by | set | 382 | `set(data not statically known)` |
| _caused_by | id | 383 | `id(current)` |
| _caused_by | isinstance | 384 | `isinstance(current, expected)` |
| _caused_by | add | 386 | `seen.add(id(...))` |
| _caused_by | id | 386 | `id(current)` |
| extract_source | WorkspaceStateError | 609 | `WorkspaceStateError(str(...))` |
| extract_source | str | 609 | `str(exc)` |
| extract_source | PathPolicyError | 610 | `PathPolicyError(str(...))` |
| extract_source | str | 610 | `str(exc)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `_caused_by` | 386 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `extract_source` | `extract_cmd.build_extract_payload` | 595 |
| unresolved_call | `_caused_by` | `id` | 383 |
| unresolved_call | `_caused_by` | `isinstance` | 384 |
| unresolved_call | `extract_source` | `PathPolicyError` | 610 |
| step_limit | `extract_source` | `first 12 steps` | 0 |

## Behavior

Returns the stable extraction payload directly instead of printing it. The API
supports changed, summary, deep, path, package, and source-selection controls
and defaults to a read-only source boundary. It maps invalid options, path
policy failures, and extractor/workspace failures to distinct public API error
types so callers need not parse command output.
