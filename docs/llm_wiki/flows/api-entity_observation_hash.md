# entity_observation_hash

**Entry point:** `entity_observation_hash` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as entity_observation_hash
    participant p1 as _validate_inventory_complete
    participant p2 as normalize_entity_observation
    participant p3 as _hash_normalized_observation
    participant p4 as require_bool
    participant p5 as _validate_entity_coordinate
    participant p6 as hash_json
    participant p7 as TypeError
    participant p8 as _normalize_entity_observation
    participant p9 as isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)
    participant p10 as require_nonempty_text
    participant p11 as _inventory_language
    participant p12 as sha256_bytes
    participant p13 as ValueError
    participant p14 as isinstance (src/llm_wiki_cli/services…malize_entity_observation)
    participant p15 as canonical_json_bytes
    participant p16 as require_positive_int
    participant p17 as _record_array
    participant p18 as _record_name
    participant p19 as _InventoryNormalizationError
    participant p20 as _validate_entity_record
    participant p21 as _structural_copy
    participant p22 as isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)
    participant p23 as require_nonnegative_int
    participant p24 as isinstance (src/llm_wiki_cli/services…ce.py:_inventory_language)
    participant p25 as _validate_module_entity_record
    participant p26 as set
    participant p27 as hashlib.sha256(…).hexdigest
    p0->>p1: _validate_inventory_complete
    p0->>p2: normalize_entity_observation
    p0->>p3: _hash_normalized_observation
    p1->>p4: require_bool
    p2->>p5: _validate_entity_coordinate
    p3->>p6: hash_json
    p1-->>p7: TypeError('inventory_complete must be a boolean')
    p2->>p8: _normalize_entity_observation
    p4-->>p9: isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)(value, bool)
    p5->>p10: require_nonempty_text
    p8->>p11: _inventory_language
    p6->>p12: sha256_bytes
    p5-->>p13: ValueError('entity_name must be a non-empty string')
    p8-->>p14: isinstance (src/llm_wiki_cli/services…malize_entity_observation)(file_data, Mapping)
    p6->>p15: canonical_json_bytes
    p5->>p16: require_positive_int
    p8->>p17: _record_array
    p5-->>p13: ValueError('occurrence must be a positive integer')
    p8->>p18: _record_name
    p8->>p19: _InventoryNormalizationError
    p8->>p20: _validate_entity_record
    p8->>p21: _structural_copy
    p10-->>p22: isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)(value, str)
    p16->>p23: require_nonnegative_int
    p11-->>p24: isinstance (src/llm_wiki_cli/services…ce.py:_inventory_language)(file_data, Mapping)
    p17->>p19: _InventoryNormalizationError
    p18->>p10: require_nonempty_text
    p20->>p25: _validate_module_entity_record
    p21-->>p26: set
    p12-->>p27: hashlib.sha256(…).hexdigest
```

> Call sequence diagram shows 30 of 115 interactions; 85 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 27 (19 omitted); unresolved 1 of 11 (10 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonempty_text` | 8 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:contains_control_character` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_nonnegative_int` | 15 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_int` | 16 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:_inventory_language` | 21 | [src/llm_wiki_cli/services/knowledge_evidence.py](../modules/knowledge_evidence.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:_inventory_language` | 21 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:_inventory_language` | 21 | - | external | 1 |
> Omission summary shows 8 of 38 groups; 30 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
    s11["11. contains_control_character"]
    s12["12. pattern.search"]
    s1 -->|"_validate_inventory_complete(inventory_complete)"| s2
    s2 -->|"require_bool(inventory_complete, error=TypeError(...))"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…alidation.py:require_bool)(value, bool)" .-> s4
    s2 -. "TypeError('inventory_complete must be a boolean')" .-> s5
    s1 -->|"normalize_entity_observation(file_data, entity_name, occurrence)"| s6
    s6 -->|"_validate_entity_coordinate(entity_name, occurrence)"| s7
    s7 -->|"require_nonempty_text(entity_name, error=ValueError(...), reject_control_characters=False)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services….py:require_nonempty_text)(value, str)" .-> s9
    s8 -. "value.strip(data not statically known)" .-> s10
    s8 -->|"contains_control_character(parsed, reject_delete_character=reject_delete_character)"| s11
    s11 -. "pattern.search(value)" .-> s12
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s3 "../modules/validation.md"
    click s6 "../modules/knowledge_evidence.md"
    click s7 "../modules/knowledge_evidence.md"
    click s8 "../modules/validation.md"
    click s11 "../modules/validation.md"
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
| `contains_control_character` | `value: str`, `reject_delete_character: bool` | `_ASCII_CONTROL_DELETE`, `_ASCII_CONTROL` | - | `...` |
| `pattern.search` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| entity_observation_hash | _validate_inventory_complete | 272 | `_validate_inventory_complete(inventory_complete)` |
| _validate_inventory_complete | require_bool | 853 | `require_bool(inventory_complete, error=TypeError(...))` |
| require_bool | isinstance (src/llm_wiki_cli/services…alidation.py:require_bool) | 810 | `isinstance(value, bool)` |
| _validate_inventory_complete | TypeError | 855 | `TypeError('inventory_complete must be a boolean')` |
| entity_observation_hash | normalize_entity_observation | 275 | `normalize_entity_observation(file_data, entity_name, occurrence)` |
| normalize_entity_observation | _validate_entity_coordinate | 238 | `_validate_entity_coordinate(entity_name, occurrence)` |
| _validate_entity_coordinate | require_nonempty_text | 909 | `require_nonempty_text(entity_name, error=ValueError(...), reject_control_characters=False)` |
| require_nonempty_text | isinstance (src/llm_wiki_cli/services….py:require_nonempty_text) | 623 | `isinstance(value, str)` |
| require_nonempty_text | value.strip | 625 | `value.strip(data not statically known)` |
| require_nonempty_text | contains_control_character | 631 | `contains_control_character(parsed, reject_delete_character=reject_delete_character)` |
| contains_control_character | pattern.search | 685 | `pattern.search(value)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_bool` | `isinstance` | 810 |
| external_call | `_validate_inventory_complete` | `TypeError` | 855 |
| external_call | `require_nonempty_text` | `isinstance` | 623 |
| unresolved_call | `require_nonempty_text` | `value.strip` | 625 |
| unresolved_call | `contains_control_character` | `pattern.search` | 685 |
| step_limit | `entity_observation_hash` | `first 12 steps` | 0 |
| truncated_flow | `entity_observation_hash` | `depth limit` | 0 |

## Behavior

This flow starts at `entity_observation_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
