# runtime_generation_options_hash

**Entry point:** `runtime_generation_options_hash` (`api`)
**Source:** [knowledge_orchestration](../modules/knowledge_orchestration.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as runtime_generation_options_hash
    participant p1 as prepare_runtime_generation_options
    participant p2 as hash_generation_options
    participant p3 as _normalized_allowlist
    participant p4 as _reject_unknown_option_keys
    participant p5 as _hash_structured
    participant p6 as canonical_json_bytes
    participant p7 as KnowledgeEnvelopeError
    participant p8 as PreparedRuntimeGenerationOptions
    participant p9 as _reject_machine_local_paths
    participant p10 as _validate_json_tree
    participant p11 as sha256_bytes
    participant p12 as canonical_json_text
    participant p13 as tuple (src/llm_wiki_cli/services…me_generation_options_hash)
    participant p14 as payload.values
    participant p15 as isinstance (src/llm_wiki_cli/services…runtime_generation_options)
    participant p16 as isinstance (src/llm_wiki_cli/services…py:hash_generation_options)
    participant p17 as TypeError
    participant p18 as dict
    participant p19 as tuple (src/llm_wiki_cli/services…runtime_generation_options)
    participant p20 as dict.fromkeys
    participant p21 as isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)
    participant p22 as any (src/llm_wiki_cli/services…reject_unknown_option_keys)
    participant p23 as set (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p24 as isinstance (src/llm_wiki_cli/services…reject_unknown_option_keys)
    participant p25 as walk (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p26 as tuple (src/llm_wiki_cli/services…e.py:_normalized_allowlist)
    participant p27 as set (src/llm_wiki_cli/services…reject_unknown_option_keys)
    participant p28 as any (src/llm_wiki_cli/services…e.py:_normalized_allowlist)
    p0->>p1: prepare_runtime_generation_options
    p0->>p2: hash_generation_options
    p2->>p3: _normalized_allowlist
    p2->>p4: _reject_unknown_option_keys
    p2->>p5: _hash_structured
    p5->>p6: canonical_json_bytes
    p2->>p7: KnowledgeEnvelopeError
    p1->>p8: PreparedRuntimeGenerationOptions
    p2->>p9: _reject_machine_local_paths
    p5->>p10: _validate_json_tree
    p5->>p11: sha256_bytes
    p6->>p12: canonical_json_text
    p0-->>p13: tuple (src/llm_wiki_cli/services…me_generation_options_hash)(RUNTIME_GENERATION_OPTION_DEFAULTS)
    p5-->>p14: payload.values
    p1-->>p15: isinstance (src/llm_wiki_cli/services…runtime_generation_options)(inventory_complete, bool)
    p2-->>p16: isinstance (src/llm_wiki_cli/services…py:hash_generation_options)(values, Mapping)
    p1-->>p17: TypeError('inventory_complete must be a boolean')
    p1-->>p18: dict(generation_options)
    p2-->>p16: isinstance (src/llm_wiki_cli/services…py:hash_generation_options)(defaults, Mapping)
    p1-->>p18: dict(generation_option_defaults)
    p1-->>p19: tuple (src/llm_wiki_cli/services…runtime_generation_options)(dict.fromkeys(...))
    p1-->>p20: dict.fromkeys((...))
    p3-->>p21: isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(value, (...))
    p4-->>p22: any (src/llm_wiki_cli/services…reject_unknown_option_keys)(...)
    p9-->>p23: set (src/llm_wiki_cli/services…reject_machine_local_paths)
    p4-->>p24: isinstance (src/llm_wiki_cli/services…reject_unknown_option_keys)(key, str)
    p9-->>p25: walk (src/llm_wiki_cli/services…reject_machine_local_paths)(value, field_name)
    p3-->>p26: tuple (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(value)
    p4-->>p27: set (src/llm_wiki_cli/services…reject_unknown_option_keys)(value)
    p3-->>p28: any (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(...)
```

> Call sequence diagram shows 30 of 54 interactions; 24 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 27 (11 omitted); unresolved 2 of 5 (3 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_envelope.py:hash_generation_options` | 11 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_normalized_allowlist` | 16 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 4 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_normalized_allowlist` | 16 | - | external | 6 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_reject_unknown_option_keys` | 30 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_reject_unknown_option_keys` | 30 | - | external | 2 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validate_json_tree` | 45 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validate_json_tree` | 45 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 48 | - | unresolved | 1 |
> Omission summary shows 8 of 12 groups; 4 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. runtime_generation_options_hash"]
    s2["2. prepare_runtime_generation_options"]
    s3["3. isinstance (src/llm_wiki_cli/services…runtime_generation_options)"]
    s4["4. TypeError"]
    s5["5. dict"]
    s6["6. dict"]
    s7["7. tuple (src/llm_wiki_cli/services…runtime_generation_options)"]
    s8["8. dict.fromkeys"]
    s9["9. PreparedRuntimeGenerationOptions"]
    s10["10. tuple (src/llm_wiki_cli/services…me_generation_options_hash)"]
    s11["11. hash_generation_options"]
    s12["12. isinstance (src/llm_wiki_cli/services…py:hash_generation_options)"]
    s1 -->|"prepare_runtime_generation_options(…)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…runtime_generation_options)(inventory_complete, bool)" .-> s3
    s2 -. "TypeError('inventory_complete must be a boolean')" .-> s4
    s2 -. "dict(generation_options)" .-> s5
    s2 -. "dict(generation_option_defaults)" .-> s6
    s2 -. "tuple (src/llm_wiki_cli/services…runtime_generation_options)(dict.fromkeys(...))" .-> s7
    s2 -. "dict.fromkeys((...))" .-> s8
    s2 -->|"PreparedRuntimeGenerationOptions(values=values, defaults=defaults, allowlist=allowlist)"| s9
    s1 -. "tuple (src/llm_wiki_cli/services…me_generation_options_hash)(RUNTIME_GENERATION_OPTION_DEFAULTS)" .-> s10
    s1 -->|"hash_generation_options(prepared.values, defaults=prepared.defaults, allowlist=prepared.allowlist)"| s11
    s11 -. "isinstance (src/llm_wiki_cli/services…py:hash_generation_options)(values, Mapping)" .-> s12
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
| `isinstance (src/llm_wiki_cli/services…runtime_generation_options)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `dict` | - | - | - | - |
| `dict` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…runtime_generation_options)` | - | - | - | - |
| `dict.fromkeys` | - | - | - | - |
| `PreparedRuntimeGenerationOptions` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…me_generation_options_hash)` | - | - | - | - |
| `hash_generation_options` | `values: Mapping[str, Any]`, `defaults: Mapping[str, Any]`, `allowlist: Iterable[str]` | `Mapping`, `Mapping`, `GENERATION_OPTIONS_DOMAIN` | `effective[...]`, `effective[...]` | `_hash_structured(...)` |
| `isinstance (src/llm_wiki_cli/services…py:hash_generation_options)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| runtime_generation_options_hash | prepare_runtime_generation_options | 1221 | `prepare_runtime_generation_options(generation_options, generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS, generation_option_allowlist=tuple(...), inventory_complete=inventory_complete)` |
| prepare_runtime_generation_options | isinstance (src/llm_wiki_cli/services…runtime_generation_options) | 345 | `isinstance(inventory_complete, bool)` |
| prepare_runtime_generation_options | TypeError | 346 | `TypeError('inventory_complete must be a boolean')` |
| prepare_runtime_generation_options | dict | 347 | `dict(generation_options)` |
| prepare_runtime_generation_options | dict | 349 | `dict(generation_option_defaults)` |
| prepare_runtime_generation_options | tuple (src/llm_wiki_cli/services…runtime_generation_options) | 351 | `tuple(dict.fromkeys(...))` |
| prepare_runtime_generation_options | dict.fromkeys | 352 | `dict.fromkeys((...))` |
| prepare_runtime_generation_options | PreparedRuntimeGenerationOptions | 354 | `PreparedRuntimeGenerationOptions(values=values, defaults=defaults, allowlist=allowlist)` |
| runtime_generation_options_hash | tuple (src/llm_wiki_cli/services…me_generation_options_hash) | 1224 | `tuple(RUNTIME_GENERATION_OPTION_DEFAULTS)` |
| runtime_generation_options_hash | hash_generation_options | 1227 | `hash_generation_options(prepared.values, defaults=prepared.defaults, allowlist=prepared.allowlist)` |
| hash_generation_options | isinstance (src/llm_wiki_cli/services…py:hash_generation_options) | 827 | `isinstance(values, Mapping)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `prepare_runtime_generation_options` | `isinstance` | 345 |
| external_call | `prepare_runtime_generation_options` | `TypeError` | 346 |
| external_call | `prepare_runtime_generation_options` | `dict.fromkeys` | 352 |
| external_call | `hash_generation_options` | `isinstance` | 827 |
| step_limit | `runtime_generation_options_hash` | `first 12 steps` | 0 |

## Behavior

This flow starts at `runtime_generation_options_hash` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
