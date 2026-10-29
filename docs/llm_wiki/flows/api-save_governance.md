# save_governance

**Entry point:** `save_governance` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), and 4 more

**Complete modules touched:**

- [concept_identity](../modules/concept_identity.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [validation](../modules/validation.md)
- [wiki_media](../modules/wiki_media.md)
- [wiki_surface](../modules/wiki_surface.md)
- [wiki_write_basis](../modules/wiki_write_basis.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as save_governance
    participant p1 as validate_governance_ledger
    participant p2 as _read_governance_bytes
    participant p3 as _write_durable_atomic
    participant p4 as GovernanceError
    participant p5 as first_unsafe_path_component
    participant p6 as sha256_bytes
    participant p7 as is_valid_sha256
    participant p8 as GovernanceConflictError
    participant p9 as GovernanceWriteResult
    participant p10 as _bundle_id
    participant p11 as _concept_uid
    participant p12 as _concept_kind
    participant p13 as _identity_value
    participant p14 as _identity_ownership_key
    participant p15 as _validate_lifecycle_event_fields
    participant p16 as _validate_lifecycle_histories
    participant p17 as _validate_review_event_fields
    participant p18 as validate_bundle_id
    participant p19 as validate_concept_uid
    participant p20 as validate_concept_kind
    participant p21 as _alias_type
    participant p22 as identity_coordinate_key
    participant p23 as _event_id
    participant p24 as validate_alias_value
    participant p25 as _existing_uid
    participant p26 as _section_locator
    participant p27 as _hash
    participant p28 as _review_evidence
    participant p29 as len (src/llm_wiki_cli/services…rnance.py:save_governance)
    participant p30 as validated.to_bytes
    p0->>p1: validate_governance_ledger
    p0->>p2: _read_governance_bytes
    p0->>p3: _write_durable_atomic
    p0->>p4: GovernanceError
    p0->>p5: first_unsafe_path_component
    p0->>p6: sha256_bytes
    p0->>p7: is_valid_sha256
    p0->>p8: GovernanceConflictError
    p0->>p9: GovernanceWriteResult
    p1->>p10: _bundle_id
    p1->>p11: _concept_uid
    p1->>p12: _concept_kind
    p1->>p13: _identity_value
    p1->>p14: _identity_ownership_key
    p1->>p15: _validate_lifecycle_event_fields
    p1->>p16: _validate_lifecycle_histories
    p1->>p17: _validate_review_event_fields
    p10->>p18: validate_bundle_id
    p11->>p19: validate_concept_uid
    p12->>p20: validate_concept_kind
    p13->>p21: _alias_type
    p14->>p22: identity_coordinate_key
    p15->>p23: _event_id
    p13->>p24: validate_alias_value
    p15->>p25: _existing_uid
    p17->>p26: _section_locator
    p17->>p27: _hash
    p17->>p28: _review_evidence
    p0-->>p29: len (src/llm_wiki_cli/services…rnance.py:save_governance)(content)
    p0-->>p30: validated.to_bytes
```

> Call sequence diagram shows 30 of 426 interactions; 396 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 120 (119 omitted); unresolved 1 of 104 (103 omitted). These counts cover the captured static trace.

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
> Omission summary shows 8 of 108 groups; 100 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 203; effect analysis evaluated: 92, partial: 0, unavailable: 111. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `save_governance` | `available` | `evaluated` | `available` |
| `validate_governance_ledger` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `TypeError` | `not_applicable` | `not_applicable` | `not_applicable` |
| `GovernanceError` | `unavailable` | `unavailable` | `unavailable` |
| `_bundle_id` | `available` | `evaluated` | `available` |
| `validate_bundle_id` | `available` | `evaluated` | `available` |
| `_machine_text` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` |
| `len (src/llm_wiki_cli/services…identity.py:_machine_text)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `ConceptIdentityError` | `unavailable` | `unavailable` | `unavailable` |

```mermaid
flowchart LR
    s1["1. save_governance"]
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
| `save_governance` | `wiki_dir: str \| Path`, `ledger: GovernanceLedger`, `expected_hash: str \| None \| object`, `fault_injector: FaultInjector \| None` | `MAX_LEDGER_BYTES`, `GOVERNANCE_FILENAME`, `MAX_LEDGER_BYTES`, `GOVERNANCE_FILENAME`, `_MISSING`, `GOVERNANCE_FILENAME` | - | `GovernanceWriteResult(...)`, `GovernanceWriteResult(...)` |
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
| save_governance | validate_governance_ledger | 810 | `validate_governance_ledger(ledger)` |
| validate_governance_ledger | isinstance (src/llm_wiki_cli/services…alidate_governance_ledger) | 526 | `isinstance(ledger, GovernanceLedger)` |
| validate_governance_ledger | TypeError | 527 | `TypeError('ledger must be a GovernanceLedger')` |
| validate_governance_ledger | GovernanceError | 529 | `GovernanceError('schema_version', ..., code='governance-version-unsupported')` |
| validate_governance_ledger | _bundle_id | 534 | `_bundle_id(ledger.bundle_id, 'bundle_id')` |
| _bundle_id | validate_bundle_id | 3387 | `validate_bundle_id(value)` |
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
| step_limit | `save_governance` | `first 12 steps` | 0 |
| truncated_flow | `save_governance` | `depth limit` | 0 |

## Behavior

This flow starts at `save_governance` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
