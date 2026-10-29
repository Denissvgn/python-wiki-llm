# hash_inventory

**Entry point:** `hash_inventory` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_inventory
    participant p1 as _repository_relative_path
    participant p2 as _hash_structured
    participant p3 as KnowledgeEnvelopeError
    participant p4 as require_repository_relative_path
    participant p5 as canonical_json_bytes
    participant p6 as require_portable_relative_path
    participant p7 as _default_path_error
    participant p8 as _check_path_collision
    participant p9 as require_portable_path_component
    participant p10 as _validate_json_tree
    participant p11 as sha256_bytes
    participant p12 as _syntax_key
    participant p13 as canonical_json_text
    participant p14 as _known_syntax
    participant p15 as _remember_syntax
    participant p16 as SharedValidationError
    participant p17 as portable_path_key
    participant p18 as isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)
    participant p19 as inventory.items
    participant p20 as payload.values
    participant p21 as isinstance (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p22 as set
    participant p23 as hashlib.sha256(…).hexdigest
    participant p24 as canonical_json_text(…).encode
    participant p25 as walk
    participant p26 as hashlib.sha256
    participant p27 as value.strip
    participant p28 as any (src/llm_wiki_cli/services…e_repository_relative_path)
    participant p29 as ord (src/llm_wiki_cli/services…e_repository_relative_path)
    p0->>p1: _repository_relative_path
    p0->>p2: _hash_structured
    p0->>p3: KnowledgeEnvelopeError
    p1->>p4: require_repository_relative_path
    p2->>p5: canonical_json_bytes
    p4->>p6: require_portable_relative_path
    p6->>p7: _default_path_error
    p6->>p8: _check_path_collision
    p6->>p9: require_portable_path_component
    p2->>p10: _validate_json_tree
    p2->>p11: sha256_bytes
    p4->>p12: _syntax_key
    p5->>p13: canonical_json_text
    p4->>p14: _known_syntax
    p4->>p15: _remember_syntax
    p7->>p16: SharedValidationError
    p8->>p17: portable_path_key
    p0-->>p18: isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)(inventory, Mapping)
    p0-->>p19: inventory.items
    p0-->>p18: isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)(source_path, str)
    p2-->>p20: payload.values
    p4-->>p21: isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)
    p10-->>p22: set
    p11-->>p23: hashlib.sha256(…).hexdigest
    p5-->>p24: canonical_json_text(…).encode('utf-8')
    p10-->>p25: walk(value, field_name)
    p11-->>p26: hashlib.sha256(value)
    p4-->>p27: value.strip
    p4-->>p28: any (src/llm_wiki_cli/services…e_repository_relative_path)(...)
    p4-->>p29: ord (src/llm_wiki_cli/services…e_repository_relative_path)(character)
