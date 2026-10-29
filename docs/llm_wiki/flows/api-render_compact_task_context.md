# render_compact_task_context

**Entry point:** `render_compact_task_context` (`api`)
**Source:** [api](../modules/api.md)
**Modules touched:** [analysis_capture](../modules/analysis_capture.md), [api](../modules/api.md), [change_selection](../modules/change_selection.md), [concept_identity](../modules/concept_identity.md), and 24 more

**Complete modules touched:**

- [analysis_capture](../modules/analysis_capture.md)
- [api](../modules/api.md)
- [change_selection](../modules/change_selection.md)
- [concept_identity](../modules/concept_identity.md)
- [context_budget](../modules/context_budget.md)
- [context_packet](../modules/context_packet.md)
- [documentation_queries](../modules/documentation_queries.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_status](../modules/maintenance_status.md)
- [packet_field_policy](../modules/packet_field_policy.md)
- [storage_receipts](../modules/storage_receipts.md)
- [task_compact](../modules/task_compact.md)
- [task_compact_readable](../modules/task_compact_readable.md)
- [task_context](../modules/task_context.md)
- [task_context_v2](../modules/task_context_v2.md)
- [task_contract](../modules/task_contract.md)
- [task_evidence](../modules/task_evidence.md)
- [task_implementation](../modules/task_implementation.md)
- [token_counting](../modules/token_counting.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)
- [workflow_profile](../modules/workflow_profile.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_compact_task_context (src/llm_wiki_cli/api.py)
    participant p1 as render_compact_task_context (src/llm_wiki_cli/services/task_compact.py)
    participant p2 as _validated
    participant p3 as normalize_view_options
    participant p4 as _projection
    participant p5 as _same
    participant p6 as normalize_task_request
    participant p7 as _counter
    participant p8 as validate_task_context
    participant p9 as _encode_observation
    participant p10 as exact_fields
    participant p11 as _encode_contract
    participant p12 as bounded_text
    participant p13 as _array
    participant p14 as coordinate
    participant p15 as _validate_task_claims
    participant p16 as validate_changes
    participant p17 as normalize_profile
    participant p18 as content_id
    participant p19 as validate_context_packet
    participant p20 as validate_task_implementations
    participant p21 as validate_scoped_bindings
    participant p22 as _coerce_packet_bytes
    participant p23 as normalize_supplied_paths
    participant p24 as _strict_json_payload
    participant p25 as normalize_concept_coordinate
    participant p26 as _packet_contract_for_schema
    participant p27 as expand_storage_receipt
    participant p28 as _validate_packet_shape
    participant p29 as isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)
    participant p30 as facts[…][…].items
    p0->>p1: render_compact_task_context (src/llm_wiki_cli/services/task_compact.py)
    p1->>p2: _validated
    p1->>p3: normalize_view_options
    p1->>p4: _projection
    p4->>p5: _same
    p2->>p6: normalize_task_request
    p2->>p7: _counter
    p2->>p8: validate_task_context
    p4->>p9: _encode_observation
    p6->>p10: exact_fields
    p9->>p11: _encode_contract
    p6->>p12: bounded_text
    p6->>p13: _array
    p6->>p14: coordinate
    p8->>p15: _validate_task_claims
    p6->>p16: validate_changes
    p6->>p17: normalize_profile
    p6->>p18: content_id
    p8->>p19: validate_context_packet
    p8->>p20: validate_task_implementations
    p8->>p21: validate_scoped_bindings
    p19->>p22: _coerce_packet_bytes
    p14->>p23: normalize_supplied_paths
    p19->>p24: _strict_json_payload
    p14->>p25: normalize_concept_coordinate
    p19->>p26: _packet_contract_for_schema
    p21->>p27: expand_storage_receipt
    p19->>p28: _validate_packet_shape
    p2-->>p29: isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)(canonical_text, TaskContext)
    p4-->>p30: facts[…][…].items
