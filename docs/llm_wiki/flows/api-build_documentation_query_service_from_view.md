# build_documentation_query_service_from_view

**Entry point:** `build_documentation_query_service_from_view` (`api`)
**Source:** [documentation_query_builder](../modules/documentation_query_builder.md)
**Modules touched:** [documentation_query_builder](../modules/documentation_query_builder.md), [io](../modules/io.md), [knowledge_consumption](../modules/knowledge_consumption.md), and 3 more

**Complete modules touched:**

- [documentation_query_builder](../modules/documentation_query_builder.md)
- [io](../modules/io.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [verification_contracts](../modules/verification_contracts.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as build_documentation_query_service_from_view
    participant p1 as attach_machine_verification_read_view
    participant p2 as assemble_documentation_query_service
    participant p3 as verification_summaries_for_concepts
    participant p4 as isinstance (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p5 as service_factory
    participant p6 as isinstance (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p7 as TypeError (src/llm_wiki_cli/services…ne_verification_read_view)
    participant p8 as TypeError (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p9 as replace
    participant p10 as load_machine_verification_read_view
    participant p11 as MappingProxyType (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p12 as concept.extensions.get (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p13 as governance.get (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p14 as _frozen_summaries
    participant p15 as dict (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p16 as sorted (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p17 as set
    participant p18 as concept_coordinates.values
    participant p19 as list (src/llm_wiki_cli/services…on_summaries_for_concepts)
    participant p20 as _deep_copy
    participant p21 as selected.checks.items
    p0->>p1: attach_machine_verification_read_view
    p0->>p2: assemble_documentation_query_service
    p0->>p3: verification_summaries_for_concepts
    p1-->>p4: isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)
    p2-->>p5: service_factory(…)
    p3-->>p6: isinstance (src/llm_wiki_cli/services…on_summaries_for_concepts)(knowledge_view, KnowledgeReadView)
    p1-->>p7: TypeError (src/llm_wiki_cli/services…ne_verification_read_view)('knowledge_view must be a KnowledgeReadView')
    p3-->>p8: TypeError (src/llm_wiki_cli/services…on_summaries_for_concepts)('knowledge_view must be a KnowledgeReadView')
    p1-->>p9: replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))
    p3-->>p6: isinstance (src/llm_wiki_cli/services…on_summaries_for_concepts)(selected, MachineVerificationReadView)
    p1->>p10: load_machine_verification_read_view
    p3-->>p8: TypeError (src/llm_wiki_cli/services…on_summaries_for_concepts)('evaluated must be a MachineVerificationReadView')
    p3-->>p11: MappingProxyType (src/llm_wiki_cli/services…on_summaries_for_concepts)({...})
    p3-->>p12: concept.extensions.get (src/llm_wiki_cli/services…on_summaries_for_concepts)(GOVERNANCE_EXTENSION_KEY)
    p3-->>p6: isinstance (src/llm_wiki_cli/services…on_summaries_for_concepts)(governance, Mapping)
    p3-->>p13: governance.get (src/llm_wiki_cli/services…on_summaries_for_concepts)('uid')
    p3-->>p6: isinstance (src/llm_wiki_cli/services…on_summaries_for_concepts)(uid, str)
    p3-->>p11: MappingProxyType (src/llm_wiki_cli/services…on_summaries_for_concepts)({...})
    p3->>p14: _frozen_summaries
    p3-->>p15: dict (src/llm_wiki_cli/services…on_summaries_for_concepts)(invalid)
    p3-->>p16: sorted (src/llm_wiki_cli/services…on_summaries_for_concepts)(set(...))
    p3-->>p17: set(concept_coordinates.values(...))
    p3-->>p18: concept_coordinates.values
    p3-->>p19: list (src/llm_wiki_cli/services…on_summaries_for_concepts)(selected.invalidation_reasons)
    p3->>p20: _deep_copy
    p3-->>p16: sorted (src/llm_wiki_cli/services…on_summaries_for_concepts)(selected.checks.items(...))
    p3-->>p21: selected.checks.items
    p3->>p14: _frozen_summaries
    p3-->>p11: MappingProxyType (src/llm_wiki_cli/services…on_summaries_for_concepts)({...})
    p3-->>p11: MappingProxyType (src/llm_wiki_cli/services…on_summaries_for_concepts)({...})
```

> Call sequence diagram shows 30 of 198 interactions; 168 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 18 of 95 (77 omitted); unresolved 5 of 33 (28 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_verification.py:load_machine_verification_read_view` | 6 | - | external | 11 |
| `src/llm_wiki_cli/services/knowledge_verification.py:load_machine_verification_read_view` | 6 | [src/llm_wiki_cli/services/knowledge_consumption.py](../modules/knowledge_consumption.md) | internal | 4 |
| `src/llm_wiki_cli/services/knowledge_verification.py:load_machine_verification_read_view` | 6 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 2 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 10 | - | external | 1 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 10 | [src/llm_wiki_cli/services/io.py](../modules/io.md) | internal | 1 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 12 | - | external | 20 |
| `src/llm_wiki_cli/services/io.py:first_unsafe_path_component` | 12 | - | unresolved | 5 |
| `src/llm_wiki_cli/services/verification_contracts.py:load_verification_receipt` | 10 | [src/llm_wiki_cli/services/verification_contracts.py](../modules/verification_contracts.md) | internal | 5 |
> Omission summary shows 8 of 37 groups; 29 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. build_documentation_query_service_from_view"]
    s2["2. attach_machine_verification_read_view"]
    s3["3. isinstance (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s4["4. TypeError (src/llm_wiki_cli/services…ne_verification_read_view)"]
    s5["5. replace"]
    s6["6. load_machine_verification_read_view"]
    s7["7. isinstance (src/llm_wiki_cli/services…verification_read_view, 1)"]
    s8["8. TypeError (src/llm_wiki_cli/services…verification_read_view, 1)"]
    s9["9. MachineVerificationReadView"]
    s10["10. load_verification_receipt"]
    s11["11. Path (src/llm_wiki_cli/services…load_verification_receipt)"]
    s12["12. first_unsafe_path_component"]
    s1 -->|"attach_machine_verification_read_view(wiki_root, knowledge_view)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…ne_verification_read_view)(knowledge_view, KnowledgeReadView)" .-> s3
    s2 -. "TypeError (src/llm_wiki_cli/services…ne_verification_read_view)('knowledge_view must be a KnowledgeReadView')" .-> s4
    s2 -. "replace(knowledge_view, machine_verification=load_machine_verification_read_view(...))" .-> s5
    s2 -->|"load_machine_verification_read_view(wiki_dir, knowledge_view)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…verification_read_view, 1)(knowledge_view, KnowledgeReadView)" .-> s7
    s6 -. "TypeError (src/llm_wiki_cli/services…verification_read_view, 1)('knowledge_view must be a KnowledgeReadView')" .-> s8
    s6 -->|"MachineVerificationReadView(availability=MachineVerificationAvailability.ABSENT, reason='verification-receipt-not-present')"| s9
    s6 -->|"load_verification_receipt(Path(...))"| s10
    s10 -. "Path (src/llm_wiki_cli/services…load_verification_receipt)(wiki_dir)" .-> s11
    s10 -->|"first_unsafe_path_component(root)"| s12
    b0["mutation pending_parts.pop"]
    s12 -. "mutation pending_parts.pop" .-> b0
    click s1 "../modules/documentation_query_builder.md"
    click s2 "../modules/knowledge_verification.md"
    click s6 "../modules/knowledge_verification.md"
    click s9 "../modules/knowledge_consumption.md"
    click s10 "../modules/verification_contracts.md"
    click s12 "../modules/io.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `build_documentation_query_service_from_view` | `wiki_root: Path`, `knowledge_view: KnowledgeReadView`, `limit: int`, `inventory: Mapping[str, Mapping[str, Any]] \| None`, `call_edges: Iterable[Mapping[str, Any]]`, `flows: Iterable[Mapping[str, Any]]`, `data_flows: object`, `dependency_analysis: Mapping[str, Any] \| None` | - | - | `assemble_documentation_query_service(...)` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| build_documentation_query_service_from_view | attach_machine_verification_read_view | 413 | `attach_machine_verification_read_view(wiki_root, knowledge_view)` |
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
| step_limit | `build_documentation_query_service_from_view` | `first 12 steps` | 0 |
| truncated_flow | `build_documentation_query_service_from_view` | `depth limit` | 0 |

## Behavior

This flow starts at `build_documentation_query_service_from_view` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
