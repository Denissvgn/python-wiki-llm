# validate_surface_index_bytes

**Entry point:** `validate_surface_index_bytes` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_surface_index_bytes
    participant p1 as _decode_json_object
    participant p2 as isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    participant p3 as KnowledgeArtifactError
    participant p4 as content.decode
    participant p5 as json.loads
    participant p6 as _unique_json_object
    participant p7 as _reject_json_constant
    participant p8 as _validate_surface_payload
    participant p9 as _validate_utf8_json
    participant p10 as isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    participant p11 as value.encode
    participant p12 as value.items
    participant p13 as enumerate (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    participant p14 as payload.get
    p0->>p1: _decode_json_object
    p1-->>p2: isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p1->>p3: KnowledgeArtifactError
    p1-->>p4: content.decode
    p1->>p3: KnowledgeArtifactError
    p1-->>p5: json.loads
    p1->>p6: _unique_json_object
    p6->>p3: KnowledgeArtifactError
    p1->>p7: _reject_json_constant
    p7->>p3: KnowledgeArtifactError
    p1-->>p2: isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p1->>p3: KnowledgeArtifactError
    p1-->>p2: isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p1->>p3: KnowledgeArtifactError
    p0->>p8: _validate_surface_payload
    p8->>p9: _validate_utf8_json
    p9-->>p10: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p9-->>p11: value.encode
    p9->>p3: KnowledgeArtifactError
    p9-->>p10: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p9-->>p12: value.items
    p9-->>p10: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p9->>p3: KnowledgeArtifactError
    p9->>p9: _validate_utf8_json
    p9->>p9: _validate_utf8_json
    p9-->>p10: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p9-->>p13: enumerate (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p9->>p9: _validate_utf8_json
    p8-->>p14: payload.get
    p8->>p3: KnowledgeArtifactError
```

> Call sequence diagram shows 30 of 334 interactions; 304 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_surface_index_bytes"]
    s2["2. _decode_json_object"]
    s3["3. isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)"]
    s4["4. KnowledgeArtifactError"]
    s5["5. content.decode"]
    s6["6. KnowledgeArtifactError"]
    s7["7. json.loads"]
    s8["8. _unique_json_object"]
    s9["9. KnowledgeArtifactError"]
    s10["10. _reject_json_constant"]
    s11["11. KnowledgeArtifactError"]
    s12["12. isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)"]
    s1 -->|"_decode_json_object(surface_index_bytes, 'surface_index_bytes')"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)(content, bytes)" .-> s3
    s2 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s4
    s2 -. "content.decode('utf-8')" .-> s5
    s2 -->|"KnowledgeArtifactError(field, 'must be valid UTF-8')"| s6
    s2 -. "json.loads(text, object_pairs_hook=..., parse_constant=...)" .-> s7
    s2 -->|"_unique_json_object(pairs, field)"| s8
    s8 -->|"KnowledgeArtifactError(field, ...)"| s9
    s2 -->|"_reject_json_constant(value, field)"| s10
    s10 -->|"KnowledgeArtifactError(field, ...)"| s11
    s2 -. "isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)(exc, KnowledgeArtifactError)" .-> s12
    click s1 "../modules/knowledge_artifacts.md"
    click s2 "../modules/knowledge_artifacts.md"
    click s4 "../modules/knowledge_artifacts.md"
    click s6 "../modules/knowledge_artifacts.md"
    click s8 "../modules/knowledge_artifacts.md"
    click s9 "../modules/knowledge_artifacts.md"
    click s10 "../modules/knowledge_artifacts.md"
    click s11 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_surface_index_bytes` | `surface_index_bytes: bytes` | - | - | `surface_payload` |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `content.decode` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `json.loads` | - | - | - | - |
| `_unique_json_object` | `pairs: list[tuple[str, Any]]`, `field: str` | - | `result[...]` | `result` |
| `KnowledgeArtifactError` | - | - | - | - |
| `_reject_json_constant` | `value: str`, `field: str` | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_surface_index_bytes | _decode_json_object | 233 | `_decode_json_object(surface_index_bytes, 'surface_index_bytes')` |
| _decode_json_object | isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 574 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 575 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | content.decode | 577 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 579 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |
| _decode_json_object | json.loads | 581 | `json.loads(text, object_pairs_hook=..., parse_constant=...)` |
| _decode_json_object | _unique_json_object | 583 | `_unique_json_object(pairs, field)` |
| _unique_json_object | KnowledgeArtifactError | 602 | `KnowledgeArtifactError(field, ...)` |
| _decode_json_object | _reject_json_constant | 584 | `_reject_json_constant(value, field)` |
| _reject_json_constant | KnowledgeArtifactError | 608 | `KnowledgeArtifactError(field, ...)` |
| _decode_json_object | isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 587 | `isinstance(exc, KnowledgeArtifactError)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_decode_json_object` | `isinstance` | 574 |
| unresolved_call | `_decode_json_object` | `content.decode` | 577 |
| external_call | `_decode_json_object` | `json.loads` | 581 |
| external_call | `_decode_json_object` | `isinstance` | 587 |
| step_limit | `validate_surface_index_bytes` | `first 12 steps` | 0 |
| truncated_flow | `validate_surface_index_bytes` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_surface_index_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
