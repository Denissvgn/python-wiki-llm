# governance_bundle_id_from_knowledge

**Entry point:** `governance_bundle_id_from_knowledge` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 5 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
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
    participant p0 as governance_bundle_id_from_knowledge
    participant p1 as validate_governance_projection
    participant p2 as _object (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p3 as _exact_fields
    participant p4 as _bundle_id
    participant p5 as validate_governance_ledger
    participant p6 as _event_limit
    participant p7 as _validate_concept_summary
    participant p8 as _validate_supersession_projection
    participant p9 as apply_governance_projection
    participant p10 as _governance_supersession_edge_payloads
    participant p11 as validate_bundle_id
    participant p12 as strip_governance_projection
    participant p13 as concept_references_from_knowledge
    participant p14 as _array (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p15 as lifecycle_state_by_uid
    participant p16 as _concept_uid
    participant p17 as _concept_kind
    participant p18 as _identity_value
    participant p19 as _identity_ownership_key
    participant p20 as _validate_bounded_events
    participant p21 as evaluate_review_event
    participant p22 as _add_supersession_edges
    participant p23 as _validate_lifecycle_event_fields
    participant p24 as _validate_lifecycle_histories
    participant p25 as _validate_review_event_fields
    participant p26 as _machine_text
    participant p27 as validate_concept_uid
    participant p28 as validate_concept_kind
    participant p29 as isinstance (src/llm_wiki_cli/services…_bundle_id_from_knowledge)
    participant p30 as knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)
    p0->>p1: validate_governance_projection
    p1->>p2: _object (src/llm_wiki_cli/services/knowledge_governance.py)
    p1->>p3: _exact_fields
    p1->>p4: _bundle_id
    p1->>p5: validate_governance_ledger
    p1->>p6: _event_limit
    p1->>p7: _validate_concept_summary
    p1->>p8: _validate_supersession_projection
    p1->>p9: apply_governance_projection
    p1->>p10: _governance_supersession_edge_payloads
    p4->>p11: validate_bundle_id
    p9->>p12: strip_governance_projection
    p9->>p13: concept_references_from_knowledge
    p7->>p14: _array (src/llm_wiki_cli/services/knowledge_governance.py)
    p9->>p15: lifecycle_state_by_uid
    p5->>p16: _concept_uid
    p5->>p17: _concept_kind
    p5->>p18: _identity_value
    p5->>p19: _identity_ownership_key
    p7->>p20: _validate_bounded_events
    p9->>p21: evaluate_review_event
    p9->>p22: _add_supersession_edges
    p5->>p23: _validate_lifecycle_event_fields
    p5->>p24: _validate_lifecycle_histories
    p5->>p25: _validate_review_event_fields
    p11->>p26: _machine_text
    p16->>p27: validate_concept_uid
    p17->>p28: validate_concept_kind
    p0-->>p29: isinstance (src/llm_wiki_cli/services…_bundle_id_from_knowledge)(value, str)
    p1-->>p30: knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)(GOVERNANCE_EXTENSION_KEY)
