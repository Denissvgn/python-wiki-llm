# normalize_supplied_paths

**Entry point:** `normalize_supplied_paths` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_queries](../modules/documentation_queries.md), [documentation_query_builder](../modules/documentation_query_builder.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_supplied_paths
    participant p1 as _portable_supplied_path
    participant p2 as _supplied_path_values
    participant p3 as tuple
    participant p4 as sorted
    participant p5 as item.casefold
    participant p6 as DocumentationQueryError
    participant p7 as isinstance (src/llm_wiki_cli/services…r.py:_supplied_path_values)
    participant p8 as require_portable_relative_path
    participant p9 as list
    participant p10 as islice
    participant p11 as iter
    participant p12 as len (src/llm_wiki_cli/services…r.py:_supplied_path_values)
    participant p13 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p14 as _default_path_error
    participant p15 as os.fspath
    participant p16 as _syntax_key
    participant p17 as _known_syntax
    participant p18 as _check_path_collision
    participant p19 as raw.encode
    participant p20 as raw.replace
    participant p21 as PurePosixPath
    participant p22 as path.is_absolute
    p0->>p1: _portable_supplied_path
    p0->>p2: _supplied_path_values
    p0-->>p3: tuple(sorted(...))
    p0-->>p4: sorted(normalized, key=...)
    p0-->>p5: item.casefold
    p1->>p6: DocumentationQueryError
    p2-->>p7: isinstance (src/llm_wiki_cli/services…r.py:_supplied_path_values)(values, (...))
    p1->>p8: require_portable_relative_path
    p2-->>p7: isinstance (src/llm_wiki_cli/services…r.py:_supplied_path_values)(values, Iterable)
    p2->>p6: DocumentationQueryError
    p2-->>p9: list(islice(...))
    p2-->>p10: islice(iter(...), ...)
    p2-->>p11: iter(values)
    p2->>p6: DocumentationQueryError
    p2-->>p12: len (src/llm_wiki_cli/services…r.py:_supplied_path_values)(requested)
    p2->>p6: DocumentationQueryError
    p8-->>p13: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))
    p8->>p14: _default_path_error
    p8-->>p15: os.fspath(value)
    p8-->>p13: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)
    p8->>p14: _default_path_error
    p8->>p16: _syntax_key
    p8->>p17: _known_syntax
    p8->>p18: _check_path_collision
    p8-->>p19: raw.encode('utf-8')
    p8->>p14: _default_path_error
    p8->>p14: _default_path_error
    p8-->>p20: raw.replace('\\', '/')
    p8-->>p21: PurePosixPath(normalized)
    p8-->>p22: path.is_absolute
```

> Call sequence diagram shows 30 of 74 interactions; 44 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 12 of 25 (13 omitted); unresolved 4 of 21 (17 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 6 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 11 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 18 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 21 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 22 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 22 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 21 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 4 | - | unresolved | 6 |
> Omission summary shows 8 of 14 groups; 6 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_supplied_paths"]
    s2["2. _portable_supplied_path"]
    s3["3. DocumentationQueryError"]
    s4["4. require_portable_relative_path"]
    s5["5. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s6["6. _default_path_error"]
    s7["7. SharedValidationError"]
    s8["8. os.fspath"]
    s9["9. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s10["10. _default_path_error"]
    s11["11. _syntax_key"]
    s12["12. type"]
    s1 -->|"_portable_supplied_path(value)"| s2
    s2 -->|"DocumentationQueryError('paths must contain normalized portable relative source paths.')"| s3
    s2 -->|"require_portable_relative_path(…)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))" .-> s5
    s4 -->|"_default_path_error(value)"| s6
    s6 -->|"SharedValidationError(...)"| s7
    s4 -. "os.fspath(value)" .-> s8
    s4 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)" .-> s9
    s4 -->|"_default_path_error(value)"| s10
    s4 -->|"_syntax_key('portable', raw, normalize_backslashes, normalize_posix_spelling, required_suffix, defer_non_nfc_error, reject_delete_character)"| s11
    s11 -. "type(value)" .-> s12
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/documentation_query_builder.md"
    click s3 "../modules/documentation_queries.md"
    click s4 "../modules/validation.md"
    click s6 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s10 "../modules/validation.md"
    click s11 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_supplied_paths` | `values: object` | - | - | `tuple(...)` |
| `_portable_supplied_path` | `value: object` | - | - | `require_portable_relative_path(...)` |
| `DocumentationQueryError` | - | - | - | - |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |
| `type` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_supplied_paths | _portable_supplied_path | 139 | `_portable_supplied_path(value)` |
| _portable_supplied_path | DocumentationQueryError | 117 | `DocumentationQueryError('paths must contain normalized portable relative source paths.')` |
| _portable_supplied_path | require_portable_relative_path | 120 | `require_portable_relative_path(value, text_error=error, relative_error=error, escape_error=error, traversal_error=error, separator_error=error, utf8_error=error, control_error=error, non_nfc_error=error, nonportable_error=error, reserved_error=error)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 216 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 217 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 113 | `SharedValidationError(...)` |
| require_portable_relative_path | os.fspath | 218 | `os.fspath(value)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 219 | `isinstance(raw, str)` |
| require_portable_relative_path | _default_path_error | 220 | `_default_path_error(value)` |
| require_portable_relative_path | _syntax_key | 221 | `_syntax_key('portable', raw, normalize_backslashes, normalize_posix_spelling, required_suffix, defer_non_nfc_error, reject_delete_character)` |
| _syntax_key | type | 54 | `type(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_portable_relative_path` | `isinstance` | 216 |
| external_call | `require_portable_relative_path` | `os.fspath` | 218 |
| external_call | `require_portable_relative_path` | `isinstance` | 219 |
| external_call | `_syntax_key` | `type` | 54 |
| step_limit | `normalize_supplied_paths` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_supplied_paths` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
