# move_concept

**Entry point:** `move_concept` (`api`)
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
    participant p0 as move_concept
    participant p1 as validate_governance_ledger
    participant p2 as _existing_uid
    participant p3 as _concept_kind
    participant p4 as GovernanceError
    participant p5 as ConceptGovernanceReference
    participant p6 as _identity_value
    participant p7 as dict (src/llm_wiki_cli/services…overnance.py:move_concept)
    participant p8 as allocations.items (src/llm_wiki_cli/services…overnance.py:move_concept)
    participant p9 as _identity_ownership_key
    participant p10 as tuple (src/llm_wiki_cli/services…overnance.py:move_concept)
    participant p11 as aliases.items (src/llm_wiki_cli/services…overnance.py:move_concept)
    participant p12 as aliases.pop
    participant p13 as GovernanceAllocation
    participant p14 as _put_alias
    participant p15 as GovernanceAlias
    participant p16 as replace
    participant p17 as isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p18 as TypeError
    participant p19 as allocations.items (src/llm_wiki_cli/services…_governance.py:_put_alias)
    p0->>p1: validate_governance_ledger
    p0->>p2: _existing_uid
    p0->>p3: _concept_kind
    p0->>p4: GovernanceError
    p0->>p5: ConceptGovernanceReference
    p0->>p6: _identity_value
    p0->>p6: _identity_value
    p0-->>p7: dict (src/llm_wiki_cli/services…overnance.py:move_concept)(current.aliases)
    p0-->>p7: dict (src/llm_wiki_cli/services…overnance.py:move_concept)(current.concepts)
    p0-->>p8: allocations.items (src/llm_wiki_cli/services…overnance.py:move_concept)
    p0->>p9: _identity_ownership_key
    p0->>p9: _identity_ownership_key
    p0->>p4: GovernanceError
    p0->>p4: GovernanceError
    p0->>p9: _identity_ownership_key
    p0-->>p10: tuple (src/llm_wiki_cli/services…overnance.py:move_concept)(aliases.items(...))
    p0-->>p11: aliases.items (src/llm_wiki_cli/services…overnance.py:move_concept)
    p0->>p9: _identity_ownership_key
    p0-->>p12: aliases.pop(promoted_key)
    p0->>p13: GovernanceAllocation
    p0->>p14: _put_alias
    p0->>p15: GovernanceAlias
    p0->>p14: _put_alias
    p0->>p15: GovernanceAlias
    p0->>p1: validate_governance_ledger
    p0-->>p16: replace(current, concepts=allocations, aliases=aliases)
    p1-->>p17: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)
    p14->>p9: _identity_ownership_key
    p1-->>p18: TypeError('ledger must be a GovernanceLedger')
    p14-->>p19: allocations.items (src/llm_wiki_cli/services…_governance.py:_put_alias)
```

> Call sequence diagram shows 30 of 352 interactions; 322 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 6 of 70 (64 omitted); unresolved 4 of 79 (75 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_ledger` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 27 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_bundle_id` | 6 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 4 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 25 | - | unresolved | 2 |
> Omission summary shows 8 of 96 groups; 88 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. move_concept"]
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
    b0["mutation aliases.pop"]
    s1 -. "mutation aliases.pop" .-> b0
    click s1 "../modules/knowledge_governance.md"
    click s2 "../modules/knowledge_governance.md"
    click s5 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s7 "../modules/concept_identity.md"
    click s8 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `move_concept` | `ledger: GovernanceLedger`, `uid: str`, `locator: str`, `natural_key: str`, `concept_kind: str \| None` | `ALIAS_LOCATOR`, `ALIAS_NATURAL_KEY`, `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_NATURAL_KEY`, `ALIAS_LOCATOR`, `ALIAS_NATURAL_KEY` | `allocations[...]` | `validate_governance_ledger(...)` |
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
| move_concept | validate_governance_ledger | 1120 | `validate_governance_ledger(ledger)` |
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

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `aliases.pop` | `move_concept` | 1177 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 525 |
| external_call | `validate_governance_ledger` | `TypeError` | 526 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `move_concept` | `first 12 steps` | 0 |
| truncated_flow | `move_concept` | `depth limit` | 0 |

## Behavior

This flow starts at `move_concept` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
