# verification_summaries_for_concepts

**Entry point:** `verification_summaries_for_concepts` (`api`)
**Source:** [knowledge_verification](../modules/knowledge_verification.md)
**Modules touched:** [knowledge_verification](../modules/knowledge_verification.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as verification_summaries_for_concepts
    participant p1 as _deep_copy
    participant p2 as _frozen_summaries
    participant p3 as isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)
    participant p4 as concept.extensions.get
    participant p5 as TypeError
    participant p6 as MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)
    participant p7 as governance.get
    participant p8 as dict (src/llm_wiki_cli/services…ion_summaries_for_concepts)
    participant p9 as sorted (src/llm_wiki_cli/services…ion_summaries_for_concepts)
    participant p10 as set
    participant p11 as concept_coordinates.values
    participant p12 as list
    participant p13 as selected.checks.items
    participant p14 as MappingProxyType (src/llm_wiki_cli/services…ation.py:_frozen_summaries)
    participant p15 as isinstance (src/llm_wiki_cli/services…verification.py:_deep_copy)
    participant p16 as str
    participant p17 as dict (src/llm_wiki_cli/services…ation.py:_frozen_summaries)
    p0->>p1: _deep_copy
    p0->>p2: _frozen_summaries
    p0-->>p3: isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(knowledge_view, KnowledgeReadView)
    p0-->>p4: concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
    p0-->>p5: TypeError('knowledge_view must be a KnowledgeReadView')
    p0-->>p3: isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(selected, MachineVerificationReadView)
    p0-->>p5: TypeError('evaluated must be a MachineVerificationReadView')
    p0-->>p6: MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)({...})
    p0-->>p3: isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(governance, Mapping)
    p0-->>p7: governance.get('uid')
    p0-->>p3: isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(uid, str)
    p0-->>p6: MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)({...})
    p0-->>p8: dict (src/llm_wiki_cli/services…ion_summaries_for_concepts)(invalid)
    p0-->>p9: sorted (src/llm_wiki_cli/services…ion_summaries_for_concepts)(set(...))
    p0-->>p10: set(concept_coordinates.values(...))
    p0-->>p11: concept_coordinates.values
    p0-->>p12: list(selected.invalidation_reasons)
    p0-->>p9: sorted (src/llm_wiki_cli/services…ion_summaries_for_concepts)(selected.checks.items(...))
    p0-->>p13: selected.checks.items
    p0-->>p6: MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)({...})
    p0-->>p6: MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)({...})
    p0-->>p8: dict (src/llm_wiki_cli/services…ion_summaries_for_concepts)(summary)
    p0-->>p9: sorted (src/llm_wiki_cli/services…ion_summaries_for_concepts)(set(...))
    p0-->>p10: set(concept_coordinates.values(...))
    p0-->>p11: concept_coordinates.values
    p2-->>p14: MappingProxyType (src/llm_wiki_cli/services…ation.py:_frozen_summaries)(...)
    p1-->>p15: isinstance (src/llm_wiki_cli/services…verification.py:_deep_copy)(value, Mapping)
    p2-->>p14: MappingProxyType (src/llm_wiki_cli/services…ation.py:_frozen_summaries)(dict(...))
    p1-->>p16: str(key)
    p2-->>p17: dict (src/llm_wiki_cli/services…ation.py:_frozen_summaries)(values[...])
