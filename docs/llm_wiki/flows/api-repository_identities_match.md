# repository_identities_match

**Entry point:** `repository_identities_match` (`api`)
**Source:** [knowledge_model](../modules/knowledge_model.md)
**Modules touched:** [knowledge_model](../modules/knowledge_model.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as repository_identities_match
    participant p1 as isinstance (src/llm_wiki_cli/services…epository_identities_match)
    participant p2 as TypeError
    participant p3 as _repository_identity
    participant p4 as _nonempty_string
    participant p5 as _REPOSITORY_IDENTITY_RE.fullmatch
    participant p6 as KnowledgeModelError
    participant p7 as text.lower().endswith
    participant p8 as text.lower
    participant p9 as _string
    participant p10 as require_nonempty_text
    participant p11 as require_string
    participant p12 as isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)
    participant p13 as value.strip
    participant p14 as contains_control_character
    participant p15 as isinstance (src/llm_wiki_cli/services…lidation.py:require_string)
    participant p16 as pattern.search
    participant p17 as value.encode
    p0-->>p1: isinstance (src/llm_wiki_cli/services…epository_identities_match)(left, RepositoryRecord)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…epository_identities_match)(right, RepositoryRecord)
    p0-->>p2: TypeError('left and right must be RepositoryRecord values')
    p0->>p3: _repository_identity
    p0->>p3: _repository_identity
    p3->>p4: _nonempty_string
    p3-->>p5: _REPOSITORY_IDENTITY_RE.fullmatch(text)
    p3->>p6: KnowledgeModelError
    p3-->>p7: text.lower().endswith('.git')
    p3-->>p8: text.lower
    p3->>p6: KnowledgeModelError
    p4->>p9: _string
    p4->>p10: require_nonempty_text
    p4->>p6: KnowledgeModelError
    p9->>p11: require_string
    p10-->>p12: isinstance (src/llm_wiki_cli/services…n.py:require_nonempty_text)(value, str)
    p9->>p6: KnowledgeModelError
    p10-->>p13: value.strip
    p9->>p6: KnowledgeModelError
    p10->>p14: contains_control_character
    p11-->>p15: isinstance (src/llm_wiki_cli/services…lidation.py:require_string)(value, str)
    p14-->>p16: pattern.search(value)
    p11-->>p17: value.encode('utf-8')
```

> Call sequence diagram shows 23 of 23 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 6 of 6 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| _repository_identity | _nonempty_string | 1823 | `_nonempty_string(value, path)` |
| _nonempty_string | _string | 1730 | `_string(value, path)` |
| _string | require_string | 1719 | `require_string(value, error=KnowledgeModelError(...), utf8_error=KnowledgeModelError(...))` |
| require_string | isinstance (src/llm_wiki_cli/services…lidation.py:require_string) | 744 | `isinstance(value, str)` |
| require_string | value.encode | 748 | `value.encode('utf-8')` |
| _string | KnowledgeModelError | 1721 | `KnowledgeModelError(path, 'must be a string')` |
| _string | KnowledgeModelError | 1722 | `KnowledgeModelError(path, 'must contain only Unicode scalar values encodable as UTF-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `repository_identities_match` | `isinstance` | 503 |
| external_call | `repository_identities_match` | `TypeError` | 506 |
| external_call | `require_string` | `isinstance` | 744 |
| unresolved_call | `require_string` | `value.encode` | 748 |
| step_limit | `repository_identities_match` | `first 12 steps` | 0 |

## Behavior

This flow starts at `repository_identities_match` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
