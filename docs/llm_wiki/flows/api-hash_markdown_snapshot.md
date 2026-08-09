# hash_markdown_snapshot

**Entry point:** `hash_markdown_snapshot` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_markdown_snapshot
    participant p1 as isinstance
    participant p2 as KnowledgeEnvelopeError
    participant p3 as set
    participant p4 as items
    participant p5 as _repository_relative_path
    participant p6 as require_repository_relative_path
    participant p7 as strip
    participant p8 as any
    participant p9 as ord
    participant p10 as startswith
    participant p11 as match
    participant p12 as split
    participant p13 as PurePosixPath
    participant p14 as normpath
    participant p15 as require_portable_relative_path
    participant p16 as _default_path_error
    participant p17 as SharedValidationError
    participant p18 as fspath
    participant p19 as encode
    participant p20 as replace
    p0-->>p1: isinstance
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: set
    p0-->>p4: items
    p0->>p5: _repository_relative_path
    p5->>p6: require_repository_relative_path
    p6-->>p1: isinstance
    p6-->>p7: strip
    p6-->>p8: any
    p6-->>p9: ord
    p6-->>p9: ord
    p6-->>p10: startswith
    p6-->>p10: startswith
    p6-->>p11: match
    p6-->>p12: split
    p6-->>p13: PurePosixPath
    p6-->>p8: any
    p6-->>p14: normpath
    p6->>p15: require_portable_relative_path
    p15-->>p1: isinstance
    p15->>p16: _default_path_error
    p16->>p17: SharedValidationError
    p15-->>p18: fspath
    p15-->>p1: isinstance
    p15->>p16: _default_path_error
    p15-->>p19: encode
    p15->>p16: _default_path_error
    p15->>p16: _default_path_error
    p15-->>p20: replace
    p15-->>p13: PurePosixPath
```

> Call sequence diagram shows 30 of 94 interactions; 64 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_markdown_snapshot"]
    s2["2. isinstance"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. set"]
    s5["5. items"]
    s6["6. _repository_relative_path"]
    s7["7. require_repository_relative_path"]
    s8["8. isinstance"]
    s9["9. strip"]
    s10["10. any"]
    s11["11. ord"]
    s12["12. ord"]
    s1 -. "isinstance(pages, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('markdown_pages', 'must be an object')"| s3
    s1 -. "set(data not statically known)" .-> s4
    s1 -. "pages.items(data not statically known)" .-> s5
    s1 -->|"_repository_relative_path(path, 'markdown_pages.path')"| s6
    s6 -->|"require_repository_relative_path(value, text_error=KnowledgeEnvelopeError(...), posix_error=KnowledgeEnvelopeError(...), normalized_error=KnowledgeEnvelopeErro…"| s7
    s7 -. "isinstance(value, str)" .-> s8
    s7 -. "value.strip(data not statically known)" .-> s9
    s7 -. "any(...)" .-> s10
    s7 -. "ord(character)" .-> s11
    s7 -. "ord(character)" .-> s12
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
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_markdown_snapshot` | `pages: Mapping[str, str \| bytes]` | `Mapping`, `MARKDOWN_SNAPSHOT_DOMAIN` | - | `_hash_structured(...)` |
| `isinstance` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `set` | - | - | - | - |
| `items` | - | - | - | - |
| `_repository_relative_path` | `value: object`, `field_name: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `require_portable_relative_path(...)` |
| `isinstance` | - | - | - | - |
| `strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |
| `ord` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_markdown_snapshot | isinstance | 775 | `isinstance(pages, Mapping)` |
| hash_markdown_snapshot | KnowledgeEnvelopeError | 776 | `KnowledgeEnvelopeError('markdown_pages', 'must be an object')` |
| hash_markdown_snapshot | set | 778 | `set(data not statically known)` |
| hash_markdown_snapshot | items | 779 | `pages.items(data not statically known)` |
| hash_markdown_snapshot | _repository_relative_path | 780 | `_repository_relative_path(path, 'markdown_pages.path')` |
| _repository_relative_path | require_repository_relative_path | 1381 | `require_repository_relative_path(value, text_error=KnowledgeEnvelopeError(...), posix_error=KnowledgeEnvelopeError(...), normalized_error=KnowledgeEnvelopeError(...))` |
| require_repository_relative_path | isinstance | 256 | `isinstance(value, str)` |
| require_repository_relative_path | strip | 258 | `value.strip(data not statically known)` |
| require_repository_relative_path | any | 260 | `any(...)` |
| require_repository_relative_path | ord | 261 | `ord(character)` |
| require_repository_relative_path | ord | 262 | `ord(character)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `seen.add` | `hash_markdown_snapshot` | 791 |
| mutation | `records.append` | `hash_markdown_snapshot` | 796 |
| mutation | `records.sort` | `hash_markdown_snapshot` | 802 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `hash_markdown_snapshot` | `isinstance` | 775 |
| unresolved_call | `hash_markdown_snapshot` | `pages.items` | 779 |
| unresolved_call | `require_repository_relative_path` | `isinstance` | 256 |
| unresolved_call | `require_repository_relative_path` | `value.strip` | 258 |
| unresolved_call | `require_repository_relative_path` | `any` | 260 |
| unresolved_call | `require_repository_relative_path` | `ord` | 261 |
| unresolved_call | `require_repository_relative_path` | `ord` | 262 |
| step_limit | `hash_markdown_snapshot` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_markdown_snapshot` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
