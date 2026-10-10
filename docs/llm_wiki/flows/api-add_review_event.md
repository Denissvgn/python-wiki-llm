# add_review_event

**Entry point:** `add_review_event` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), and 2 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as add_review_event
    participant p1 as validate_governance_ledger
    participant p2 as _existing_uid
    participant p3 as _section_locator
    participant p4 as selected_section.partition
    participant p5 as _identity_ownership_key
    participant p6 as GovernanceError
    participant p7 as _hash
    participant p8 as _review_evidence
    participant p9 as _actor
    participant p10 as _safe_name
    participant p11 as authored_event_time
    participant p12 as ReviewEvent
    participant p13 as replace
    participant p14 as _derived_event_id
    participant p15 as _review_event_digest_payload
    participant p16 as dict (src/llm_wiki_cli/services…nance.py:add_review_event)
    participant p17 as events.get
    participant p18 as isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p19 as TypeError
    participant p20 as _bundle_id
    participant p21 as dict (src/llm_wiki_cli/services…alidate_governance_ledger)
    p0->>p1: validate_governance_ledger
    p0->>p2: _existing_uid
    p0->>p3: _section_locator
    p0-->>p4: selected_section.partition(' section/')
    p0->>p5: _identity_ownership_key
    p0->>p5: _identity_ownership_key
    p0->>p6: GovernanceError
    p0->>p7: _hash
    p0->>p8: _review_evidence
    p0->>p9: _actor
    p0->>p10: _safe_name
    p0->>p10: _safe_name
    p0->>p11: authored_event_time
    p0->>p12: ReviewEvent
    p0-->>p13: replace(event, event_id=_derived_event_id(...))
    p0->>p14: _derived_event_id
    p0->>p15: _review_event_digest_payload
    p0-->>p16: dict (src/llm_wiki_cli/services…nance.py:add_review_event)(current.review_events)
    p0-->>p17: events.get(event_id)
    p0->>p6: GovernanceError
    p0->>p1: validate_governance_ledger
    p0-->>p13: replace(current, review_events=events)
    p1-->>p18: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)
    p1-->>p19: TypeError('ledger must be a GovernanceLedger')
    p1->>p6: GovernanceError
    p1->>p20: _bundle_id
    p1->>p6: GovernanceError
    p1-->>p21: dict (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger.concepts)
    p1-->>p21: dict (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger.aliases)
    p1-->>p21: dict (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger.lifecycle_events)
```

> Call sequence diagram shows 30 of 341 interactions; 311 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 69 (61 omitted); unresolved 2 of 76 (74 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:_bundle_id` | 6 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 4 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 25 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 28 | - | external | 1 |
> Omission summary shows 8 of 94 groups; 86 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. add_review_event"]
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
| `add_review_event` | `ledger: GovernanceLedger`, `uid: str`, `section_locator: str`, `scope_hash: str`, `evidence: ReviewEvidence`, `reviewer: GovernanceActor`, `method: str`, `method_version: str` | `ALIAS_LOCATOR`, `ALIAS_LOCATOR` | `events[...]` | `validate_governance_ledger(...)` |
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
| add_review_event | validate_governance_ledger | 1369 | `validate_governance_ledger(ledger)` |
| validate_governance_ledger | isinstance (src/llm_wiki_cli/services…alidate_governance_ledger) | 525 | `isinstance(ledger, GovernanceLedger)` |
| validate_governance_ledger | TypeError | 526 | `TypeError('ledger must be a GovernanceLedger')` |
| validate_governance_ledger | GovernanceError | 528 | `GovernanceError('schema_version', ..., code='governance-version-unsupported')` |
| validate_governance_ledger | _bundle_id | 533 | `_bundle_id(ledger.bundle_id, 'bundle_id')` |
| _bundle_id | validate_bundle_id | 3367 | `validate_bundle_id(value)` |
| validate_bundle_id | _machine_text | 289 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 944 | `len(value)` |
| _machine_text | ConceptIdentityError | 945 | `ConceptIdentityError(field, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 525 |
| external_call | `validate_governance_ledger` | `TypeError` | 526 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `add_review_event` | `first 12 steps` | 0 |
| truncated_flow | `add_review_event` | `depth limit` | 0 |

## Behavior

This flow starts at `add_review_event` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
