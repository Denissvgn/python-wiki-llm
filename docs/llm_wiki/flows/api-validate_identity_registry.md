# validate_identity_registry

**Entry point:** `validate_identity_registry` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_identity_registry
    participant p1 as _typed_tuple
    participant p2 as find_identity_collisions
    participant p3 as IdentityCollisionError
    participant p4 as tuple (src/llm_wiki_cli/services…alidate_identity_registry)
    participant p5 as sorted (src/llm_wiki_cli/services…alidate_identity_registry)
    participant p6 as _sorted_aliases
    participant p7 as isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    participant p8 as tuple (src/llm_wiki_cli/services…entity.py:_sorted_aliases)
    participant p9 as TypeError
    participant p10 as sorted (src/llm_wiki_cli/services…entity.py:_sorted_aliases)
    participant p11 as tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    participant p12 as defaultdict
    participant p13 as cast (src/llm_wiki_cli/services…entity.py:_sorted_aliases)
    participant p14 as enumerate
    participant p15 as allocations_by_uid[…].append
    participant p16 as current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)
    participant p17 as current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)
    participant p18 as identity_coordinate_key
    participant p19 as allocations_by_uid.items
    participant p20 as len (src/llm_wiki_cli/services…:find_identity_collisions)
    participant p21 as collisions.append
    participant p22 as IdentityCollision
    p0->>p1: _typed_tuple
    p0->>p1: _typed_tuple
    p0->>p2: find_identity_collisions
    p0->>p3: IdentityCollisionError
    p0-->>p4: tuple (src/llm_wiki_cli/services…alidate_identity_registry)(sorted(...))
    p0-->>p5: sorted (src/llm_wiki_cli/services…alidate_identity_registry)(current, key=...)
    p0->>p6: _sorted_aliases
    p1-->>p7: isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values, (...))
    p2->>p1: _typed_tuple
    p6-->>p8: tuple (src/llm_wiki_cli/services…entity.py:_sorted_aliases)(sorted(...))
    p1-->>p9: TypeError(...)
    p2->>p1: _typed_tuple
    p6-->>p10: sorted (src/llm_wiki_cli/services…entity.py:_sorted_aliases)(values, key=...)
    p1-->>p11: tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values)
    p2-->>p12: defaultdict(list)
    p6-->>p13: cast (src/llm_wiki_cli/services…entity.py:_sorted_aliases)(AliasType, item.alias_type)
    p1-->>p9: TypeError(...)
    p2-->>p12: defaultdict(list)
    p1-->>p14: enumerate(result)
    p2-->>p12: defaultdict(list)
    p1-->>p7: isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(value, expected_type)
    p2-->>p15: allocations_by_uid[…].append(allocation)
    p1-->>p9: TypeError(...)
    p2-->>p16: current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)(allocation)
    p2-->>p17: current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)(allocation)
    p2->>p18: identity_coordinate_key
    p2-->>p19: allocations_by_uid.items
    p2-->>p20: len (src/llm_wiki_cli/services…:find_identity_collisions)(records)
    p2-->>p21: collisions.append(IdentityCollision(...))
    p2->>p22: IdentityCollision
