# validate_knowledge_artifacts

**Entry point:** `validate_knowledge_artifacts` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [immutable](../modules/immutable.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), and 13 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [immutable](../modules/immutable.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [progress](../modules/progress.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_knowledge_artifacts
    participant p1 as validate_surface_index_bytes
    participant p2 as _decode_json_object
    participant p3 as isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    participant p4 as KnowledgeArtifactError
    participant p5 as content.decode
    participant p6 as json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    participant p7 as _unique_json_object
    participant p8 as _reject_json_constant
    participant p9 as _validate_surface_payload
    participant p10 as _validate_utf8_json
    participant p11 as isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    participant p12 as value.encode (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    participant p13 as value.items (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    participant p14 as enumerate (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    participant p15 as payload.get
    p0->>p1: validate_surface_index_bytes
    p1->>p2: _decode_json_object
    p2-->>p3: isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p2->>p4: KnowledgeArtifactError
    p2-->>p5: content.decode
    p2->>p4: KnowledgeArtifactError
    p2-->>p6: json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p2->>p7: _unique_json_object
    p7->>p4: KnowledgeArtifactError
    p2->>p8: _reject_json_constant
    p8->>p4: KnowledgeArtifactError
    p2-->>p3: isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p2->>p4: KnowledgeArtifactError
    p2-->>p3: isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)
    p2->>p4: KnowledgeArtifactError
    p1->>p9: _validate_surface_payload
    p9->>p10: _validate_utf8_json
    p10-->>p11: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p10-->>p12: value.encode (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p10->>p4: KnowledgeArtifactError
    p10-->>p11: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p10-->>p13: value.items (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p10-->>p11: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p10->>p4: KnowledgeArtifactError
    p10->>p10: _validate_utf8_json
    p10->>p10: _validate_utf8_json
    p10-->>p11: isinstance (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p10-->>p14: enumerate (src/llm_wiki_cli/services…ts.py:_validate_utf8_json)
    p10->>p10: _validate_utf8_json
    p9-->>p15: payload.get
```

> Call sequence diagram shows 30 of 1575 interactions; 1545 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_knowledge_artifacts"]
    s2["2. validate_surface_index_bytes"]
    s3["3. _decode_json_object"]
    s4["4. isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)"]
    s5["5. KnowledgeArtifactError"]
    s6["6. content.decode"]
    s7["7. KnowledgeArtifactError"]
    s8["8. json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)"]
    s9["9. _unique_json_object"]
    s10["10. KnowledgeArtifactError"]
    s11["11. _reject_json_constant"]
    s12["12. KnowledgeArtifactError"]
    s1 -->|"validate_surface_index_bytes(surface_index_bytes)"| s2
    s2 -->|"_decode_json_object(surface_index_bytes, 'surface_index_bytes')"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)(content, bytes)" .-> s4
    s3 -->|"KnowledgeArtifactError(field, 'must be bytes')"| s5
    s3 -. "content.decode('utf-8')" .-> s6
    s3 -->|"KnowledgeArtifactError(field, 'must be valid UTF-8')"| s7
    s3 -. "json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)(text, object_pairs_hook=..., parse_constant=...)" .-> s8
    s3 -->|"_unique_json_object(pairs, field)"| s9
    s9 -->|"KnowledgeArtifactError(field, ...)"| s10
    s3 -->|"_reject_json_constant(value, field)"| s11
    s11 -->|"KnowledgeArtifactError(field, ...)"| s12
    click s1 "../modules/knowledge_artifacts.md"
    click s2 "../modules/knowledge_artifacts.md"
    click s3 "../modules/knowledge_artifacts.md"
    click s5 "../modules/knowledge_artifacts.md"
    click s7 "../modules/knowledge_artifacts.md"
    click s9 "../modules/knowledge_artifacts.md"
    click s10 "../modules/knowledge_artifacts.md"
    click s11 "../modules/knowledge_artifacts.md"
    click s12 "../modules/knowledge_artifacts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_knowledge_artifacts` | `surface_index_bytes: bytes`, `knowledge_index_bytes: bytes`, `manifest: SyncManifest` | `KNOWLEDGE_SCHEMA_VERSION`, `_KNOWLEDGE_SCHEMA_VERSION_RE`, `ConceptKind`, `KnowledgeGraphError`, `TYPED_GRAPH_EXTENSION_KEY`, `INVENTORY_HASH_EXTENSION`, `TYPED_GRAPH_EXTENSION_KEY`, `SECTION_OWNERSHIP_EXTENSION_KEY` | - | `validated` |
| `validate_surface_index_bytes` | `surface_index_bytes: bytes` | - | - | `surface_payload` |
| `_decode_json_object` | `content: bytes`, `field: str` | `KnowledgeArtifactError`, `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `content.decode` | - | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |
| `json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object)` | - | - | - | - |
| `_unique_json_object` | `pairs: list[tuple[str, Any]]`, `field: str` | - | `result[...]` | `result` |
| `KnowledgeArtifactError` | - | - | - | - |
| `_reject_json_constant` | `value: str`, `field: str` | - | - | - |
| `KnowledgeArtifactError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_knowledge_artifacts | validate_surface_index_bytes | 265 | `validate_surface_index_bytes(surface_index_bytes)` |
| validate_surface_index_bytes | _decode_json_object | 233 | `_decode_json_object(surface_index_bytes, 'surface_index_bytes')` |
| _decode_json_object | isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 574 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 575 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | content.decode | 577 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 579 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |
| _decode_json_object | json.loads (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 581 | `json.loads(text, object_pairs_hook=..., parse_constant=...)` |
| _decode_json_object | _unique_json_object | 583 | `_unique_json_object(pairs, field)` |
| _unique_json_object | KnowledgeArtifactError | 602 | `KnowledgeArtifactError(field, ...)` |
| _decode_json_object | _reject_json_constant | 584 | `_reject_json_constant(value, field)` |
| _reject_json_constant | KnowledgeArtifactError | 608 | `KnowledgeArtifactError(field, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_decode_json_object` | `isinstance` | 574 |
| unresolved_call | `_decode_json_object` | `content.decode` | 577 |
| external_call | `_decode_json_object` | `json.loads` | 581 |
| step_limit | `validate_knowledge_artifacts` | `first 12 steps` | 0 |
| truncated_flow | `validate_knowledge_artifacts` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_knowledge_artifacts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
