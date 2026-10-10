# validate_portable_relative_path

**Entry point:** `validate_portable_relative_path` (`api`)
**Source:** [protected_artifacts](../modules/protected_artifacts.md)
**Modules touched:** [protected_artifacts](../modules/protected_artifacts.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_portable_relative_path
    participant p1 as os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)
    participant p2 as isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)
    participant p3 as raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)
    participant p4 as require_portable_relative_path
    participant p5 as ProtectedArtifactIntegrityError
    participant p6 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p7 as _default_path_error
    participant p8 as os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p9 as _syntax_key
    participant p10 as _known_syntax
    participant p11 as _check_path_collision
    participant p12 as raw.encode
    participant p13 as raw.replace (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p14 as PurePosixPath
    participant p15 as path.is_absolute
    participant p16 as _WINDOWS_ABSOLUTE_RE.match
    participant p17 as path.as_posix
    participant p18 as normalized.strip
    participant p19 as canonical.casefold().endswith
    participant p20 as canonical.casefold
    p0-->>p1: os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)(relative)
    p0-->>p2: isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)(raw, str)
    p0-->>p3: raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)('\\', '/')
    p0->>p4: require_portable_relative_path
    p0->>p5: ProtectedArtifactIntegrityError
    p0->>p5: ProtectedArtifactIntegrityError
    p0->>p5: ProtectedArtifactIntegrityError
    p0->>p5: ProtectedArtifactIntegrityError
    p0->>p5: ProtectedArtifactIntegrityError
    p4-->>p6: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))
    p4->>p7: _default_path_error
    p4-->>p8: os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)(value)
    p4-->>p6: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)
    p4->>p7: _default_path_error
    p4->>p9: _syntax_key
    p4->>p10: _known_syntax
    p4->>p11: _check_path_collision
    p4-->>p12: raw.encode('utf-8')
    p4->>p7: _default_path_error
    p4->>p7: _default_path_error
    p4-->>p13: raw.replace (src/llm_wiki_cli/services…ire_portable_relative_path)('\\', '/')
    p4-->>p14: PurePosixPath(normalized)
    p4-->>p15: path.is_absolute
    p4-->>p16: _WINDOWS_ABSOLUTE_RE.match(raw)
    p4->>p7: _default_path_error
    p4->>p7: _default_path_error
    p4-->>p17: path.as_posix
    p4-->>p18: normalized.strip
    p4-->>p19: canonical.casefold().endswith(required_suffix.casefold(...))
    p4-->>p20: canonical.casefold
```

> Call sequence diagram shows 30 of 67 interactions; 37 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 6 of 19 (13 omitted); unresolved 9 of 21 (12 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 7 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 12 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 19 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 22 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 23 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 23 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 22 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 5 | - | unresolved | 1 |
> Omission summary shows 8 of 14 groups; 6 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_portable_relative_path"]
    s2["2. os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)"]
    s3["3. isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)"]
    s4["4. raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)"]
    s5["5. require_portable_relative_path"]
    s6["6. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s7["7. _default_path_error"]
    s8["8. SharedValidationError"]
    s9["9. os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s10["10. isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)"]
    s11["11. _default_path_error"]
    s12["12. _syntax_key"]
    s1 -. "os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)(relative)" .-> s2
    s1 -. "isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)(raw, str)" .-> s3
    s1 -. "raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)('\\', '/')" .-> s4
    s1 -->|"require_portable_relative_path(…)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))" .-> s6
    s5 -->|"_default_path_error(value)"| s7
    s7 -->|"SharedValidationError(...)"| s8
    s5 -. "os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)(value)" .-> s9
    s5 -. "isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)" .-> s10
    s5 -->|"_default_path_error(value)"| s11
    s5 -->|"_syntax_key('portable', raw, normalize_backslashes, normalize_posix_spelling, required_suffix, defer_non_nfc_error, reject_delete_character)"| s12
    click s1 "../modules/protected_artifacts.md"
    click s5 "../modules/validation.md"
    click s7 "../modules/validation.md"
    click s8 "../modules/validation.md"
    click s11 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_portable_relative_path` | `relative: str \| Path`, `normalize_backslashes: bool` | - | - | `require_portable_relative_path(...)` |
| `os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)` | - | - | - | - |
| `raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)` | - | - | - | - |
| `require_portable_relative_path` | `value: object`, `normalize_backslashes: bool`, `normalize_posix_spelling: bool`, `required_suffix: str \| None`, `defer_non_nfc_error: bool`, `reject_delete_character: bool`, `text_error: Exception \| None`, `relative_error: Exception \| None` | `os` | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `SharedValidationError` | - | - | - | - |
| `os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | - | - | - | - |
| `_default_path_error` | `value: object` | - | - | `SharedValidationError(...)` |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_portable_relative_path | os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path) | 106 | `os.fspath(relative)` |
| validate_portable_relative_path | isinstance (src/llm_wiki_cli/services…ate_portable_relative_path) | 107 | `isinstance(raw, str)` |
| validate_portable_relative_path | raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path) | 107 | `raw.replace('\\', '/')` |
| validate_portable_relative_path | require_portable_relative_path | 108 | `require_portable_relative_path(raw, normalize_backslashes=normalize_backslashes, text_error=ProtectedArtifactIntegrityError(...), relative_error=ProtectedArtifactIntegrityError(...), non_nfc_error=ProtectedArtifactIntegrityError(...), nonportable_error=ProtectedArtifactIntegrityError(...), reserved_error=ProtectedArtifactIntegrityError(...))` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 216 | `isinstance(value, (...))` |
| require_portable_relative_path | _default_path_error | 217 | `_default_path_error(value)` |
| _default_path_error | SharedValidationError | 113 | `SharedValidationError(...)` |
| require_portable_relative_path | os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path) | 218 | `os.fspath(value)` |
| require_portable_relative_path | isinstance (src/llm_wiki_cli/services…ire_portable_relative_path) | 219 | `isinstance(raw, str)` |
| require_portable_relative_path | _default_path_error | 220 | `_default_path_error(value)` |
| require_portable_relative_path | _syntax_key | 221 | `_syntax_key('portable', raw, normalize_backslashes, normalize_posix_spelling, required_suffix, defer_non_nfc_error, reject_delete_character)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_portable_relative_path` | `os.fspath` | 106 |
| external_call | `validate_portable_relative_path` | `isinstance` | 107 |
| unresolved_call | `validate_portable_relative_path` | `raw.replace` | 107 |
| external_call | `require_portable_relative_path` | `isinstance` | 216 |
| external_call | `require_portable_relative_path` | `os.fspath` | 218 |
| external_call | `require_portable_relative_path` | `isinstance` | 219 |
| step_limit | `validate_portable_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `validate_portable_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
