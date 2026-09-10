# require_mapping_list

**Entry point:** `require_mapping_list` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as require_mapping_list
    participant p1 as require_list
    participant p2 as isinstance (src/llm_wiki_cli/services/validation.py:require_list)
    participant p3 as require_mapping
    participant p4 as isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)
    participant p5 as key.encode
    p0->>p1: require_list
    p1-->>p2: isinstance (src/llm_wiki_cli/services/validation.py:require_list)
    p0->>p3: require_mapping
    p3-->>p4: isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)
    p3-->>p4: isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)
    p3-->>p5: key.encode
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. require_mapping_list"]
    s2["2. require_list"]
    s3["3. isinstance (src/llm_wiki_cli/services/validation.py:require_list)"]
    s4["4. require_mapping"]
    s5["5. isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)"]
    s6["6. isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)"]
    s7["7. key.encode"]
    s1 -->|"require_list(value, error=error)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services/validation.py:require_list)(value, list)" .-> s3
    s1 -->|"require_mapping(item, error=..., require_string_keys=require_string_keys)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)(value, Mapping)" .-> s5
    s4 -. "isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)(key, str)" .-> s6
    s4 -. "key.encode('utf-8')" .-> s7
    click s1 "../modules/validation.md"
    click s2 "../modules/validation.md"
    click s4 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `require_mapping_list` | `value: object`, `error: Exception`, `item_error: Exception \| None`, `require_string_keys: bool` | - | - | `items` |
| `require_list` | `value: object`, `error: Exception` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services/validation.py:require_list)` | - | - | - | - |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…idation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| require_mapping_list | require_list | 1015 | `require_list(value, error=error)` |
| require_list | isinstance (src/llm_wiki_cli/services/validation.py:require_list) | 764 | `isinstance(value, list)` |
| require_mapping_list | require_mapping | 1017 | `require_mapping(item, error=..., require_string_keys=require_string_keys)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…idation.py:require_mapping) | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…idation.py:require_mapping) | 731 | `isinstance(key, str)` |
| require_mapping | key.encode | 736 | `key.encode('utf-8')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_list` | `isinstance` | 764 |
| external_call | `require_mapping` | `isinstance` | 727 |
| external_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |

## Behavior

This flow starts at `require_mapping_list` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
