# attach_machine_verification_read_view

**Entry point:** `attach_machine_verification_read_view` (`api`)
**Source:** [knowledge_verification](../modules/knowledge_verification.md)
**Modules touched:** [io](../modules/io.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_verification](../modules/knowledge_verification.md), and 2 more

**Complete modules touched:**

- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [validation](../modules/validation.md)
- [verification_contracts](../modules/verification_contracts.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as attach_machine_verification_read_view
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as replace
    participant p4 as load_machine_verification_read_view
    participant p5 as MachineVerificationReadView
    participant p6 as load_verification_receipt
    participant p7 as Path
    participant p8 as first_unsafe_path_component
    participant p9 as fspath
    participant p10 as abspath
    participant p11 as is_absolute
    participant p12 as cwd
    participant p13 as list
    participant p14 as pop
    participant p15 as lstat
    participant p16 as getattr
    participant p17 as S_ISLNK
    participant p18 as bool
    participant p19 as trusted_symlink_owner
    participant p20 as callable
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p3: replace
    p0->>p4: load_machine_verification_read_view
    p4-->>p1: isinstance
    p4-->>p2: TypeError
    p4->>p5: MachineVerificationReadView
    p4->>p6: load_verification_receipt
    p6-->>p7: Path
    p6->>p8: first_unsafe_path_component
    p8-->>p7: Path
    p8-->>p9: fspath
    p8-->>p7: Path
    p8-->>p10: abspath
    p8-->>p11: is_absolute
    p8-->>p12: cwd
    p8-->>p7: Path
    p8-->>p13: list
    p8-->>p14: pop
    p8-->>p15: lstat
    p8-->>p16: getattr
    p8-->>p16: getattr
    p8-->>p17: S_ISLNK
    p8-->>p18: bool
    p8-->>p18: bool
    p8-->>p16: getattr
    p8-->>p19: trusted_symlink_owner
    p8-->>p20: callable
    p8-->>p16: getattr
    p8-->>p7: Path
```

> Call sequence diagram shows 30 of 212 interactions; 182 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. attach_machine_verification_read_view"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. replace"]
    s5["5. load_machine_verification_read_view"]
    s6["6. isinstance"]
    s7["7. TypeError"]
    s8["8. MachineVerificationReadView"]
    s9["9. load_verification_receipt"]
    s10["10. Path"]
    s11["11. first_unsafe_path_component"]
    s12["12. Path"]
    s1 -. "isinstance(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError('knowledge_view must be a KnowledgeReadView')" .-> s3
    s1 -. "replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))" .-> s4
    s1 -->|"load_machine_verification_read_view(wiki_dir, knowledge_view)"| s5
    s5 -. "isinstance(knowledge_view, KnowledgeReadView)" .-> s6
    s5 -. "TypeError('knowledge_view must be a KnowledgeReadView')" .-> s7
    s5 -->|"MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')"| s8
    s5 -->|"load_verification_receipt(Path(...))"| s9
    s9 -. "Path(wiki_dir)" .-> s10
    s9 -->|"first_unsafe_path_component(root)"| s11
    s11 -. "Path(os.fspath(...))" .-> s12
    b0["mutation pending_parts.pop"]
    s11 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_verification.md"
    click s5 "../modules/knowledge_verification.md"
    click s8 "../modules/knowledge_consumption.md"
    click s9 "../modules/verification_contracts.md"
    click s11 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `attach_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability` | - | `knowledge_view`, `replace(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `replace` | - | - | - | - |
| `load_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability` | - | `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `MachineVerificationReadView` | - | - | - | - |
| `load_verification_receipt` | `wiki_dir: str \| Path`, `missing_ok: bool` | - | - | `None`, `deserialize_verification_receipt(...)` |
| `Path` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| attach_machine_verification_read_view | isinstance | 53 | `isinstance(knowledge_view, KnowledgeReadView)` |
| attach_machine_verification_read_view | TypeError | 54 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| attach_machine_verification_read_view | replace | 60 | `replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))` |
| attach_machine_verification_read_view | load_machine_verification_read_view | 62 | `load_machine_verification_read_view(wiki_dir, knowledge_view)` |
| load_machine_verification_read_view | isinstance | 75 | `isinstance(knowledge_view, KnowledgeReadView)` |
| load_machine_verification_read_view | TypeError | 76 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| load_machine_verification_read_view | MachineVerificationReadView | 80 | `MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')` |
| load_machine_verification_read_view | load_verification_receipt | 86 | `load_verification_receipt(Path(...))` |
| load_verification_receipt | Path | 956 | `Path(wiki_dir)` |
| load_verification_receipt | first_unsafe_path_component | 957 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path | 50 | `Path(os.fspath(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 70 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `attach_machine_verification_read_view` | `isinstance` | 53 |
| unresolved_call | `attach_machine_verification_read_view` | `TypeError` | 54 |
| external_call | `attach_machine_verification_read_view` | `replace` | 60 |
| unresolved_call | `load_machine_verification_read_view` | `isinstance` | 75 |
| unresolved_call | `load_machine_verification_read_view` | `TypeError` | 76 |
| step_limit | `attach_machine_verification_read_view` | `first 12 steps` | 0 |
| truncated_flow | `attach_machine_verification_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `attach_machine_verification_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
