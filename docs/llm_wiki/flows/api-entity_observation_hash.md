# entity_observation_hash

**Entry point:** `entity_observation_hash` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as entity_observation_hash
    participant p1 as _validate_inventory_complete
    participant p2 as require_bool
    participant p3 as isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)
    participant p4 as TypeError
    participant p5 as normalize_entity_observation
    participant p6 as _validate_entity_coordinate
    participant p7 as require_nonempty_text
    participant p8 as isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)
    participant p9 as value.strip
    participant p10 as any
    participant p11 as ord
    participant p12 as ValueError
    participant p13 as require_positive_int
    participant p14 as require_nonnegative_int
    participant p15 as require_int
    participant p16 as isinstance (src/llm_wiki_cli/services/validation.py:require_int)
    participant p17 as _normalize_entity_observation
    participant p18 as _inventory_language
    participant p19 as isinstance (src/llm_wiki_cli/services…ce.py:_inventory_language)
    participant p20 as _InventoryNormalizationError
    participant p21 as file_data.get
    participant p22 as isinstance (src/llm_wiki_cli/services…malize_entity_observation)
    participant p23 as _record_array
    p0->>p1: _validate_inventory_complete
    p1->>p2: require_bool
    p2-->>p3: isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)
    p1-->>p4: TypeError
    p0->>p5: normalize_entity_observation
    p5->>p6: _validate_entity_coordinate
    p6->>p7: require_nonempty_text
    p7-->>p8: isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)
    p7-->>p9: value.strip
    p7-->>p10: any
    p7-->>p11: ord
    p7-->>p11: ord
    p6-->>p12: ValueError
    p6->>p13: require_positive_int
    p13->>p14: require_nonnegative_int
    p14->>p15: require_int
    p15-->>p16: isinstance (src/llm_wiki_cli/services/validation.py:require_int)
    p15-->>p16: isinstance (src/llm_wiki_cli/services/validation.py:require_int)
    p6-->>p12: ValueError
    p5->>p17: _normalize_entity_observation
    p17->>p18: _inventory_language
    p18-->>p19: isinstance (src/llm_wiki_cli/services…ce.py:_inventory_language)
    p18->>p20: _InventoryNormalizationError
    p18-->>p21: file_data.get
    p18-->>p19: isinstance (src/llm_wiki_cli/services…ce.py:_inventory_language)
    p18->>p20: _InventoryNormalizationError
    p18->>p20: _InventoryNormalizationError
    p17-->>p22: isinstance (src/llm_wiki_cli/services…malize_entity_observation)
    p17->>p23: _record_array
    p23->>p20: _InventoryNormalizationError
```

> Call sequence diagram shows 30 of 116 interactions; 86 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. entity_observation_hash"]
    s2["2. _validate_inventory_complete"]
    s3["3. require_bool"]
    s4["4. isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)"]
    s5["5. TypeError"]
    s6["6. normalize_entity_observation"]
    s7["7. _validate_entity_coordinate"]
    s8["8. require_nonempty_text"]
    s9["9. isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)"]
    s10["10. value.strip"]
    s11["11. any"]
    s12["12. ord"]
    s1 -->|"_validate_inventory_complete(inventory_complete)"| s2
    s2 -->|"require_bool(inventory_complete, error=TypeError(...))"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)(value, bool)" .-> s4
    s2 -. "TypeError('inventory_complete must be a boolean')" .-> s5
    s1 -->|"normalize_entity_observation(file_data, entity_name, occurrence)"| s6
    s6 -->|"_validate_entity_coordinate(entity_name, occurrence)"| s7
    s7 -->|"require_nonempty_text(entity_name, error=ValueError(...), reject_control_characters=False)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)(value, str)" .-> s9
    s8 -. "value.strip(data not statically known)" .-> s10
    s8 -. "any(...)" .-> s11
    s8 -. "ord(character)" .-> s12
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s3 "../modules/validation.md"
    click s6 "../modules/knowledge_evidence.md"
    click s7 "../modules/knowledge_evidence.md"
    click s8 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `entity_observation_hash` | `file_data: Mapping[str, Any]`, `entity_name: str`, `occurrence: int`, `inventory_complete: bool` | - | - | `None`, `_hash_normalized_observation(...)` |
| `_validate_inventory_complete` | `inventory_complete: object` | - | - | - |
| `require_bool` | `value: object`, `error: Exception` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `normalize_entity_observation` | `file_data: Mapping[str, Any]`, `entity_name: str`, `occurrence: int` | `_InventoryNormalizationError` | - | `_normalize_entity_observation(...)`, `None` |
| `_validate_entity_coordinate` | `entity_name: object`, `occurrence: object` | - | - | - |
| `require_nonempty_text` | `value: object`, `error: Exception`, `trim_error: Exception \| None`, `normalize: bool`, `require_trimmed: bool`, `reject_control_characters: bool`, `reject_delete_character: bool` | - | - | `parsed` |
| `isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)` | - | - | - | - |
| `value.strip` | - | - | - | - |
| `any` | - | - | - | - |
| `ord` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| entity_observation_hash | _validate_inventory_complete | 271 | `_validate_inventory_complete(inventory_complete)` |
| _validate_inventory_complete | require_bool | 852 | `require_bool(inventory_complete, error=TypeError(...))` |
| require_bool | isinstance (src/llm_wiki_cli/services…alidation.py:require_bool) | 772 | `isinstance(value, bool)` |
| _validate_inventory_complete | TypeError | 854 | `TypeError('inventory_complete must be a boolean')` |
| entity_observation_hash | normalize_entity_observation | 274 | `normalize_entity_observation(file_data, entity_name, occurrence)` |
| normalize_entity_observation | _validate_entity_coordinate | 237 | `_validate_entity_coordinate(entity_name, occurrence)` |
| _validate_entity_coordinate | require_nonempty_text | 908 | `require_nonempty_text(entity_name, error=ValueError(...), reject_control_characters=False)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services….py:require_nonempty_text) | 574 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 576 | `value.strip(data not statically known)` |
| require_nonempty_text | any | 582 | `any(...)` |
| require_nonempty_text | ord | 583 | `ord(character)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_bool` | `isinstance` | 772 |
| external_call | `_validate_inventory_complete` | `TypeError` | 854 |
| external_call | `require_nonempty_text` | `isinstance` | 574 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 576 |
| external_call | `require_nonempty_text` | `any` | 582 |
| external_call | `require_nonempty_text` | `ord` | 583 |
| step_limit | `entity_observation_hash` | `first 12 steps` | 0 |
| truncated_flow | `entity_observation_hash` | `depth limit` | 0 |

## Behavior

This flow starts at `entity_observation_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
