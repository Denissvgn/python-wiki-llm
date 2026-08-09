# verification_summaries_for_concepts

**Entry point:** `verification_summaries_for_concepts` (`api`)
**Source:** [knowledge_verification](../modules/knowledge_verification.md)
**Modules touched:** [knowledge_verification](../modules/knowledge_verification.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as verification_summaries_for_concepts
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as MappingProxyType
    participant p4 as get
    participant p5 as _frozen_summaries
    participant p6 as dict
    participant p7 as sorted
    participant p8 as set
    participant p9 as values
    participant p10 as list
    participant p11 as _deep_copy
    participant p12 as str
    participant p13 as items
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: MappingProxyType
    p0-->>p4: get
    p0-->>p1: isinstance
    p0-->>p4: get
    p0-->>p1: isinstance
    p0-->>p3: MappingProxyType
    p0->>p5: _frozen_summaries
    p5-->>p3: MappingProxyType
    p5-->>p3: MappingProxyType
    p5-->>p6: dict
    p5-->>p7: sorted
    p0-->>p6: dict
    p0-->>p7: sorted
    p0-->>p8: set
    p0-->>p9: values
    p0-->>p10: list
    p0->>p11: _deep_copy
    p11-->>p1: isinstance
    p11-->>p12: str
    p11->>p11: _deep_copy
    p11-->>p7: sorted
    p11-->>p13: items
    p11-->>p12: str
    p11-->>p1: isinstance
    p11->>p11: _deep_copy
    p11-->>p1: isinstance
```

> Call sequence diagram shows 30 of 41 interactions; 11 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. verification_summaries_for_concepts"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. TypeError"]
    s6["6. MappingProxyType"]
    s7["7. get"]
    s8["8. isinstance"]
    s9["9. get"]
    s10["10. isinstance"]
    s11["11. MappingProxyType"]
    s12["12. _frozen_summaries"]
    s1 -. "isinstance(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError('knowledge_view must be a KnowledgeReadView')" .-> s3
    s1 -. "isinstance(selected, MachineVerificationReadView)" .-> s4
    s1 -. "TypeError('evaluated must be a MachineVerificationReadView')" .-> s5
    s1 -. "MappingProxyType({...})" .-> s6
    s1 -. "concept.extensions.get(GOVERNANCE_EXTENSION_KEY)" .-> s7
    s1 -. "isinstance(governance, Mapping)" .-> s8
    s1 -. "governance.get('uid')" .-> s9
    s1 -. "isinstance(uid, str)" .-> s10
    s1 -. "MappingProxyType({...})" .-> s11
    s1 -->|"_frozen_summaries(...)"| s12
    click s1 "../modules/knowledge_verification.md"
    click s12 "../modules/knowledge_verification.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `verification_summaries_for_concepts` | `knowledge_view: KnowledgeReadView`, `evaluated: MachineVerificationReadView \| None` | `KnowledgeReadView`, `MachineVerificationReadView`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability` | `concept_coordinates[...]` | `MappingProxyType(...)`, `MappingProxyType(...)`, `_frozen_summaries(...)`, `_frozen_summaries(...)`, `MappingProxyType(...)`, `MappingProxyType(...)`, `_frozen_summaries(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `MappingProxyType` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `MappingProxyType` | - | - | - | - |
| `_frozen_summaries` | `values: Mapping[str, Mapping[str, Any]]` | - | - | `MappingProxyType(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| verification_summaries_for_concepts | isinstance | 167 | `isinstance(knowledge_view, KnowledgeReadView)` |
| verification_summaries_for_concepts | TypeError | 168 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| verification_summaries_for_concepts | isinstance | 174 | `isinstance(selected, MachineVerificationReadView)` |
| verification_summaries_for_concepts | TypeError | 175 | `TypeError('evaluated must be a MachineVerificationReadView')` |
| verification_summaries_for_concepts | MappingProxyType | 178 | `MappingProxyType({...})` |
| verification_summaries_for_concepts | get | 181 | `concept.extensions.get(GOVERNANCE_EXTENSION_KEY)` |
| verification_summaries_for_concepts | isinstance | 182 | `isinstance(governance, Mapping)` |
| verification_summaries_for_concepts | get | 182 | `governance.get('uid')` |
| verification_summaries_for_concepts | isinstance | 184 | `isinstance(uid, str)` |
| verification_summaries_for_concepts | MappingProxyType | 191 | `MappingProxyType({...})` |
| verification_summaries_for_concepts | _frozen_summaries | 197 | `_frozen_summaries(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `verification_summaries_for_concepts` | `isinstance` | 167 |
| unresolved_call | `verification_summaries_for_concepts` | `TypeError` | 168 |
| unresolved_call | `verification_summaries_for_concepts` | `isinstance` | 174 |
| unresolved_call | `verification_summaries_for_concepts` | `TypeError` | 175 |
| external_call | `verification_summaries_for_concepts` | `MappingProxyType` | 178 |
| unresolved_call | `verification_summaries_for_concepts` | `concept.extensions.get` | 181 |
| unresolved_call | `verification_summaries_for_concepts` | `isinstance` | 182 |
| unresolved_call | `verification_summaries_for_concepts` | `governance.get` | 182 |
| unresolved_call | `verification_summaries_for_concepts` | `isinstance` | 184 |
| external_call | `verification_summaries_for_concepts` | `MappingProxyType` | 191 |
| step_limit | `verification_summaries_for_concepts` | `first 12 steps` | 0 |

## Behavior

This flow starts at `verification_summaries_for_concepts` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
