# concept_references_from_knowledge

**Entry point:** `concept_references_from_knowledge` (`api`)
**Source:** [knowledge_governance](../modules/knowledge_governance.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [knowledge_governance](../modules/knowledge_governance.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as concept_references_from_knowledge
    participant p1 as isinstance (src/llm_wiki_cli/services…references_from_knowledge)
    participant p2 as TypeError
    participant p3 as references.append (src/llm_wiki_cli/services…references_from_knowledge)
    participant p4 as ConceptGovernanceReference
    participant p5 as natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)
    participant p6 as _validated_references
    participant p7 as natural_key_for (src/llm_wiki_cli/services/concept_identity.py)
    participant p8 as isinstance (src/llm_wiki_cli/services….py:_validated_references)
    participant p9 as GovernanceError
    participant p10 as set
    participant p11 as enumerate
    participant p12 as _identity_value
    participant p13 as _concept_kind
    participant p14 as seen_locators.add
    participant p15 as seen_keys.add
    participant p16 as references.append (src/llm_wiki_cli/services….py:_validated_references)
    participant p17 as tuple
    participant p18 as sorted
    participant p19 as item.locator.casefold
    participant p20 as validate_concept_kind
    p0-->>p1: isinstance (src/llm_wiki_cli/services…references_from_knowledge)(knowledge, KnowledgeIndex)
    p0-->>p2: TypeError('knowledge must be a KnowledgeIndex')
    p0-->>p1: isinstance (src/llm_wiki_cli/services…references_from_knowledge)(concept.concept_kind, ConceptKind)
    p0-->>p3: references.append (src/llm_wiki_cli/services…references_from_knowledge)(ConceptGovernanceReference(...))
    p0->>p4: ConceptGovernanceReference
    p0->>p5: natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)
    p0->>p6: _validated_references
    p5->>p7: natural_key_for (src/llm_wiki_cli/services/concept_identity.py)
    p6-->>p8: isinstance (src/llm_wiki_cli/services….py:_validated_references)(values, (...))
    p5->>p9: GovernanceError
    p6-->>p8: isinstance (src/llm_wiki_cli/services….py:_validated_references)(values, Sequence)
    p6->>p9: GovernanceError
    p6-->>p10: set
    p6-->>p10: set
    p6-->>p11: enumerate(values)
    p6-->>p8: isinstance (src/llm_wiki_cli/services….py:_validated_references)(value, ConceptGovernanceReference)
    p6->>p9: GovernanceError
    p6->>p4: ConceptGovernanceReference
    p6->>p12: _identity_value
    p6->>p13: _concept_kind
    p6->>p12: _identity_value
    p6->>p9: GovernanceError
    p6->>p9: GovernanceError
    p6-->>p14: seen_locators.add(reference.locator)
    p6-->>p15: seen_keys.add(reference.natural_key)
    p6-->>p16: references.append (src/llm_wiki_cli/services….py:_validated_references)(reference)
    p6-->>p17: tuple(sorted(...))
    p6-->>p18: sorted(references, key=...)
    p6-->>p19: item.locator.casefold
    p7->>p20: validate_concept_kind
```

> Call sequence diagram shows 30 of 203 interactions; 173 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 54 (43 omitted); unresolved 5 of 54 (49 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:validate_concept_kind` | 9 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 10 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 10 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 10 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_concept_kind` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:natural_key_for` | 8 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 1 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 27 | - | external | 7 |
| `src/llm_wiki_cli/services/validation.py:require_repository_relative_path` | 27 | [src/llm_wiki_cli/services/validation.py](../modules/validation.md) | internal | 4 |
> Omission summary shows 8 of 47 groups; 39 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. concept_references_from_knowledge"]
    s2["2. isinstance (src/llm_wiki_cli/services…references_from_knowledge)"]
    s3["3. TypeError"]
    s4["4. isinstance (src/llm_wiki_cli/services…references_from_knowledge)"]
    s5["5. references.append (src/llm_wiki_cli/services…references_from_knowledge)"]
    s6["6. ConceptGovernanceReference"]
    s7["7. natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)"]
    s8["8. natural_key_for (src/llm_wiki_cli/services/concept_identity.py)"]
    s9["9. validate_concept_kind"]
    s10["10. _machine_text"]
    s11["11. isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)"]
    s12["12. ConceptIdentityError"]
    s1 -. "isinstance (src/llm_wiki_cli/services…references_from_knowledge)(knowledge, KnowledgeIndex)" .-> s2
    s1 -. "TypeError('knowledge must be a KnowledgeIndex')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…references_from_knowledge)(concept.concept_kind, ConceptKind)" .-> s4
    s1 -. "references.append (src/llm_wiki_cli/services…references_from_knowledge)(ConceptGovernanceReference(...))" .-> s5
    s1 -->|"ConceptGovernanceReference(locator=concept.locator, concept_kind=kind, natural_key=natural_key_for(...))"| s6
    s1 -->|"natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)(kind, concept.document.canonical_path)"| s7
    s7 -->|"natural_key_for (src/llm_wiki_cli/services/concept_identity.py)(concept_kind, canonical_path)"| s8
    s8 -->|"validate_concept_kind(concept_kind)"| s9
    s9 -->|"_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)"| s10
    s10 -. "isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)(value, str)" .-> s11
    s10 -->|"ConceptIdentityError(field, 'must be a non-empty string')"| s12
    b0["mutation references.append"]
    s1 -. "mutation references.append" .-> b0
    click s1 "../modules/knowledge_governance.md"
    click s6 "../modules/knowledge_governance.md"
    click s7 "../modules/knowledge_governance.md"
    click s8 "../modules/concept_identity.md"
    click s9 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `concept_references_from_knowledge` | `knowledge: KnowledgeIndex` | `KnowledgeIndex`, `ConceptKind` | - | `_validated_references(...)` |
