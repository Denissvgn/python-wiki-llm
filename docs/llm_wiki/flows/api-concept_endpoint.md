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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as concept_endpoint
    participant p1 as _normalise_endpoint
    participant p2 as _object
    participant p3 as _enum
    participant p4 as _only_fields
    participant p5 as _locator
    participant p6 as _relative_path
    participant p7 as _external_uri
    participant p8 as _array
    participant p9 as _canonical_json
    participant p10 as require_mapping
    participant p11 as require_exact_fields
    participant p12 as _name
    participant p13 as require_list
    participant p14 as validate_exact_page_coordinate
    participant p15 as require_repository_relative_path
    participant p16 as require_choice
    participant p17 as contains_uri_authority_userinfo
    participant p18 as require_trimmed_text
    participant p19 as _matches_directory_path
    participant p20 as _matches_directory_uri
    participant p21 as require_portable_relative_path
    participant p22 as require_nonempty_text
    participant p23 as _default_path_error
    participant p24 as is_safe_page_id
    participant p25 as canonical_path
    participant p26 as mcp_uri
    participant p27 as _check_path_collision
    participant p28 as require_portable_path_component
    participant p29 as len (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)
    participant p30 as endpoint.get
    p0->>p1: _normalise_endpoint
    p1->>p2: _object
    p1->>p3: _enum
    p1->>p4: _only_fields
    p1->>p5: _locator
    p1->>p6: _relative_path
    p1->>p7: _external_uri
    p1->>p8: _array
    p1->>p9: _canonical_json
    p2->>p10: require_mapping
    p4->>p11: require_exact_fields
    p5->>p12: _name
    p8->>p13: require_list
    p5->>p14: validate_exact_page_coordinate
    p6->>p15: require_repository_relative_path
    p3->>p16: require_choice
    p7->>p17: contains_uri_authority_userinfo
    p16->>p18: require_trimmed_text
    p14->>p19: _matches_directory_path
    p14->>p20: _matches_directory_uri
    p15->>p21: require_portable_relative_path
    p18->>p22: require_nonempty_text
    p21->>p23: _default_path_error
    p19->>p24: is_safe_page_id
    p19->>p25: canonical_path
    p20->>p26: mcp_uri
    p21->>p27: _check_path_collision
    p21->>p28: require_portable_path_component
    p1-->>p29: len (src/llm_wiki_cli/services…ph.py:_normalise_endpoint)(present)
    p1-->>p30: endpoint.get('kind')
```

> Call sequence diagram shows 30 of 227 interactions; 197 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 66 (65 omitted); unresolved 1 of 59 (58 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 3 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 6 | - | external | 1 |
| `src/llm_wiki_cli/services/validation.py:_validation_error` | 6 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 4 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_object` | 3 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_enum` | 14 | - | external | 3 |
| `src/llm_wiki_cli/services/knowledge_graph.py:_enum` | 14 | - | unresolved | 3 |
> Omission summary shows 8 of 68 groups; 60 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 103; effect analysis evaluated: 72, partial: 4, unavailable: 27. Counts include steps omitted from the displayed trace.

Collector observations for 76 source steps with known totals: observed: 363, emitted: 346, omitted: 17. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `concept_endpoint` | `available` | `evaluated` | `available` | `2` | `2` | `0` |
| `_normalise_endpoint` | `available` | `evaluated` | `available` | `10` | `10` | `0` |
| `_object` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `require_mapping` | `available` | `evaluated` | `available` | `9` | `9` | `0` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `error` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `key.encode` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_validation_error` | `available` | `evaluated` | `available` | `3` | `3` | `0` |

```mermaid
flowchart LR
    s1["1. concept_endpoint"]
    s2["2. _normalise_endpoint"]
    s3["3. _object"]
    s4["4. require_mapping"]
    s5["5. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s6["6. _validation_error"]
    s7["7. isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)"]
    s8["8. error"]
    s9["9. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s10["10. _validation_error"]
    s11["11. key.encode"]
    s12["12. _validation_error"]
    s1 -->|"_normalise_endpoint({...}, 'endpoint')"| s2
    s2 -->|"_object(value, path)"| s3
    s3 -->|"require_mapping(value, error=_OBJECT_ERROR, error_context=path, require_string_keys=True, key_error=_OBJECT_KEYS_ERROR)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s5
    s4 -->|"_validation_error(error, error_context)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)(error, Exception)" .-> s7
    s6 -. "error(context)" .-> s8
    s4 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(key, str)" .-> s9
    s4 -->|"_validation_error(..., error_context)"| s10
    s4 -. "key.encode('utf-8')" .-> s11
    s4 -->|"_validation_error(..., error_context)"| s12
    click s1 "../modules/knowledge_graph.md"
    click s2 "../modules/knowledge_graph.md"
    click s3 "../modules/knowledge_graph.md"
    click s4 "../modules/validation.md"
    click s6 "../modules/validation.md"
    click s10 "../modules/validation.md"
    click s12 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `concept_endpoint` | `locator: str` | - | - | `_normalise_endpoint(...)` |
| `_normalise_endpoint` | `value: object`, `path: str` | `ENDPOINT_KINDS` | `result[...]`, `result[...]` | `{...}`, `{...}`, `{...}`, `result`, `result` |
| `_object` | `value: object`, `path: str` | `_OBJECT_ERROR`, `_OBJECT_KEYS_ERROR` | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: _ValidationError`, `error_context: str`, `require_string_keys: bool`, `key_error: _ValidationError \| None`, `require_utf8_keys: bool`, `utf8_key_error: _ValidationError \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `isinstance (src/llm_wiki_cli/services…tion.py:_validation_error)` | - | - | - | - |
| `error` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |
| `key.encode` | - | - | - | - |
| `_validation_error` | `error: _ValidationError`, `context: str` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| concept_endpoint | _normalise_endpoint | 268 | `_normalise_endpoint({...}, 'endpoint')` |
| _normalise_endpoint | _object | 1444 | `_object(value, path)` |
| _object | require_mapping | 2342 | `require_mapping(value, error=_OBJECT_ERROR, error_context=path, require_string_keys=True, key_error=_OBJECT_KEYS_ERROR)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 783 | `isinstance(value, Mapping)` |
| require_mapping | _validation_error | 784 | `_validation_error(error, error_context)` |
| _validation_error | isinstance (src/llm_wiki_cli/services…tion.py:_validation_error) | 95 | `isinstance(error, Exception)` |
| _validation_error | error | 95 | `error(context)` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 787 | `isinstance(key, str)` |
| require_mapping | _validation_error | 788 | `_validation_error(..., error_context)` |
| require_mapping | key.encode | 792 | `key.encode('utf-8')` |
| require_mapping | _validation_error | 794 | `_validation_error(..., error_context)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_mapping` | `isinstance` | 783 |
| external_call | `_validation_error` | `isinstance` | 95 |
| unresolved_call | `_validation_error` | `error` | 95 |
| external_call | `require_mapping` | `isinstance` | 787 |
| unresolved_call | `require_mapping` | `key.encode` | 792 |
| step_limit | `concept_endpoint` | `first 12 steps` | 0 |
| truncated_flow | `concept_endpoint` | `depth limit` | 0 |

## Behavior

This flow starts at `concept_endpoint` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
