# hash_markdown_snapshot

**Entry point:** `hash_markdown_snapshot` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_markdown_snapshot
    participant p1 as isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)
    participant p2 as KnowledgeEnvelopeError
    participant p3 as set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)
    participant p4 as pages.items
    participant p5 as _repository_relative_path
    participant p6 as canonical_path.endswith
    participant p7 as seen.add
    participant p8 as _normalized_markdown_bytes
    participant p9 as records.append
    participant p10 as sha256_bytes
    participant p11 as records.sort
    participant p12 as _hash_structured
    participant p13 as require_repository_relative_path
    participant p14 as isinstance (src/llm_wiki_cli/services…normalized_markdown_bytes)
    participant p15 as hashlib.sha256(…).hexdigest
    participant p16 as payload.values
    participant p17 as value.decode
    participant p18 as hashlib.sha256
    participant p19 as _validate_json_tree
    participant p20 as canonical_json_bytes
    p0-->>p1: isinstance (src/llm_wiki_cli/services…py:hash_markdown_snapshot)(pages, Mapping)
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: set (src/llm_wiki_cli/services…py:hash_markdown_snapshot)
    p0-->>p4: pages.items
    p0->>p5: _repository_relative_path
    p0-->>p6: canonical_path.endswith('.md')
    p0->>p2: KnowledgeEnvelopeError
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p7: seen.add(canonical_path)
    p0->>p8: _normalized_markdown_bytes
    p0-->>p9: records.append({...})
    p0->>p10: sha256_bytes
    p0-->>p11: records.sort(key=...)
    p0->>p12: _hash_structured
    p5->>p13: require_repository_relative_path
    p8-->>p14: isinstance (src/llm_wiki_cli/services…normalized_markdown_bytes)(value, bytes)
    p10-->>p15: hashlib.sha256(…).hexdigest
    p12-->>p16: payload.values
    p5->>p2: KnowledgeEnvelopeError
    p8-->>p17: value.decode('utf-8')
    p10-->>p18: hashlib.sha256(value)
    p12->>p19: _validate_json_tree
    p5->>p2: KnowledgeEnvelopeError
    p8->>p2: KnowledgeEnvelopeError
    p12->>p10: sha256_bytes
    p5->>p2: KnowledgeEnvelopeError
    p8-->>p14: isinstance (src/llm_wiki_cli/services…normalized_markdown_bytes)(value, str)
    p12->>p20: canonical_json_bytes
    p8->>p2: KnowledgeEnvelopeError
    p12->>p2: KnowledgeEnvelopeError
```

> Call sequence diagram shows 30 of 113 interactions; 83 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 31 (26 omitted); unresolved 8 of 38 (30 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 7 | - | external | 7 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 7 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 4 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 9 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 16 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 7 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 30 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 30 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 13 |
| `src/llm_wiki_cli/services/validation.py:_default_path_error` | 32 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 25 groups; 17 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
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
