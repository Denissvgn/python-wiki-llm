# load_machine_verification_read_view

**Entry point:** `load_machine_verification_read_view` (`api`)
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
    participant p0 as load_machine_verification_read_view
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as MachineVerificationReadView
    participant p4 as load_verification_receipt
    participant p5 as Path
    participant p6 as first_unsafe_path_component
    participant p7 as fspath
    participant p8 as abspath
    participant p9 as is_absolute
    participant p10 as cwd
    participant p11 as list
    participant p12 as pop
    participant p13 as lstat
    participant p14 as getattr
    participant p15 as S_ISLNK
    participant p16 as bool
    participant p17 as trusted_symlink_owner
    participant p18 as callable
    participant p19 as readlink
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: MachineVerificationReadView
    p0->>p4: load_verification_receipt
    p4-->>p5: Path
    p4->>p6: first_unsafe_path_component
    p6-->>p5: Path
    p6-->>p7: fspath
    p6-->>p5: Path
    p6-->>p8: abspath
    p6-->>p9: is_absolute
    p6-->>p10: cwd
    p6-->>p5: Path
    p6-->>p11: list
    p6-->>p12: pop
    p6-->>p13: lstat
    p6-->>p14: getattr
    p6-->>p14: getattr
    p6-->>p15: S_ISLNK
    p6-->>p16: bool
    p6-->>p16: bool
    p6-->>p14: getattr
    p6-->>p17: trusted_symlink_owner
    p6-->>p18: callable
    p6-->>p14: getattr
    p6-->>p5: Path
    p6-->>p5: Path
    p6-->>p19: readlink
    p6-->>p9: is_absolute
    p6-->>p5: Path
```

> Call sequence diagram shows 30 of 271 interactions; 241 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. load_machine_verification_read_view"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. MachineVerificationReadView"]
    s5["5. load_verification_receipt"]
    s6["6. Path"]
    s7["7. first_unsafe_path_component"]
    s8["8. Path"]
    s9["9. fspath"]
    s10["10. Path"]
    s11["11. abspath"]
    s12["12. is_absolute"]
    s1 -. "isinstance(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError('knowledge_view must be a KnowledgeReadView')" .-> s3
    s1 -->|"MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')"| s4
    s1 -->|"load_verification_receipt(Path(...))"| s5
    s5 -. "Path(wiki_dir)" .-> s6
    s5 -->|"first_unsafe_path_component(root)"| s7
    s7 -. "Path(os.fspath(...))" .-> s8
    s7 -. "os.fspath(path)" .-> s9
    s7 -. "Path(os.path.abspath(...))" .-> s10
    s7 -. "os.path.abspath(lexical)" .-> s11
    s7 -. "lexical.is_absolute(data not statically known)" .-> s12
    b0["mutation pending_parts.pop"]
    s7 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/knowledge_verification.md"
    click s4 "../modules/knowledge_consumption.md"
    click s5 "../modules/verification_contracts.md"
    click s7 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `load_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability` | - | `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `MachineVerificationReadView` | - | - | - | - |
| `load_verification_receipt` | `wiki_dir: str \| Path`, `missing_ok: bool` | - | - | `None`, `deserialize_verification_receipt(...)` |
| `Path` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path` | - | - | - | - |
| `fspath` | - | - | - | - |
| `Path` | - | - | - | - |
| `abspath` | - | - | - | - |
| `is_absolute` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| load_machine_verification_read_view | isinstance | 75 | `isinstance(knowledge_view, KnowledgeReadView)` |
| load_machine_verification_read_view | TypeError | 76 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| load_machine_verification_read_view | MachineVerificationReadView | 80 | `MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')` |
| load_machine_verification_read_view | load_verification_receipt | 86 | `load_verification_receipt(Path(...))` |
| load_verification_receipt | Path | 956 | `Path(wiki_dir)` |
| load_verification_receipt | first_unsafe_path_component | 957 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path | 50 | `Path(os.fspath(...))` |
| first_unsafe_path_component | fspath | 50 | `os.fspath(path)` |
| first_unsafe_path_component | Path | 58 | `Path(os.path.abspath(...))` |
| first_unsafe_path_component | abspath | 58 | `os.path.abspath(lexical)` |
| first_unsafe_path_component | is_absolute | 59 | `lexical.is_absolute(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 70 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `load_machine_verification_read_view` | `isinstance` | 75 |
| unresolved_call | `load_machine_verification_read_view` | `TypeError` | 76 |
| external_call | `first_unsafe_path_component` | `os.fspath` | 50 |
| external_call | `first_unsafe_path_component` | `os.path.abspath` | 58 |
| unresolved_call | `first_unsafe_path_component` | `lexical.is_absolute` | 59 |
| step_limit | `load_machine_verification_read_view` | `first 12 steps` | 0 |
| truncated_flow | `load_machine_verification_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `load_machine_verification_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
