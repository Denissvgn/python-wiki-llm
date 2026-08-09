# runtime_generation_options

**Entry point:** `runtime_generation_options` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [knowledge_generation](../modules/knowledge_generation.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as runtime_generation_options
    participant p1 as surface_value
    participant p2 as isinstance
    participant p3 as sorted
    participant p4 as str
    participant p5 as _runtime_policy_from_generation_inputs
    participant p6 as KnowledgeGenerationError
    participant p7 as dict
    participant p8 as _validate_runtime_policy
    participant p9 as set
    participant p10 as min
    participant p11 as bool
    p0-->>p1: surface_value
    p0-->>p2: isinstance
    p0-->>p3: sorted
    p0-->>p4: str
    p0->>p5: _runtime_policy_from_generation_inputs
    p5-->>p2: isinstance
    p5->>p6: KnowledgeGenerationError
    p5-->>p7: dict
    p5->>p8: _validate_runtime_policy
    p8-->>p9: set
    p8-->>p3: sorted
    p8-->>p10: min
    p8->>p6: KnowledgeGenerationError
    p8-->>p2: isinstance
    p8->>p6: KnowledgeGenerationError
    p8-->>p2: isinstance
    p8->>p6: KnowledgeGenerationError
    p0-->>p11: bool
    p0-->>p1: surface_value
    p0-->>p11: bool
    p0-->>p1: surface_value
    p0-->>p11: bool
    p0-->>p1: surface_value
    p0-->>p1: surface_value
    p0-->>p11: bool
    p0-->>p1: surface_value
    p0-->>p3: sorted
    p0-->>p4: str
    p0-->>p11: bool
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. runtime_generation_options"]
    s2["2. surface_value"]
    s3["3. isinstance"]
    s4["4. sorted"]
    s5["5. str"]
    s6["6. _runtime_policy_from_generation_inputs"]
    s7["7. isinstance"]
    s8["8. KnowledgeGenerationError"]
    s9["9. dict"]
    s10["10. _validate_runtime_policy"]
    s11["11. set"]
    s12["12. sorted"]
    s1 -. "surface_value('flows', 'categories', None)" .-> s2
    s1 -. "isinstance(raw_categories, (...))" .-> s3
    s1 -. "sorted(...)" .-> s4
    s1 -. "str(value)" .-> s5
    s1 -->|"_runtime_policy_from_generation_inputs(generation_inputs)"| s6
    s6 -. "isinstance(raw_policy, Mapping)" .-> s7
    s6 -->|"KnowledgeGenerationError(..., 'must be an object')"| s8
    s6 -. "dict(raw_policy)" .-> s9
    s6 -->|"_validate_runtime_policy(policy)"| s10
    s10 -. "set(policy)" .-> s11
    s10 -. "sorted(...)" .-> s12
    click s1 "../modules/knowledge_orchestration.md"
    click s6 "../modules/knowledge_orchestration.md"
    click s8 "../modules/knowledge_generation.md"
    click s10 "../modules/knowledge_orchestration.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `runtime_generation_options` | `surfaces: Mapping[str, Mapping[str, Any]]`, `generation_inputs: Mapping[str, object] \| None`, `include_tests: Iterable[str] \| None`, `preserve_semantic: bool` | `RUNTIME_GENERATION_OPTION_DEFAULTS`, `RUNTIME_GENERATION_OPTION_DEFAULTS` | - | `{...}` |
| `surface_value` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `sorted` | - | - | - | - |
| `str` | - | - | - | - |
| `_runtime_policy_from_generation_inputs` | `generation_inputs: Mapping[str, object] \| None` | `RUNTIME_GENERATION_INPUT_KEY`, `RUNTIME_GENERATION_INPUT_KEY`, `Mapping`, `RUNTIME_GENERATION_INPUT_KEY` | - | `None`, `policy` |
| `isinstance` | - | - | - | - |
| `KnowledgeGenerationError` | - | - | - | - |
| `dict` | - | - | - | - |
| `_validate_runtime_policy` | `policy: Mapping[str, object]` | `_RUNTIME_POLICY_KEYS`, `_RUNTIME_POLICY_KEYS`, `_RUNTIME_POLICY_KEYS`, `RUNTIME_GENERATION_INPUT_KEY`, `RUNTIME_GENERATION_INPUT_KEY`, `_DEPENDENCY_GRAPH_DETAILS`, `RUNTIME_GENERATION_INPUT_KEY` | - | - |
| `set` | - | - | - | - |
| `sorted` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| runtime_generation_options | surface_value | 914 | `surface_value('flows', 'categories', None)` |
| runtime_generation_options | isinstance | 917 | `isinstance(raw_categories, (...))` |
| runtime_generation_options | sorted | 916 | `sorted(...)` |
| runtime_generation_options | str | 916 | `str(value)` |
| runtime_generation_options | _runtime_policy_from_generation_inputs | 920 | `_runtime_policy_from_generation_inputs(generation_inputs)` |
| _runtime_policy_from_generation_inputs | isinstance | 1002 | `isinstance(raw_policy, Mapping)` |
| _runtime_policy_from_generation_inputs | KnowledgeGenerationError | 1003 | `KnowledgeGenerationError(..., 'must be an object')` |
| _runtime_policy_from_generation_inputs | dict | 1007 | `dict(raw_policy)` |
| _runtime_policy_from_generation_inputs | _validate_runtime_policy | 1008 | `_validate_runtime_policy(policy)` |
| _validate_runtime_policy | set | 1013 | `set(policy)` |
| _validate_runtime_policy | sorted | 1015 | `sorted(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `runtime_generation_options` | `surface_value` | 914 |
| unresolved_call | `runtime_generation_options` | `isinstance` | 917 |
| unresolved_call | `runtime_generation_options` | `sorted` | 916 |
| unresolved_call | `_runtime_policy_from_generation_inputs` | `isinstance` | 1002 |
| unresolved_call | `_validate_runtime_policy` | `sorted` | 1015 |
| step_limit | `runtime_generation_options` | `first 12 steps` | 0 |

## Behavior

This flow starts at `runtime_generation_options` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
