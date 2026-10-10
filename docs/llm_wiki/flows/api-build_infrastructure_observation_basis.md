# build_infrastructure_observation_basis

**Entry point:** `build_infrastructure_observation_basis` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_infrastructure_observation_basis
    participant p1 as _validate_source_path
    participant p2 as _validate_hash
    participant p3 as _validate_extractor_ref
    participant p4 as ConceptObservationBasis
    participant p5 as require_repository_relative_path
    participant p6 as require_sha256
    participant p7 as require_string
    participant p8 as ValueError (src/llm_wiki_cli/services….py:_validate_source_path)
    participant p9 as ValueError (src/llm_wiki_cli/services…vidence.py:_validate_hash)
    participant p10 as ValueError (src/llm_wiki_cli/services…y:_validate_extractor_ref)
    participant p11 as _COMPONENT_ID_RE.fullmatch
    participant p12 as isinstance (src/llm_wiki_cli/services…_repository_relative_path)
    participant p13 as isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)
    participant p14 as isinstance (src/llm_wiki_cli/services…idation.py:require_string)
    participant p15 as _syntax_key
    participant p16 as require_trimmed_text
    participant p17 as value.encode
    participant p18 as _known_syntax
    participant p19 as _SHA256_RE.fullmatch
    participant p20 as value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    participant p21 as any (src/llm_wiki_cli/services…_repository_relative_path)
    participant p22 as ord (src/llm_wiki_cli/services…_repository_relative_path)
    participant p23 as value.startswith
    participant p24 as _WINDOWS_DRIVE_PREFIX_RE.match
    p0->>p1: _validate_source_path
    p0->>p2: _validate_hash
    p0->>p2: _validate_hash
    p0->>p3: _validate_extractor_ref
    p0->>p4: ConceptObservationBasis
    p1->>p5: require_repository_relative_path
    p2->>p6: require_sha256
    p3->>p7: require_string
    p1-->>p8: ValueError (src/llm_wiki_cli/services….py:_validate_source_path)('source_path must be a non-empty repository-relative path')
    p2-->>p9: ValueError (src/llm_wiki_cli/services…vidence.py:_validate_hash)(...)
    p3-->>p10: ValueError (src/llm_wiki_cli/services…y:_validate_extractor_ref)('extractor_ref must be a normalized producer component ID')
    p1-->>p8: ValueError (src/llm_wiki_cli/services….py:_validate_source_path)('source_path must be a repository-relative POSIX path')
    p3-->>p11: _COMPONENT_ID_RE.fullmatch(parsed)
    p1-->>p8: ValueError (src/llm_wiki_cli/services….py:_validate_source_path)('source_path must be a normalized repository-relative path')
    p3-->>p10: ValueError (src/llm_wiki_cli/services…y:_validate_extractor_ref)('extractor_ref must be a normalized producer component ID')
    p5-->>p12: isinstance (src/llm_wiki_cli/services…_repository_relative_path)(value, str)
    p6-->>p13: isinstance (src/llm_wiki_cli/services…idation.py:require_sha256)(value, str)
    p7-->>p14: isinstance (src/llm_wiki_cli/services…idation.py:require_string)(value, str)
    p5->>p15: _syntax_key
    p6->>p16: require_trimmed_text
    p7-->>p17: value.encode('utf-8')
    p5->>p18: _known_syntax
    p6-->>p19: _SHA256_RE.fullmatch(parsed)
    p5-->>p20: value.strip (src/llm_wiki_cli/services…_repository_relative_path)
    p5-->>p21: any (src/llm_wiki_cli/services…_repository_relative_path)(...)
    p5-->>p22: ord (src/llm_wiki_cli/services…_repository_relative_path)(character)
    p5-->>p22: ord (src/llm_wiki_cli/services…_repository_relative_path)(character)
    p5-->>p23: value.startswith('/')
    p5-->>p23: value.startswith('\\')
    p5-->>p24: _WINDOWS_DRIVE_PREFIX_RE.match(value)
```

> Call sequence diagram shows 30 of 99 interactions; 69 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 12 of 33 (21 omitted); unresolved 7 of 30 (23 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 5 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 12 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 3 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 3 | - | external | 3 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 3 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 2 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 26 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 26 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 13 |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 28 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 23 groups; 15 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| build_infrastructure_observation_basis | _validate_source_path | 411 | `_validate_source_path(source_path)` |
| _validate_source_path | require_repository_relative_path | 874 | `require_repository_relative_path(source_path, text_error=ValueError(...), posix_error=ValueError(...), normalized_error=ValueError(...))` |
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