| `isinstance (src/llm_wiki_cli/services…references_from_knowledge)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…references_from_knowledge)` | - | - | - | - |
| `references.append (src/llm_wiki_cli/services…references_from_knowledge)` | - | - | - | - |
| `ConceptGovernanceReference` | - | - | - | - |
| `natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py)` | `concept_kind: str`, `canonical_path: str` | `ConceptIdentityError` | - | `_identity_natural_key_for(...)` |
| `natural_key_for (src/llm_wiki_cli/services/concept_identity.py)` | `concept_kind: str`, `canonical_path: str` | - | - | `validate_natural_key(...)` |
| `validate_concept_kind` | `value: object` | `_MAX_CONCEPT_KIND_LENGTH`, `_UID_TAG_BY_KIND` | - | `text` |
| `_machine_text` | `value: object`, `field: str`, `maximum: int` | - | - | `value` |
| `isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)` | - | - | - | - |
| `ConceptIdentityError` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| concept_references_from_knowledge | isinstance (src/llm_wiki_cli/services…references_from_knowledge) | 1474 | `isinstance(knowledge, KnowledgeIndex)` |
| concept_references_from_knowledge | TypeError | 1475 | `TypeError('knowledge must be a KnowledgeIndex')` |
| concept_references_from_knowledge | isinstance (src/llm_wiki_cli/services…references_from_knowledge) | 1480 | `isinstance(concept.concept_kind, ConceptKind)` |
| concept_references_from_knowledge | references.append (src/llm_wiki_cli/services…references_from_knowledge) | 1483 | `references.append(ConceptGovernanceReference(...))` |
| concept_references_from_knowledge | ConceptGovernanceReference | 1484 | `ConceptGovernanceReference(locator=concept.locator, concept_kind=kind, natural_key=natural_key_for(...))` |
| concept_references_from_knowledge | natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py) | 1487 | `natural_key_for(kind, concept.document.canonical_path)` |
| natural_key_for (src/llm_wiki_cli/services/knowledge_governance.py) | natural_key_for (src/llm_wiki_cli/services/concept_identity.py) | 396 | `_identity_natural_key_for(concept_kind, canonical_path)` |
| natural_key_for (src/llm_wiki_cli/services/concept_identity.py) | validate_concept_kind | 327 | `validate_concept_kind(concept_kind)` |
| validate_concept_kind | _machine_text | 306 | `_machine_text(value, 'concept_kind', maximum=_MAX_CONCEPT_KIND_LENGTH)` |
| _machine_text | isinstance (src/llm_wiki_cli/services…identity.py:_machine_text) | 942 | `isinstance(value, str)` |
| _machine_text | ConceptIdentityError | 943 | `ConceptIdentityError(field, 'must be a non-empty string')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `references.append` | `concept_references_from_knowledge` | 1483 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `concept_references_from_knowledge` | `isinstance` | 1474 |
| external_call | `concept_references_from_knowledge` | `TypeError` | 1475 |
| external_call | `concept_references_from_knowledge` | `isinstance` | 1480 |
| external_call | `_machine_text` | `isinstance` | 942 |
| step_limit | `concept_references_from_knowledge` | `first 12 steps` | 0 |
| truncated_flow | `concept_references_from_knowledge` | `depth limit` | 0 |

## Behavior

This flow starts at `concept_references_from_knowledge` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
