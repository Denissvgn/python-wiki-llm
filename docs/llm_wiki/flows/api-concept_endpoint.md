# concept_endpoint

**Entry point:** `concept_endpoint` (`api`)
**Source:** [knowledge_graph](../modules/knowledge_graph.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md), and 1 more

**Complete modules touched:**

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as concept_endpoint
    participant p1 as _normalise_endpoint
    participant p2 as _object
    participant p3 as require_mapping
    participant p4 as isinstance
    participant p5 as encode
    participant p6 as KnowledgeGraphError
    participant p7 as dict
    participant p8 as _enum
    participant p9 as join
    participant p10 as repr
    participant p11 as require_choice
    participant p12 as require_trimmed_text
    participant p13 as require_nonempty_text
    participant p14 as strip
    participant p15 as any
    participant p16 as ord
    participant p17 as frozenset
    participant p18 as choice_error
    participant p19 as get
    participant p20 as _only_fields
    participant p21 as require_exact_fields
    participant p22 as str
    participant p23 as set
    p0->>p1: _normalise_endpoint
    p1->>p2: _object
    p2->>p3: require_mapping
    p3-->>p4: isinstance
    p3-->>p4: isinstance
    p3-->>p5: encode
    p2->>p6: KnowledgeGraphError
    p2->>p6: KnowledgeGraphError
    p2-->>p7: dict
    p1->>p8: _enum
    p8->>p6: KnowledgeGraphError
    p8-->>p9: join
    p8-->>p10: repr
    p8->>p11: require_choice
    p11->>p12: require_trimmed_text
    p12->>p13: require_nonempty_text
    p13-->>p4: isinstance
    p13-->>p14: strip
    p13-->>p15: any
    p13-->>p16: ord
    p13-->>p16: ord
    p11-->>p17: frozenset
    p11-->>p18: choice_error
    p1-->>p19: get
    p1->>p20: _only_fields
    p20->>p21: require_exact_fields
    p21-->>p4: isinstance
    p21-->>p22: str
    p21-->>p23: set
    p21-->>p23: set
```

> Call sequence diagram shows 30 of 201 interactions; 171 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. concept_endpoint"]
    s2["2. _normalise_endpoint"]
    s3["3. _object"]
    s4["4. require_mapping"]
    s5["5. isinstance"]
    s6["6. isinstance"]
    s7["7. encode"]
    s8["8. KnowledgeGraphError"]
    s9["9. KnowledgeGraphError"]
    s10["10. dict"]
    s11["11. _enum"]
    s12["12. KnowledgeGraphError"]
    s1 -->|"_normalise_endpoint({...}, 'endpoint')"| s2
    s2 -->|"_object(value, path)"| s3
    s3 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s4
    s4 -. "isinstance(value, Mapping)" .-> s5
    s4 -. "isinstance(key, str)" .-> s6
    s4 -. "key.encode('utf-8')" .-> s7
    s3 -->|"KnowledgeGraphError(path, 'must be an object')"| s8
    s3 -->|"KnowledgeGraphError(path, 'object keys must be strings')"| s9
    s3 -. "dict(selected)" .-> s10
    s2 -->|"_enum(endpoint.get(...), ENDPOINT_KINDS, ...)"| s11
    s11 -->|"KnowledgeGraphError(path, ...)"| s12
    click s1 "../modules/knowledge_graph.md"
    click s2 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s4 "../modules/validation.md"
    click s8 "../modules/knowledge_graph.md"
    click s9 "../modules/knowledge_graph.md"
    click s11 "../modules/knowledge_graph.md"
    click s12 "../modules/knowledge_graph.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `concept_endpoint` | `locator: str` | - | - | `_normalise_endpoint(...)` |
| `_normalise_endpoint` | `value: object`, `path: str` | `ENDPOINT_KINDS` | `result[...]`, `result[...]` | `{...}`, `{...}`, `{...}`, `result`, `result` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `encode` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `dict` | - | - | - | - |
| `_enum` | `value: object`, `values: Sequence[str]`, `path: str` | - | - | `require_choice(...)` |
| `KnowledgeGraphError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| concept_endpoint | _normalise_endpoint | 253 | `_normalise_endpoint({...}, 'endpoint')` |
| _normalise_endpoint | _object | 1390 | `_object(value, path)` |
| _object | require_mapping | 2282 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance | 727 | `isinstance(value, Mapping)` |
| require_mapping | isinstance | 731 | `isinstance(key, str)` |
| require_mapping | encode | 736 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2284 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2286 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2288 | `dict(selected)` |
| _normalise_endpoint | _enum | 1391 | `_enum(endpoint.get(...), ENDPOINT_KINDS, ...)` |
| _enum | KnowledgeGraphError | 2321 | `KnowledgeGraphError(path, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `require_mapping` | `isinstance` | 727 |
| unresolved_call | `require_mapping` | `isinstance` | 731 |
| unresolved_call | `require_mapping` | `key.encode` | 736 |
| step_limit | `concept_endpoint` | `first 12 steps` | 0 |
| truncated_flow | `concept_endpoint` | `depth limit` | 0 |

## Behavior

This flow starts at `concept_endpoint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