```

> Call sequence diagram shows 30 of 41 interactions; 11 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 23 of 28 (5 omitted); unresolved 5 of 6 (1 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_verification.py:_frozen_summaries` | 12 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_verification.py:_deep_copy` | 22 | [src/llm_wiki_cli/services/knowledge_verification.py](../modules/knowledge_verification.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_verification.py:_deep_copy` | 22 | - | external | 4 |
| `src/llm_wiki_cli/services/knowledge_verification.py:_deep_copy` | 22 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_verification.py:verification_summaries_for_concepts` | 1 | [src/llm_wiki_cli/services/knowledge_verification.py](../modules/knowledge_verification.md) | internal | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. verification_summaries_for_concepts"]
    s2["2. isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)"]
    s3["3. TypeError"]
    s4["4. isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)"]
    s5["5. TypeError"]
    s6["6. MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)"]
    s7["7. concept.extensions.get"]
    s8["8. isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)"]
    s9["9. governance.get"]
    s10["10. isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)"]
    s11["11. MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)"]
    s12["12. _frozen_summaries"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError('knowledge_view must be a KnowledgeReadView')" .-> s3
    s1 -. "isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(selected, MachineVerificationReadView)" .-> s4
    s1 -. "TypeError('evaluated must be a MachineVerificationReadView')" .-> s5
    s1 -. "MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)({...})" .-> s6
    s1 -. "concept.extensions.get(GOVERNANCE_EXTENSION_KEY)" .-> s7
    s1 -. "isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(governance, Mapping)" .-> s8
    s1 -. "governance.get('uid')" .-> s9
    s1 -. "isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)(uid, str)" .-> s10
    s1 -. "MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)({...})" .-> s11
    s1 -->|"_frozen_summaries(...)"| s12
    click s1 "../modules/knowledge_verification.md"
    click s12 "../modules/knowledge_verification.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `verification_summaries_for_concepts` | `knowledge_view: KnowledgeReadView`, `evaluated: MachineVerificationReadView \| None` | `KnowledgeReadView`, `MachineVerificationReadView`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability` | `concept_coordinates[...]` | `MappingProxyType(...)`, `MappingProxyType(...)`, `_frozen_summaries(...)`, `_frozen_summaries(...)`, `MappingProxyType(...)`, `MappingProxyType(...)`, `_frozen_summaries(...)` |
| `isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)` | - | - | - | - |
| `concept.extensions.get` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)` | - | - | - | - |
| `governance.get` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts)` | - | - | - | - |
| `MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts)` | - | - | - | - |
| `_frozen_summaries` | `values: Mapping[str, Mapping[str, Any]]` | - | - | `MappingProxyType(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verification_summaries_for_concepts | isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts) | 167 | `isinstance(knowledge_view, KnowledgeReadView)` |
| verification_summaries_for_concepts | TypeError | 168 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| verification_summaries_for_concepts | isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts) | 174 | `isinstance(selected, MachineVerificationReadView)` |
| verification_summaries_for_concepts | TypeError | 175 | `TypeError('evaluated must be a MachineVerificationReadView')` |
| verification_summaries_for_concepts | MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts) | 178 | `MappingProxyType({...})` |
| verification_summaries_for_concepts | concept.extensions.get | 181 | `concept.extensions.get(GOVERNANCE_EXTENSION_KEY)` |
| verification_summaries_for_concepts | isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts) | 182 | `isinstance(governance, Mapping)` |
| verification_summaries_for_concepts | governance.get | 182 | `governance.get('uid')` |
| verification_summaries_for_concepts | isinstance (src/llm_wiki_cli/services…ion_summaries_for_concepts) | 184 | `isinstance(uid, str)` |
| verification_summaries_for_concepts | MappingProxyType (src/llm_wiki_cli/services…ion_summaries_for_concepts) | 191 | `MappingProxyType({...})` |
| verification_summaries_for_concepts | _frozen_summaries | 197 | `_frozen_summaries(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `verification_summaries_for_concepts` | `isinstance` | 167 |
| external_call | `verification_summaries_for_concepts` | `TypeError` | 168 |
| external_call | `verification_summaries_for_concepts` | `isinstance` | 174 |
| external_call | `verification_summaries_for_concepts` | `TypeError` | 175 |
| external_call | `verification_summaries_for_concepts` | `MappingProxyType` | 178 |
| unresolved_call | `verification_summaries_for_concepts` | `concept.extensions.get` | 181 |
| external_call | `verification_summaries_for_concepts` | `isinstance` | 182 |
| unresolved_call | `verification_summaries_for_concepts` | `governance.get` | 182 |
| external_call | `verification_summaries_for_concepts` | `isinstance` | 184 |
| external_call | `verification_summaries_for_concepts` | `MappingProxyType` | 191 |
| step_limit | `verification_summaries_for_concepts` | `first 12 steps` | 0 |

## Behavior

This flow starts at `verification_summaries_for_concepts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
