# persist_runtime_generation_policy

**Entry point:** `persist_runtime_generation_policy` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [knowledge_generation](../modules/knowledge_generation.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as persist_runtime_generation_policy
    participant p1 as _validate_runtime_policy
    participant p2 as dict
    participant p3 as set
    participant p4 as sorted
    participant p5 as min
    participant p6 as KnowledgeGenerationError
    participant p7 as isinstance
    p0->>p1: _validate_runtime_policy
    p0-->>p2: dict(generation_inputs)
    p1-->>p3: set(policy)
    p1-->>p4: sorted(...)
    p1-->>p5: min(...)
    p1->>p6: KnowledgeGenerationError
    p1-->>p7: isinstance(policy[...], bool)
    p1->>p6: KnowledgeGenerationError
    p1-->>p7: isinstance(detail, str)
    p1->>p6: KnowledgeGenerationError
```

> Call sequence diagram shows 10 of 10 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 6 of 6 (0 omitted); unresolved 0 of 0 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. persist_runtime_generation_policy"]
    s2["2. _validate_runtime_policy"]
    s3["3. set"]
    s4["4. sorted"]
    s5["5. min"]
    s6["6. KnowledgeGenerationError"]
    s7["7. isinstance"]
    s8["8. KnowledgeGenerationError"]
    s9["9. isinstance"]
    s10["10. KnowledgeGenerationError"]
    s11["11. dict"]
    s1 -->|"_validate_runtime_policy(policy)"| s2
    s2 -. "set(policy)" .-> s3
    s2 -. "sorted(...)" .-> s4
    s2 -. "min(...)" .-> s5
    s2 -->|"KnowledgeGenerationError(..., message)"| s6
    s2 -. "isinstance(policy[...], bool)" .-> s7
    s2 -->|"KnowledgeGenerationError(..., 'must be a boolean')"| s8
    s2 -. "isinstance(detail, str)" .-> s9
    s2 -->|"KnowledgeGenerationError(..., 'must be one of: auto, module, package')"| s10
    s1 -. "dict(generation_inputs)" .-> s11
    click s1 "../modules/knowledge_orchestration.md"
    click s2 "../modules/knowledge_orchestration.md"
    click s6 "../modules/knowledge_generation.md"
    click s8 "../modules/knowledge_generation.md"
    click s10 "../modules/knowledge_generation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `persist_runtime_generation_policy` | `generation_inputs: Mapping[str, object]`, `data_flow_enabled: bool`, `dependency_graph_detail: str`, `workflows_enabled: bool` | - | `persisted[...]` | `persisted` |
| `_validate_runtime_policy` | `policy: Mapping[str, object]` | `_RUNTIME_POLICY_KEYS`, `_RUNTIME_POLICY_KEYS`, `_RUNTIME_POLICY_KEYS`, `RUNTIME_GENERATION_INPUT_KEY`, `RUNTIME_GENERATION_INPUT_KEY`, `_DEPENDENCY_GRAPH_DETAILS`, `RUNTIME_GENERATION_INPUT_KEY` | - | - |
| `set` | - | - | - | - |
| `sorted` | - | - | - | - |
| `min` | - | - | - | - |
| `KnowledgeGenerationError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeGenerationError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `KnowledgeGenerationError` | - | - | - | - |
| `dict` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| persist_runtime_generation_policy | _validate_runtime_policy | 1248 | `_validate_runtime_policy(policy)` |
| _validate_runtime_policy | set | 1274 | `set(policy)` |
| _validate_runtime_policy | sorted | 1276 | `sorted(...)` |
| _validate_runtime_policy | min | 1281 | `min(...)` |
| _validate_runtime_policy | KnowledgeGenerationError | 1283 | `KnowledgeGenerationError(..., message)` |
| _validate_runtime_policy | isinstance | 1288 | `isinstance(policy[...], bool)` |
| _validate_runtime_policy | KnowledgeGenerationError | 1289 | `KnowledgeGenerationError(..., 'must be a boolean')` |
| _validate_runtime_policy | isinstance | 1294 | `isinstance(detail, str)` |
| _validate_runtime_policy | KnowledgeGenerationError | 1295 | `KnowledgeGenerationError(..., 'must be one of: auto, module, package')` |
| persist_runtime_generation_policy | dict | 1249 | `dict(generation_inputs)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_validate_runtime_policy` | `sorted` | 1276 |
| external_call | `_validate_runtime_policy` | `min` | 1281 |
| external_call | `_validate_runtime_policy` | `isinstance` | 1288 |
| external_call | `_validate_runtime_policy` | `isinstance` | 1294 |

## Behavior

This flow starts at `persist_runtime_generation_policy` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
