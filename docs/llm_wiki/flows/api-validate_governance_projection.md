# validate_governance_projection

**Entry point:** `validate_governance_projection` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), and 6 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_governance_projection
    participant p1 as _object (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p2 as _exact_fields
    participant p3 as _bundle_id
    participant p4 as validate_governance_ledger
    participant p5 as _event_limit
    participant p6 as _validate_concept_summary
    participant p7 as _validate_supersession_projection
    participant p8 as _validate_governance_ledger_parity
    participant p9 as apply_governance_projection
    participant p10 as require_validated_artifacts
    participant p11 as GovernanceError
    participant p12 as _hash (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p13 as _nonnegative_int (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p14 as strip_governance_projection
    participant p15 as _governance_supersession_edge_payloads
    participant p16 as validate_bundle_id
    participant p17 as _governance_concept_summaries
    participant p18 as _supersession_records
    participant p19 as _array (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p20 as _add_supersession_edges
    participant p21 as _supersession_edges
    participant p22 as _concept_uid
    participant p23 as _concept_kind
    participant p24 as _identity_value
    participant p25 as _identity_ownership_key
    participant p26 as _validate_bounded_events
    participant p27 as _validate_lifecycle_event_fields
    participant p28 as _validate_lifecycle_histories
    participant p29 as TypeError (src/llm_wiki_cli/services…ate_governance_projection)
    participant p30 as knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)
    p0->>p1: _object (src/llm_wiki_cli/services/knowledge_governance.py)
    p0->>p2: _exact_fields
    p0->>p3: _bundle_id
    p0->>p4: validate_governance_ledger
    p0->>p5: _event_limit
    p0->>p6: _validate_concept_summary
    p0->>p7: _validate_supersession_projection
    p0->>p8: _validate_governance_ledger_parity
    p0->>p9: apply_governance_projection
    p0->>p10: require_validated_artifacts
    p0->>p11: GovernanceError
    p0->>p12: _hash (src/llm_wiki_cli/services/knowledge_governance.py)
    p0->>p13: _nonnegative_int (src/llm_wiki_cli/services/knowledge_governance.py)
    p0->>p14: strip_governance_projection
    p0->>p15: _governance_supersession_edge_payloads
    p3->>p16: validate_bundle_id
    p8->>p17: _governance_concept_summaries
    p8->>p18: _supersession_records
    p6->>p19: _array (src/llm_wiki_cli/services/knowledge_governance.py)
    p9->>p20: _add_supersession_edges
    p8->>p21: _supersession_edges
    p4->>p22: _concept_uid
    p4->>p23: _concept_kind
    p4->>p24: _identity_value
    p4->>p25: _identity_ownership_key
    p6->>p26: _validate_bounded_events
    p4->>p27: _validate_lifecycle_event_fields
    p4->>p28: _validate_lifecycle_histories
    p0-->>p29: TypeError (src/llm_wiki_cli/services…ate_governance_projection)('governance validation requires its exact validated knowledge')
    p0-->>p30: knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)(GOVERNANCE_EXTENSION_KEY)
```

> Call sequence diagram shows 30 of 1279 interactions; 1249 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 397 (396 omitted); unresolved 1 of 307 (306 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_artifacts.py:require_validated_artifacts` | 2 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_projection` | 1 | - | external | 15 |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_projection` | 1 | - | unresolved | 12 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_object` | 15 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 16 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 16 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_object` | 15 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_object` | 15 | - | external | 1 |
> Omission summary shows 8 of 285 groups; 277 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 576; effect analysis evaluated: 347, partial: 10, unavailable: 219. Counts include steps omitted from the displayed trace.

Collector observations for 357 source steps with known totals: observed: 1799, emitted: 1753, omitted: 46. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `validate_governance_projection` | `available` | `partial` | `available` | `23` | `17` | `6` |
| `require_validated_artifacts` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `knowledge.bundle.snapshot.extensions.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `concept.extensions.get` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. validate_governance_projection"]
    s2["2. require_validated_artifacts"]
    s3["3. isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s4["4. TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s5["5. isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s6["6. TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)"]
    s7["7. TypeError (src/llm_wiki_cli/services…ate_governance_projection)"]
    s8["8. isinstance (src/llm_wiki_cli/services…ate_governance_projection)"]
    s9["9. TypeError (src/llm_wiki_cli/services…ate_governance_projection)"]
    s10["10. knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)"]
    s11["11. knowledge.bundle.snapshot.extensions.get"]
    s12["12. concept.extensions.get"]
    s1 -->|"require_validated_artifacts(_validated_artifacts)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)(value, ValidatedKnowledgeArtifacts)" .-> s3
    s2 -. "TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)('expected validator-issued knowledge artifacts')" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)(validation, _ArtifactValidation)" .-> s5
    s2 -. "TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)('knowledge artifacts were not issued by the validator or were replaced')" .-> s6
    s1 -. "TypeError (src/llm_wiki_cli/services…ate_governance_projection)('governance validation requires its exact validated knowledge')" .-> s7
    s1 -. "isinstance (src/llm_wiki_cli/services…ate_governance_projection)(knowledge, KnowledgeIndex)" .-> s8
    s1 -. "TypeError (src/llm_wiki_cli/services…ate_governance_projection)('knowledge must be a KnowledgeIndex')" .-> s9
    s1 -. "knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)(GOVERNANCE_EXTENSION_KEY)" .-> s10
    s1 -. "knowledge.bundle.snapshot.extensions.get(GOVERNANCE_HASH_EXTENSION_KEY)" .-> s11
    s1 -. "concept.extensions.get(GOVERNANCE_EXTENSION_KEY)" .-> s12
    b0["mutation declared_limits.add"]
    s1 -. "mutation declared_limits.add" .-> b0
    b1["mutation seen_uids.add"]
    s1 -. "mutation seen_uids.add" .-> b1
    b2["mutation successor_pairs.add"]
    s1 -. "mutation successor_pairs.add" .-> b2
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_artifacts.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_governance_projection` | `knowledge: KnowledgeIndex`, `ledger: GovernanceLedger \| None`, `event_limit: int \| None`, `_validated_artifacts: object \| None` | `KnowledgeIndex`, `GOVERNANCE_EXTENSION_KEY`, `GOVERNANCE_HASH_EXTENSION_KEY`, `GOVERNANCE_EXTENSION_KEY`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_HASH_EXTENSION_KEY`, `GOVERNANCE_EXTENSION_KEY` | - | `None`, `projection` |
| `require_validated_artifacts` | `value: object` | `ValidatedKnowledgeArtifacts`, `_ArtifactValidation` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…quire_validated_artifacts)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `knowledge.bundle.snapshot.extensions.get` | - | - | - | - |
| `concept.extensions.get` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_governance_projection | require_validated_artifacts | 1872 | `require_validated_artifacts(_validated_artifacts)` |
| require_validated_artifacts | isinstance (src/llm_wiki_cli/services…quire_validated_artifacts) | 177 | `isinstance(value, ValidatedKnowledgeArtifacts)` |
| require_validated_artifacts | TypeError (src/llm_wiki_cli/services…quire_validated_artifacts) | 178 | `TypeError('expected validator-issued knowledge artifacts')` |
| require_validated_artifacts | isinstance (src/llm_wiki_cli/services…quire_validated_artifacts) | 181 | `isinstance(validation, _ArtifactValidation)` |
| require_validated_artifacts | TypeError (src/llm_wiki_cli/services…quire_validated_artifacts) | 195 | `TypeError('knowledge artifacts were not issued by the validator or were replaced')` |
| validate_governance_projection | TypeError (src/llm_wiki_cli/services…ate_governance_projection) | 1874 | `TypeError('governance validation requires its exact validated knowledge')` |
| validate_governance_projection | isinstance (src/llm_wiki_cli/services…ate_governance_projection) | 1876 | `isinstance(knowledge, KnowledgeIndex)` |
| validate_governance_projection | TypeError (src/llm_wiki_cli/services…ate_governance_projection) | 1877 | `TypeError('knowledge must be a KnowledgeIndex')` |
| validate_governance_projection | knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection) | 1878 | `knowledge.extensions.get(GOVERNANCE_EXTENSION_KEY)` |
| validate_governance_projection | knowledge.bundle.snapshot.extensions.get | 1879 | `knowledge.bundle.snapshot.extensions.get(GOVERNANCE_HASH_EXTENSION_KEY)` |
| validate_governance_projection | concept.extensions.get | 1883 | `concept.extensions.get(GOVERNANCE_EXTENSION_KEY)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `declared_limits.add` | `validate_governance_projection` | 1981 |
| mutation | `seen_uids.add` | `validate_governance_projection` | 1988 |
| mutation | `successor_pairs.add` | `validate_governance_projection` | 2003 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `require_validated_artifacts` | `isinstance` | 177 |
| external_call | `require_validated_artifacts` | `TypeError` | 178 |
| external_call | `require_validated_artifacts` | `isinstance` | 181 |
| external_call | `require_validated_artifacts` | `TypeError` | 195 |
| external_call | `validate_governance_projection` | `TypeError` | 1874 |
| external_call | `validate_governance_projection` | `isinstance` | 1876 |
| external_call | `validate_governance_projection` | `TypeError` | 1877 |
| unresolved_call | `validate_governance_projection` | `knowledge.extensions.get` | 1878 |
| unresolved_call | `validate_governance_projection` | `knowledge.bundle.snapshot.extensions.get` | 1879 |
| unresolved_call | `validate_governance_projection` | `concept.extensions.get` | 1883 |
| step_limit | `validate_governance_projection` | `first 12 steps` | 0 |
| truncated_flow | `validate_governance_projection` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_governance_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
