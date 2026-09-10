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
    participant p1 as isinstance (src/llm_wiki_cli/services…ne_verification_summaries)
    participant p2 as MappingProxyType (src/llm_wiki_cli/services…ne_verification_summaries)
    participant p3 as attach_machine_verification_read_view
    participant p4 as isinstance (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p5 as TypeError (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p6 as replace
    participant p7 as load_machine_verification_read_view
    participant p8 as isinstance (src/llm_wiki_cli/services…verification_read_view, 1)
    participant p9 as TypeError (src/llm_wiki_cli/services…verification_read_view, 1)
    participant p10 as MachineVerificationReadView
    participant p11 as load_verification_receipt
    participant p12 as Path (src/llm_wiki_cli/services…load_verification_receipt)
    participant p13 as first_unsafe_path_component
    participant p14 as Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p15 as os.fspath
    participant p16 as os.path.abspath
    participant p17 as lexical.is_absolute
    participant p18 as Path.cwd
    participant p19 as list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p20 as pending_parts.pop
    participant p21 as current.lstat
    participant p22 as getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p23 as stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p24 as bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
    participant p25 as trusted_symlink_owner
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ne_verification_summaries)
    p0-->>p2: MappingProxyType (src/llm_wiki_cli/services…ne_verification_summaries)
    p0->>p3: attach_machine_verification_read_view
    p3-->>p4: isinstance (src/llm_wiki_cli/services…ne_verification_read_view)
    p3-->>p5: TypeError (src/llm_wiki_cli/services…ne_verification_read_view)
    p3-->>p6: replace
    p3->>p7: load_machine_verification_read_view
    p7-->>p8: isinstance (src/llm_wiki_cli/services…verification_read_view, 1)
    p7-->>p9: TypeError (src/llm_wiki_cli/services…verification_read_view, 1)
    p7->>p10: MachineVerificationReadView
    p7->>p11: load_verification_receipt
    p11-->>p12: Path (src/llm_wiki_cli/services…load_verification_receipt)
    p11->>p13: first_unsafe_path_component
    p13-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p15: os.fspath
    p13-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p16: os.path.abspath
    p13-->>p17: lexical.is_absolute
    p13-->>p18: Path.cwd
    p13-->>p14: Path (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p19: list (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p20: pending_parts.pop
    p13-->>p21: current.lstat
    p13-->>p22: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p22: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p23: stat.S_ISLNK (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p24: bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p24: bool (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p22: getattr (src/llm_wiki_cli/services…rst_unsafe_path_component)
    p13-->>p25: trusted_symlink_owner
```

> Call sequence diagram shows 30 of 198 interactions; 168 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. machine_verification_summaries"]
    s2["2. isinstance (src/llm_wiki_cli/services…ne_verification_summaries)"]
    s3["3. MappingProxyType (src/llm_wiki_cli/services…ne_verification_summaries)"]
    s4["4. attach_machine_verification_read_view"]
    s5["5. isinstance (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s6["6. TypeError (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s7["7. replace"]
    s8["8. load_machine_verification_read_view"]
    s9["9. isinstance (src/llm_wiki_cli/services…verification_read_view, 1)"]
    s10["10. TypeError (src/llm_wiki_cli/services…verification_read_view, 1)"]
    s11["11. MachineVerificationReadView"]
    s12["12. load_verification_receipt"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ne_verification_summaries)(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "MappingProxyType (src/llm_wiki_cli/services…ne_verification_summaries)({...})" .-> s3
    s1 -->|"attach_machine_verification_read_view(wiki_dir, knowledge_view)"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)" .-> s5
    s4 -. "TypeError (src/llm_wiki_cli/services…ne_verification_read_view)('knowledge_view must be a KnowledgeReadView')" .-> s6
    s4 -. "replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))" .-> s7
    s4 -->|"load_machine_verification_read_view(wiki_dir, knowledge_view)"| s8
    s8 -. "isinstance (src/llm_wiki_cli/services…verification_read_view, 1)(knowledge_view, KnowledgeReadView)" .-> s9
    s8 -. "TypeError (src/llm_wiki_cli/services…verification_read_view, 1)('knowledge_view must be a KnowledgeReadView')" .-> s10
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
| `isinstance (src/llm_wiki_cli/services…ne_verification_summaries)` | - | - | - | - |
| `MappingProxyType (src/llm_wiki_cli/services…ne_verification_summaries)` | - | - | - | - |
| `attach_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability` | - | `knowledge_view`, `replace(...)` |
| `isinstance (src/llm_wiki_cli/services…ne_verification_read_view)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ne_verification_read_view)` | - | - | - | - |
| `replace` | - | - | - | - |
| `load_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability` | - | `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)` |
| `isinstance (src/llm_wiki_cli/services…verification_read_view, 1)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…verification_read_view, 1)` | - | - | - | - |
| `MachineVerificationReadView` | - | - | - | - |
| `load_verification_receipt` | `wiki_dir: str \| Path`, `missing_ok: bool` | - | - | `None`, `deserialize_verification_receipt(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| machine_verification_summaries | isinstance (src/llm_wiki_cli/services…ne_verification_summaries) | 38 | `isinstance(knowledge_view, KnowledgeReadView)` |
| machine_verification_summaries | MappingProxyType (src/llm_wiki_cli/services…ne_verification_summaries) | 42 | `MappingProxyType({...})` |
| machine_verification_summaries | attach_machine_verification_read_view | 43 | `attach_machine_verification_read_view(wiki_dir, knowledge_view)` |
| attach_machine_verification_read_view | isinstance (src/llm_wiki_cli/services…ne_verification_read_view) | 53 | `isinstance(knowledge_view, KnowledgeReadView)` |
| attach_machine_verification_read_view | TypeError (src/llm_wiki_cli/services…ne_verification_read_view) | 54 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| attach_machine_verification_read_view | replace | 60 | `replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))` |
| attach_machine_verification_read_view | load_machine_verification_read_view | 62 | `load_machine_verification_read_view(wiki_dir, knowledge_view)` |
| load_machine_verification_read_view | isinstance (src/llm_wiki_cli/services…verification_read_view, 1) | 75 | `isinstance(knowledge_view, KnowledgeReadView)` |
| load_machine_verification_read_view | TypeError (src/llm_wiki_cli/services…verification_read_view, 1) | 76 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| load_machine_verification_read_view | MachineVerificationReadView | 80 | `MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')` |
| load_machine_verification_read_view | load_verification_receipt | 86 | `load_verification_receipt(Path(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `machine_verification_summaries` | `isinstance` | 38 |
| external_call | `machine_verification_summaries` | `MappingProxyType` | 42 |
| external_call | `attach_machine_verification_read_view` | `isinstance` | 53 |
| external_call | `attach_machine_verification_read_view` | `TypeError` | 54 |
| external_call | `attach_machine_verification_read_view` | `replace` | 60 |
| external_call | `load_machine_verification_read_view` | `isinstance` | 75 |
| external_call | `load_machine_verification_read_view` | `TypeError` | 76 |
| step_limit | `machine_verification_summaries` | `first 12 steps` | 0 |
| truncated_flow | `machine_verification_summaries` | `depth limit` | 0 |

## Behavior

This flow starts at `machine_verification_summaries` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
