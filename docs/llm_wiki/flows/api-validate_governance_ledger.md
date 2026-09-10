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
    participant p1 as isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    participant p2 as TypeError
    participant p3 as GovernanceError
    participant p4 as _bundle_id
    participant p5 as validate_bundle_id
    participant p6 as _machine_text
    participant p7 as isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p8 as ConceptIdentityError
    participant p9 as len (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p10 as value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p11 as any (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p12 as character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p13 as unicodedata.normalize (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p14 as unicodedata.category(…).startswith (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p15 as unicodedata.category (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p16 as _BUNDLE_ID_RE.fullmatch
    participant p17 as text.casefold
    participant p18 as _looks_absolute_path
    participant p19 as value.startswith (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    participant p20 as _WINDOWS_ABSOLUTE_RE.match (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    participant p21 as _contains_uri_userinfo
    participant p22 as urlsplit
    p0-->>p1: isinstance (src/llm_wiki_cli/services…alidate_governance_ledger)
    p0-->>p2: TypeError
    p0->>p3: GovernanceError
    p0->>p4: _bundle_id
    p4->>p5: validate_bundle_id
    p5->>p6: _machine_text
    p6-->>p7: isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6->>p8: ConceptIdentityError
    p6-->>p9: len (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6->>p8: ConceptIdentityError
    p6-->>p10: value.strip (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6-->>p11: any (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6-->>p12: character.isspace (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6->>p8: ConceptIdentityError
    p6-->>p13: unicodedata.normalize (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6->>p8: ConceptIdentityError
    p6-->>p11: any (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6-->>p14: unicodedata.category(…).startswith (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6-->>p15: unicodedata.category (src/llm_wiki_cli/services…identity.py:_machine_text)
    p6->>p8: ConceptIdentityError
    p5-->>p16: _BUNDLE_ID_RE.fullmatch
    p5-->>p17: text.casefold
    p5->>p18: _looks_absolute_path
    p18-->>p19: value.startswith (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    p18-->>p20: _WINDOWS_ABSOLUTE_RE.match (src/llm_wiki_cli/services…y.py:_looks_absolute_path)
    p5->>p21: _contains_uri_userinfo
    p21-->>p22: urlsplit
    p5->>p8: ConceptIdentityError
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
| _machine_text | value.strip (src/llm_wiki_cli/services…identity.py:_machine_text) | 916 | `value.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `validate_governance_ledger` | `isinstance` | 523 |
| external_call | `validate_governance_ledger` | `TypeError` | 524 |
| external_call | `_machine_text` | `isinstance` | 912 |
| unresolved_call | `_machine_text` | `value.strip` | 916 |
| step_limit | `validate_governance_ledger` | `first 12 steps` | 0 |
| truncated_flow | `validate_governance_ledger` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_governance_ledger` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
