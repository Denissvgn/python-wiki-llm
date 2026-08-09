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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as set_lifecycle
    participant p1 as validate_governance_ledger
    participant p2 as isinstance
    participant p3 as TypeError
    participant p4 as GovernanceError
    participant p5 as _bundle_id
    participant p6 as validate_bundle_id
    participant p7 as _machine_text
    participant p8 as ConceptIdentityError
    participant p9 as len
    participant p10 as strip
    participant p11 as any
    participant p12 as isspace
    participant p13 as normalize
    participant p14 as startswith
    participant p15 as category
    participant p16 as fullmatch
    participant p17 as casefold
    participant p18 as _looks_absolute_path
    participant p19 as match
    participant p20 as _contains_uri_userinfo
    participant p21 as urlsplit
    p0->>p1: validate_governance_ledger
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1->>p4: GovernanceError
    p1->>p5: _bundle_id
    p5->>p6: validate_bundle_id
    p6->>p7: _machine_text
    p7-->>p2: isinstance
    p7->>p8: ConceptIdentityError
    p7-->>p9: len
    p7->>p8: ConceptIdentityError
    p7-->>p10: strip
    p7-->>p11: any
    p7-->>p12: isspace
    p7->>p8: ConceptIdentityError
    p7-->>p13: normalize
    p7->>p8: ConceptIdentityError
    p7-->>p11: any
    p7-->>p14: startswith
    p7-->>p15: category
    p7->>p8: ConceptIdentityError
    p6-->>p16: fullmatch
    p6-->>p17: casefold
    p6->>p18: _looks_absolute_path
    p18-->>p14: startswith
    p18-->>p19: match
    p6->>p20: _contains_uri_userinfo
    p20-->>p21: urlsplit
    p6->>p8: ConceptIdentityError
    p5->>p4: GovernanceError
```

> Call sequence diagram shows 30 of 342 interactions; 312 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. set_lifecycle"]
    s2["2. validate_governance_ledger"]
    s3["3. isinstance"]
    s4["4. TypeError"]
    s5["5. GovernanceError"]
    s6["6. _bundle_id"]
    s7["7. validate_bundle_id"]
    s8["8. _machine_text"]
    s9["9. isinstance"]
    s10["10. ConceptIdentityError"]
    s11["11. len"]
    s12["12. ConceptIdentityError"]
    s1 -->|"validate_governance_ledger(ledger)"| s2
    s2 -. "isinstance(ledger, GovernanceLedger)" .-> s3
    s2 -. "TypeError('ledger must be a GovernanceLedger')" .-> s4
    s2 -->|"GovernanceError('schema_version', ..., code='governance-version-unsupported')"| s5
    s2 -->|"_bundle_id(ledger.bundle_id, 'bundle_id')"| s6
    s6 -->|"validate_bundle_id(value)"| s7
    s7 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s8
    s8 -. "isinstance(value, str)" .-> s9
    s8 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s10
    s8 -. "len(value)" .-> s11
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
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `GovernanceError` | - | - | - | - |
| `_bundle_id` | `value: object`, `path: str` | `ConceptIdentityError` | - | `validate_bundle_id(...)` |
| `validate_bundle_id` | `value: object` | `_MAX_BUNDLE_ID_LENGTH` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |
| `len` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| set_lifecycle | validate_governance_ledger | 1260 | `validate_governance_ledger(ledger)` |
| validate_governance_ledger | isinstance | 523 | `isinstance(ledger, GovernanceLedger)` |
| validate_governance_ledger | TypeError | 524 | `TypeError('ledger must be a GovernanceLedger')` |
| validate_governance_ledger | GovernanceError | 526 | `GovernanceError('schema_version', ..., code='governance-version-unsupported')` |
| validate_governance_ledger | _bundle_id | 531 | `_bundle_id(ledger.bundle_id, 'bundle_id')` |
| _bundle_id | validate_bundle_id | 3357 | `validate_bundle_id(value)` |
| validate_bundle_id | _machine_text | 288 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len | 914 | `len(value)` |
| _machine_text | ConceptIdentityError | 915 | `ConceptIdentityError(field, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_governance_ledger` | `isinstance` | 523 |
| unresolved_call | `validate_governance_ledger` | `TypeError` | 524 |
| unresolved_call | `_machine_text` | `isinstance` | 912 |
| step_limit | `set_lifecycle` | `first 12 steps` | 0 |
| truncated_flow | `set_lifecycle` | `depth limit` | 0 |

## Behavior

This flow starts at `set_lifecycle` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
