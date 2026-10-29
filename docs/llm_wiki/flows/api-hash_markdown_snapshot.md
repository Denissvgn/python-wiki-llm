# hash_markdown_snapshot

**Entry point:** `hash_markdown_snapshot` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_markdown_snapshot
    participant p1 as _repository_relative_path
    participant p2 as _normalized_markdown_bytes
    participant p3 as _hash_structured
    participant p4 as KnowledgeEnvelopeError
    participant p5 as sha256_bytes
    participant p6 as require_repository_relative_path
    participant p7 as canonical_json_bytes
    participant p8 as require_portable_relative_path
    participant p9 as _default_path_error
    participant p10 as _check_path_collision
    participant p11 as require_portable_path_component
    participant p12 as _validate_json_tree
    participant p13 as _syntax_key
    participant p14 as canonical_json_text
    participant p15 as _known_syntax
    participant p16 as _remember_syntax
    participant p17 as SharedValidationError
    participant p18 as portable_path_key
    participant p19 as isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)
    participant p20 as pages.items
    participant p21 as set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)
    participant p22 as canonical_path.endswith
    participant p23 as seen.add
    participant p24 as records.append
    participant p25 as records.sort
    participant p26 as isinstance (src/llm_wiki_cli/services…normalized_markdown_bytes)
    participant p27 as hashlib.sha256(…).hexdigest
    participant p28 as payload.values
    participant p29 as value.decode
    participant p30 as hashlib.sha256
    p0->>p1: _repository_relative_path
    p0->>p2: _normalized_markdown_bytes
    p0->>p3: _hash_structured
    p0->>p4: KnowledgeEnvelopeError
    p0->>p5: sha256_bytes
    p1->>p6: require_repository_relative_path
    p3->>p7: canonical_json_bytes
    p6->>p8: require_portable_relative_path
    p8->>p9: _default_path_error
    p8->>p10: _check_path_collision
    p8->>p11: require_portable_path_component
    p3->>p12: _validate_json_tree
    p6->>p13: _syntax_key
    p7->>p14: canonical_json_text
    p6->>p15: _known_syntax
    p6->>p16: _remember_syntax
    p9->>p17: SharedValidationError
    p10->>p18: portable_path_key
    p0-->>p19: isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)(pages, Mapping)
    p0-->>p20: pages.items
    p0-->>p21: set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)
    p0-->>p22: canonical_path.endswith('.md')
    p0-->>p23: seen.add(canonical_path)
    p0-->>p24: records.append({...})
    p0-->>p25: records.sort(key=...)
    p2-->>p26: isinstance (src/llm_wiki_cli/services…normalized_markdown_bytes)(value, bytes)
    p5-->>p27: hashlib.sha256(…).hexdigest
    p3-->>p28: payload.values
    p2-->>p29: value.decode('utf-8')
    p5-->>p30: hashlib.sha256(value)
```

> Call sequence diagram shows 30 of 113 interactions; 83 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 31 (27 omitted); unresolved 8 of 38 (30 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 7 | - | external | 7 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 9 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 16 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 7 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 30 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 30 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 10 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 40 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 40 | - | external | 1 |
> Omission summary shows 8 of 27 groups; 19 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 45; effect analysis evaluated: 25, partial: 3, unavailable: 17. Counts include steps omitted from the displayed trace.

Collector observations for 28 source steps with known totals: observed: 129, emitted: 114, omitted: 15. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `hash_markdown_snapshot` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `pages.items` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_repository_relative_path` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `require_repository_relative_path` | `available` | `partial` | `available` | `14` | `10` | `4` |
| `isinstance (src/llm_wiki_cli/services…_repository_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_syntax_key` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `type` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. hash_markdown_snapshot"]
    s2["2. isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)"]
    s5["5. pages.items"]
    s6["6. _repository_relative_path"]
    s7["7. require_repository_relative_path"]
    s8["8. isinstance (src/llm_wiki_cli/services…_repository_relative_path)"]
    s9["9. _syntax_key"]
    s10["10. type"]
    s11["11. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s12["12. any (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)(pages, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('markdown_pages', 'must be an object')"| s3
    s1 -. "set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)(data not statically known)" .-> s4
    s1 -. "pages.items(data not statically known)" .-> s5
    s1 -->|"_repository_relative_path(path, 'markdown_pages.path')"| s6
    s6 -->|"require_repository_relative_path(…)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…_repository_relative_path)(value, str)" .-> s8
    s7 -->|"_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)"| s9
    s9 -. "type(value)" .-> s10
    s9 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s11
    s9 -. "any (src/llm_wiki_cli/services/validation.py:_syntax_key)(...)" .-> s12
    b0["mutation seen.add"]
    s1 -. "mutation seen.add" .-> b0
    b1["mutation records.append"]
    s1 -. "mutation records.append" .-> b1
    b2["mutation records.sort"]
    s1 -. "mutation records.sort" .-> b2
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s7 "../modules/validation.md"
    click s9 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_markdown_snapshot` | `pages: Mapping[str, str \| bytes]` | `Mapping`, `MARKDOWN_SNAPSHOT_DOMAIN` | - | `_hash_structured(...)` |
| `isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)` | - | - | - | - |
| `pages.items` | - | - | - | - |
| `_repository_relative_path` | `value: object`, `field_name: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…_repository_relative_path)` | - | - | - | - |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |
| `type` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |
| `any (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_markdown_snapshot | isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot) | 784 | `isinstance(pages, Mapping)` |
| hash_markdown_snapshot | KnowledgeEnvelopeError | 785 | `KnowledgeEnvelopeError('markdown_pages', 'must be an object')` |
| hash_markdown_snapshot | set (src/llm_wiki_cli/services…py:hash_markdown_snapshot) | 787 | `set(data not statically known)` |
| hash_markdown_snapshot | pages.items | 788 | `pages.items(data not statically known)` |
| hash_markdown_snapshot | _repository_relative_path | 789 | `_repository_relative_path(path, 'markdown_pages.path')` |
| _repository_relative_path | require_repository_relative_path | 1505 | `require_repository_relative_path(value, text_error=KnowledgeEnvelopeError(...), posix_error=KnowledgeEnvelopeError(...), normalized_error=KnowledgeEnvelopeError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…_repository_relative_path) | 299 | `isinstance(value, str)` |
| require_repository_relative_path | _syntax_key | 301 | `_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)` |
| _syntax_key | type | 54 | `type(value)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 54 | `len(value)` |
| _syntax_key | any (src/llm_wiki_cli/services/validation.py:_syntax_key) | 55 | `any(...)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `hash_markdown_snapshot` | 800 |
| mutation | `records.append` | `hash_markdown_snapshot` | 805 |
| mutation | `records.sort` | `hash_markdown_snapshot` | 811 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_markdown_snapshot` | `isinstance` | 784 |
| unresolved_call | `hash_markdown_snapshot` | `pages.items` | 788 |
| external_call | `require_repository_relative_path` | `isinstance` | 299 |
| external_call | `_syntax_key` | `type` | 54 |
| external_call | `_syntax_key` | `any` | 55 |
| step_limit | `hash_markdown_snapshot` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_markdown_snapshot` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
