# require_portable_relative_path

**Entry point:** `require_portable_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_portable_relative_path
    participant p1 as isinstance
    participant p2 as _default_path_error
    participant p3 as os.fspath
    participant p4 as _syntax_key
    participant p5 as _known_syntax
    participant p6 as _check_path_collision
    participant p7 as raw.encode
    participant p8 as raw.replace
    participant p9 as PurePosixPath
    participant p10 as path.is_absolute
    participant p11 as _WINDOWS_ABSOLUTE_RE.match
    participant p12 as path.as_posix
    participant p13 as normalized.strip
    participant p14 as canonical.casefold().endswith
    participant p15 as canonical.casefold
    participant p16 as required_suffix.casefold
    participant p17 as require_portable_path_component
    participant p18 as _remember_syntax
    participant p19 as SharedValidationError
    participant p20 as type
    participant p21 as _PATH_SYNTAX.get
    participant p22 as portable_path_key
    p0-->>p1: isinstance(value, (...))
    p0->>p2: _default_path_error
    p0-->>p3: os.fspath(value)
    p0-->>p1: isinstance(raw, str)
    p0->>p2: _default_path_error
    p0->>p4: _syntax_key
    p0->>p5: _known_syntax
    p0->>p6: _check_path_collision
    p0-->>p7: raw.encode('utf-8')
    p0->>p2: _default_path_error
    p0->>p2: _default_path_error
    p0-->>p8: raw.replace('\\', '/')
    p0-->>p9: PurePosixPath(normalized)
    p0-->>p10: path.is_absolute
    p0-->>p11: _WINDOWS_ABSOLUTE_RE.match(raw)
    p0->>p2: _default_path_error
    p0->>p2: _default_path_error
    p0-->>p12: path.as_posix
    p0-->>p13: normalized.strip
    p0-->>p14: canonical.casefold().endswith(required_suffix.casefold(...))
    p0-->>p15: canonical.casefold
    p0-->>p16: required_suffix.casefold
    p0->>p2: _default_path_error
    p0->>p17: require_portable_path_component
    p0->>p6: _check_path_collision
    p0->>p18: _remember_syntax
    p2->>p19: SharedValidationError
    p4-->>p20: type(value)
    p5-->>p21: _PATH_SYNTAX.get(key)
    p6->>p22: portable_path_key
```

> Call sequence diagram shows 30 of 58 interactions; 28 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 17 (12 omitted); unresolved 10 of 20 (10 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 8 | - | external | 5 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 15 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 19 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 19 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 18 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 18 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 40 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 40 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 5 |
> Omission summary shows 8 of 11 groups; 3 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_portable_relative_path"]
    s2["2. isinstance"]
    s3["3. _default_path_error"]
    s4["4. SharedValidationError"]
    s5["5. os.fspath"]
    s6["6. isinstance"]
    s7["7. _default_path_error"]
    s8["8. _syntax_key"]
    s9["9. type"]
    s10["10. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s11["11. any (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s12["12. type"]
    s1 -. "isinstance(value, (...))" .-> s2
    s1 -->|"_default_path_error(value)"| s3
    s3 -->|"SharedValidationError(...)"| s4
    s1 -. "os.fspath(value)" .-> s5
    s1 -. "isinstance(raw, str)" .-> s6
    s1 -->|"_default_path_error(value)"| s7
    s1 -->|"_syntax_key('portable', raw, normalize_backslashes, normalize_posix_spelling, required_suffix, defer_non_nfc_error, reject_delete_character)"| s8
    s8 -. "type(value)" .-> s9
    s8 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s10
    s8 -. "any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)" .-> s11
    s8 -. "type(v)" .-> s12
    click s1 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s4 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s8 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `type` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _syntax_key | type | 55 | `type(v)` |

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
| external_call | `_syntax_key` | `type` | 55 |
| step_limit | `require_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
