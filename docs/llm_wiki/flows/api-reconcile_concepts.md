# reconcile_concepts

**Entry point:** `reconcile_concepts` (`api`)
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
    participant p0 as reconcile_concepts
    participant p1 as validate_governance_ledger
    participant p2 as dict (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    participant p3 as _identity_ownership_key
    participant p4 as allocations.items (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    participant p5 as _validated_references
    participant p6 as sorted (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    participant p7 as (…).items
    participant p8 as _identity_value
    participant p9 as by_locator.get
    participant p10 as refs_by_locator.get
    participant p11 as GovernanceError
    participant p12 as by_natural_key.get
    participant p13 as tuple (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    participant p14 as aliases.items (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    participant p15 as aliases.pop
    participant p16 as GovernanceAllocation
    participant p17 as _put_alias
    participant p18 as GovernanceAlias
    p0->>p1: validate_governance_ledger
    p0-->>p2: dict (src/llm_wiki_cli/services…nce.py:reconcile_concepts)(current.concepts)
    p0-->>p2: dict (src/llm_wiki_cli/services…nce.py:reconcile_concepts)(current.aliases)
    p0->>p3: _identity_ownership_key
    p0-->>p4: allocations.items (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    p0-->>p4: allocations.items (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    p0->>p5: _validated_references
    p0->>p3: _identity_ownership_key
    p0-->>p6: sorted (src/llm_wiki_cli/services…nce.py:reconcile_concepts)(...)
    p0-->>p7: (…).items
    p0->>p8: _identity_value
    p0->>p8: _identity_value
    p0->>p3: _identity_ownership_key
    p0->>p3: _identity_ownership_key
    p0-->>p9: by_locator.get(old_coordinate)
    p0-->>p10: refs_by_locator.get(new_coordinate)
    p0->>p11: GovernanceError
    p0-->>p9: by_locator.get(new_coordinate)
    p0->>p11: GovernanceError
    p0->>p11: GovernanceError
    p0-->>p12: by_natural_key.get(target_reference.natural_key)
    p0->>p11: GovernanceError
    p0->>p3: _identity_ownership_key
    p0-->>p13: tuple (src/llm_wiki_cli/services…nce.py:reconcile_concepts)(aliases.items(...))
    p0-->>p14: aliases.items (src/llm_wiki_cli/services…nce.py:reconcile_concepts)
    p0->>p3: _identity_ownership_key
    p0-->>p15: aliases.pop(promoted_key)
    p0->>p16: GovernanceAllocation
    p0->>p17: _put_alias
    p0->>p18: GovernanceAlias
```

> Call sequence diagram shows 30 of 406 interactions; 376 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 82 (78 omitted); unresolved 9 of 97 (88 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_ledger` | 2 | - | external | 15 |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_ledger` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 27 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_bundle_id` | 6 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 4 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | - | unresolved | 2 |
> Omission summary shows 8 of 108 groups; 100 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. reconcile_concepts"]
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
    b1["mutation by_locator.pop"]
    s1 -. "mutation by_locator.pop" .-> b1
    b2["mutation by_natural_key.pop"]
    s1 -. "mutation by_natural_key.pop" .-> b2
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
    class b1 boundary
    class b2 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `reconcile_concepts` | `ledger: GovernanceLedger`, `concepts: Sequence[ConceptGovernanceReference]`, `moves: Mapping[str, str] \| None` | `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_LOCATOR`, `ALIAS_NATURAL_KEY` | `allocations[...]`, `by_natural_key[...]`, `allocations[...]`, `allocations[...]`, `by_natural_key[...]` | `validate_governance_ledger(...)` |
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
| reconcile_concepts | validate_governance_ledger | 942 | `validate_governance_ledger(ledger)` |
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
| mutation | `aliases.pop` | `reconcile_concepts` | 1022 |
| mutation | `by_locator.pop` | `reconcile_concepts` | 1040 |
| mutation | `by_natural_key.pop` | `reconcile_concepts` | 1050 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 525 |
| external_call | `validate_governance_ledger` | `TypeError` | 526 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `reconcile_concepts` | `first 12 steps` | 0 |
| truncated_flow | `reconcile_concepts` | `depth limit` | 0 |

## Behavior

This flow starts at `reconcile_concepts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
