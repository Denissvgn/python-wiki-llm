# machine_verification_summaries

**Entry point:** `machine_verification_summaries` (`api`)
**Source:** [knowledge_verification](../modules/knowledge_verification.md)
**Modules touched:** [io](../modules/io.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_verification](../modules/knowledge_verification.md), and 1 more

**Complete modules touched:**

- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as machine_verification_summaries
    participant p1 as isinstance
    participant p2 as MappingProxyType
    participant p3 as attach_machine_verification_read_view
    participant p4 as TypeError
    participant p5 as replace
    participant p6 as load_machine_verification_read_view
    participant p7 as MachineVerificationReadView
    participant p8 as load_verification_receipt
    participant p9 as Path
    participant p10 as first_unsafe_path_component
    participant p11 as fspath
    participant p12 as abspath
    participant p13 as is_absolute
    participant p14 as cwd
    participant p15 as list
    participant p16 as pop
    participant p17 as lstat
    participant p18 as getattr
    participant p19 as S_ISLNK
    participant p20 as bool
    participant p21 as trusted_symlink_owner
    p0-->>p1: isinstance
    p0-->>p2: MappingProxyType
    p0->>p3: attach_machine_verification_read_view
    p3-->>p1: isinstance
    p3-->>p4: TypeError
    p3-->>p5: replace
    p3->>p6: load_machine_verification_read_view
    p6-->>p1: isinstance
    p6-->>p4: TypeError
    p6->>p7: MachineVerificationReadView
    p6->>p8: load_verification_receipt
    p8-->>p9: Path
    p8->>p10: first_unsafe_path_component
    p10-->>p9: Path
    p10-->>p11: fspath
    p10-->>p9: Path
    p10-->>p12: abspath
    p10-->>p13: is_absolute
    p10-->>p14: cwd
    p10-->>p9: Path
    p10-->>p15: list
    p10-->>p16: pop
    p10-->>p17: lstat
    p10-->>p18: getattr
    p10-->>p18: getattr
    p10-->>p19: S_ISLNK
    p10-->>p20: bool
    p10-->>p20: bool
    p10-->>p18: getattr
    p10-->>p21: trusted_symlink_owner
```

> Call sequence diagram shows 30 of 197 interactions; 167 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. machine_verification_summaries"]
    s2["2. isinstance"]
    s3["3. MappingProxyType"]
    s4["4. attach_machine_verification_read_view"]
    s5["5. isinstance"]
    s6["6. TypeError"]
    s7["7. replace"]
    s8["8. load_machine_verification_read_view"]
    s9["9. isinstance"]
    s10["10. TypeError"]
    s11["11. MachineVerificationReadView"]
    s12["12. load_verification_receipt"]
    s1 -. "isinstance(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "MappingProxyType({...})" .-> s3
    s1 -->|"attach_machine_verification_read_view(wiki_dir, knowledge_view)"| s4
    s4 -. "isinstance(knowledge_view, KnowledgeReadView)" .-> s5
    s4 -. "TypeError('knowledge_view must be a KnowledgeReadView')" .-> s6
    s4 -. "replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))" .-> s7
    s4 -->|"load_machine_verification_read_view(wiki_dir, knowledge_view)"| s8
    s8 -. "isinstance(knowledge_view, KnowledgeReadView)" .-> s9
    s8 -. "TypeError('knowledge_view must be a KnowledgeReadView')" .-> s10
    s8 -->|"MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')"| s11
    s8 -->|"load_verification_receipt(Path(...))"| s12
    click s1 "../modules/knowledge_verification.md"
    click s4 "../modules/knowledge_verification.md"
    click s8 "../modules/knowledge_verification.md"
    click s11 "../modules/knowledge_consumption.md"
    click s12 "../modules/verification_contracts.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `machine_verification_summaries` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView` | - | `MappingProxyType(...)`, `verification_summaries_for_concepts(...)` |
| `isinstance` | - | - | - | - |
| `MappingProxyType` | - | - | - | - |
| `attach_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability` | - | `knowledge_view`, `replace(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `replace` | - | - | - | - |
| `load_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability` | - | `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `MachineVerificationReadView` | - | - | - | - |
| `load_verification_receipt` | `wiki_dir: str \| Path`, `missing_ok: bool` | - | - | `None`, `deserialize_verification_receipt(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| machine_verification_summaries | isinstance | 38 | `isinstance(knowledge_view, KnowledgeReadView)` |
| machine_verification_summaries | MappingProxyType | 42 | `MappingProxyType({...})` |
| machine_verification_summaries | attach_machine_verification_read_view | 43 | `attach_machine_verification_read_view(wiki_dir, knowledge_view)` |
| attach_machine_verification_read_view | isinstance | 53 | `isinstance(knowledge_view, KnowledgeReadView)` |
| attach_machine_verification_read_view | TypeError | 54 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| attach_machine_verification_read_view | replace | 60 | `replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))` |
| attach_machine_verification_read_view | load_machine_verification_read_view | 62 | `load_machine_verification_read_view(wiki_dir, knowledge_view)` |
| load_machine_verification_read_view | isinstance | 75 | `isinstance(knowledge_view, KnowledgeReadView)` |
| load_machine_verification_read_view | TypeError | 76 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| load_machine_verification_read_view | MachineVerificationReadView | 80 | `MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')` |
| load_machine_verification_read_view | load_verification_receipt | 86 | `load_verification_receipt(Path(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `machine_verification_summaries` | `isinstance` | 38 |
| external_call | `machine_verification_summaries` | `MappingProxyType` | 42 |
| unresolved_call | `attach_machine_verification_read_view` | `isinstance` | 53 |
| unresolved_call | `attach_machine_verification_read_view` | `TypeError` | 54 |
| external_call | `attach_machine_verification_read_view` | `replace` | 60 |
| unresolved_call | `load_machine_verification_read_view` | `isinstance` | 75 |
| unresolved_call | `load_machine_verification_read_view` | `TypeError` | 76 |
| step_limit | `machine_verification_summaries` | `first 12 steps` | 0 |
| truncated_flow | `machine_verification_summaries` | `depth limit` | 0 |

## Behavior

This flow starts at `machine_verification_summaries` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
