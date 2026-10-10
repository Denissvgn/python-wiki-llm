# external_resource_endpoint

**Entry point:** `external_resource_endpoint` (`api`)
**Source:** [knowledge_graph](../modules/knowledge_graph.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_graph](../modules/knowledge_graph.md), [validation](../modules/validation.md), [wiki_media](../modules/wiki_media.md), and 1 more

**Complete modules touched:**

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as external_resource_endpoint
    participant p1 as _normalise_endpoint
    participant p2 as _object
    participant p3 as _enum
    participant p4 as endpoint.get
    participant p5 as _only_fields
    participant p6 as len (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)
    participant p7 as KnowledgeGraphError
    participant p8 as _locator
    participant p9 as _name
    participant p10 as _relative_path
    participant p11 as _external_uri
    participant p12 as _array
    participant p13 as enumerate
    participant p14 as any (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)
    participant p15 as _canonical_json
    participant p16 as sorted (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)
    participant p17 as require_mapping
    participant p18 as require_exact_fields
    p0->>p1: _normalise_endpoint
    p1->>p2: _object
    p1->>p3: _enum
    p1-->>p4: endpoint.get('kind')
    p1->>p5: _only_fields
    p1-->>p6: len (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)(present)
    p1->>p7: KnowledgeGraphError
    p1->>p8: _locator
    p1->>p9: _name
    p1->>p5: _only_fields
    p1->>p10: _relative_path
    p1->>p9: _name
    p1->>p5: _only_fields
    p1->>p9: _name
    p1->>p11: _external_uri
    p1->>p5: _only_fields
    p1->>p9: _name
    p1->>p12: _array
    p1->>p1: _normalise_endpoint
    p1-->>p13: enumerate(raw_candidates)
    p1-->>p14: any (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)(...)
    p1->>p7: KnowledgeGraphError
    p1->>p15: _canonical_json
    p1-->>p16: sorted (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)(canonical)
    p2->>p17: require_mapping
    p3->>p7: KnowledgeGraphError
    p5->>p18: require_exact_fields
    p8->>p9: _name
    p10->>p9: _name
    p11->>p9: _name
```

> Call sequence diagram shows 30 of 216 interactions; 186 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 63 (59 omitted); unresolved 1 of 56 (55 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 3 | [src/llm_wiki_cli/services/knowledge_graph.py](../modules/knowledge_graph.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 3 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_enum` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_enum` | 11 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_enum` | 11 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_choice` | 15 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
> Omission summary shows 8 of 71 groups; 63 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. external_resource_endpoint"]
    s2["2. _normalise_endpoint"]
    s3["3. _object"]
    s4["4. require_mapping"]
    s5["5. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s6["6. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s7["7. key.encode"]
    s8["8. KnowledgeGraphError"]
    s9["9. KnowledgeGraphError"]
    s10["10. dict"]
    s11["11. _enum"]
    s12["12. KnowledgeGraphError"]
    s1 -->|"_normalise_endpoint(value, 'endpoint')"| s2
    s2 -->|"_object(value, path)"| s3
    s3 -->|"require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s5
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s6
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
| `external_resource_endpoint` | `resource: str`, `uri: str \| None` | - | `value[...]` | `_normalise_endpoint(...)` |
| `_normalise_endpoint` | `value: object`, `path: str` | `ENDPOINT_KINDS` | `result[...]`, `result[...]` | `{...}`, `{...}`, `{...}`, `result`, `result` |
| `_object` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `key.encode` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `KnowledgeGraphError` | - | - | - | - |
| `dict` | - | - | - | - |
| `_enum` | `value: object`, `values: Sequence[str]`, `path: str` | - | - | `require_choice(...)` |
| `KnowledgeGraphError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| external_resource_endpoint | _normalise_endpoint | 284 | `_normalise_endpoint(value, 'endpoint')` |
| _normalise_endpoint | _object | 1411 | `_object(value, path)` |
| _object | require_mapping | 2309 | `require_mapping(value, error=KnowledgeGraphError(...), require_string_keys=True, key_error=KnowledgeGraphError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 769 | `isinstance(key, str)` |
| require_mapping | key.encode | 774 | `key.encode('utf-8')` |
| _object | KnowledgeGraphError | 2311 | `KnowledgeGraphError(path, 'must be an object')` |
| _object | KnowledgeGraphError | 2313 | `KnowledgeGraphError(path, 'object keys must be strings')` |
| _object | dict | 2315 | `dict(selected)` |
| _normalise_endpoint | _enum | 1412 | `_enum(endpoint.get(...), ENDPOINT_KINDS, ...)` |
| _enum | KnowledgeGraphError | 2348 | `KnowledgeGraphError(path, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 765 |
| external_call | `require_mapping` | `isinstance` | 769 |
| unresolved_call | `require_mapping` | `key.encode` | 774 |
| step_limit | `external_resource_endpoint` | `first 12 steps` | 0 |
| truncated_flow | `external_resource_endpoint` | `depth limit` | 0 |

## Behavior

This flow starts at `external_resource_endpoint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