```

> Call sequence diagram shows 30 of 1065 interactions; 1035 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 317 (316 omitted); unresolved 1 of 274 (273 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_projection` | 2 | - | external | 15 |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_projection` | 2 | - | unresolved | 12 |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_projection` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 19 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_object` | 10 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 11 | - | external | 2 |
| `src/llm_wiki_cli/services/validation.py:require_mapping` | 11 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_object` | 10 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_object` | 10 | - | external | 1 |
> Omission summary shows 8 of 216 groups; 208 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 475; effect analysis evaluated: 304, partial: 0, unavailable: 171. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `governance_bundle_id_from_knowledge` | `available` | `evaluated` | `available` |
| `validate_governance_projection` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `TypeError (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `knowledge.bundle.snapshot.extensions.get` | `not_applicable` | `not_applicable` | `not_applicable` |
| `concept.extensions.get` | `not_applicable` | `not_applicable` | `not_applicable` |
| `any (src/llm_wiki_cli/services…ate_governance_projection)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `GovernanceError` | `unavailable` | `unavailable` | `unavailable` |
| `_object (src/llm_wiki_cli/services/knowledge_governance.py)` | `available` | `evaluated` | `available` |
| `require_mapping` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. governance_bundle_id_from_knowledge"]
    s2["2. validate_governance_projection"]
    s3["3. isinstance (src/llm_wiki_cli/services…ate_governance_projection)"]
    s4["4. TypeError (src/llm_wiki_cli/services…ate_governance_projection)"]
    s5["5. knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)"]
    s6["6. knowledge.bundle.snapshot.extensions.get"]
    s7["7. concept.extensions.get"]
    s8["8. any (src/llm_wiki_cli/services…ate_governance_projection)"]
    s9["9. GovernanceError"]
    s10["10. _object (src/llm_wiki_cli/services/knowledge_governance.py)"]
    s11["11. require_mapping"]
    s12["12. isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)"]
    s1 -->|"validate_governance_projection(knowledge)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…ate_governance_projection)(knowledge, KnowledgeIndex)" .-> s3
    s2 -. "TypeError (src/llm_wiki_cli/services…ate_governance_projection)('knowledge must be a KnowledgeIndex')" .-> s4
    s2 -. "knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)(GOVERNANCE_EXTENSION_KEY)" .-> s5
    s2 -. "knowledge.bundle.snapshot.extensions.get(GOVERNANCE_HASH_EXTENSION_KEY)" .-> s6
    s2 -. "concept.extensions.get(GOVERNANCE_EXTENSION_KEY)" .-> s7
    s2 -. "any (src/llm_wiki_cli/services…ate_governance_projection)(...)" .-> s8
    s2 -->|"GovernanceError('extensions', 'contains an incomplete governance projection', code='governance-projection-mismatch')"| s9
    s2 -->|"_object (src/llm_wiki_cli/services/knowledge_governance.py)(raw, 'governance_projection')"| s10
    s10 -->|"require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)(value, Mapping)" .-> s12
    b0["mutation declared_limits.add"]
    s2 -. "mutation declared_limits.add" .-> b0
    b1["mutation seen_uids.add"]
    s2 -. "mutation seen_uids.add" .-> b1
    b2["mutation successor_pairs.add"]
    s2 -. "mutation successor_pairs.add" .-> b2
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s9 "../modules/knowledge_governance.md"
    click s10 "../modules/knowledge_governance.md"
    click s11 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `governance_bundle_id_from_knowledge` | `knowledge: KnowledgeIndex` | - | - | `None`, `value` |
| `validate_governance_projection` | `knowledge: KnowledgeIndex`, `ledger: GovernanceLedger \| None`, `event_limit: int \| None` | `KnowledgeIndex`, `GOVERNANCE_EXTENSION_KEY`, `GOVERNANCE_HASH_EXTENSION_KEY`, `GOVERNANCE_EXTENSION_KEY`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_HASH_EXTENSION_KEY`, `GOVERNANCE_EXTENSION_KEY` | - | `None`, `projection` |
| `isinstance (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `knowledge.bundle.snapshot.extensions.get` | - | - | - | - |
| `concept.extensions.get` | - | - | - | - |
| `any (src/llm_wiki_cli/services…ate_governance_projection)` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `_object (src/llm_wiki_cli/services/knowledge_governance.py)` | `value: object`, `path: str` | - | - | `dict(...)` |
| `require_mapping` | `value: object`, `error: Exception`, `require_string_keys: bool`, `key_error: Exception \| None`, `require_utf8_keys: bool`, `utf8_key_error: Exception \| None` | `Mapping` | - | `value` |
| `isinstance (src/llm_wiki_cli/services…dation.py:require_mapping)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| governance_bundle_id_from_knowledge | validate_governance_projection | 2048 | `validate_governance_projection(knowledge)` |
| validate_governance_projection | isinstance (src/llm_wiki_cli/services…ate_governance_projection) | 1848 | `isinstance(knowledge, KnowledgeIndex)` |
| validate_governance_projection | TypeError (src/llm_wiki_cli/services…ate_governance_projection) | 1849 | `TypeError('knowledge must be a KnowledgeIndex')` |
| validate_governance_projection | knowledge.extensions.get (src/llm_wiki_cli/services…ate_governance_projection) | 1850 | `knowledge.extensions.get(GOVERNANCE_EXTENSION_KEY)` |
| validate_governance_projection | knowledge.bundle.snapshot.extensions.get | 1851 | `knowledge.bundle.snapshot.extensions.get(GOVERNANCE_HASH_EXTENSION_KEY)` |
| validate_governance_projection | concept.extensions.get | 1855 | `concept.extensions.get(GOVERNANCE_EXTENSION_KEY)` |
| validate_governance_projection | any (src/llm_wiki_cli/services…ate_governance_projection) | 1859 | `any(...)` |
| validate_governance_projection | GovernanceError | 1862 | `GovernanceError('extensions', 'contains an incomplete governance projection', code='governance-projection-mismatch')` |
| validate_governance_projection | _object (src/llm_wiki_cli/services/knowledge_governance.py) | 1868 | `_object(raw, 'governance_projection')` |
| _object (src/llm_wiki_cli/services/knowledge_governance.py) | require_mapping | 3173 | `require_mapping(value, error=GovernanceError(...), require_string_keys=True, key_error=GovernanceError(...))` |
| require_mapping | isinstance (src/llm_wiki_cli/services…dation.py:require_mapping) | 765 | `isinstance(value, Mapping)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `declared_limits.add` | `validate_governance_projection` | 1953 |
| mutation | `seen_uids.add` | `validate_governance_projection` | 1960 |
| mutation | `successor_pairs.add` | `validate_governance_projection` | 1975 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_projection` | `isinstance` | 1848 |
| external_call | `validate_governance_projection` | `TypeError` | 1849 |
| unresolved_call | `validate_governance_projection` | `knowledge.extensions.get` | 1850 |
| unresolved_call | `validate_governance_projection` | `knowledge.bundle.snapshot.extensions.get` | 1851 |
| unresolved_call | `validate_governance_projection` | `concept.extensions.get` | 1855 |
| external_call | `validate_governance_projection` | `any` | 1859 |
| external_call | `require_mapping` | `isinstance` | 765 |
| step_limit | `governance_bundle_id_from_knowledge` | `first 12 steps` | 0 |
| truncated_flow | `governance_bundle_id_from_knowledge` | `depth limit` | 0 |

## Behavior

This flow starts at `governance_bundle_id_from_knowledge` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
