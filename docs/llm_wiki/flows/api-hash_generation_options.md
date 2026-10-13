# hash_generation_options

**Entry point:** `hash_generation_options` (`api`)
**Source:** [knowledge_envelope](../modules/knowledge_envelope.md)
**Modules touched:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as hash_generation_options
    participant p1 as _normalized_allowlist
    participant p2 as _reject_unknown_option_keys
    participant p3 as _hash_structured
    participant p4 as KnowledgeEnvelopeError
    participant p5 as _reject_machine_local_paths
    participant p6 as canonical_json_bytes
    participant p7 as _validate_json_tree
    participant p8 as sha256_bytes
    participant p9 as canonical_json_text
    participant p10 as isinstance (src/llm_wiki_cli/services…py:hash_generation_options)
    participant p11 as payload.values
    participant p12 as isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)
    participant p13 as any (src/llm_wiki_cli/services…reject_unknown_option_keys)
    participant p14 as set (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p15 as isinstance (src/llm_wiki_cli/services…reject_unknown_option_keys)
    participant p16 as walk (src/llm_wiki_cli/services…reject_machine_local_paths)
    participant p17 as tuple
    participant p18 as set (src/llm_wiki_cli/services…reject_unknown_option_keys)
    participant p19 as any (src/llm_wiki_cli/services…e.py:_normalized_allowlist)
    participant p20 as min
    participant p21 as len
    participant p22 as set (src/llm_wiki_cli/services…e.py:_normalized_allowlist)
    participant p23 as sorted
    participant p24 as set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    participant p25 as hashlib.sha256(…).hexdigest
    p0->>p1: _normalized_allowlist
    p0->>p2: _reject_unknown_option_keys
    p0->>p3: _hash_structured
    p0->>p4: KnowledgeEnvelopeError
    p0->>p5: _reject_machine_local_paths
    p3->>p6: canonical_json_bytes
    p3->>p7: _validate_json_tree
    p3->>p8: sha256_bytes
    p6->>p9: canonical_json_text
    p0-->>p10: isinstance (src/llm_wiki_cli/services…py:hash_generation_options)(values, Mapping)
    p3-->>p11: payload.values
    p0-->>p10: isinstance (src/llm_wiki_cli/services…py:hash_generation_options)(defaults, Mapping)
    p1-->>p12: isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(value, (...))
    p2-->>p13: any (src/llm_wiki_cli/services…reject_unknown_option_keys)(...)
    p5-->>p14: set (src/llm_wiki_cli/services…reject_machine_local_paths)
    p2-->>p15: isinstance (src/llm_wiki_cli/services…reject_unknown_option_keys)(key, str)
    p5-->>p16: walk (src/llm_wiki_cli/services…reject_machine_local_paths)(value, field_name)
    p1-->>p17: tuple(value)
    p2-->>p18: set (src/llm_wiki_cli/services…reject_unknown_option_keys)(value)
    p1-->>p19: any (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(...)
    p2-->>p18: set (src/llm_wiki_cli/services…reject_unknown_option_keys)(allowlist)
    p1-->>p12: isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(item, str)
    p2-->>p20: min(unknown)
    p1-->>p21: len(items)
    p1-->>p21: len(set(...))
    p1-->>p22: set (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(items)
    p1-->>p17: tuple(sorted(...))
    p1-->>p23: sorted(items)
    p7-->>p24: set (src/llm_wiki_cli/services…ope.py:_validate_json_tree)
    p8-->>p25: hashlib.sha256(…).hexdigest
```

> Call sequence diagram shows 30 of 44 interactions; 14 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 18 of 20 (2 omitted); unresolved 3 of 5 (2 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/knowledge_envelope.py:hash_generation_options` | 1 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 3 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_normalized_allowlist` | 6 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 4 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_reject_unknown_option_keys` | 20 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 2 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_validate_json_tree` | 35 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:sha256_bytes` | 38 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_bytes` | 41 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/knowledge_evidence.py:canonical_json_text` | 43 | - | external | 1 |
| `src/llm_wiki_cli/services/knowledge_envelope.py:_hash_structured` | 33 | [src/llm_wiki_cli/services/knowledge_envelope.py](../modules/knowledge_envelope.md) | internal | 1 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. hash_generation_options"]
    s2["2. isinstance (src/llm_wiki_cli/services…py:hash_generation_options)"]
    s3["3. KnowledgeEnvelopeError"]
    s4["4. isinstance (src/llm_wiki_cli/services…py:hash_generation_options)"]
    s5["5. KnowledgeEnvelopeError"]
    s6["6. _normalized_allowlist"]
    s7["7. isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)"]
    s8["8. KnowledgeEnvelopeError"]
    s9["9. tuple"]
    s10["10. KnowledgeEnvelopeError"]
    s11["11. any (src/llm_wiki_cli/services…e.py:_normalized_allowlist)"]
    s12["12. isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)"]
    s1 -. "isinstance (src/llm_wiki_cli/services…py:hash_generation_options)(values, Mapping)" .-> s2
    s1 -->|"KnowledgeEnvelopeError('generation_options', 'must be an object')"| s3
    s1 -. "isinstance (src/llm_wiki_cli/services…py:hash_generation_options)(defaults, Mapping)" .-> s4
    s1 -->|"KnowledgeEnvelopeError('generation_option_defaults', 'must be an object')"| s5
    s1 -->|"_normalized_allowlist(allowlist)"| s6
    s6 -. "isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(value, (...))" .-> s7
    s6 -->|"KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names, not scalar text or bytes')"| s8
    s6 -. "tuple(value)" .-> s9
    s6 -->|"KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names')"| s10
    s6 -. "any (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(...)" .-> s11
    s6 -. "isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)(item, str)" .-> s12
    click s1 "../modules/knowledge_envelope.md"
    click s3 "../modules/knowledge_envelope.md"
    click s5 "../modules/knowledge_envelope.md"
    click s6 "../modules/knowledge_envelope.md"
    click s8 "../modules/knowledge_envelope.md"
    click s10 "../modules/knowledge_envelope.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `hash_generation_options` | `values: Mapping[str, Any]`, `defaults: Mapping[str, Any]`, `allowlist: Iterable[str]` | `Mapping`, `Mapping`, `GENERATION_OPTIONS_DOMAIN` | `effective[...]`, `effective[...]` | `_hash_structured(...)` |
| `isinstance (src/llm_wiki_cli/services…py:hash_generation_options)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:hash_generation_options)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `_normalized_allowlist` | `value: Iterable[str]` | - | - | `tuple(...)` |
| `isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `tuple` | - | - | - | - |
| `KnowledgeEnvelopeError` | - | - | - | - |
| `any (src/llm_wiki_cli/services…e.py:_normalized_allowlist)` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| hash_generation_options | isinstance (src/llm_wiki_cli/services…py:hash_generation_options) | 827 | `isinstance(values, Mapping)` |
| hash_generation_options | KnowledgeEnvelopeError | 828 | `KnowledgeEnvelopeError('generation_options', 'must be an object')` |
| hash_generation_options | isinstance (src/llm_wiki_cli/services…py:hash_generation_options) | 829 | `isinstance(defaults, Mapping)` |
| hash_generation_options | KnowledgeEnvelopeError | 830 | `KnowledgeEnvelopeError('generation_option_defaults', 'must be an object')` |
| hash_generation_options | _normalized_allowlist | 834 | `_normalized_allowlist(allowlist)` |
| _normalized_allowlist | isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist) | 1675 | `isinstance(value, (...))` |
| _normalized_allowlist | KnowledgeEnvelopeError | 1676 | `KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names, not scalar text or bytes')` |
| _normalized_allowlist | tuple | 1681 | `tuple(value)` |
| _normalized_allowlist | KnowledgeEnvelopeError | 1683 | `KnowledgeEnvelopeError('generation_option_allowlist', 'must be an iterable of option names')` |
| _normalized_allowlist | any (src/llm_wiki_cli/services…e.py:_normalized_allowlist) | 1687 | `any(...)` |
| _normalized_allowlist | isinstance (src/llm_wiki_cli/services…e.py:_normalized_allowlist) | 1687 | `isinstance(item, str)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `hash_generation_options` | `isinstance` | 827 |
| external_call | `hash_generation_options` | `isinstance` | 829 |
| external_call | `_normalized_allowlist` | `isinstance` | 1675 |
| external_call | `_normalized_allowlist` | `any` | 1687 |
| external_call | `_normalized_allowlist` | `isinstance` | 1687 |
| step_limit | `hash_generation_options` | `first 12 steps` | 0 |

## Behavior

This flow starts at `hash_generation_options` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
