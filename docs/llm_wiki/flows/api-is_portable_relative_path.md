# is_portable_relative_path

**Entry point:** `is_portable_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_portable_relative_path
    participant p1 as require_portable_relative_path
    participant p2 as isinstance
    participant p3 as _default_path_error
    participant p4 as SharedValidationError
    participant p5 as os.fspath
    participant p6 as _syntax_key
    participant p7 as type
    participant p8 as len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p9 as any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p10 as _known_syntax
    participant p11 as _PATH_SYNTAX.get
    participant p12 as _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)
    participant p13 as _check_path_collision
    participant p14 as portable_path_key
    participant p15 as unicodedata.normalize(…).casefold
    participant p16 as unicodedata.normalize (src/llm_wiki_cli/services…ation.py:portable_path_key)
    participant p17 as collision_seen.setdefault
    participant p18 as collision_error
    participant p19 as raw.encode
    participant p20 as raw.replace
    participant p21 as PurePosixPath
    participant p22 as path.is_absolute
    p0->>p1: require_portable_relative_path
    p1-->>p2: isinstance
    p1->>p3: _default_path_error
    p3->>p4: SharedValidationError
    p1-->>p5: os.fspath
    p1-->>p2: isinstance
    p1->>p3: _default_path_error
    p1->>p6: _syntax_key
    p6-->>p7: type
    p6-->>p8: len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p6-->>p9: any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p6-->>p7: type
    p6-->>p7: type
    p6-->>p8: len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p1->>p10: _known_syntax
    p10-->>p11: _PATH_SYNTAX.get
    p10-->>p12: _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)
    p1->>p13: _check_path_collision
    p13->>p14: portable_path_key
    p14-->>p15: unicodedata.normalize(…).casefold
    p14-->>p16: unicodedata.normalize (src/llm_wiki_cli/services…ation.py:portable_path_key)
    p13-->>p17: collision_seen.setdefault
    p13->>p4: SharedValidationError
    p13-->>p18: collision_error
    p1-->>p19: raw.encode
    p1->>p3: _default_path_error
    p1->>p3: _default_path_error
    p1-->>p20: raw.replace
    p1-->>p21: PurePosixPath
    p1-->>p22: path.is_absolute
```

> Call sequence diagram shows 30 of 59 interactions; 29 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_portable_relative_path"]
    s2["2. require_portable_relative_path"]
    s3["3. isinstance"]
    s4["4. _default_path_error"]
    s5["5. SharedValidationError"]
    s6["6. os.fspath"]
    s7["7. isinstance"]
    s8["8. _default_path_error"]
    s9["9. _syntax_key"]
    s10["10. type"]
    s11["11. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s12["12. any (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s1 -->|"require_portable_relative_path(value, normalize_backslashes=normalize_backslashes)"| s2
    s2 -. "isinstance(value, (...))" .-> s3
    s2 -->|"_default_path_error(value)"| s4
    s4 -->|"SharedValidationError(...)"| s5
    s2 -. "os.fspath(value)" .-> s6
    s2 -. "isinstance(raw, str)" .-> s7
    s2 -->|"_default_path_error(value)"| s8
    s2 -->|"_syntax_key('portable', raw, normalize_backslashes, normalize_posix_spelling, required_suffix, defer_non_nfc_error, reject_delete_character)"| s9
    s9 -. "type(value)" .-> s10
    s9 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s11
    s9 -. "any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)" .-> s12
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s5 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s9 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_portable_relative_path` | `value: object`, `normalize_backslashes: bool` | `SharedValidationError` | - | `False`, `True` |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `cached`, `_remember_syntax(...)` |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `os.fspath` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |
| `type` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_portable_relative_path | require_portable_relative_path | 360 | `require_portable_relative_path(value, normalize_backslashes=normalize_backslashes)` |
| require_portable_relative_path | isinstance | 216 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 217 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 113 | `SharedValidationError(...)` |
| require_portable_relative_path | os.fspath | 218 | `os.fspath(value)` |
| require_portable_relative_path | isinstance | 219 | `isinstance(raw, str)` |
| require_portable_relative_path | _default_path_error | 220 | `_default_path_error(value)` |
| require_portable_relative_path | _syntax_key | 221 | `_syntax_key('portable', raw, normalize_backslashes, normalize_posix_spelling, required_suffix, defer_non_nfc_error, reject_delete_character)` |
| _syntax_key | type | 54 | `type(value)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 54 | `len(value)` |
| _syntax_key | any (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `any(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_portable_relative_path` | `isinstance` | 216 |
| external_call | `require_portable_relative_path` | `os.fspath` | 218 |
| external_call | `require_portable_relative_path` | `isinstance` | 219 |
| external_call | `_syntax_key` | `type` | 54 |
| external_call | `_syntax_key` | `any` | 55 |
| step_limit | `is_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `is_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
