# require_repository_relative_path

**Entry point:** `require_repository_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_repository_relative_path
    participant p1 as require_portable_relative_path
    participant p2 as _syntax_key
    participant p3 as _known_syntax
    participant p4 as _remember_syntax
    participant p5 as _default_path_error
    participant p6 as _check_path_collision
    participant p7 as require_portable_path_component
    participant p8 as SharedValidationError
    participant p9 as portable_path_key
    participant p10 as isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p11 as value.strip
    participant p12 as any (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p13 as ord (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p14 as value.startswith
    participant p15 as _WINDOWS_DRIVE_PREFIX_RE.match
    participant p16 as value.split
    participant p17 as PurePosixPath (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p18 as posixpath.normpath
    participant p19 as type
    participant p20 as _PATH_SYNTAX.get
    participant p21 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p22 as len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p23 as _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)
    participant p24 as any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p25 as os.fspath
    p0->>p1: require_portable_relative_path
    p0->>p2: _syntax_key
    p0->>p3: _known_syntax
    p0->>p4: _remember_syntax
    p1->>p5: _default_path_error
    p1->>p6: _check_path_collision
    p1->>p7: require_portable_path_component
    p5->>p8: SharedValidationError
    p6->>p9: portable_path_key
    p0-->>p10: isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)
    p0-->>p11: value.strip
    p0-->>p12: any (src/llm_wiki_cli/services…e_repository_relative_path)(...)
    p0-->>p13: ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)
    p0-->>p13: ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)
    p0-->>p14: value.startswith('/')
    p0-->>p14: value.startswith('\\')
    p0-->>p15: _WINDOWS_DRIVE_PREFIX_RE.match(value)
    p0-->>p16: value.split('/')
    p0-->>p17: PurePosixPath (src/llm_wiki_cli/services…e_repository_relative_path)(value)
    p0-->>p12: any (src/llm_wiki_cli/services…e_repository_relative_path)(...)
    p0-->>p18: posixpath.normpath(value)
    p2-->>p19: type(value)
    p3-->>p20: _PATH_SYNTAX.get(key)
    p1-->>p21: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))
    p2-->>p22: len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)
    p3-->>p23: _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)(key)
    p2-->>p24: any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)
    p1-->>p25: os.fspath(value)
    p2-->>p19: type(v)
    p1-->>p21: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)
```

> Call sequence diagram shows 30 of 74 interactions; 44 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 14 of 24 (10 omitted); unresolved 7 of 25 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 3 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 24 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 10 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 34 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 34 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 33 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 33 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 24 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 24 | - | external | 1 |
> Omission summary shows 8 of 13 groups; 5 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 26; effect analysis evaluated: 16, partial: 3, unavailable: 7. Counts include steps omitted from the displayed trace.

Collector observations for 19 source steps with known totals: observed: 101, emitted: 86, omitted: 15. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `require_repository_relative_path` | `available` | `partial` | `available` | `14` | `10` | `4` |
| `isinstance (src/llm_wiki_cli/services…e_repository_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_syntax_key` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `type` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `type` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_known_syntax` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `_PATH_SYNTAX.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. require_repository_relative_path"]
    s2["2. isinstance (src/llm_wiki_cli/services…e_repository_relative_path)"]
    s3["3. _syntax_key"]
    s4["4. type"]
    s5["5. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s6["6. any (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s7["7. type"]
    s8["8. type"]
    s9["9. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s10["10. _known_syntax"]
    s11["11. _PATH_SYNTAX.get"]
    s12["12. _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)" .-> s2
    s1 -->|"_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)"| s3
    s3 -. "type(value)" .-> s4
    s3 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s5
    s3 -. "any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)" .-> s6
    s3 -. "type(v)" .-> s7
    s3 -. "type(v)" .-> s8
    s3 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(v)" .-> s9
    s1 -->|"_known_syntax(syntax_key)"| s10
    s10 -. "_PATH_SYNTAX.get(key)" .-> s11
    s10 -. "_PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)(key)" .-> s12
    click s1 "../modules/validation.md"
    click s3 "../modules/validation.md"
    click s10 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…e_repository_relative_path)` | - | - | - | - |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |
| `type` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `type` | - | - | - | - |
| `type` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `_known_syntax` | `key` | `_PATH_SYNTAX_LOCK` | - | `None`, `value` |
| `_PATH_SYNTAX.get` | - | - | - | - |
| `_PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…e_repository_relative_path) | 299 | `isinstance(value, str)` |
| require_repository_relative_path | _syntax_key | 301 | `_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)` |
| _syntax_key | type | 54 | `type(value)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 54 | `len(value)` |
| _syntax_key | any (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `any(...)` |
| _syntax_key | type | 55 | `type(v)` |
| _syntax_key | type | 55 | `type(v)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `len(v)` |
| require_repository_relative_path | _known_syntax | 303 | `_known_syntax(syntax_key)` |
| _known_syntax | _PATH_SYNTAX.get | 64 | `_PATH_SYNTAX.get(key)` |
| _known_syntax | _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax) | 66 | `_PATH_SYNTAX.move_to_end(key)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_repository_relative_path` | `isinstance` | 299 |
| external_call | `_syntax_key` | `type` | 54 |
| external_call | `_syntax_key` | `any` | 55 |
| external_call | `_syntax_key` | `type` | 55 |
| unresolved_call | `_known_syntax` | `_PATH_SYNTAX.get` | 64 |
| unresolved_call | `_known_syntax` | `_PATH_SYNTAX.move_to_end` | 66 |
| step_limit | `require_repository_relative_path` | `first 12 steps` | 0 |

## Behavior

This flow starts at `require_repository_relative_path` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
