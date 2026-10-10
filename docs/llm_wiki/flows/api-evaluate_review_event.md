# evaluate_review_event

**Entry point:** `evaluate_review_event` (`api`)
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
    participant p0 as evaluate_review_event
    participant p1 as validate_governance_ledger
    participant p2 as isinstance (src/llm_wiki_cli/services….py:evaluate_review_event)
    participant p3 as TypeError (src/llm_wiki_cli/services….py:evaluate_review_event)
    participant p4 as _validate_review_event_fields
    participant p5 as concepts.get
    participant p6 as reasons.append
    participant p7 as _section_records_by_locator(…).get
    participant p8 as _section_records_by_locator
    participant p9 as section.get (src/llm_wiki_cli/services….py:evaluate_review_event)
    participant p10 as is_valid_sha256
    participant p11 as current_review_evidence
    participant p12 as ReviewValidity
    participant p13 as tuple (src/llm_wiki_cli/services….py:evaluate_review_event)
    participant p14 as isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p15 as knowledge.extensions.get
    participant p16 as isinstance (src/llm_wiki_cli/services…idence.py:is_valid_sha256)
    participant p17 as isinstance (src/llm_wiki_cli/services…y:current_review_evidence)
    participant p18 as TypeError (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p19 as isinstance (src/llm_wiki_cli/services…ection_records_by_locator)
    participant p20 as _SHA256_RE.fullmatch (src/llm_wiki_cli/services…idence.py:is_valid_sha256)
    participant p21 as TypeError (src/llm_wiki_cli/services…y:current_review_evidence)
    participant p22 as GovernanceError
    participant p23 as extension.get
    p0->>p1: validate_governance_ledger
    p0-->>p2: isinstance (src/llm_wiki_cli/services….py:evaluate_review_event)(event, ReviewEvent)
    p0-->>p3: TypeError (src/llm_wiki_cli/services….py:evaluate_review_event)('event must be a ReviewEvent')
    p0->>p4: _validate_review_event_fields
    p0-->>p2: isinstance (src/llm_wiki_cli/services….py:evaluate_review_event)(knowledge, KnowledgeIndex)
    p0-->>p3: TypeError (src/llm_wiki_cli/services….py:evaluate_review_event)('knowledge must be a KnowledgeIndex')
    p0-->>p5: concepts.get(allocation.locator)
    p0-->>p6: reasons.append('concept-missing')
    p0-->>p7: _section_records_by_locator(…).get(event.section_locator)
    p0->>p8: _section_records_by_locator
    p0-->>p6: reasons.append('section-missing')
    p0-->>p9: section.get (src/llm_wiki_cli/services….py:evaluate_review_event)('semantic_hash')
    p0->>p10: is_valid_sha256
    p0-->>p6: reasons.append('basis-incompatible')
    p0-->>p6: reasons.append('scope-changed')
    p0->>p11: current_review_evidence
    p0-->>p6: reasons.append('basis-incompatible')
    p0-->>p6: reasons.append('evidence-changed')
    p0->>p12: ReviewValidity
    p0-->>p13: tuple (src/llm_wiki_cli/services….py:evaluate_review_event)(...)
    p1-->>p14: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)(ledger, GovernanceLedger)
    p8-->>p15: knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY)
    p10-->>p16: isinstance (src/llm_wiki_cli/services…idence.py:is_valid_sha256)(value, str)
    p11-->>p17: isinstance (src/llm_wiki_cli/services…y:current_review_evidence)(concept, ConceptRecord)
    p1-->>p18: TypeError (src/llm_wiki_cli/services…alidate_governance_ledger)('ledger must be a GovernanceLedger')
    p8-->>p19: isinstance (src/llm_wiki_cli/services…ection_records_by_locator)(extension, Mapping)
    p10-->>p20: _SHA256_RE.fullmatch (src/llm_wiki_cli/services…idence.py:is_valid_sha256)(value)
    p11-->>p21: TypeError (src/llm_wiki_cli/services…y:current_review_evidence)('concept must be a ConceptRecord')
    p1->>p22: GovernanceError
    p8-->>p23: extension.get('pages')
