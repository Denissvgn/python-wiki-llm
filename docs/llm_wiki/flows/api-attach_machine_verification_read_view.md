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

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as attach_machine_verification_read_view
    participant p1 as isinstance (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p2 as TypeError (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p3 as replace
    participant p4 as load_machine_verification_read_view
    participant p5 as isinstance (src/llm_wiki_cli/services…verification_read_view, 1)
    participant p6 as TypeError (src/llm_wiki_cli/services…verification_read_view, 1)
    participant p7 as MachineVerificationReadView
    participant p8 as load_verification_receipt
    participant p9 as Path (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p10 as context
    participant p11 as concept.extensions.get
    participant p12 as governance.get
    participant p13 as hash_json(…).removeprefix
    participant p14 as hash_json
    participant p15 as evaluate_verification_receipt
    participant p16 as machine_verification_summary
    participant p17 as tuple (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p18 as bool (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p19 as MappingProxyType
    participant p20 as dict (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p21 as sorted (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p22 as summary[…].items
    participant p23 as Path (src/llm_wiki_cli/services…load_verification_receipt)
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…ne_verification_read_view)('knowledge_view must be a KnowledgeReadView')
    p0-->>p3: replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))
    p0->>p4: load_machine_verification_read_view
    p4-->>p5: isinstance (src/llm_wiki_cli/services…verification_read_view, 1)(knowledge_view, KnowledgeReadView)
    p4-->>p6: TypeError (src/llm_wiki_cli/services…verification_read_view, 1)('knowledge_view must be a KnowledgeReadView')
    p4->>p7: MachineVerificationReadView
    p4->>p8: load_verification_receipt
    p4-->>p9: Path (src/llm_wiki_cli/services…ne_verification_read_view)(wiki_dir)
    p4->>p7: MachineVerificationReadView
    p4->>p7: MachineVerificationReadView
    p4-->>p10: context(None)
    p4-->>p11: concept.extensions.get(GOVERNANCE_EXTENSION_KEY)
    p4-->>p5: isinstance (src/llm_wiki_cli/services…verification_read_view, 1)(governance, Mapping)
    p4-->>p12: governance.get('uid')
    p4-->>p5: isinstance (src/llm_wiki_cli/services…verification_read_view, 1)(uid, str)
    p4-->>p13: hash_json(…).removeprefix('sha256:')
    p4->>p14: hash_json
    p4-->>p10: context(selected_locator)
    p4->>p15: evaluate_verification_receipt
    p4->>p16: machine_verification_summary
    p4->>p7: MachineVerificationReadView
    p4-->>p17: tuple (src/llm_wiki_cli/services…ne_verification_read_view)(...)
    p4-->>p18: bool (src/llm_wiki_cli/services…ne_verification_read_view)(summary[...])
    p4-->>p19: MappingProxyType(...)
    p4-->>p19: MappingProxyType(dict(...))
    p4-->>p20: dict (src/llm_wiki_cli/services…ne_verification_read_view)(check_summary)
    p4-->>p21: sorted (src/llm_wiki_cli/services…ne_verification_read_view)(...)
    p4-->>p22: summary[…].items
    p8-->>p23: Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)
```

> Call sequence diagram shows 30 of 213 interactions; 183 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 15 of 81 (66 omitted); unresolved 6 of 31 (25 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 9 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 11 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 11 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 9 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 5 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 9 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:verification_receipt_path` | 40 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 42 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/verification_contracts.py:_read_regular_receipt` | 42 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 7 |
> Omission summary shows 8 of 45 groups; 37 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. attach_machine_verification_read_view"]
    s2["2. isinstance (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s3["3. TypeError (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s4["4. replace"]
    s5["5. load_machine_verification_read_view"]
    s6["6. isinstance (src/llm_wiki_cli/services…verification_read_view, 1)"]
    s7["7. TypeError (src/llm_wiki_cli/services…verification_read_view, 1)"]
    s8["8. MachineVerificationReadView"]
    s9["9. load_verification_receipt"]
    s10["10. Path (src/llm_wiki_cli/services…load_verification_receipt)"]
    s11["11. first_unsafe_path_component"]
    s12["12. Path (src/llm_wiki_cli/services…rst_unsafe_path_component)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…ne_verification_read_view)('knowledge_view must be a KnowledgeReadView')" .-> s3
    s1 -. "replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))" .-> s4
    s1 -->|"load_machine_verification_read_view(wiki_dir, knowledge_view)"| s5
    s5 -. "isinstance (src/llm_wiki_cli/services…verification_read_view, 1)(knowledge_view, KnowledgeReadView)" .-> s6
    s5 -. "TypeError (src/llm_wiki_cli/services…verification_read_view, 1)('knowledge_view must be a KnowledgeReadView')" .-> s7
    s5 -->|"MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')"| s8
    s5 -->|"load_verification_receipt(Path(...))"| s9
    s9 -. "Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)" .-> s10
    s9 -->|"first_unsafe_path_component(root)"| s11
    s11 -. "Path (src/llm_wiki_cli/services…rst_unsafe_path_component)(os.fspath(...))" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…ne_verification_read_view)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ne_verification_read_view)` | - | - | - | - |
| `replace` | - | - | - | - |
| `load_machine_verification_read_view` | `wiki_dir: str \| Path`, `knowledge_view: KnowledgeReadView` | `KnowledgeReadView`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `MachineVerificationAvailability`, `GOVERNANCE_EXTENSION_KEY`, `Mapping`, `MachineVerificationAvailability` | - | `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)`, `MachineVerificationReadView(...)` |
| `isinstance (src/llm_wiki_cli/services…verification_read_view, 1)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…verification_read_view, 1)` | - | - | - | - |
| `MachineVerificationReadView` | - | - | - | - |
| `load_verification_receipt` | `wiki_dir: str \| Path`, `missing_ok: bool` | - | - | `None`, `deserialize_verification_receipt(...)` |
| `Path (src/llm_wiki_cli/services…load_verification_receipt)` | - | - | - | - |
| `first_unsafe_path_component` | `path: str \| Path`, `trusted_symlink_uids: Set[int] \| None`, `trusted_symlink_owner: Callable[[Path], bool] \| None` | `stat`, `os` | - | `lexical`, `None`, `current`, `current`, `current`, `current`, `current`, `None` |
| `Path (src/llm_wiki_cli/services…rst_unsafe_path_component)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| attach_machine_verification_read_view | isinstance (src/llm_wiki_cli/services…ne_verification_read_view) | 53 | `isinstance(knowledge_view, KnowledgeReadView)` |
| attach_machine_verification_read_view | TypeError (src/llm_wiki_cli/services…ne_verification_read_view) | 54 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| attach_machine_verification_read_view | replace | 60 | `replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))` |
| attach_machine_verification_read_view | load_machine_verification_read_view | 62 | `load_machine_verification_read_view(wiki_dir, knowledge_view)` |
| load_machine_verification_read_view | isinstance (src/llm_wiki_cli/services…verification_read_view, 1) | 75 | `isinstance(knowledge_view, KnowledgeReadView)` |
| load_machine_verification_read_view | TypeError (src/llm_wiki_cli/services…verification_read_view, 1) | 76 | `TypeError('knowledge_view must be a KnowledgeReadView')` |
| load_machine_verification_read_view | MachineVerificationReadView | 80 | `MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')` |
| load_machine_verification_read_view | load_verification_receipt | 86 | `load_verification_receipt(Path(...))` |
| load_verification_receipt | Path (src/llm_wiki_cli/services…load_verification_receipt) | 956 | `Path(wiki_dir)` |
| load_verification_receipt | first_unsafe_path_component | 957 | `first_unsafe_path_component(root)` |
| first_unsafe_path_component | Path (src/llm_wiki_cli/services…rst_unsafe_path_component) | 51 | `Path(os.fspath(...))` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `pending_parts.pop` | `first_unsafe_path_component` | 71 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `attach_machine_verification_read_view` | `isinstance` | 53 |
| external_call | `attach_machine_verification_read_view` | `TypeError` | 54 |
| external_call | `attach_machine_verification_read_view` | `replace` | 60 |
| external_call | `load_machine_verification_read_view` | `isinstance` | 75 |
| external_call | `load_machine_verification_read_view` | `TypeError` | 76 |
| step_limit | `attach_machine_verification_read_view` | `first 12 steps` | 0 |
| truncated_flow | `attach_machine_verification_read_view` | `depth limit` | 0 |

## Behavior

This flow starts at `attach_machine_verification_read_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
