# runtime_generation_options

**Entry point:** `runtime_generation_options` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [knowledge_generation](../modules/knowledge_generation.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as runtime_generation_options
    participant p1 as surface_value
    participant p2 as isinstance (src/llm_wiki_cli/services…runtime_generation_options)
    participant p3 as sorted (src/llm_wiki_cli/services…runtime_generation_options)
    participant p4 as str
    participant p5 as _runtime_policy_from_generation_inputs
    participant p6 as bool
    participant p7 as isinstance (src/llm_wiki_cli/services…icy_from_generation_inputs)
    participant p8 as KnowledgeGenerationError
    participant p9 as dict
    participant p10 as _validate_runtime_policy
    participant p11 as set
    participant p12 as sorted (src/llm_wiki_cli/services…y:_validate_runtime_policy)
    participant p13 as min
    participant p14 as isinstance (src/llm_wiki_cli/services…y:_validate_runtime_policy)
    p0-->>p1: surface_value('flows', 'categories', None)
    p0-->>p2: isinstance (src/llm_wiki_cli/services…runtime_generation_options)(raw_categories, (...))
    p0-->>p3: sorted (src/llm_wiki_cli/services…runtime_generation_options)(...)
    p0-->>p4: str(value)
    p0->>p5: _runtime_policy_from_generation_inputs
    p0-->>p6: bool(surface_value(...))
    p0-->>p1: surface_value('api_contracts', 'enabled', False)
    p0-->>p6: bool(surface_value(...))
    p0-->>p1: surface_value('dependencies', 'enabled', False)
    p0-->>p6: bool(...)
    p0-->>p1: surface_value('flows', 'exclude_tests', False)
    p0-->>p1: surface_value('dependencies', 'exclude_tests', False)
    p0-->>p6: bool(surface_value(...))
    p0-->>p1: surface_value('flows', 'enabled', False)
    p0-->>p3: sorted (src/llm_wiki_cli/services…runtime_generation_options)(...)
    p0-->>p4: str(value)
    p0-->>p6: bool(preserve_semantic)
    p5-->>p7: isinstance (src/llm_wiki_cli/services…icy_from_generation_inputs)(raw_policy, Mapping)
    p5->>p8: KnowledgeGenerationError
    p5-->>p9: dict(raw_policy)
    p5->>p10: _validate_runtime_policy
    p10-->>p11: set(policy)
    p10-->>p12: sorted (src/llm_wiki_cli/services…y:_validate_runtime_policy)(...)
    p10-->>p13: min(...)
    p10->>p8: KnowledgeGenerationError
    p10-->>p14: isinstance (src/llm_wiki_cli/services…y:_validate_runtime_policy)(policy[...], bool)
    p10->>p8: KnowledgeGenerationError
    p10-->>p14: isinstance (src/llm_wiki_cli/services…y:_validate_runtime_policy)(detail, str)
    p10->>p8: KnowledgeGenerationError
```

> Call sequence diagram shows 29 of 29 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 17 of 17 (0 omitted); unresolved 6 of 6 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. runtime_generation_options"]
    s2["2. surface_value"]
    s3["3. isinstance (src/llm_wiki_cli/services…runtime_generation_options)"]
    s4["4. sorted (src/llm_wiki_cli/services…runtime_generation_options)"]
    s5["5. str"]
    s6["6. _runtime_policy_from_generation_inputs"]
    s7["7. isinstance (src/llm_wiki_cli/services…icy_from_generation_inputs)"]
    s8["8. KnowledgeGenerationError"]
    s9["9. dict"]
    s10["10. _validate_runtime_policy"]
    s11["11. set"]
    s12["12. sorted (src/llm_wiki_cli/services…y:_validate_runtime_policy)"]
    s1 -. "surface_value('flows', 'categories', None)" .-> s2
    s1 -. "isinstance (src/llm_wiki_cli/services…runtime_generation_options)(raw_categories, (...))" .-> s3
    s1 -. "sorted (src/llm_wiki_cli/services…runtime_generation_options)(...)" .-> s4
    s1 -. "str(value)" .-> s5
    s1 -->|"_runtime_policy_from_generation_inputs(generation_inputs)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…icy_from_generation_inputs)(raw_policy, Mapping)" .-> s7
    s6 -->|"KnowledgeGenerationError(..., 'must be an object')"| s8
    s6 -. "dict(raw_policy)" .-> s9
    s6 -->|"_validate_runtime_policy(policy)"| s10
    s10 -. "set(policy)" .-> s11
    s10 -. "sorted (src/llm_wiki_cli/services…y:_validate_runtime_policy)(...)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…runtime_generation_options)` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…runtime_generation_options)` | - | - | - | - |
| `str` | - | - | - | - |
| `_runtime_policy_from_generation_inputs` | `generation_inputs: Mapping[str, object] \| None` | `RUNTIME_GENERATION_INPUT_KEY`, `RUNTIME_GENERATION_INPUT_KEY`, `Mapping`, `RUNTIME_GENERATION_INPUT_KEY` | - | `None`, `policy` |
| `isinstance (src/llm_wiki_cli/services…icy_from_generation_inputs)` | - | - | - | - |
| `KnowledgeGenerationError` | - | - | - | - |
| `dict` | - | - | - | - |
| `_validate_runtime_policy` | `policy: Mapping[str, object]` | `_RUNTIME_POLICY_KEYS`, `_RUNTIME_POLICY_KEYS`, `_RUNTIME_POLICY_KEYS`, `RUNTIME_GENERATION_INPUT_KEY`, `RUNTIME_GENERATION_INPUT_KEY`, `_DEPENDENCY_GRAPH_DETAILS`, `RUNTIME_GENERATION_INPUT_KEY` | - | - |
| `set` | - | - | - | - |
| `sorted (src/llm_wiki_cli/services…y:_validate_runtime_policy)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| runtime_generation_options | surface_value | 1148 | `surface_value('flows', 'categories', None)` |
| runtime_generation_options | isinstance (src/llm_wiki_cli/services…runtime_generation_options) | 1151 | `isinstance(raw_categories, (...))` |
| runtime_generation_options | sorted (src/llm_wiki_cli/services…runtime_generation_options) | 1150 | `sorted(...)` |
| runtime_generation_options | str | 1150 | `str(value)` |
| runtime_generation_options | _runtime_policy_from_generation_inputs | 1154 | `_runtime_policy_from_generation_inputs(generation_inputs)` |
| _runtime_policy_from_generation_inputs | isinstance (src/llm_wiki_cli/services…icy_from_generation_inputs) | 1236 | `isinstance(raw_policy, Mapping)` |
| _runtime_policy_from_generation_inputs | KnowledgeGenerationError | 1237 | `KnowledgeGenerationError(..., 'must be an object')` |
| _runtime_policy_from_generation_inputs | dict | 1241 | `dict(raw_policy)` |
| _runtime_policy_from_generation_inputs | _validate_runtime_policy | 1242 | `_validate_runtime_policy(policy)` |
| _validate_runtime_policy | set | 1247 | `set(policy)` |
| _validate_runtime_policy | sorted (src/llm_wiki_cli/services…y:_validate_runtime_policy) | 1249 | `sorted(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `runtime_generation_options` | `surface_value` | 1148 |
| external_call | `runtime_generation_options` | `isinstance` | 1151 |
| external_call | `runtime_generation_options` | `sorted` | 1150 |
| external_call | `_runtime_policy_from_generation_inputs` | `isinstance` | 1236 |
| external_call | `_validate_runtime_policy` | `sorted` | 1249 |
| step_limit | `runtime_generation_options` | `first 12 steps` | 0 |

## Behavior

This flow starts at `runtime_generation_options` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
