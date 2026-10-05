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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_governance_ledger
    participant p1 as isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p2 as TypeError
    participant p3 as GovernanceError
    participant p4 as _bundle_id
    participant p5 as dict
    participant p6 as concepts.items
    participant p7 as _concept_uid
    participant p8 as _concept_kind
    participant p9 as ConceptAllocation
    participant p10 as _identity_value
    participant p11 as _identity_ownership_key
    participant p12 as current_keys.get
    participant p13 as defaultdict (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p14 as aliases.items
    p0-->>p1: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)
    p0-->>p2: TypeError('ledger must be a GovernanceLedger')
    p0->>p3: GovernanceError
    p0->>p4: _bundle_id
    p0->>p3: GovernanceError
    p0-->>p5: dict(ledger.concepts)
    p0-->>p5: dict(ledger.aliases)
    p0-->>p5: dict(ledger.lifecycle_events)
    p0-->>p5: dict(ledger.review_events)
    p0-->>p6: concepts.items
    p0-->>p1: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(allocation, GovernanceAllocation)
    p0->>p3: GovernanceError
    p0->>p3: GovernanceError
    p0->>p7: _concept_uid
    p0->>p8: _concept_kind
    p0->>p9: ConceptAllocation
    p0->>p3: GovernanceError
    p0->>p10: _identity_value
    p0->>p10: _identity_value
    p0->>p11: _identity_ownership_key
    p0-->>p12: current_keys.get(coordinate)
    p0->>p3: GovernanceError
    p0-->>p13: defaultdict (src/llm_wiki_cli/services…alidate_governance_ledger)(int)
    p0-->>p14: aliases.items
    p0-->>p1: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(alias, GovernanceAlias)
    p0->>p3: GovernanceError
    p0->>p3: GovernanceError
    p0->>p3: GovernanceError
    p0->>p3: GovernanceError
    p0->>p11: _identity_ownership_key
```

> Call sequence diagram shows 30 of 356 interactions; 326 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 9 of 76 (67 omitted); unresolved 3 of 92 (89 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:_bundle_id` | 5 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 6 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 4 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 7 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 7 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 6 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 24 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 27 | - | external | 1 |
> Omission summary shows 8 of 107 groups; 99 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_governance_ledger"]
    s2["2. isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)"]
    s3["3. TypeError"]
    s4["4. GovernanceError"]
    s5["5. _bundle_id"]
    s6["6. validate_bundle_id"]
    s7["7. _machine_text"]
    s8["8. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s9["9. ConceptIdentityError"]
    s10["10. len (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s11["11. ConceptIdentityError"]
    s12["12. value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)" .-> s2
    s1 -. "TypeError('ledger must be a GovernanceLedger')" .-> s3
    s1 -->|"GovernanceError('schema_version', ..., code='governance-version-unsupported')"| s4
    s1 -->|"_bundle_id(ledger.bundle_id, 'bundle_id')"| s5
    s5 -->|"validate_bundle_id(value)"| s6
    s6 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s7
    s7 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s8
    s7 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s9
    s7 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s10
    s7 -->|"ConceptIdentityError(field, ...)"| s11
    s7 -. "value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)(data not statically known)" .-> s12
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
| `value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
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
| _machine_text | value.strip (src/llm_wiki_cli/services…identity.py:_machine_text) | 946 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 525 |
| external_call | `validate_governance_ledger` | `TypeError` | 526 |
| external_call | `_machine_text` | `isinstance` | 942 |
| unresolved_call | `_machine_text` | `value.strip` | 946 |
| step_limit | `validate_governance_ledger` | `first 12 steps` | 0 |
| truncated_flow | `validate_governance_ledger` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_governance_ledger` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