```

> Call sequence diagram shows 30 of 357 interactions; 327 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 80 (69 omitted); unresolved 12 of 88 (76 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_governance.py:validate_governance_ledger` | 2 | [src/llm_wiki_cli/services/knowledge_governance.py](../modules/knowledge_governance.md) | internal | 26 |
| `src/llm_wiki_cli/services/knowledge_governance.py:_bundle_id` | 6 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 4 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 8 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_bundle_id` | 7 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_looks_absolute_path` | 25 | - | unresolved | 2 |
> Omission summary shows 8 of 97 groups; 89 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. evaluate_review_event"]
    s2["2. validate_governance_ledger"]
    s3["3. isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)"]
    s4["4. TypeError (src/llm_wiki_cli/services…alidate_governance_ledger)"]
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
    s2 -. "TypeError (src/llm_wiki_cli/services…alidate_governance_ledger)('ledger must be a GovernanceLedger')" .-> s4
    s2 -->|"GovernanceError('schema_version', ..., code='governance-version-unsupported')"| s5
    s2 -->|"_bundle_id(ledger.bundle_id, 'bundle_id')"| s6
    s6 -->|"validate_bundle_id(value)"| s7
    s7 -->|"_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s9
    s8 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s10
    s8 -. "len (src/llm_wiki_cli/services…identity.py:_machine_text)(value)" .-> s11
    s8 -->|"ConceptIdentityError(field, ...)"| s12
    b0["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b0
    b1["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b1
    b2["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b2
    b3["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b3
    b4["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b4
    b5["mutation reasons.append"]
    s1 -. "mutation reasons.append" .-> b5
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
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `evaluate_review_event` | `event: ReviewEvent`, `ledger: GovernanceLedger`, `knowledge: KnowledgeIndex` | `ReviewEvent`, `KnowledgeIndex` | - | `ReviewValidity(...)` |
| `validate_governance_ledger` | `ledger: GovernanceLedger`, `expected_bundle_id: str \| None` | `GovernanceLedger`, `GOVERNANCE_SCHEMA_VERSION`, `GOVERNANCE_SCHEMA_VERSION`, `GovernanceAllocation`, `ConceptIdentityError`, `ALIAS_NATURAL_KEY`, `ALIAS_LOCATOR`, `ALIAS_NATURAL_KEY` | `current_keys[...]`, `alias_counts[...]`, `alias_owners[...]` | `GovernanceLedger(...)` |
| `isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…alidate_governance_ledger)` | - | - | - | - |
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
| evaluate_review_event | validate_governance_ledger | 1576 | `validate_governance_ledger(ledger)` |
| validate_governance_ledger | isinstance (src/llm_wiki_cli/services…alidate_governance_ledger) | 525 | `isinstance(ledger, GovernanceLedger)` |
| validate_governance_ledger | TypeError (src/llm_wiki_cli/services…alidate_governance_ledger) | 526 | `TypeError('ledger must be a GovernanceLedger')` |
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
| mutation | `reasons.append` | `evaluate_review_event` | 1587 |
| mutation | `reasons.append` | `evaluate_review_event` | 1590 |
| mutation | `reasons.append` | `evaluate_review_event` | 1594 |
| mutation | `reasons.append` | `evaluate_review_event` | 1596 |
| mutation | `reasons.append` | `evaluate_review_event` | 1600 |
| mutation | `reasons.append` | `evaluate_review_event` | 1605 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 525 |
| external_call | `validate_governance_ledger` | `TypeError` | 526 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `evaluate_review_event` | `first 12 steps` | 0 |
| truncated_flow | `evaluate_review_event` | `depth limit` | 0 |

## Behavior

This flow starts at `evaluate_review_event` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
