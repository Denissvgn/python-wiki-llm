# validate_governance_ledger

**Entry point:** `validate_governance_ledger` (`api`)
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

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_governance_ledger
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as GovernanceError
    participant p4 as _bundle_id
    participant p5 as validate_bundle_id
    participant p6 as _machine_text
    participant p7 as ConceptIdentityError
    participant p8 as len
    participant p9 as strip
    participant p10 as any
    participant p11 as isspace
    participant p12 as normalize
    participant p13 as startswith
    participant p14 as category
    participant p15 as fullmatch
    participant p16 as casefold
    participant p17 as _looks_absolute_path
    participant p18 as match
    participant p19 as _contains_uri_userinfo
    participant p20 as urlsplit
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: GovernanceError
    p0->>p4: _bundle_id
    p4->>p5: validate_bundle_id
    p5->>p6: _machine_text
    p6-->>p1: isinstance
    p6->>p7: ConceptIdentityError
    p6-->>p8: len
    p6->>p7: ConceptIdentityError
    p6-->>p9: strip
    p6-->>p10: any
    p6-->>p11: isspace
    p6->>p7: ConceptIdentityError
    p6-->>p12: normalize
    p6->>p7: ConceptIdentityError
    p6-->>p10: any
    p6-->>p13: startswith
    p6-->>p14: category
    p6->>p7: ConceptIdentityError
    p5-->>p15: fullmatch
    p5-->>p16: casefold
    p5->>p17: _looks_absolute_path
    p17-->>p13: startswith
    p17-->>p18: match
    p5->>p19: _contains_uri_userinfo
    p19-->>p20: urlsplit
    p5->>p7: ConceptIdentityError
    p4->>p3: GovernanceError
    p0->>p3: GovernanceError
```

> Call sequence diagram shows 30 of 351 interactions; 321 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_governance_ledger"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. GovernanceError"]
    s5["5. _bundle_id"]
    s6["6. validate_bundle_id"]
    s7["7. _machine_text"]
    s8["8. isinstance"]
    s9["9. ConceptIdentityError"]
    s10["10. len"]
    s11["11. ConceptIdentityError"]
    s12["12. strip"]
    s1 -. "isinstance(ledger, GovernanceLedger)" .-> s2
    s1 -. "TypeError('ledger must be a GovernanceLedger')" .-> s3
    s1 -->|"GovernanceError('schema_version', ..., code='governance-version-unsupported')"| s4
    s1 -->|"_bundle_id(ledger.bundle_id, 'bundle_id')"| s5
    s5 -->|"validate_bundle_id(value)"| s6
    s6 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s7
    s7 -. "isinstance(value, str)" .-> s8
    s7 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s9
    s7 -. "len(value)" .-> s10
    s7 -->|"ConceptIdentityError(field, ...)"| s11
    s7 -. "value.strip(data not statically known)" .-> s12
    click s1 "../modules/knowledge_governance.md"
    click s4 "../modules/knowledge_governance.md"
    click s5 "../modules/knowledge_governance.md"
    click s6 "../modules/concept_identity.md"
    click s7 "../modules/concept_identity.md"
    click s9 "../modules/concept_identity.md"
    click s11 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
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
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _machine_text | strip | 916 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `validate_governance_ledger` | `isinstance` | 523 |
| unresolved_call | `validate_governance_ledger` | `TypeError` | 524 |
| unresolved_call | `_machine_text` | `isinstance` | 912 |
| unresolved_call | `_machine_text` | `value.strip` | 916 |
| step_limit | `validate_governance_ledger` | `first 12 steps` | 0 |
| truncated_flow | `validate_governance_ledger` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_governance_ledger` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
