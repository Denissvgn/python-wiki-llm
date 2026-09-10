# hash_markdown_snapshot

**Entry point:** `hash_markdown_snapshot` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_markdown_snapshot
    participant p1 as isinstance (src/llm_wiki_cli/services….py:hash_markdown_snapshot)
    participant p2 as KnowledgeEnvelopeError
    participant p3 as set (src/llm_wiki_cli/services….py:hash_markdown_snapshot)
    participant p4 as pages.items
    participant p5 as _repository_relative_path
    participant p6 as require_repository_relative_path
    participant p7 as isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p8 as value.strip
    participant p9 as any (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p10 as ord (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p11 as value.startswith
    participant p12 as _WINDOWS_DRIVE_PREFIX_RE.match
    participant p13 as value.split
    participant p14 as PurePosixPath (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p15 as posixpath.normpath
    participant p16 as require_portable_relative_path
    participant p17 as isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    participant p18 as _default_path_error
    participant p19 as SharedValidationError
    participant p20 as os.fspath
    participant p21 as raw.encode
    participant p22 as raw.replace
    participant p23 as PurePosixPath (src/llm_wiki_cli/services…ire_portable_relative_path)
    p0-->>p1: isinstance (src/llm_wiki_cli/services….py:hash_markdown_snapshot)
    p0->>p2: KnowledgeEnvelopeError
    p0-->>p3: set (src/llm_wiki_cli/services….py:hash_markdown_snapshot)
    p0-->>p4: pages.items
    p0->>p5: _repository_relative_path
    p5->>p6: require_repository_relative_path
    p6-->>p7: isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    p6-->>p8: value.strip
    p6-->>p9: any (src/llm_wiki_cli/services…e_repository_relative_path)
    p6-->>p10: ord (src/llm_wiki_cli/services…e_repository_relative_path)
    p6-->>p10: ord (src/llm_wiki_cli/services…e_repository_relative_path)
    p6-->>p11: value.startswith
    p6-->>p11: value.startswith
    p6-->>p12: _WINDOWS_DRIVE_PREFIX_RE.match
    p6-->>p13: value.split
    p6-->>p14: PurePosixPath (src/llm_wiki_cli/services…e_repository_relative_path)
    p6-->>p9: any (src/llm_wiki_cli/services…e_repository_relative_path)
    p6-->>p15: posixpath.normpath
    p6->>p16: require_portable_relative_path
    p16-->>p17: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    p16->>p18: _default_path_error
    p18->>p19: SharedValidationError
    p16-->>p20: os.fspath
    p16-->>p17: isinstance (src/llm_wiki_cli/services…ire_portable_relative_path)
    p16->>p18: _default_path_error
    p16-->>p21: raw.encode
    p16->>p18: _default_path_error
    p16->>p18: _default_path_error
    p16-->>p22: raw.replace
    p16-->>p23: PurePosixPath (src/llm_wiki_cli/services…ire_portable_relative_path)
```

> Call sequence diagram shows 30 of 94 interactions; 64 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_markdown_snapshot"]
    s2["2. isinstance (src/llm_wiki_cli/services….py:hash_markdown_snapshot)"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. set (src/llm_wiki_cli/services….py:hash_markdown_snapshot)"]
    s5["5. pages.items"]
    s6["6. _repository_relative_path"]
    s7["7. require_repository_relative_path"]
    s8["8. isinstance (src/llm_wiki_cli/services…e_repository_relative_path)"]
    s9["9. value.strip"]
    s10["10. any (src/llm_wiki_cli/services…e_repository_relative_path)"]
    s11["11. ord (src/llm_wiki_cli/services…e_repository_relative_path)"]
    s12["12. ord (src/llm_wiki_cli/services…e_repository_relative_path)"]
    s1 -. "isinstance (src/llm_wiki_cli/services….py:hash_markdown_snapshot)(pages, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('markdown_pages', 'must be an object')"| s3
    s1 -. "set (src/llm_wiki_cli/services….py:hash_markdown_snapshot)(data not statically known)" .-> s4
    s1 -. "pages.items(data not statically known)" .-> s5
    s1 -->|"_repository_relative_path(path, 'markdown_pages.path')"| s6
    s6 -->|"require_repository_relative_path(…)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)" .-> s8
    s7 -. "value.strip(data not statically known)" .-> s9
    s7 -. "any (src/llm_wiki_cli/services…e_repository_relative_path)(...)" .-> s10
    s7 -. "ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)" .-> s11
    s7 -. "ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services….py:hash_markdown_snapshot)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `set (src/llm_wiki_cli/services….py:hash_markdown_snapshot)` | - | - | - | - |
| `pages.items` | - | - | - | - |
| `_repository_relative_path` | `value: object`, `field_name: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `require_portable_relative_path(...)` |
| `isinstance (src/llm_wiki_cli/services…e_repository_relative_path)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `any (src/llm_wiki_cli/services…e_repository_relative_path)` | - | - | - | - |
| `ord (src/llm_wiki_cli/services…e_repository_relative_path)` | - | - | - | - |
| `ord (src/llm_wiki_cli/services…e_repository_relative_path)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_markdown_snapshot | isinstance (src/llm_wiki_cli/services….py:hash_markdown_snapshot) | 784 | `isinstance(pages, Mapping)` |
| hash_markdown_snapshot | KnowledgeEnvelopeError | 785 | `KnowledgeEnvelopeError('markdown_pages', 'must be an object')` |
| hash_markdown_snapshot | set (src/llm_wiki_cli/services….py:hash_markdown_snapshot) | 787 | `set(data not statically known)` |
| hash_markdown_snapshot | pages.items | 788 | `pages.items(data not statically known)` |
| hash_markdown_snapshot | _repository_relative_path | 789 | `_repository_relative_path(path, 'markdown_pages.path')` |
| _repository_relative_path | require_repository_relative_path | 1501 | `require_repository_relative_path(value, text_error=KnowledgeEnvelopeError(...), posix_error=KnowledgeEnvelopeError(...), normalized_error=KnowledgeEnvelopeError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…e_repository_relative_path) | 256 | `isinstance(value, str)` |
| require_repository_relative_path | value.strip | 258 | `value.strip(data not statically known)` |
| require_repository_relative_path | any (src/llm_wiki_cli/services…e_repository_relative_path) | 260 | `any(...)` |
| require_repository_relative_path | ord (src/llm_wiki_cli/services…e_repository_relative_path) | 261 | `ord(character)` |
| require_repository_relative_path | ord (src/llm_wiki_cli/services…e_repository_relative_path) | 262 | `ord(character)` |

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
| external_call | `require_repository_relative_path` | `isinstance` | 256 |
| unresolved_call | `require_repository_relative_path` | `value.strip` | 258 |
| external_call | `require_repository_relative_path` | `any` | 260 |
| external_call | `require_repository_relative_path` | `ord` | 261 |
| external_call | `require_repository_relative_path` | `ord` | 262 |
| step_limit | `hash_markdown_snapshot` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_markdown_snapshot` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
