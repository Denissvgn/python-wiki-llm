# require_repository_relative_path

**Entry point:** `require_repository_relative_path` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_repository_relative_path
    participant p1 as isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p2 as _syntax_key
    participant p3 as _known_syntax
    participant p4 as value.strip
    participant p5 as any (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p6 as ord (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p7 as value.startswith
    participant p8 as _WINDOWS_DRIVE_PREFIX_RE.match
    participant p9 as value.split
    participant p10 as PurePosixPath (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p11 as posixpath.normpath
    participant p12 as require_portable_relative_path
    participant p13 as _remember_syntax
    participant p14 as type
    participant p15 as _PATH_SYNTAX.get
    participant p16 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p17 as len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p18 as _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)
    participant p19 as _default_path_error
    participant p20 as any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p21 as os.fspath
    p0-->>p1: isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)
    p0->>p2: _syntax_key
    p0->>p3: _known_syntax
    p0-->>p4: value.strip
    p0-->>p5: any (src/llm_wiki_cli/services…e_repository_relative_path)(...)
    p0-->>p6: ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)
    p0-->>p6: ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)
    p0-->>p7: value.startswith('/')
    p0-->>p7: value.startswith('\\')
    p0-->>p8: _WINDOWS_DRIVE_PREFIX_RE.match(value)
    p0-->>p9: value.split('/')
    p0-->>p10: PurePosixPath (src/llm_wiki_cli/services…e_repository_relative_path)(value)
    p0-->>p5: any (src/llm_wiki_cli/services…e_repository_relative_path)(...)
    p0-->>p11: posixpath.normpath(value)
    p0->>p12: require_portable_relative_path
    p0->>p13: _remember_syntax
    p2-->>p14: type(value)
    p3-->>p15: _PATH_SYNTAX.get(key)
    p12-->>p16: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(value, (...))
    p2-->>p17: len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)
    p3-->>p18: _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…alidation.py:_known_syntax)(key)
    p12->>p19: _default_path_error
    p2-->>p20: any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)
    p12-->>p21: os.fspath(value)
    p2-->>p14: type(v)
    p12-->>p16: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)(raw, str)
    p2-->>p14: type(v)
    p12->>p19: _default_path_error
    p2-->>p17: len (src/llm_wiki_cli/services/validation.py:_syntax_key)(v)
    p12->>p2: _syntax_key
```

> Call sequence diagram shows 30 of 74 interactions; 44 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 24 (8 omitted); unresolved 7 of 25 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 26 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 24 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 10 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 33 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 34 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 34 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_check_path_collision` | 33 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 24 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 24 | - | external | 1 |
> Omission summary shows 8 of 13 groups; 5 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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

*No boundary effects detected.*

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