```

> Call sequence diagram shows 30 of 97 interactions; 67 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 29 (22 omitted); unresolved 6 of 30 (24 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_envelope.py:hash_inventory` | 1 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:_syntax_key` | 10 | - | external | 6 |
| `src/llm_wiki_cli/services/validation.py:_known_syntax` | 17 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 8 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 8 | - | unresolved | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 31 | - | external | 4 |
| `src/llm_wiki_cli/services/validation.py:require_portable_relative_path` | 31 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 10 |
| `src/llm_wiki_cli/services/validation.py:portable_path_key` | 41 | - | unresolved | 1 |
> Omission summary shows 8 of 20 groups; 12 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 39; effect analysis evaluated: 26, partial: 0, unavailable: 13. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `hash_inventory` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` |
| `inventory.items` | `not_applicable` | `not_applicable` | `not_applicable` |
| `isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` |
| `_repository_relative_path` | `available` | `evaluated` | `available` |
| `require_repository_relative_path` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…e_repository_relative_path)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_syntax_key` | `available` | `evaluated` | `available` |
| `type` | `not_applicable` | `not_applicable` | `not_applicable` |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. hash_inventory"]
    s2["2. isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. inventory.items"]
    s5["5. isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)"]
    s6["6. KnowledgeEnvelopeError"]
    s7["7. _repository_relative_path"]
    s8["8. require_repository_relative_path"]
    s9["9. isinstance (src/llm_wiki_cli/services…e_repository_relative_path)"]
    s10["10. _syntax_key"]
    s11["11. type"]
    s12["12. len (src/llm_wiki_cli/services/validation.py:_syntax_key)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)(inventory, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('inventory', 'must be an object')"| s3
    s1 -. "inventory.items(data not statically known)" .-> s4
    s1 -. "isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)(source_path, str)" .-> s5
    s1 -->|"KnowledgeEnvelopeError('inventory', 'must use string source keys')"| s6
    s1 -->|"_repository_relative_path(source_path, 'inventory.source_path')"| s7
    s7 -->|"require_repository_relative_path(…)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…e_repository_relative_path)(value, str)" .-> s9
    s8 -->|"_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)"| s10
    s10 -. "type(value)" .-> s11
    s10 -. "len (src/llm_wiki_cli/services/validation.py:_syntax_key)(value)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s7 "../modules/knowledge_envelope.md"
    click s8 "../modules/validation.md"
    click s10 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_inventory` | `inventory: Mapping[str, Any]` | `Mapping`, `INVENTORY_SNAPSHOT_DOMAIN` | - | `_hash_structured(...)` |
| `isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `inventory.items` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_repository_relative_path` | `value: object`, `field_name: str` | - | - | `require_repository_relative_path(...)` |
| `require_repository_relative_path` | `value: object`, `text_error: Exception`, `posix_error: Exception`, `normalized_error: Exception`, `absolute_error: Exception \| None`, `separator_error: Exception \| None`, `control_error: Exception \| None`, `reject_delete_character: bool` | - | - | `cached`, `_remember_syntax(...)` |
| `isinstance (src/llm_wiki_cli/services…e_repository_relative_path)` | - | - | - | - |
| `_syntax_key` | `kind`, `value`, `options` | - | - | `None`, `(...)` |
| `type` | - | - | - | - |
| `len (src/llm_wiki_cli/services/validation.py:_syntax_key)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_inventory | isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory) | 765 | `isinstance(inventory, Mapping)` |
| hash_inventory | KnowledgeEnvelopeError | 766 | `KnowledgeEnvelopeError('inventory', 'must be an object')` |
| hash_inventory | inventory.items | 768 | `inventory.items(data not statically known)` |
| hash_inventory | isinstance (src/llm_wiki_cli/services…envelope.py:hash_inventory) | 769 | `isinstance(source_path, str)` |
| hash_inventory | KnowledgeEnvelopeError | 770 | `KnowledgeEnvelopeError('inventory', 'must use string source keys')` |
| hash_inventory | _repository_relative_path | 771 | `_repository_relative_path(source_path, 'inventory.source_path')` |
| _repository_relative_path | require_repository_relative_path | 1505 | `require_repository_relative_path(value, text_error=KnowledgeEnvelopeError(...), posix_error=KnowledgeEnvelopeError(...), normalized_error=KnowledgeEnvelopeError(...))` |
| require_repository_relative_path | isinstance (src/llm_wiki_cli/services…e_repository_relative_path) | 299 | `isinstance(value, str)` |
| require_repository_relative_path | _syntax_key | 301 | `_syntax_key('repository', value, reject_delete_character, control_after_normalization, leading_backslash_is_absolute, normalize_posix_spelling)` |
| _syntax_key | type | 54 | `type(value)` |
| _syntax_key | len (src/llm_wiki_cli/services/validation.py:_syntax_key) | 54 | `len(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_inventory` | `isinstance` | 765 |
| unresolved_call | `hash_inventory` | `inventory.items` | 768 |
| external_call | `hash_inventory` | `isinstance` | 769 |
| external_call | `require_repository_relative_path` | `isinstance` | 299 |
| external_call | `_syntax_key` | `type` | 54 |
| step_limit | `hash_inventory` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_inventory` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
