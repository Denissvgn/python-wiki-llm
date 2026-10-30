# validate_portable_relative_path

**Entry point:** `validate_portable_relative_path` (`api`)
**Source:** [protected_artifacts](../modules/protected_artifacts.md)
**Modules touched:** [protected_artifacts](../modules/protected_artifacts.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_portable_relative_path
    participant p1 as require_portable_relative_path
    participant p2 as ProtectedArtifactIntegrityError
    participant p3 as _default_path_error
    participant p4 as _check_path_collision
    participant p5 as require_portable_path_component
    participant p6 as _syntax_key
    participant p7 as _known_syntax
    participant p8 as _remember_syntax
    participant p9 as SharedValidationError
    participant p10 as portable_path_key
    participant p11 as os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)
    participant p12 as raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)
    participant p13 as isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)
    participant p14 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p15 as os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p16 as raw.encode
    participant p17 as raw.replace (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p18 as PurePosixPath
    participant p19 as path.is_absolute
    participant p20 as _WINDOWS_ABSOLUTE_RE.match
    participant p21 as path.as_posix
    participant p22 as normalized.strip
    participant p23 as canonical.casefold().endswith
    participant p24 as canonical.casefold
    participant p25 as required_suffix.casefold
    participant p26 as type
    participant p27 as _PATH_SYNTAX.get
    participant p28 as component.encode
    participant p29 as _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…dation.py:_remember_syntax)
    p0->>p1: require_portable_relative_path
    p0->>p2: ProtectedArtifactIntegrityError
    p1->>p3: _default_path_error
    p1->>p4: _check_path_collision
    p1->>p5: require_portable_path_component
    p1->>p6: _syntax_key
    p1->>p7: _known_syntax
    p1->>p8: _remember_syntax
    p3->>p9: SharedValidationError
    p4->>p10: portable_path_key
    p0-->>p11: os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)(relative)
    p0-->>p12: raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)('\\', '/')
    p0-->>p13: isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)(raw, str)
    p1-->>p14: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))
    p1-->>p15: os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)(value)
    p1-->>p14: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)
    p1-->>p16: raw.encode('utf-8')
    p1-->>p17: raw.replace (src/llm_wiki_cli/services…ire_portable_relative_path)('\\', '/')
    p1-->>p18: PurePosixPath(normalized)
    p1-->>p19: path.is_absolute
    p1-->>p20: _WINDOWS_ABSOLUTE_RE.match(raw)
    p1-->>p21: path.as_posix
    p1-->>p22: normalized.strip
    p1-->>p23: canonical.casefold().endswith(required_suffix.casefold(...))
    p1-->>p24: canonical.casefold
    p1-->>p25: required_suffix.casefold
    p6-->>p26: type(value)
    p7-->>p27: _PATH_SYNTAX.get(key)
    p5-->>p28: component.encode('utf-8')
    p8-->>p29: _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…dation.py:_remember_syntax)(key)
```

> Call sequence diagram shows 30 of 67 interactions; 37 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 19 (12 omitted); unresolved 13 of 21 (8 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 5 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 7 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 12 | - | external | 5 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 19 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 23 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 23 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 22 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 22 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_portable_path_component` | 44 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 5 |
> Omission summary shows 8 of 13 groups; 5 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 28; effect analysis evaluated: 14, partial: 2, unavailable: 12. Counts include steps omitted from the displayed trace.

Collector observations for 16 source steps with known totals: observed: 74, emitted: 63, omitted: 11. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_portable_relative_path` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `os.fspath (src/llm_wiki_cli/services…ate_portable_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…ate_portable_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `raw.replace (src/llm_wiki_cli/services…ate_portable_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `require_portable_relative_path` | `available` | `partial` | `available` | `21` | `11` | `10` |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_default_path_error` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `SharedValidationError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `os.fspath (src/llm_wiki_cli/services…ire_portable_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_default_path_error` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_syntax_key` | `available` | `evaluated` | `available` | `5` | `5` | `0` |

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

*No boundary-effect observations were captured in this static trace.*

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
