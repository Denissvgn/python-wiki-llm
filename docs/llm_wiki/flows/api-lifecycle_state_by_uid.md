# lifecycle_state_by_uid

**Entry point:** `lifecycle_state_by_uid` (`api`)
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
    participant p0 as lifecycle_state_by_uid
    participant p1 as validate_governance_ledger
    participant p2 as isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p3 as TypeError
    participant p4 as GovernanceError
    participant p5 as _bundle_id
    participant p6 as validate_bundle_id
    participant p7 as _machine_text
    participant p8 as isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p9 as ConceptIdentityError
    participant p10 as len (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p11 as value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p12 as any (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p13 as character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p14 as unicodedata.normalize (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p15 as unicodedata.category(…).startswith (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p16 as unicodedata.category (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p17 as _BUNDLE_ID_RE.fullmatch
    participant p18 as text.casefold
    participant p19 as _looks_absolute_path
    participant p20 as value.startswith (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    participant p21 as _WINDOWS_ABSOLUTE_RE.match (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    participant p22 as _contains_uri_userinfo
    participant p23 as urlsplit
    p0->>p1: validate_governance_ledger
    p1-->>p2: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    p1-->>p3: TypeError
    p1->>p4: GovernanceError
    p1->>p5: _bundle_id
    p5->>p6: validate_bundle_id
    p6->>p7: _machine_text
    p7-->>p8: isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7->>p9: ConceptIdentityError
    p7-->>p10: len (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7->>p9: ConceptIdentityError
    p7-->>p11: value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7-->>p12: any (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7-->>p13: character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7->>p9: ConceptIdentityError
    p7-->>p14: unicodedata.normalize (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7->>p9: ConceptIdentityError
    p7-->>p12: any (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7-->>p15: unicodedata.category(…).startswith (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7-->>p16: unicodedata.category (src/llm_wiki_cli/services…identity.py:_machine_text)
    p7->>p9: ConceptIdentityError
    p6-->>p17: _BUNDLE_ID_RE.fullmatch
    p6-->>p18: text.casefold
    p6->>p19: _looks_absolute_path
    p19-->>p20: value.startswith (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    p19-->>p21: _WINDOWS_ABSOLUTE_RE.match (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    p6->>p22: _contains_uri_userinfo
    p22-->>p23: urlsplit
    p6->>p9: ConceptIdentityError
    p5->>p4: GovernanceError
```

> Call sequence diagram shows 30 of 319 interactions; 289 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. lifecycle_state_by_uid"]
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
| `lifecycle_state_by_uid` | `ledger: GovernanceLedger` | - | `result[...]` | `result` |
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
| lifecycle_state_by_uid | validate_governance_ledger | 1444 | `validate_governance_ledger(ledger)` |
| validate_governance_ledger | isinstance (src/llm_wiki_cli/services…alidate_governance_ledger) | 523 | `isinstance(ledger, GovernanceLedger)` |
| validate_governance_ledger | TypeError | 524 | `TypeError('ledger must be a GovernanceLedger')` |
| validate_governance_ledger | GovernanceError | 526 | `GovernanceError('schema_version', ..., code='governance-version-unsupported')` |
| validate_governance_ledger | _bundle_id | 531 | `_bundle_id(ledger.bundle_id, 'bundle_id')` |
| _bundle_id | validate_bundle_id | 3357 | `validate_bundle_id(value)` |
| validate_bundle_id | _machine_text | 288 | `_machine_text(value, 'bundle_id', maximum=_MAX_BUNDLE_ID_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 912 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 913 | `ConceptIdentityError(field, 'must be a non-empty string')` |
| _machine_text | len (src/llm_wiki_cli/services…identity.py:_machine_text) | 914 | `len(value)` |
| _machine_text | ConceptIdentityError | 915 | `ConceptIdentityError(field, ...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 523 |
| external_call | `validate_governance_ledger` | `TypeError` | 524 |
| external_call | `_machine_text` | `isinstance` | 912 |
| step_limit | `lifecycle_state_by_uid` | `first 12 steps` | 0 |
| truncated_flow | `lifecycle_state_by_uid` | `depth limit` | 0 |

## Behavior

This flow starts at `lifecycle_state_by_uid` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
