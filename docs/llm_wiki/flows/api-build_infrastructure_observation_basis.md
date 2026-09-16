# build_infrastructure_observation_basis

**Entry point:** `build_infrastructure_observation_basis` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_infrastructure_observation_basis
    participant p1 as _validate_source_path
    participant p2 as require_repository_relative_path
    participant p3 as isinstance (src/llm_wiki_cli/services…_repository_relative_path)
    participant p4 as _syntax_key
    participant p5 as type
    participant p6 as len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p7 as any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    participant p8 as _known_syntax
    participant p9 as _PATH_SYNTAX.get
    participant p10 as _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…lidation.py:_known_syntax)
    participant p11 as value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    participant p12 as any (src/llm_wiki_cli/services…_repository_relative_path)
    participant p13 as ord (src/llm_wiki_cli/services…_repository_relative_path)
    participant p14 as value.startswith
    participant p15 as _WINDOWS_DRIVE_PREFIX_RE.match
    participant p16 as value.split
    participant p17 as PurePosixPath (src/llm_wiki_cli/services…_repository_relative_path)
    participant p18 as posixpath.normpath
    participant p19 as require_portable_relative_path
    participant p20 as isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    participant p21 as _default_path_error
    participant p22 as SharedValidationError
    participant p23 as os.fspath
    p0->>p1: _validate_source_path
    p1->>p2: require_repository_relative_path
    p2-->>p3: isinstance (src/llm_wiki_cli/services…_repository_relative_path)
    p2->>p4: _syntax_key
    p4-->>p5: type
    p4-->>p6: len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p4-->>p7: any (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p4-->>p5: type
    p4-->>p5: type
    p4-->>p6: len (src/llm_wiki_cli/services/validation.py:_syntax_key)
    p2->>p8: _known_syntax
    p8-->>p9: _PATH_SYNTAX.get
    p8-->>p10: _PATH_SYNTAX.move_to_end (src/llm_wiki_cli/services…lidation.py:_known_syntax)
    p2-->>p11: value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    p2-->>p12: any (src/llm_wiki_cli/services…_repository_relative_path)
    p2-->>p13: ord (src/llm_wiki_cli/services…_repository_relative_path)
    p2-->>p13: ord (src/llm_wiki_cli/services…_repository_relative_path)
    p2-->>p14: value.startswith
    p2-->>p14: value.startswith
    p2-->>p15: _WINDOWS_DRIVE_PREFIX_RE.match
    p2-->>p16: value.split
    p2-->>p17: PurePosixPath (src/llm_wiki_cli/services…_repository_relative_path)
    p2-->>p12: any (src/llm_wiki_cli/services…_repository_relative_path)
    p2-->>p18: posixpath.normpath
    p2->>p19: require_portable_relative_path
    p19-->>p20: isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
    p19->>p21: _default_path_error
    p21->>p22: SharedValidationError
    p19-->>p23: os.fspath
    p19-->>p20: isinstance (src/llm_wiki_cli/services…re_portable_relative_path)
```

> Call sequence diagram shows 30 of 99 interactions; 69 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_infrastructure_observation_basis"]
    s2["2. _validate_source_path"]
    s3["3. require_repository_relative_path"]
    s4["4. isinstance (src/llm_wiki_cli/services…_repository_relative_path)"]
    s5["5. _syntax_key"]
    s6["6. type"]
    s7["7. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s8["8. any (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s9["9. type"]
    s10["10. type"]
    s11["11. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s12["12. _known_syntax"]
    s1 -->|"_validate_source_path(source_path)"| s2
    s2 -->|"require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…_repository_relative_path)(value, str)" .-> s4
    s3 -->|"_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)"| s5
    s5 -. "type(value)" .-> s6
    s5 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s7
    s5 -. "any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)" .-> s8
    s5 -. "type(v)" .-> s9
    s5 -. "type(v)" .-> s10
    s5 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(v)" .-> s11
    s3 -->|"_known_syntax(syntax_key)"| s12
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s3 "../modules/validation.md"
    click s5 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_infrastructure_observation_basis` | `source_path: str`, `source_content_hash: str`, `observation_hash: str`, `extractor_ref: str` | `INFRASTRUCTURE_OBSERVATION_SCOPE` | - | `ConceptObservationBasis(...)` |
| `_validate_source_path` | `source_path: object` | - | - | - |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |
| `type` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `type` | - | - | - | - |
| `type` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `_known_syntax` | `key` | `_PATH_SYNTAX_LOCK` | - | `None`, `value` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_infrastructure_observation_basis | _validate_source_path | 410 | `_validate_source_path(source_path)` |
| _validate_source_path | require_repository_relative_path | 873 | `require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…_repository_relative_path) | 299 | `isinstance(value, str)` |
| require_repository_relative_path | _syntax_key | 301 | `_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)` |
| _syntax_key | type | 54 | `type(value)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 54 | `len(value)` |
| _syntax_key | any (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `any(...)` |
| _syntax_key | type | 55 | `type(v)` |
| _syntax_key | type | 55 | `type(v)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `len(v)` |
| require_repository_relative_path | _known_syntax | 303 | `_known_syntax(syntax_key)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_repository_relative_path` | `isinstance` | 299 |
| external_call | `_syntax_key` | `type` | 54 |
| external_call | `_syntax_key` | `any` | 55 |
| external_call | `_syntax_key` | `type` | 55 |
| step_limit | `build_infrastructure_observation_basis` | `first 12 steps` | 0 |

## Behavior

This flow starts at `build_infrastructure_observation_basis` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
