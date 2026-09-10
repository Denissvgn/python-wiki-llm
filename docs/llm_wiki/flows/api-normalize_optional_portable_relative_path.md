# normalize_optional_portable_relative_path

**Entry point:** `normalize_optional_portable_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

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
    participant p8 as SharedValidationError
    participant p9 as os.fspath
    participant p10 as raw.encode
    participant p11 as raw.replace
    participant p12 as PurePosixPath
    participant p13 as path.is_absolute
    participant p14 as _WINDOWS_ABSOLUTE_RE.match
    participant p15 as path.as_posix
    participant p16 as normalized.strip
    participant p17 as canonical.casefold().endswith
    participant p18 as canonical.casefold
    participant p19 as required_suffix.casefold
    participant p20 as require_portable_path_component
    participant p21 as component.encode
    p0-->>p1: isinstance (src/llm_wiki_cli/services…nal_portable_relative_path)
    p0-->>p2: value.strip
    p0-->>p3: value.strip().replace
    p0-->>p2: value.strip
    p0-->>p4: normalized.startswith
    p0->>p5: require_portable_relative_path
    p5-->>p6: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    p5->>p7: _default_path_error
    p7->>p8: SharedValidationError
    p5-->>p9: os.fspath
    p5-->>p6: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    p5->>p7: _default_path_error
    p5-->>p10: raw.encode
    p5->>p7: _default_path_error
    p5->>p7: _default_path_error
    p5-->>p11: raw.replace
    p5-->>p12: PurePosixPath
    p5-->>p13: path.is_absolute
    p5-->>p14: _WINDOWS_ABSOLUTE_RE.match
    p5->>p7: _default_path_error
    p5->>p7: _default_path_error
    p5-->>p15: path.as_posix
    p5-->>p16: normalized.strip
    p5-->>p17: canonical.casefold().endswith
    p5-->>p18: canonical.casefold
    p5-->>p19: required_suffix.casefold
    p5->>p7: _default_path_error
    p5->>p20: require_portable_path_component
    p20-->>p21: component.encode
    p20->>p8: SharedValidationError
```

> Call sequence diagram shows 30 of 48 interactions; 18 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `canonical` |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_optional_portable_relative_path | isinstance (src/llm_wiki_cli/services…nal_portable_relative_path) | 382 | `isinstance(value, str)` |
| normalize_optional_portable_relative_path | value.strip | 382 | `value.strip(data not statically known)` |
| normalize_optional_portable_relative_path | value.strip().replace | 384 | `value.strip().replace('\\', '/')` |
| normalize_optional_portable_relative_path | value.strip | 384 | `value.strip(data not statically known)` |
| normalize_optional_portable_relative_path | normalized.startswith | 385 | `normalized.startswith('./')` |
| normalize_optional_portable_relative_path | require_portable_relative_path | 388 | `require_portable_relative_path(normalized)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 170 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 171 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 67 | `SharedValidationError(...)` |
| require_portable_relative_path | os.fspath | 172 | `os.fspath(value)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 173 | `isinstance(raw, str)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_optional_portable_relative_path` | `isinstance` | 382 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip` | 382 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip().replace` | 384 |
| unresolved_call | `normalize_optional_portable_relative_path` | `value.strip` | 384 |
| unresolved_call | `normalize_optional_portable_relative_path` | `normalized.startswith` | 385 |
| external_call | `require_portable_relative_path` | `isinstance` | 170 |
| external_call | `require_portable_relative_path` | `os.fspath` | 172 |
| external_call | `require_portable_relative_path` | `isinstance` | 173 |
| step_limit | `normalize_optional_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_optional_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
