# normalize_optional_portable_relative_path

**Entry point:** `normalize_optional_portable_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_optional_portable_relative_path
    participant p1 as isinstance (src/llm_wiki_cli/services…nal_portable_relative_path)
    participant p2 as value.strip
    participant p3 as value.strip().replace
    participant p4 as normalized.startswith
    participant p5 as require_portable_relative_path
    participant p6 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p7 as _default_path_error
    participant p8 as os.fspath
    participant p9 as _syntax_key
    participant p10 as _known_syntax
    participant p11 as _check_path_collision
    participant p12 as raw.encode
    participant p13 as raw.replace
    participant p14 as PurePosixPath
    participant p15 as path.is_absolute
    participant p16 as _WINDOWS_ABSOLUTE_RE.match
    participant p17 as path.as_posix
    participant p18 as normalized.strip
    participant p19 as canonical.casefold().endswith
    participant p20 as canonical.casefold
    participant p21 as required_suffix.casefold
    participant p22 as require_portable_path_component
    p0-->>p1: isinstance (src/llm_wiki_cli/services…nal_portable_relative_path)(value, str)
    p0-->>p2: value.strip
    p0-->>p3: value.strip().replace('\\', '/')
    p0-->>p2: value.strip
    p0-->>p4: normalized.startswith('./')
    p0->>p5: require_portable_relative_path
    p5-->>p6: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))
    p5->>p7: _default_path_error
    p5-->>p8: os.fspath(value)
    p5-->>p6: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)
    p5->>p7: _default_path_error
    p5->>p9: _syntax_key
    p5->>p10: _known_syntax
    p5->>p11: _check_path_collision
    p5-->>p12: raw.encode('utf-8')
    p5->>p7: _default_path_error
    p5->>p7: _default_path_error
    p5-->>p13: raw.replace('\\', '/')
    p5-->>p14: PurePosixPath(normalized)
    p5-->>p15: path.is_absolute
    p5-->>p16: _WINDOWS_ABSOLUTE_RE.match(raw)
    p5->>p7: _default_path_error
    p5->>p7: _default_path_error
    p5-->>p17: path.as_posix
    p5-->>p18: normalized.strip
    p5-->>p19: canonical.casefold().endswith(required_suffix.casefold(...))
    p5-->>p20: canonical.casefold
    p5-->>p21: required_suffix.casefold
    p5->>p7: _default_path_error
    p5->>p22: require_portable_path_component
```

> Call sequence diagram shows 30 of 64 interactions; 34 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 18 (13 omitted); unresolved 13 of 24 (11 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 9 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 14 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 21 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 24 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 25 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 25 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 24 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 46 | - | unresolved | 4 |
> Omission summary shows 8 of 13 groups; 5 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_optional_portable_relative_path"]
    s2["2. isinstance (src/llm_wiki_cli/services…nal_portable_relative_path)"]
    s3["3. value.strip"]
    s4["4. value.strip().replace"]
    s5["5. value.strip"]
    s6["6. normalized.startswith"]
    s7["7. require_portable_relative_path"]
    s8["8. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s9["9. _default_path_error"]
    s10["10. SharedValidationError"]
    s11["11. os.fspath"]
    s12["12. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…nal_portable_relative_path)(value, str)" .-> s2
    s1 -. "value.strip(data not statically known)" .-> s3
    s1 -. "value.strip().replace('\\', '/')" .-> s4
    s1 -. "value.strip(data not statically known)" .-> s5
    s1 -. "normalized.startswith('./')" .-> s6
    s1 -->|"require_portable_relative_path(normalized)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))" .-> s8
    s7 -->|"_default_path_error(value)"| s9
    s9 -->|"SharedValidationError(...)"| s10
    s7 -. "os.fspath(value)" .-> s11
    s7 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)" .-> s12
    click s1 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s9 "../modules/validation.md"
    click s10 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_optional_portable_relative_path` | `value: object` | `SharedValidationError` | - | `None`, `require_portable_relative_path(...)`, `None` |
| `isinstance (src/llm_wiki_cli/services…nal_portable_relative_path)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `value.strip().replace` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `normalized.startswith` | - | - | - | - |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_optional_portable_relative_path | isinstance (src/llm_wiki_cli/services…nal_portable_relative_path) | 431 | `isinstance(value, str)` |
| normalize_optional_portable_relative_path | value.strip | 431 | `value.strip(data not statically known)` |
| normalize_optional_portable_relative_path | value.strip().replace | 433 | `value.strip().replace('\\', '/')` |
| normalize_optional_portable_relative_path | value.strip | 433 | `value.strip(data not statically known)` |
| normalize_optional_portable_relative_path | normalized.startswith | 434 | `normalized.startswith('./')` |
| normalize_optional_portable_relative_path | require_portable_relative_path | 437 | `require_portable_relative_path(normalized)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 216 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 217 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 113 | `SharedValidationError(...)` |
| require_portable_relative_path | os.fspath | 218 | `os.fspath(value)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 219 | `isinstance(raw, str)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_optional_portable_relative_path` | `isinstance` | 431 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip` | 431 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip().replace` | 433 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip` | 433 |
| unresolved_call | `normalize_optional_portable_relative_path` | `normalized.startswith` | 434 |
| external_call | `require_portable_relative_path` | `isinstance` | 216 |
| external_call | `require_portable_relative_path` | `os.fspath` | 218 |
| external_call | `require_portable_relative_path` | `isinstance` | 219 |
| step_limit | `normalize_optional_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_optional_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
