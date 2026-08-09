# normalize_module_observation

**Entry point:** `normalize_module_observation` (`api`)
**Source:** [knowledge_evidence](../modules/knowledge_evidence.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as normalize_module_observation
    participant p1 as _normalize_module_observation
    participant p2 as _inventory_language
    participant p3 as isinstance
    participant p4 as _InventoryNormalizationError
    participant p5 as get
    participant p6 as _record_array
    participant p7 as all
    participant p8 as _validate_import_record
    participant p9 as _validate_optional_strings
    participant p10 as require_string
    participant p11 as encode
    participant p12 as _validate_optional_booleans
    participant p13 as require_bool
    p0->>p1: _normalize_module_observation
    p1->>p2: _inventory_language
    p2-->>p3: isinstance
    p2->>p4: _InventoryNormalizationError
    p2-->>p5: get
    p2-->>p3: isinstance
    p2->>p4: _InventoryNormalizationError
    p2->>p4: _InventoryNormalizationError
    p1-->>p3: isinstance
    p1->>p6: _record_array
    p6->>p4: _InventoryNormalizationError
    p6-->>p3: isinstance
    p6->>p4: _InventoryNormalizationError
    p6-->>p7: all
    p6-->>p3: isinstance
    p6->>p4: _InventoryNormalizationError
    p1->>p6: _record_array
    p1->>p6: _record_array
    p1->>p8: _validate_import_record
    p8-->>p5: get
    p8-->>p3: isinstance
    p8->>p4: _InventoryNormalizationError
    p8->>p9: _validate_optional_strings
    p9->>p10: require_string
    p10-->>p3: isinstance
    p10-->>p11: encode
    p9->>p4: _InventoryNormalizationError
    p8->>p9: _validate_optional_strings
    p8->>p12: _validate_optional_booleans
    p12->>p13: require_bool
```

> Call sequence diagram shows 30 of 121 interactions; 91 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. normalize_module_observation"]
    s2["2. _normalize_module_observation"]
    s3["3. _inventory_language"]
    s4["4. isinstance"]
    s5["5. _InventoryNormalizationError"]
    s6["6. get"]
    s7["7. isinstance"]
    s8["8. _InventoryNormalizationError"]
    s9["9. _InventoryNormalizationError"]
    s10["10. isinstance"]
    s11["11. _record_array"]
    s12["12. _InventoryNormalizationError"]
    s1 -->|"_normalize_module_observation(file_data)"| s2
    s2 -->|"_inventory_language(file_data)"| s3
    s3 -. "isinstance(file_data, Mapping)" .-> s4
    s3 -->|"_InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)"| s5
    s3 -. "file_data.get('language')" .-> s6
    s3 -. "isinstance(language, str)" .-> s7
    s3 -->|"_InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)"| s8
    s3 -->|"_InventoryNormalizationError(UNKNOWN_UNSUPPORTED_LANGUAGE)"| s9
    s2 -. "isinstance(file_data, Mapping)" .-> s10
    s2 -->|"_record_array(file_data, 'classes', required=True)"| s11
    s11 -->|"_InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)"| s12
    b0["mutation class_summaries.append"]
    s2 -. "mutation class_summaries.append" .-> b0
    b1["mutation function_summaries.append"]
    s2 -. "mutation function_summaries.append" .-> b1
    b2["mutation constant_summaries.append"]
    s2 -. "mutation constant_summaries.append" .-> b2
    b3["mutation call_summaries.append"]
    s2 -. "mutation call_summaries.append" .-> b3
    click s1 "../modules/knowledge_evidence.md"
    click s2 "../modules/knowledge_evidence.md"
    click s3 "../modules/knowledge_evidence.md"
    click s5 "../modules/knowledge_evidence.md"
    click s8 "../modules/knowledge_evidence.md"
    click s9 "../modules/knowledge_evidence.md"
    click s11 "../modules/knowledge_evidence.md"
    click s12 "../modules/knowledge_evidence.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `normalize_module_observation` | `file_data: Mapping[str, Any]` | `_InventoryNormalizationError` | - | `_normalize_module_observation(...)`, `None` |
| `_normalize_module_observation` | `file_data: Mapping[str, Any] \| None` | `Mapping`, `_MODULE_ENTITY_FIELDS`, `_MODULE_NONSTRUCTURAL_KEYS`, `_MODULE_FUNCTION_FIELDS`, `_MODULE_NONSTRUCTURAL_KEYS`, `MODULE_OBSERVATION_SCOPE`, `_MODULE_NONSTRUCTURAL_KEYS`, `UNKNOWN_INVALID_INVENTORY` | `seen_names[...]`, `summary[...]`, `payload[...]`, `payload[...]`, `payload[...]`, `payload[...]` | `payload` |
| `_inventory_language` | `file_data: Mapping[str, Any] \| None` | `Mapping`, `UNKNOWN_INVALID_INVENTORY`, `UNKNOWN_INVALID_INVENTORY`, `_SUPPORTED_OBSERVATION_LANGUAGES`, `UNKNOWN_UNSUPPORTED_LANGUAGE` | - | `language` |
| `isinstance` | - | - | - | - |
| `_InventoryNormalizationError` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `_InventoryNormalizationError` | - | - | - | - |
| `_InventoryNormalizationError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `_record_array` | `file_data: Mapping[str, Any]`, `field: str`, `required: bool` | `UNKNOWN_INVALID_INVENTORY`, `UNKNOWN_INVALID_INVENTORY`, `Mapping`, `UNKNOWN_INVALID_INVENTORY` | - | `[...]`, `value` |
| `_InventoryNormalizationError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| normalize_module_observation | _normalize_module_observation | 218 | `_normalize_module_observation(file_data)` |
| _normalize_module_observation | _inventory_language | 425 | `_inventory_language(file_data)` |
| _inventory_language | isinstance | 541 | `isinstance(file_data, Mapping)` |
| _inventory_language | _InventoryNormalizationError | 542 | `_InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)` |
| _inventory_language | get | 543 | `file_data.get('language')` |
| _inventory_language | isinstance | 544 | `isinstance(language, str)` |
| _inventory_language | _InventoryNormalizationError | 545 | `_InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)` |
| _inventory_language | _InventoryNormalizationError | 547 | `_InventoryNormalizationError(UNKNOWN_UNSUPPORTED_LANGUAGE)` |
| _normalize_module_observation | isinstance | 426 | `isinstance(file_data, Mapping)` |
| _normalize_module_observation | _record_array | 427 | `_record_array(file_data, 'classes', required=True)` |
| _record_array | _InventoryNormalizationError | 559 | `_InventoryNormalizationError(UNKNOWN_INVALID_INVENTORY)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `class_summaries.append` | `_normalize_module_observation` | 445 |
| mutation | `function_summaries.append` | `_normalize_module_observation` | 450 |
| mutation | `constant_summaries.append` | `_normalize_module_observation` | 479 |
| mutation | `call_summaries.append` | `_normalize_module_observation` | 494 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_inventory_language` | `isinstance` | 541 |
| unresolved_call | `_inventory_language` | `file_data.get` | 543 |
| unresolved_call | `_inventory_language` | `isinstance` | 544 |
| unresolved_call | `_normalize_module_observation` | `isinstance` | 426 |
| step_limit | `normalize_module_observation` | `first 12 steps` | 0 |

## Behavior

This flow starts at `normalize_module_observation` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
