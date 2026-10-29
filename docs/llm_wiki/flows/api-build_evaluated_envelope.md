# build_evaluated_envelope

**Entry point:** `build_evaluated_envelope` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [implementation_evidence](../modules/implementation_evidence.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 10 more

**Complete modules touched:**

- [implementation_evidence](../modules/implementation_evidence.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [maintenance_state](../modules/maintenance_state.md)
- [section_ownership](../modules/section_ownership.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_evaluated_envelope
    participant p1 as _extensions_copy
    participant p2 as hash_source_snapshot
    participant p3 as hash_inventory
    participant p4 as _validate_inventory_source_parity
    participant p5 as hash_markdown_snapshot
    participant p6 as hash_generation_options
    participant p7 as build_producer_record
    participant p8 as evaluated_envelope_to_payload
    participant p9 as KnowledgeEnvelopeError
    participant p10 as SnapshotRecord
    participant p11 as sha256_bytes
    participant p12 as BundleRecord
    participant p13 as EvaluatedEnvelope
    participant p14 as _build_component
    participant p15 as _validated_bundle_payload
    participant p16 as _normalized_allowlist
    participant p17 as _repository_relative_path
    participant p18 as _reject_unknown_option_keys
    participant p19 as _hash_structured
    participant p20 as _normalized_markdown_bytes
    participant p21 as require_repository_relative_path
    participant p22 as canonical_json_bytes
    participant p23 as knowledge_index_to_payload
    participant p24 as _validated_limitations
    participant p25 as hash_component_configuration
    participant p26 as _emit_extensions
    participant p27 as _bundle_to_payload
    participant p28 as _concept_to_payload
    participant p29 as isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)
    participant p30 as snapshot_extensions.get
    p0->>p1: _extensions_copy
    p0->>p2: hash_source_snapshot
    p0->>p3: hash_inventory
    p0->>p4: _validate_inventory_source_parity
    p0->>p5: hash_markdown_snapshot
    p0->>p6: hash_generation_options
    p0->>p7: build_producer_record
    p0->>p8: evaluated_envelope_to_payload
    p0->>p9: KnowledgeEnvelopeError
    p0->>p10: SnapshotRecord
    p0->>p11: sha256_bytes
    p0->>p12: BundleRecord
    p0->>p13: EvaluatedEnvelope
    p7->>p14: _build_component
    p8->>p15: _validated_bundle_payload
    p6->>p16: _normalized_allowlist
    p3->>p17: _repository_relative_path
    p6->>p18: _reject_unknown_option_keys
    p2->>p19: _hash_structured
    p5->>p20: _normalized_markdown_bytes
    p17->>p21: require_repository_relative_path
    p19->>p22: canonical_json_bytes
    p15->>p23: knowledge_index_to_payload
    p14->>p24: _validated_limitations
    p14->>p25: hash_component_configuration
    p23->>p26: _emit_extensions
    p23->>p27: _bundle_to_payload
    p23->>p28: _concept_to_payload
    p0-->>p29: isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)(inputs, EnvelopeInputs)
    p0-->>p30: snapshot_extensions.get(INVENTORY_HASH_EXTENSION)
```

> Call sequence diagram shows 30 of 550 interactions; 520 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 150 (149 omitted); unresolved 1 of 78 (77 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_envelope.py:build_evaluated_envelope` | 1 | - | external | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_extensions_copy` | 6 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_extensions_copy` | 6 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_reject_machine_local_paths` | 12 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_reject_machine_local_paths` | 12 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:build_evaluated_envelope` | 1 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 4 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:hash_source_snapshot` | 18 | - | external | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:hash_source_snapshot` | 18 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 2 |
> Omission summary shows 8 of 137 groups; 129 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 323; effect analysis evaluated: 209, partial: 10, unavailable: 104. Counts include steps omitted from the displayed trace.

Collector observations for 219 source steps with known totals: observed: 1045, emitted: 991, omitted: 54. Unavailable totals are excluded.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `build_evaluated_envelope` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…:build_evaluated_envelope)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_extensions_copy` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `any (src/llm_wiki_cli/services…elope.py:_extensions_copy)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `KnowledgeEnvelopeError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_reject_machine_local_paths` | `available` | `evaluated` | `available` | `2` | `2` | `0` |

```mermaid
flowchart LR
    s1["1. build_evaluated_envelope"]
    s2["2. isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)"]
    s3["3. TypeError (src/llm_wiki_cli/services…:build_evaluated_envelope)"]
    s4["4. isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)"]
    s5["5. KnowledgeEnvelopeError"]
    s6["6. _extensions_copy"]
    s7["7. isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)"]
    s8["8. KnowledgeEnvelopeError"]
    s9["9. any (src/llm_wiki_cli/services…elope.py:_extensions_copy)"]
    s10["10. isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)"]
    s11["11. KnowledgeEnvelopeError"]
    s12["12. _reject_machine_local_paths"]
    s1 -. "isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)(inputs, EnvelopeInputs)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…:build_evaluated_envelope)('inputs must be an EnvelopeInputs')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)(inputs.repository, RepositoryRecord)" .-> s4
    s1 -->|"KnowledgeEnvelopeError('repository', 'must be a pre-evaluated RepositoryRecord')"| s5
    s1 -->|"_extensions_copy(inputs.repository.extensions, 'repository.extensions')"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)(value, Mapping)" .-> s7
    s6 -->|"KnowledgeEnvelopeError(field_name, 'must be an object')"| s8
    s6 -. "any (src/llm_wiki_cli/services…elope.py:_extensions_copy)(...)" .-> s9
    s6 -. "isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)(key, str)" .-> s10
    s6 -->|"KnowledgeEnvelopeError(field_name, 'must use string extension keys')"| s11
    s6 -->|"_reject_machine_local_paths(value, field_name)"| s12
    click s1 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s11 "../modules/knowledge_envelope.md"
    click s12 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_evaluated_envelope` | `inputs: EnvelopeInputs` | `EnvelopeInputs`, `RepositoryRecord`, `INVENTORY_HASH_EXTENSION`, `INVENTORY_HASH_EXTENSION` | `snapshot_extensions[...]` | `envelope` |
| `isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…:build_evaluated_envelope)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_extensions_copy` | `value: Mapping[str, Any]`, `field_name: str` | `Mapping` | - | `dict(...)` |
| `isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `any (src/llm_wiki_cli/services…elope.py:_extensions_copy)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_reject_machine_local_paths` | `value: object`, `field_name: str` | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_evaluated_envelope | isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope) | 895 | `isinstance(inputs, EnvelopeInputs)` |
| build_evaluated_envelope | TypeError (src/llm_wiki_cli/services…:build_evaluated_envelope) | 896 | `TypeError('inputs must be an EnvelopeInputs')` |
| build_evaluated_envelope | isinstance (src/llm_wiki_cli/services…:build_evaluated_envelope) | 897 | `isinstance(inputs.repository, RepositoryRecord)` |
| build_evaluated_envelope | KnowledgeEnvelopeError | 898 | `KnowledgeEnvelopeError('repository', 'must be a pre-evaluated RepositoryRecord')` |
| build_evaluated_envelope | _extensions_copy | 902 | `_extensions_copy(inputs.repository.extensions, 'repository.extensions')` |
| _extensions_copy | isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy) | 1774 | `isinstance(value, Mapping)` |
| _extensions_copy | KnowledgeEnvelopeError | 1775 | `KnowledgeEnvelopeError(field_name, 'must be an object')` |
| _extensions_copy | any (src/llm_wiki_cli/services…elope.py:_extensions_copy) | 1776 | `any(...)` |
| _extensions_copy | isinstance (src/llm_wiki_cli/services…elope.py:_extensions_copy) | 1776 | `isinstance(key, str)` |
| _extensions_copy | KnowledgeEnvelopeError | 1777 | `KnowledgeEnvelopeError(field_name, 'must use string extension keys')` |
| _extensions_copy | _reject_machine_local_paths | 1778 | `_reject_machine_local_paths(value, field_name)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `build_evaluated_envelope` | `isinstance` | 895 |
| external_call | `build_evaluated_envelope` | `TypeError` | 896 |
| external_call | `build_evaluated_envelope` | `isinstance` | 897 |
| external_call | `_extensions_copy` | `isinstance` | 1774 |
| external_call | `_extensions_copy` | `any` | 1776 |
| external_call | `_extensions_copy` | `isinstance` | 1776 |
| step_limit | `build_evaluated_envelope` | `first 12 steps` | 0 |
| truncated_flow | `build_evaluated_envelope` | `depth limit` | 0 |

## Behavior

This flow starts at `build_evaluated_envelope` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