```

> Call sequence diagram shows 30 of 883 interactions; 853 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 447 (446 omitted); unresolved 1 of 211 (210 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/task_compact.py:_validated` | 3 | [src/llm_wiki_cli/services/task_compact.py](../modules/task_compact.md) | internal | 5 |
| `src/llm_wiki_cli/services/task_compact.py:_validated` | 3 | - | external | 2 |
| `src/llm_wiki_cli/services/workflow_profile.py:exact_fields` | 9 | - | external | 5 |
| `src/llm_wiki_cli/services/workflow_profile.py:exact_fields` | 9 | [src/llm_wiki_cli/services/workflow_profile.py](../modules/workflow_profile.md) | internal | 2 |
| `src/llm_wiki_cli/services/task_contract.py:normalize_task_request` | 8 | - | unresolved | 22 |
| `src/llm_wiki_cli/services/task_contract.py:normalize_task_request` | 8 | - | external | 10 |
| `src/llm_wiki_cli/services/task_contract.py:normalize_task_request` | 8 | [src/llm_wiki_cli/services/workflow_profile.py](../modules/workflow_profile.md) | internal | 16 |
| `src/llm_wiki_cli/services/workflow_profile.py:bounded_text` | 20 | - | external | 2 |
> Omission summary shows 8 of 159 groups; 151 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 226; effect analysis evaluated: 157, partial: 2, unavailable: 67. Counts include steps omitted from the displayed trace.