```

> Call sequence diagram shows 30 of 163 interactions; 133 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 16 of 58 (42 omitted); unresolved 5 of 42 (37 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:identity_coordinate_key` | 20 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 21 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 21 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_value` | 25 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_locator` | 27 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 28 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 28 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 28 | - | unresolved | 3 |
> Omission summary shows 8 of 28 groups; 20 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. validate_identity_registry"]
    s2["2. _typed_tuple"]
    s3["3. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s4["4. TypeError"]
    s5["5. tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s6["6. TypeError"]
    s7["7. enumerate"]
    s8["8. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s9["9. TypeError"]
    s10["10. _typed_tuple"]
    s11["11. find_identity_collisions"]
    s12["12. _typed_tuple"]
    s1 -->|"_typed_tuple(allocations, ConceptAllocation, 'allocations')"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values, (...))" .-> s3
    s2 -. "TypeError(...)" .-> s4
    s2 -. "tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values)" .-> s5
    s2 -. "TypeError(...)" .-> s6
    s2 -. "enumerate(result)" .-> s7
    s2 -. "isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(value, expected_type)" .-> s8
    s2 -. "TypeError(...)" .-> s9
    s1 -->|"_typed_tuple(aliases, IdentityAlias, 'aliases')"| s10
    s1 -->|"find_identity_collisions(current, historical)"| s11
    s11 -->|"_typed_tuple(allocations, ConceptAllocation, 'allocations')"| s12
    b0["mutation collisions.append"]
    s11 -. "mutation collisions.append" .-> b0
    b1["mutation collisions.append"]
    s11 -. "mutation collisions.append" .-> b1
    b2["mutation collisions.append"]
    s11 -. "mutation collisions.append" .-> b2
    b3["mutation collisions.append"]
    s11 -. "mutation collisions.append" .-> b3
    b4["mutation collisions.append"]
    s11 -. "mutation collisions.append" .-> b4
    b5["mutation collisions.append"]
    s11 -. "mutation collisions.append" .-> b5
    click s1 "../modules/concept_identity.md"
    click s2 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
    click s11 "../modules/concept_identity.md"
    click s12 "../modules/concept_identity.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `validate_identity_registry` | `allocations: Iterable[ConceptAllocation]`, `aliases: Iterable[IdentityAlias]` | `ConceptAllocation`, `IdentityAlias` | - | `(...)` |
| `_typed_tuple` | `values: Iterable[_RecordT]`, `expected_type: type[_RecordT]`, `field: str` | - | - | `result` |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_typed_tuple` | `values: Iterable[_RecordT]`, `expected_type: type[_RecordT]`, `field: str` | - | - | `result` |
| `find_identity_collisions` | `allocations: Iterable[ConceptAllocation]`, `aliases: Iterable[IdentityAlias]` | `ConceptAllocation`, `IdentityAlias`, `AliasType`, `AliasType`, `AliasType` | - | `tuple(...)` |
| `_typed_tuple` | `values: Iterable[_RecordT]`, `expected_type: type[_RecordT]`, `field: str` | - | - | `result` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| validate_identity_registry | _typed_tuple | 758 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1013 | `isinstance(values, (...))` |
| _typed_tuple | TypeError | 1014 | `TypeError(...)` |
| _typed_tuple | tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1016 | `tuple(values)` |
| _typed_tuple | TypeError | 1018 | `TypeError(...)` |
| _typed_tuple | enumerate | 1021 | `enumerate(result)` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1022 | `isinstance(value, expected_type)` |
| _typed_tuple | TypeError | 1023 | `TypeError(...)` |
| validate_identity_registry | _typed_tuple | 759 | `_typed_tuple(aliases, IdentityAlias, 'aliases')` |
| validate_identity_registry | find_identity_collisions | 760 | `find_identity_collisions(current, historical)` |
| find_identity_collisions | _typed_tuple | 645 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `collisions.append` | `find_identity_collisions` | 671 |
| mutation | `collisions.append` | `find_identity_collisions` | 683 |
| mutation | `collisions.append` | `find_identity_collisions` | 705 |
| mutation | `collisions.append` | `find_identity_collisions` | 717 |
| mutation | `collisions.append` | `find_identity_collisions` | 726 |
| mutation | `collisions.append` | `find_identity_collisions` | 740 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_typed_tuple` | `isinstance` | 1013 |
| external_call | `_typed_tuple` | `TypeError` | 1014 |
| external_call | `_typed_tuple` | `TypeError` | 1018 |
| external_call | `_typed_tuple` | `enumerate` | 1021 |
| external_call | `_typed_tuple` | `isinstance` | 1022 |
| external_call | `_typed_tuple` | `TypeError` | 1023 |
| step_limit | `validate_identity_registry` | `first 12 steps` | 0 |
| truncated_flow | `validate_identity_registry` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_identity_registry` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
