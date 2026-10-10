# add_identity_alias

**Entry point:** `add_identity_alias` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as add_identity_alias
    participant p1 as isinstance (src/llm_wiki_cli/services…ity.py:add_identity_alias)
    participant p2 as TypeError (src/llm_wiki_cli/services…ity.py:add_identity_alias)
    participant p3 as _typed_tuple
    participant p4 as all
    participant p5 as validate_identity_registry
    participant p6 as {item.uid: item for item in current}.get
    participant p7 as ConceptIdentityError
    participant p8 as validate_alias_type
    participant p9 as validate_alias_value
    participant p10 as identity_coordinate_key
    participant p11 as tuple (src/llm_wiki_cli/services…ity.py:add_identity_alias)
    participant p12 as _deduplicated_aliases
    participant p13 as IdentityAlias
    participant p14 as IdentityUpdate
    participant p15 as isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    participant p16 as cast (src/llm_wiki_cli/services….py:_deduplicated_aliases)
    participant p17 as TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    participant p18 as tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    participant p19 as find_identity_collisions
    participant p20 as IdentityCollisionError
    participant p21 as _sorted_aliases
    p0-->>p1: isinstance (src/llm_wiki_cli/services…ity.py:add_identity_alias)(allocation, ConceptAllocation)
    p0-->>p2: TypeError (src/llm_wiki_cli/services…ity.py:add_identity_alias)('allocation must be a ConceptAllocation')
    p0->>p3: _typed_tuple
    p0-->>p4: all(...)
    p0->>p5: validate_identity_registry
    p0-->>p6: {item.uid: item for item in current}.get(allocation.uid)
    p0->>p7: ConceptIdentityError
    p0->>p8: validate_alias_type
    p0->>p9: validate_alias_value
    p0->>p10: identity_coordinate_key
    p0->>p10: identity_coordinate_key
    p0-->>p11: tuple (src/llm_wiki_cli/services…ity.py:add_identity_alias)(...)
    p0->>p10: identity_coordinate_key
    p0->>p12: _deduplicated_aliases
    p0->>p13: IdentityAlias
    p0-->>p11: tuple (src/llm_wiki_cli/services…ity.py:add_identity_alias)(...)
    p0->>p5: validate_identity_registry
    p0->>p14: IdentityUpdate
    p3-->>p15: isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values, (...))
    p5->>p3: _typed_tuple
    p12-->>p16: cast (src/llm_wiki_cli/services….py:_deduplicated_aliases)(AliasType, item.alias_type)
    p3-->>p17: TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(...)
    p5->>p3: _typed_tuple
    p12->>p10: identity_coordinate_key
    p3-->>p18: tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values)
    p5->>p19: find_identity_collisions
    p12-->>p16: cast (src/llm_wiki_cli/services….py:_deduplicated_aliases)(AliasType, item.alias_type)
    p3-->>p17: TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(...)
    p5->>p20: IdentityCollisionError
    p12->>p21: _sorted_aliases
```

> Call sequence diagram shows 30 of 159 interactions; 129 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 52 (41 omitted); unresolved 1 of 33 (32 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_typed_tuple` | 4 | - | external | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 16 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 10 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 16 | - | external | 24 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 16 | - | unresolved | 15 |
| `src/llm_wiki_cli/services/concept_identity.py:identity_coordinate_key` | 25 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 26 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 26 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_value` | 30 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 3 |
> Omission summary shows 8 of 27 groups; 19 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. add_identity_alias"]
    s2["2. isinstance (src/llm_wiki_cli/services…ity.py:add_identity_alias)"]
    s3["3. TypeError (src/llm_wiki_cli/services…ity.py:add_identity_alias)"]
    s4["4. _typed_tuple"]
    s5["5. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s6["6. TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s7["7. tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s8["8. TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s9["9. enumerate"]
    s10["10. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s11["11. TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s12["12. all"]
    s1 -. "isinstance (src/llm_wiki_cli/services…ity.py:add_identity_alias)(allocation, ConceptAllocation)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…ity.py:add_identity_alias)('allocation must be a ConceptAllocation')" .-> s3
    s1 -->|"_typed_tuple(allocations, ConceptAllocation, 'allocations')"| s4
    s4 -. "isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values, (...))" .-> s5
    s4 -. "TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(...)" .-> s6
    s4 -. "tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values)" .-> s7
    s4 -. "TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(...)" .-> s8
    s4 -. "enumerate(result)" .-> s9
    s4 -. "isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(value, expected_type)" .-> s10
    s4 -. "TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(...)" .-> s11
    s1 -. "all(...)" .-> s12
    click s1 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `add_identity_alias` | `allocation: ConceptAllocation`, `alias_type: AliasType \| str`, `value: object`, `allocations: Iterable[ConceptAllocation]`, `aliases: Iterable[IdentityAlias]` | `ConceptAllocation`, `ConceptAllocation`, `AliasType` | - | `IdentityUpdate(...)` |
| `isinstance (src/llm_wiki_cli/services…ity.py:add_identity_alias)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…ity.py:add_identity_alias)` | - | - | - | - |
| `_typed_tuple` | `values: Iterable[_RecordT]`, `expected_type: type[_RecordT]`, `field: str` | - | - | `result` |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `all` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| add_identity_alias | isinstance (src/llm_wiki_cli/services…ity.py:add_identity_alias) | 891 | `isinstance(allocation, ConceptAllocation)` |
| add_identity_alias | TypeError (src/llm_wiki_cli/services…ity.py:add_identity_alias) | 892 | `TypeError('allocation must be a ConceptAllocation')` |
| add_identity_alias | _typed_tuple | 893 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1013 | `isinstance(values, (...))` |
| _typed_tuple | TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1014 | `TypeError(...)` |
| _typed_tuple | tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1016 | `tuple(values)` |
| _typed_tuple | TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1018 | `TypeError(...)` |
| _typed_tuple | enumerate | 1021 | `enumerate(result)` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1022 | `isinstance(value, expected_type)` |
| _typed_tuple | TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1023 | `TypeError(...)` |
| add_identity_alias | all | 894 | `all(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `add_identity_alias` | `isinstance` | 891 |
| external_call | `add_identity_alias` | `TypeError` | 892 |
| external_call | `_typed_tuple` | `isinstance` | 1013 |
| external_call | `_typed_tuple` | `TypeError` | 1014 |
| external_call | `_typed_tuple` | `TypeError` | 1018 |
| external_call | `_typed_tuple` | `enumerate` | 1021 |
| external_call | `_typed_tuple` | `isinstance` | 1022 |
| external_call | `_typed_tuple` | `TypeError` | 1023 |
| external_call | `add_identity_alias` | `all` | 894 |
| step_limit | `add_identity_alias` | `first 12 steps` | 0 |
| truncated_flow | `add_identity_alias` | `depth limit` | 0 |

## Behavior

This flow starts at `add_identity_alias` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
