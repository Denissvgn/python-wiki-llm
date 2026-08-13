# supplied_paths_from_unified_diff

**Entry point:** `supplied_paths_from_unified_diff` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as supplied_paths_from_unified_diff
    participant p1 as isinstance
    participant p2 as DocumentationQueryError
    participant p3 as encode
    participant p4 as len
    participant p5 as set
    participant p6 as splitlines
    participant p7 as startswith
    participant p8 as split
    participant p9 as tuple
    participant p10 as _diff_metadata_path
    participant p11 as normalize_supplied_paths
    participant p12 as _portable_supplied_path
    participant p13 as require_portable_relative_path
    participant p14 as _default_path_error
    p0-->>p1: isinstance
    p0->>p2: DocumentationQueryError
    p0-->>p3: encode
    p0->>p2: DocumentationQueryError
    p0-->>p4: len
    p0->>p2: DocumentationQueryError
    p0-->>p5: set
    p0-->>p6: splitlines
    p0-->>p7: startswith
    p0->>p2: DocumentationQueryError
    p0-->>p8: split
    p0-->>p4: len
    p0->>p2: DocumentationQueryError
    p0-->>p4: len
    p0->>p2: DocumentationQueryError
    p0-->>p9: tuple
    p0->>p10: _diff_metadata_path
    p10-->>p7: startswith
    p10-->>p8: split
    p10->>p2: DocumentationQueryError
    p10-->>p4: len
    p10->>p2: DocumentationQueryError
    p10-->>p7: startswith
    p10->>p2: DocumentationQueryError
    p10->>p11: normalize_supplied_paths
    p11->>p12: _portable_supplied_path
    p12->>p2: DocumentationQueryError
    p12->>p13: require_portable_relative_path
    p13-->>p1: isinstance
    p13->>p14: _default_path_error
```

> Call sequence diagram shows 30 of 103 interactions; 73 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. supplied_paths_from_unified_diff"]
    s2["2. isinstance"]
    s3["3. DocumentationQueryError"]
    s4["4. encode"]
    s5["5. DocumentationQueryError"]
    s6["6. len"]
    s7["7. DocumentationQueryError"]
    s8["8. set"]
    s9["9. splitlines"]
    s10["10. startswith"]
    s11["11. DocumentationQueryError"]
    s12["12. split"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -->|"DocumentationQueryError('diff must be a UTF-8 text string.')"| s3
    s1 -. "value.encode('utf-8')" .-> s4
    s1 -->|"DocumentationQueryError('diff must be valid UTF-8 text.')"| s5
    s1 -. "len(encoded)" .-> s6
    s1 -->|"DocumentationQueryError(...)"| s7
    s1 -. "set(data not statically known)" .-> s8
    s1 -. "value.splitlines(data not statically known)" .-> s9
    s1 -. "line.startswith('diff --git ')" .-> s10
    s1 -->|"DocumentationQueryError('diff contains unpaired file-header metadata.')"| s11
    s1 -. "shlex.split(..., posix=True)" .-> s12
    b0["mutation selected.update"]
    s1 -. "mutation selected.update" .-> b0
    click s1 "../modules/documentation_query_builder.md"
    click s3 "../modules/documentation_queries.md"
    click s5 "../modules/documentation_queries.md"
    click s7 "../modules/documentation_queries.md"
    click s11 "../modules/documentation_queries.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `supplied_paths_from_unified_diff` | `value: object` | `MAX_SUPPLIED_DIFF_BYTES`, `MAX_SUPPLIED_DIFF_BYTES`, `_UNSET_DIFF_HEADER`, `_UNSET_DIFF_HEADER`, `_UNSET_DIFF_HEADER`, `_UNSET_DIFF_HEADER`, `_UNSET_DIFF_HEADER`, `_UNSET_DIFF_HEADER` | - | `normalize_supplied_paths(...)` |
| `isinstance` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `encode` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `len` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `set` | - | - | - | - |
| `splitlines` | - | - | - | - |
| `startswith` | - | - | - | - |
| `DocumentationQueryError` | - | - | - | - |
| `split` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| supplied_paths_from_unified_diff | isinstance | 170 | `isinstance(value, str)` |
| supplied_paths_from_unified_diff | DocumentationQueryError | 171 | `DocumentationQueryError('diff must be a UTF-8 text string.')` |
| supplied_paths_from_unified_diff | encode | 173 | `value.encode('utf-8')` |
| supplied_paths_from_unified_diff | DocumentationQueryError | 175 | `DocumentationQueryError('diff must be valid UTF-8 text.')` |
| supplied_paths_from_unified_diff | len | 176 | `len(encoded)` |
| supplied_paths_from_unified_diff | DocumentationQueryError | 177 | `DocumentationQueryError(...)` |
| supplied_paths_from_unified_diff | set | 181 | `set(data not statically known)` |
| supplied_paths_from_unified_diff | splitlines | 187 | `value.splitlines(data not statically known)` |
| supplied_paths_from_unified_diff | startswith | 188 | `line.startswith('diff --git ')` |
| supplied_paths_from_unified_diff | DocumentationQueryError | 190 | `DocumentationQueryError('diff contains unpaired file-header metadata.')` |
| supplied_paths_from_unified_diff | split | 194 | `shlex.split(..., posix=True)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `selected.update` | `supplied_paths_from_unified_diff` | 211 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `supplied_paths_from_unified_diff` | `isinstance` | 170 |
| unresolved_call | `supplied_paths_from_unified_diff` | `value.encode` | 173 |
| unresolved_call | `supplied_paths_from_unified_diff` | `value.splitlines` | 187 |
| unresolved_call | `supplied_paths_from_unified_diff` | `line.startswith` | 188 |
| external_call | `supplied_paths_from_unified_diff` | `shlex.split` | 194 |
| step_limit | `supplied_paths_from_unified_diff` | `first 12 steps` | 0 |

## Behavior

This flow starts at `supplied_paths_from_unified_diff` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