Collector observations for 159 source steps with known totals: observed: 707, emitted: 703, omitted: 4. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `render_compact_task_context (src/llm_wiki_cli/api.py)` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `render_compact_task_context (src/llm_wiki_cli/services/task_compact.py)` | `available` | `evaluated` | `available` | `12` | `12` | `0` |
| `_validated` | `available` | `evaluated` | `available` | `8` | `8` | `0` |
| `isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TaskCompactError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TaskCompactError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `normalize_task_request` | `available` | `partial` | `available` | `23` | `21` | `2` |
| `exact_fields` | `available` | `evaluated` | `available` | `5` | `5` | `0` |
| `isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `any (src/llm_wiki_cli/services…w_profile.py:exact_fields)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. render_compact_task_context (src/llm_wiki_cli/api.py)"]
    s2["2. render_compact_task_context (src/llm_wiki_cli/services/task_compact.py)"]
    s3["3. _validated"]
    s4["4. isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)"]
    s5["5. TaskCompactError"]
    s6["6. isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)"]
    s7["7. TaskCompactError"]
    s8["8. normalize_task_request"]
    s9["9. exact_fields"]
    s10["10. isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)"]
    s11["11. any (src/llm_wiki_cli/services…w_profile.py:exact_fields)"]
    s12["12. isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)"]
    s1 -->|"render_compact_task_context (src/llm_wiki_cli/services/task_compact.py)(…)"| s2
    s2 -->|"_validated(canonical_text, request, profile, policy, counter)"| s3
    s3 -. "isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)(canonical_text, TaskContext)" .-> s4
    s3 -->|"TaskCompactError('canonical-unavailable', 'An unsuccessful canonical result has no compact context')"| s5
    s3 -. "isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)(canonical_text, str)" .-> s6
    s3 -->|"TaskCompactError('canonical-invalid', 'Canonical context must be original text')"| s7
    s3 -->|"normalize_task_request(request, profile=profile, policy=policy)"| s8
    s8 -->|"exact_fields(request, {...}, 'request')"| s9
    s9 -. "isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)(value, Mapping)" .-> s10
    s9 -. "any (src/llm_wiki_cli/services…w_profile.py:exact_fields)(...)" .-> s11
    s9 -. "isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)(key, str)" .-> s12
    b0["mutation anchors.append"]
    s8 -. "mutation anchors.append" .-> b0
    b1["mutation ids.add"]
    s8 -. "mutation ids.add" .-> b1
    b2["mutation requirements.append"]
    s8 -. "mutation requirements.append" .-> b2
    b3["mutation requirements.sort"]
    s8 -. "mutation requirements.sort" .-> b3
    click s1 "../modules/api.md"
    click s2 "../modules/task_compact.md"
    click s3 "../modules/task_compact.md"
    click s5 "../modules/task_compact.md"
    click s7 "../modules/task_compact.md"
    click s8 "../modules/task_contract.md"
    click s9 "../modules/workflow_profile.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `render_compact_task_context (src/llm_wiki_cli/api.py)` | `canonical_text: str`, `request: Mapping[str, Any]`, `view_options: Mapping[str, Any]`, `profile: WorkflowProfile \| Mapping[str, Any] \| None`, `policy: WorkflowPolicy \| None`, `counter: TokenCounter \| None` | - | - | `render(...)` |
| `render_compact_task_context (src/llm_wiki_cli/services/task_compact.py)` | `canonical_text`, `request`, `view_options`, `profile`, `policy`, `counter` | `VIEW_REQUEST_SCHEMA_V2`, `COMPACT_SCHEMA_V2`, `COMPACT_SCHEMA`, `COMPACT_SCHEMA_V2` | - | `CompactTaskContext(...)`, `CompactTaskContext(...)` |
| `_validated` | `canonical_text`, `request`, `profile`, `policy`, `counter` | `TaskContext`, `TASK_REQUEST_SCHEMA_V2` | - | `(...)` |
| `isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)` | - | - | - | - |
| `TaskCompactError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated)` | - | - | - | - |
| `TaskCompactError` | - | - | - | - |
| `normalize_task_request` | `request: Mapping[str, Any]`, `profile: WorkflowProfile \| Mapping[str, Any] \| None`, `policy: WorkflowPolicy \| None` | `TASK_REQUEST_SCHEMA_V2`, `TASK_REQUEST_SCHEMA`, `TASK_REQUEST_SCHEMA_V2`, `TASK_KINDS`, `ANCHOR_KINDS`, `canonical_json`, `FACETS`, `MAX_SELECTORS` | `changes[...]`, `normalized[...]`, `normalized[...]`, `normalized[...]`, `normalized[...]` | `(...)` |
| `exact_fields` | `value: object`, `allowed: set[str]`, `field: str` | `Mapping` | - | `dict(...)` |
| `isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)` | - | - | - | - |
| `any (src/llm_wiki_cli/services…w_profile.py:exact_fields)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_compact_task_context (src/llm_wiki_cli/api.py) | render_compact_task_context (src/llm_wiki_cli/services/task_compact.py) | 1457 | `render(canonical_text, request, view_options=view_options, profile=profile, policy=policy, counter=counter)` |
| render_compact_task_context (src/llm_wiki_cli/services/task_compact.py) | _validated | 475 | `_validated(canonical_text, request, profile, policy, counter)` |
| _validated | isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated) | 171 | `isinstance(canonical_text, TaskContext)` |
| _validated | TaskCompactError | 173 | `TaskCompactError('canonical-unavailable', 'An unsuccessful canonical result has no compact context')` |
| _validated | isinstance (src/llm_wiki_cli/services…ask_compact.py:_validated) | 178 | `isinstance(canonical_text, str)` |
| _validated | TaskCompactError | 179 | `TaskCompactError('canonical-invalid', 'Canonical context must be original text')` |
| _validated | normalize_task_request | 182 | `normalize_task_request(request, profile=profile, policy=policy)` |
| normalize_task_request | exact_fields | 53 | `exact_fields(request, {...}, 'request')` |
| exact_fields | isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields) | 67 | `isinstance(value, Mapping)` |
| exact_fields | any (src/llm_wiki_cli/services…w_profile.py:exact_fields) | 67 | `any(...)` |
| exact_fields | isinstance (src/llm_wiki_cli/services…w_profile.py:exact_fields) | 67 | `isinstance(key, str)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `anchors.append` | `normalize_task_request` | 71 |
| mutation | `ids.add` | `normalize_task_request` | 79 |
| mutation | `requirements.append` | `normalize_task_request` | 89 |
| mutation | `requirements.sort` | `normalize_task_request` | 90 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_validated` | `isinstance` | 171 |
| external_call | `_validated` | `isinstance` | 178 |
| external_call | `exact_fields` | `isinstance` | 67 |
| external_call | `exact_fields` | `any` | 67 |
| step_limit | `render_compact_task_context` | `first 12 steps` | 0 |
| truncated_flow | `render_compact_task_context` | `depth limit` | 0 |

## Behavior

This flow starts at `render_compact_task_context` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
