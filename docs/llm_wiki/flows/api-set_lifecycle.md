# set_lifecycle

**Entry point:** `set_lifecycle` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as set_lifecycle
    participant p1 as validate_governance_ledger
    participant p2 as current_lifecycle
    participant p3 as _existing_uid
    participant p4 as Lifecycle
    participant p5 as GovernanceError
    participant p6 as _actor
    participant p7 as authored_event_time
    participant p8 as _machine_code
    participant p9 as LifecycleEvent
    participant p10 as _derived_event_id
    participant p11 as _lifecycle_event_digest_payload
    participant p12 as _bundle_id
    participant p13 as _concept_uid
    participant p14 as _concept_kind
    participant p15 as _identity_value
    participant p16 as _identity_ownership_key
    participant p17 as _validate_lifecycle_event_fields
    participant p18 as _validate_lifecycle_histories
    participant p19 as _validate_review_event_fields
    participant p20 as validate_bundle_id
    participant p21 as validate_concept_uid
    participant p22 as validate_concept_kind
    participant p23 as _alias_type
    participant p24 as identity_coordinate_key
    participant p25 as _event_id
    participant p26 as validate_alias_value
    participant p27 as _section_locator
    participant p28 as _hash
    participant p29 as isinstance (src/llm_wiki_cli/services…vernance.py:set_lifecycle)
    participant p30 as events.get
    p0->>p1: validate_governance_ledger
    p0->>p2: current_lifecycle
    p0->>p3: _existing_uid
    p0->>p4: Lifecycle
    p0->>p5: GovernanceError
    p0->>p6: _actor
    p0->>p7: authored_event_time
    p0->>p8: _machine_code
    p0->>p9: LifecycleEvent
    p0->>p10: _derived_event_id
    p0->>p11: _lifecycle_event_digest_payload
    p1->>p12: _bundle_id
    p1->>p13: _concept_uid
    p1->>p14: _concept_kind
    p1->>p15: _identity_value
    p1->>p16: _identity_ownership_key
    p1->>p17: _validate_lifecycle_event_fields
    p1->>p18: _validate_lifecycle_histories
    p1->>p19: _validate_review_event_fields
    p12->>p20: validate_bundle_id
    p13->>p21: validate_concept_uid
    p14->>p22: validate_concept_kind
    p15->>p23: _alias_type
    p16->>p24: identity_coordinate_key
    p17->>p25: _event_id
    p15->>p26: validate_alias_value
    p19->>p27: _section_locator
    p19->>p28: _hash
    p0-->>p29: isinstance (src/llm_wiki_cli/services…vernance.py:set_lifecycle)(state, Lifecycle)
    p0-->>p30: events.get(event_id)
```

> Call sequence diagram shows 30 of 349 interactions; 319 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 71 (70 omitted); unresolved 1 of 76 (75 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_ledger` | 2 | - | external | 15 |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_ledger` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 19 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 4 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 25 | - | unresolved | 2 |
> Omission summary shows 8 of 94 groups; 86 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 203; effect analysis evaluated: 91, partial: 3, unavailable: 109. Counts include steps omitted from the displayed trace.

Collector observations for 94 source steps with known totals: observed: 472, emitted: 454, omitted: 18. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `set_lifecycle` | `available` | `evaluated` | `available` | `14` | `14` | `0` |
| `validate_governance_ledger` | `available` | `partial` | `available` | `20` | `14` | `6` |
| `isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `GovernanceError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `_bundle_id` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `validate_bundle_id` | `available` | `evaluated` | `available` | `3` | `3` | `0` |
| `_machine_text` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` | — | — | — |

```mermaid
flowchart LR
    s1["1. set_lifecycle"]
    s2["2. validate_governance_ledger"]
    s3["3. isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)"]
    s4["4. TypeError"]
    s5["5. GovernanceError"]
    s6["6. _bundle_id"]
    s7["7. validate_bundle_id"]
    s8["8. _machine_text"]
    s9["9. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s10["10. ConceptIdentityError"]
    s11["11. len (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s12["12. ConceptIdentityError"]
    s1 -->|"validate_governance_ledger(ledger)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)" .-> s3
    s2 -. "TypeError('ledger must be a GovernanceLedger')" .-> s4
    s2 -->|"GovernanceError('schema_version', ..., code='governance-version-unsupported')"| s5
    s2 -->|"_bundle_id(ledger.bundle_id, 'bundle_id')"| s6
    s6 -->|"validate_bundle_id(value)"| s7
    s7 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s9
    s8 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s10
    s8 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s11
    s8 -->|"ConceptIdentityError(field, ...)"| s12
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s5 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s7 "../modules/concept_identity.md"
    click s8 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `set_lifecycle` | `ledger: GovernanceLedger`, `uid: str`, `state: Lifecycle \| str`, `actor: GovernanceActor`, `authored_at: str \| datetime \| None`, `successor_uid: str \| None`, `reason: str` | `Lifecycle`, `Lifecycle`, `Lifecycle`, `_ALLOWED_TRANSITIONS` | `events[...]` | `current`, `validate_governance_ledger(...)` |
| `validate_governance_ledger` | `ledger: GovernanceLedger`, `expected_bundle_id: str \| None` | `GovernanceLedger`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_SCHEMA_VERSION`, `GovernanceAllocation`, `ConceptIdentityError`, `ALIAS_NATURAL_KEY`, `ALIAS_LOCATOR`, `ALIAS_NATURAL_KEY` | `current_keys[...]`, `alias_counts[...]`, `alias_owners[...]` | `GovernanceLedger(...)` |
| `isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `_bundle_id` | `value: object`, `path: str` | `ConceptIdentityError` | - | `validate_bundle_id(...)` |
| `validate_bundle_id` | `value: object` | `_MAX_BUNDLE_ID_LENGTH` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| set_lifecycle | validate_governance_ledger | 1286 | `validate_governance_ledger(ledger)` |
| validate_governance_ledger | isinstance (src/llm_wiki_cli/services…alidate_governance_ledger) | 526 | `isinstance(ledger, GovernanceLedger)` |
| validate_governance_ledger | TypeError | 527 | `TypeError('ledger must be a GovernanceLedger')` |
| validate_governance_ledger | GovernanceError | 529 | `GovernanceError('schema_version', ..., code='governance-version-unsupported')` |
| validate_governance_ledger | _bundle_id | 534 | `_bundle_id(ledger.bundle_id, 'bundle_id')` |
| _bundle_id | validate_bundle_id | 3474 | `validate_bundle_id(value)` |
| validate_bundle_id | _machine_text | 289 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 526 |
| external_call | `validate_governance_ledger` | `TypeError` | 527 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `set_lifecycle` | `first 12 steps` | 0 |
| truncated_flow | `set_lifecycle` | `depth limit` | 0 |

## Behavior

This flow starts at `set_lifecycle` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
