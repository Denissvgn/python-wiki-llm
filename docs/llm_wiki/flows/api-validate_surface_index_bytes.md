# validate_surface_index_bytes

**Entry point:** `validate_surface_index_bytes` (`api`)
**Source:** [knowledge_artifacts](../modules/knowledge_artifacts.md)
**Modules touched:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_surface_index_bytes
    participant p1 as _decode_json_object
    participant p2 as _validate_surface_payload
    participant p3 as _surface_page_index
    participant p4 as KnowledgeArtifactError
    participant p5 as _validate_utf8_json
    participant p6 as _unique_json_object
    participant p7 as _reject_json_constant
    participant p8 as canonical_path
    participant p9 as mcp_uri
    participant p10 as _is_safe_relative_path
    participant p11 as _validate_surface_counts
    participant p12 as _validate_surface_dependency_pages
    participant p13 as _validate_surface_assets
    participant p14 as _validate_surface_flows
    participant p15 as _entry_for
    participant p16 as is_portable_relative_path
    participant p17 as _validate_page_id
    participant p18 as _validate_exact_surface_keys
    participant p19 as _nonnegative_integer
    participant p20 as _validate_asset_path_list
    participant p21 as _validate_surface_asset_counts
    participant p22 as _validate_optional_surface_flow_fields
    participant p23 as require_portable_relative_path
    participant p24 as _validate_surface_keys
    participant p25 as require_nonnegative_int
    participant p26 as is_safe_page_id
    participant p27 as _validate_surface_flow_routes
    participant p28 as _validate_surface_flow_evidence
    participant p29 as json.dumps
    participant p30 as (…).encode
    p0->>p1: _decode_json_object
    p0->>p2: _validate_surface_payload
    p0->>p3: _surface_page_index
    p0->>p4: KnowledgeArtifactError
    p2->>p5: _validate_utf8_json
    p1->>p6: _unique_json_object
    p1->>p7: _reject_json_constant
    p3->>p8: canonical_path
    p3->>p9: mcp_uri
    p3->>p10: _is_safe_relative_path
    p3->>p11: _validate_surface_counts
    p3->>p12: _validate_surface_dependency_pages
    p3->>p13: _validate_surface_assets
    p3->>p14: _validate_surface_flows
    p8->>p15: _entry_for
    p10->>p16: is_portable_relative_path
    p8->>p17: _validate_page_id
    p11->>p18: _validate_exact_surface_keys
    p11->>p19: _nonnegative_integer
    p13->>p20: _validate_asset_path_list
    p11->>p21: _validate_surface_asset_counts
    p14->>p22: _validate_optional_surface_flow_fields
    p16->>p23: require_portable_relative_path
    p18->>p24: _validate_surface_keys
    p19->>p25: require_nonnegative_int
    p17->>p26: is_safe_page_id
    p22->>p27: _validate_surface_flow_routes
    p22->>p28: _validate_surface_flow_evidence
    p0-->>p29: json.dumps(surface_payload, indent=2, sort_keys=True, allow_nan=False)
    p0-->>p30: (…).encode('utf-8')
```

> Call sequence diagram shows 30 of 348 interactions; 318 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 124 (123 omitted); unresolved 1 of 51 (50 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_decode_json_object` | 2 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_decode_json_object` | 2 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 4 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_decode_json_object` | 2 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_unique_json_object` | 8 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_reject_json_constant` | 10 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 1 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_validate_utf8_json` | 17 | - | external | 5 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_validate_utf8_json` | 17 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:_validate_utf8_json` | 17 | [src/llm_wiki_cli/services/knowledge_artifacts.py](../modules/knowledge_artifacts.md) | internal | 5 |
> Omission summary shows 8 of 76 groups; 68 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

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
| validate_surface_index_bytes | _decode_json_object | 257 | `_decode_json_object(surface_index_bytes, 'surface_index_bytes')` |
| _decode_json_object | isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 924 | `isinstance(content, bytes)` |
| _decode_json_object | KnowledgeArtifactError | 925 | `KnowledgeArtifactError(field, 'must be bytes')` |
| _decode_json_object | content.decode | 927 | `content.decode('utf-8')` |
| _decode_json_object | KnowledgeArtifactError | 929 | `KnowledgeArtifactError(field, 'must be valid UTF-8')` |
| _decode_json_object | json.loads | 931 | `json.loads(text, object_pairs_hook=..., parse_constant=...)` |
| _decode_json_object | _unique_json_object | 933 | `_unique_json_object(pairs, field)` |
| _unique_json_object | KnowledgeArtifactError | 952 | `KnowledgeArtifactError(field, ...)` |
| _decode_json_object | _reject_json_constant | 934 | `_reject_json_constant(value, field)` |
| _reject_json_constant | KnowledgeArtifactError | 958 | `KnowledgeArtifactError(field, ...)` |
| _decode_json_object | isinstance (src/llm_wiki_cli/services…ts.py:_decode_json_object) | 937 | `isinstance(exc, KnowledgeArtifactError)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_decode_json_object` | `isinstance` | 924 |
| unresolved_call | `_decode_json_object` | `content.decode` | 927 |
| external_call | `_decode_json_object` | `json.loads` | 931 |
| external_call | `_decode_json_object` | `isinstance` | 937 |
| step_limit | `validate_surface_index_bytes` | `first 12 steps` | 0 |
| truncated_flow | `validate_surface_index_bytes` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_surface_index_bytes` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
