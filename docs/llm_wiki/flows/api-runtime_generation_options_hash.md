# runtime_generation_options_hash

**Entry point:** `runtime_generation_options_hash` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as runtime_generation_options_hash
    participant p1 as prepare_runtime_generation_options
    participant p2 as isinstance
    participant p3 as TypeError
    participant p4 as dict
    participant p5 as tuple
    participant p6 as fromkeys
    participant p7 as PreparedRuntimeGenerationOptions
    participant p8 as hash_generation_options
    participant p9 as KnowledgeEnvelopeError
    participant p10 as _normalized_allowlist
    participant p11 as any
    participant p12 as len
    participant p13 as set
    participant p14 as sorted
    participant p15 as _reject_unknown_option_keys
    p0->>p1: prepare_runtime_generation_options
    p1-->>p2: isinstance
    p1-->>p3: TypeError
    p1-->>p4: dict
    p1-->>p4: dict
    p1-->>p5: tuple
    p1-->>p6: fromkeys
    p1->>p7: PreparedRuntimeGenerationOptions
    p0-->>p5: tuple
    p0->>p8: hash_generation_options
    p8-->>p2: isinstance
    p8->>p9: KnowledgeEnvelopeError
    p8-->>p2: isinstance
    p8->>p9: KnowledgeEnvelopeError
    p8->>p10: _normalized_allowlist
    p10-->>p2: isinstance
    p10->>p9: KnowledgeEnvelopeError
    p10-->>p5: tuple
    p10->>p9: KnowledgeEnvelopeError
    p10-->>p11: any
    p10-->>p2: isinstance
    p10->>p9: KnowledgeEnvelopeError
    p10-->>p12: len
    p10-->>p12: len
    p10-->>p13: set
    p10->>p9: KnowledgeEnvelopeError
    p10-->>p5: tuple
    p10-->>p14: sorted
    p8->>p15: _reject_unknown_option_keys
    p15-->>p11: any
```

> Call sequence diagram shows 30 of 54 interactions; 24 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. runtime_generation_options_hash"]
    s2["2. prepare_runtime_generation_options"]
    s3["3. isinstance"]
    s4["4. TypeError"]
    s5["5. dict"]
    s6["6. dict"]
    s7["7. tuple"]
    s8["8. fromkeys"]
    s9["9. PreparedRuntimeGenerationOptions"]
    s10["10. tuple"]
    s11["11. hash_generation_options"]
    s12["12. isinstance"]
    s1 -->|"prepare_runtime_generation_options(generation_options, generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS, generation_option_allowlist=tuple(...), i…"| s2
    s2 -. "isinstance(inventory_complete, bool)" .-> s3
    s2 -. "TypeError('inventory_complete must be a boolean')" .-> s4
    s2 -. "dict(generation_options)" .-> s5
    s2 -. "dict(generation_option_defaults)" .-> s6
    s2 -. "tuple(dict.fromkeys(...))" .-> s7
    s2 -. "dict.fromkeys((...))" .-> s8
    s2 -->|"PreparedRuntimeGenerationOptions(values=values, defaults=defaults, allowlist=allowlist)"| s9
    s1 -. "tuple(RUNTIME_GENERATION_OPTION_DEFAULTS)" .-> s10
    s1 -->|"hash_generation_options(prepared.values, defaults=prepared.defaults, allowlist=prepared.allowlist)"| s11
    s11 -. "isinstance(values, Mapping)" .-> s12
    click s1 "../modules/knowledge_orchestration.md"
    click s2 "../modules/knowledge_orchestration.md"
    click s9 "../modules/knowledge_orchestration.md"
    click s11 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `runtime_generation_options_hash` | `generation_options: Mapping[str, Any]`, `inventory_complete: bool` | `RUNTIME_GENERATION_OPTION_DEFAULTS`, `RUNTIME_GENERATION_OPTION_DEFAULTS` | - | `hash_generation_options(...)` |
| `prepare_runtime_generation_options` | `generation_options: Mapping[str, Any]`, `generation_option_defaults: Mapping[str, Any]`, `generation_option_allowlist: Sequence[str]`, `inventory_complete: bool` | - | `values[...]`, `defaults[...]` | `PreparedRuntimeGenerationOptions(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `dict` | - | - | - | - |
| `dict` | - | - | - | - |
| `tuple` | - | - | - | - |
| `fromkeys` | - | - | - | - |
| `PreparedRuntimeGenerationOptions` | - | - | - | - |
| `tuple` | - | - | - | - |
| `hash_generation_options` | `values: Mapping[str, Any]`, `defaults: Mapping[str, Any]`, `allowlist: Iterable[str]` | `Mapping`, `Mapping`, `GENERATION_OPTIONS_DOMAIN` | `effective[...]`, `effective[...]` | `_hash_structured(...)` |
| `isinstance` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| runtime_generation_options_hash | prepare_runtime_generation_options | 960 | `prepare_runtime_generation_options(generation_options, generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS, generation_option_allowlist=tuple(...), inventory_complete=inventory_complete)` |
| prepare_runtime_generation_options | isinstance | 219 | `isinstance(inventory_complete, bool)` |
| prepare_runtime_generation_options | TypeError | 220 | `TypeError('inventory_complete must be a boolean')` |
| prepare_runtime_generation_options | dict | 221 | `dict(generation_options)` |
| prepare_runtime_generation_options | dict | 223 | `dict(generation_option_defaults)` |
| prepare_runtime_generation_options | tuple | 225 | `tuple(dict.fromkeys(...))` |
| prepare_runtime_generation_options | fromkeys | 226 | `dict.fromkeys((...))` |
| prepare_runtime_generation_options | PreparedRuntimeGenerationOptions | 228 | `PreparedRuntimeGenerationOptions(values=values, defaults=defaults, allowlist=allowlist)` |
| runtime_generation_options_hash | tuple | 963 | `tuple(RUNTIME_GENERATION_OPTION_DEFAULTS)` |
| runtime_generation_options_hash | hash_generation_options | 966 | `hash_generation_options(prepared.values, defaults=prepared.defaults, allowlist=prepared.allowlist)` |
| hash_generation_options | isinstance | 818 | `isinstance(values, Mapping)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `prepare_runtime_generation_options` | `isinstance` | 219 |
| unresolved_call | `prepare_runtime_generation_options` | `TypeError` | 220 |
| unresolved_call | `prepare_runtime_generation_options` | `dict.fromkeys` | 226 |
| unresolved_call | `hash_generation_options` | `isinstance` | 818 |
| step_limit | `runtime_generation_options_hash` | `first 12 steps` | 0 |

## Behavior

This flow starts at `runtime_generation_options_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
