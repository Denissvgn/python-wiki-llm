# repository_identities_match

**Entry point:** `repository_identities_match` (`api`)
**Source:** [knowledge_model](../modules/knowledge_model.md)
**Modules touched:** [knowledge_model](../modules/knowledge_model.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as repository_identities_match
    participant p1 as isinstance (src/llm_wiki_cli/services…epository_identities_match)
    participant p2 as TypeError
    participant p3 as _repository_identity
    participant p4 as _nonempty_string
    participant p5 as _string
    participant p6 as require_string
    participant p7 as isinstance (src/llm_wiki_cli/services…lidation.py:require_string)
    participant p8 as value.encode
    participant p9 as KnowledgeModelError
    participant p10 as require_nonempty_text
    participant p11 as isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    participant p12 as value.strip
    participant p13 as any
    participant p14 as ord
    participant p15 as _REPOSITORY_IDENTITY_RE.fullmatch
    participant p16 as text.lower().endswith
    participant p17 as text.lower
    p0-->>p1: isinstance (src/llm_wiki_cli/services…epository_identities_match)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…epository_identities_match)
    p0-->>p2: TypeError
    p0->>p3: _repository_identity
    p3->>p4: _nonempty_string
    p4->>p5: _string
    p5->>p6: require_string
    p6-->>p7: isinstance (src/llm_wiki_cli/services…lidation.py:require_string)
    p6-->>p8: value.encode
    p5->>p9: KnowledgeModelError
    p5->>p9: KnowledgeModelError
    p4->>p10: require_nonempty_text
    p10-->>p11: isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    p10-->>p12: value.strip
    p10-->>p13: any
    p10-->>p14: ord
    p10-->>p14: ord
    p4->>p9: KnowledgeModelError
    p3-->>p15: _REPOSITORY_IDENTITY_RE.fullmatch
    p3->>p9: KnowledgeModelError
    p3-->>p16: text.lower().endswith
    p3-->>p17: text.lower
    p3->>p9: KnowledgeModelError
    p0->>p3: _repository_identity
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. repository_identities_match"]
    s2["2. isinstance (src/llm_wiki_cli/services…epository_identities_match)"]
    s3["3. isinstance (src/llm_wiki_cli/services…epository_identities_match)"]
    s4["4. TypeError"]
    s5["5. _repository_identity"]
    s6["6. _nonempty_string"]
    s7["7. _string"]
    s8["8. require_string"]
    s9["9. isinstance (src/llm_wiki_cli/services…lidation.py:require_string)"]
    s10["10. value.encode"]
    s11["11. KnowledgeModelError"]
    s12["12. KnowledgeModelError"]
    s1 -. "isinstance (src/llm_wiki_cli/services…epository_identities_match)(left, RepositoryRecord)" .-> s2
    s1 -. "isinstance (src/llm_wiki_cli/services…epository_identities_match)(right, RepositoryRecord)" .-> s3
    s1 -. "TypeError('left and right must be RepositoryRecord values')" .-> s4
    s1 -->|"_repository_identity(left.identity, 'left.identity')"| s5
    s5 -->|"_nonempty_string(value, path)"| s6
    s6 -->|"_string(value, path)"| s7
    s7 -->|"require_string(value, error=KnowledgeModelError(...), utf8_error=KnowledgeModelError(...))"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…lidation.py:require_string)(value, str)" .-> s9
    s8 -. "value.encode('utf-8')" .-> s10
    s7 -->|"KnowledgeModelError(path, 'must be a string')"| s11
    s7 -->|"KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')"| s12
    click s1 "../modules/knowledge_model.md"
    click s5 "../modules/knowledge_model.md"
    click s6 "../modules/knowledge_model.md"
    click s7 "../modules/knowledge_model.md"
    click s8 "../modules/validation.md"
    click s11 "../modules/knowledge_model.md"
    click s12 "../modules/knowledge_model.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `repository_identities_match` | `left: RepositoryRecord`, `right: RepositoryRecord` | `RepositoryRecord`, `RepositoryRecord`, `RepositoryIdentitySource`, `RepositoryIdentitySource` | - | `False`, `...` |
| `isinstance (src/llm_wiki_cli/services…epository_identities_match)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…epository_identities_match)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_repository_identity` | `value: object`, `path: str` | - | - | `text` |
| `_nonempty_string` | `value: object`, `path: str` | - | - | `require_nonempty_text(...)` |
| `_string` | `value: object`, `path: str` | - | - | `require_string(...)` |
| `require_string` | `value: object`, `error: Exception`, `utf8_error: Exception \| None` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…lidation.py:require_string)` | - | - | - | - |
| `value.encode` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |
| `KnowledgeModelError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| repository_identities_match | isinstance (src/llm_wiki_cli/services…epository_identities_match) | 503 | `isinstance(left, RepositoryRecord)` |
| repository_identities_match | isinstance (src/llm_wiki_cli/services…epository_identities_match) | 503 | `isinstance(right, RepositoryRecord)` |
| repository_identities_match | TypeError | 506 | `TypeError('left and right must be RepositoryRecord values')` |
| repository_identities_match | _repository_identity | 507 | `_repository_identity(left.identity, 'left.identity')` |
| _repository_identity | _nonempty_string | 1796 | `_nonempty_string(value, path)` |
| _nonempty_string | _string | 1703 | `_string(value, path)` |
| _string | require_string | 1692 | `require_string(value, error=KnowledgeModelError(...), utf8_error=KnowledgeModelError(...))` |
| require_string | isinstance (src/llm_wiki_cli/services…lidation.py:require_string) | 706 | `isinstance(value, str)` |
| require_string | value.encode | 710 | `value.encode('utf-8')` |
| _string | KnowledgeModelError | 1694 | `KnowledgeModelError(path, 'must be a string')` |
| _string | KnowledgeModelError | 1695 | `KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `repository_identities_match` | `isinstance` | 503 |
| external_call | `repository_identities_match` | `TypeError` | 506 |
| external_call | `require_string` | `isinstance` | 706 |
| unresolved_call | `require_string` | `value.encode` | 710 |
| step_limit | `repository_identities_match` | `first 12 steps` | 0 |

## Behavior

This flow starts at `repository_identities_match` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
