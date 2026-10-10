# resolve_portable_workspace_path

**Entry point:** `resolve_portable_workspace_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as resolve_portable_workspace_path
    participant p1 as require_portable_relative_path
    participant p2 as resolve_workspace_path
    participant p3 as isinstance
    participant p4 as workspace_root.resolve
    participant p5 as _default_path_error
    participant p6 as (…).resolve
    participant p7 as os.fspath
    participant p8 as target.relative_to
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
    p0->>p1: require_portable_relative_path
    p0->>p2: resolve_workspace_path
    p1-->>p3: isinstance(value, (...))
    p2-->>p4: workspace_root.resolve
    p1->>p5: _default_path_error
    p2-->>p6: (…).resolve
    p1-->>p7: os.fspath(value)
    p2-->>p8: target.relative_to(resolved_root)
    p1-->>p3: isinstance(raw, str)
    p1->>p5: _default_path_error
    p1->>p9: _syntax_key
    p1->>p10: _known_syntax
    p1->>p11: _check_path_collision
    p1-->>p12: raw.encode('utf-8')
    p1->>p5: _default_path_error
    p1->>p5: _default_path_error
    p1-->>p13: raw.replace('\\', '/')
    p1-->>p14: PurePosixPath(normalized)
    p1-->>p15: path.is_absolute
    p1-->>p16: _WINDOWS_ABSOLUTE_RE.match(raw)
    p1->>p5: _default_path_error
    p1->>p5: _default_path_error
    p1-->>p17: path.as_posix
    p1-->>p18: normalized.strip
    p1-->>p19: canonical.casefold().endswith(required_suffix.casefold(...))
    p1-->>p20: canonical.casefold
    p1-->>p21: required_suffix.casefold
    p1->>p5: _default_path_error
    p1->>p22: require_portable_path_component
    p1->>p11: _check_path_collision
```

> Call sequence diagram shows 30 of 63 interactions; 33 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 17 (13 omitted); unresolved 12 of 23 (11 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 4 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 9 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 16 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 19 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 20 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 20 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 19 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 41 | - | unresolved | 4 |
> Omission summary shows 8 of 13 groups; 5 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. resolve_portable_workspace_path"]
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
    s1 -->|"require_portable_relative_path(…)"| s2
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
| `resolve_portable_workspace_path` | `workspace_root: Path`, `relative: str \| Path`, `path_error: Exception`, `escape_error: Exception`, `traversal_error: Exception \| None` | - | - | `resolve_workspace_path(...)` |
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
| resolve_portable_workspace_path | require_portable_relative_path | 552 | `require_portable_relative_path(relative, text_error=path_error, relative_error=path_error, escape_error=escape_error, traversal_error=..., separator_error=path_error, utf8_error=path_error, control_error=path_error, non_nfc_error=path_error, nonportable_error=path_error, reserved_error=path_error)` |
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
| step_limit | `resolve_portable_workspace_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `resolve_portable_workspace_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
