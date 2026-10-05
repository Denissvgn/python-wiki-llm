# find_identity_collisions

**Entry point:** `find_identity_collisions` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as find_identity_collisions
    participant p1 as _typed_tuple
    participant p2 as defaultdict
    participant p3 as allocations_by_uid[…].append
    participant p4 as current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)
    participant p5 as current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)
    participant p6 as identity_coordinate_key
    participant p7 as allocations_by_uid.items
    participant p8 as len (src/llm_wiki_cli/services…:find_identity_collisions)
    participant p9 as collisions.append
    participant p10 as IdentityCollision
    participant p11 as current_coordinates.items
    participant p12 as values.items
    participant p13 as tuple (src/llm_wiki_cli/services…:find_identity_collisions)
    participant p14 as sorted
    participant p15 as set
    participant p16 as cast
    participant p17 as aliases_by_coordinate[…].append
    participant p18 as aliases_by_coordinate.items
    p0->>p1: _typed_tuple
    p0->>p1: _typed_tuple
    p0-->>p2: defaultdict(list)
    p0-->>p2: defaultdict(list)
    p0-->>p2: defaultdict(list)
    p0-->>p3: allocations_by_uid[…].append(allocation)
    p0-->>p4: current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)(allocation)
    p0-->>p5: current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)(allocation)
    p0->>p6: identity_coordinate_key
    p0-->>p7: allocations_by_uid.items
    p0-->>p8: len (src/llm_wiki_cli/services…:find_identity_collisions)(records)
    p0-->>p9: collisions.append(IdentityCollision(...))
    p0->>p10: IdentityCollision
    p0-->>p11: current_coordinates.items
    p0-->>p12: values.items
    p0-->>p13: tuple (src/llm_wiki_cli/services…:find_identity_collisions)(sorted(...))
    p0-->>p14: sorted(...)
    p0-->>p8: len (src/llm_wiki_cli/services…:find_identity_collisions)(uids)
    p0-->>p9: collisions.append(IdentityCollision(...))
    p0->>p10: IdentityCollision
    p0-->>p2: defaultdict(list)
    p0-->>p15: set(allocations_by_uid)
    p0-->>p16: cast(AliasType, alias.alias_type)
    p0-->>p17: aliases_by_coordinate[…].append(alias)
    p0->>p6: identity_coordinate_key
    p0-->>p9: collisions.append(IdentityCollision(...))
    p0->>p10: IdentityCollision
    p0-->>p18: aliases_by_coordinate.items
    p0-->>p13: tuple (src/llm_wiki_cli/services…:find_identity_collisions)(sorted(...))
    p0-->>p14: sorted(...)
```

> Call sequence diagram shows 30 of 167 interactions; 137 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 12 of 60 (48 omitted); unresolved 11 of 45 (34 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_typed_tuple` | 2 | - | external | 7 |
| `src/llm_wiki_cli/services/concept_identity.py:identity_coordinate_key` | 17 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 18 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 18 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_value` | 22 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_locator` | 24 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 25 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 25 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
> Omission summary shows 8 of 35 groups; 27 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. find_identity_collisions"]
    s2["2. _typed_tuple"]
    s3["3. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s4["4. TypeError"]
    s5["5. tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s6["6. TypeError"]
    s7["7. enumerate"]
    s8["8. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s9["9. TypeError"]
    s10["10. _typed_tuple"]
    s11["11. defaultdict"]
    s12["12. defaultdict"]
    s1 -->|"_typed_tuple(allocations, ConceptAllocation, 'allocations')"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values, (...))" .-> s3
    s2 -. "TypeError(...)" .-> s4
    s2 -. "tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(values)" .-> s5
    s2 -. "TypeError(...)" .-> s6
    s2 -. "enumerate(result)" .-> s7
    s2 -. "isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)(value, expected_type)" .-> s8
    s2 -. "TypeError(...)" .-> s9
    s1 -->|"_typed_tuple(aliases, IdentityAlias, 'aliases')"| s10
    s1 -. "defaultdict(list)" .-> s11
    s1 -. "defaultdict(list)" .-> s12
    b0["mutation collisions.append"]
    s1 -. "mutation collisions.append" .-> b0
    b1["mutation collisions.append"]
    s1 -. "mutation collisions.append" .-> b1
    b2["mutation collisions.append"]
    s1 -. "mutation collisions.append" .-> b2
    b3["mutation collisions.append"]
    s1 -. "mutation collisions.append" .-> b3
    b4["mutation collisions.append"]
    s1 -. "mutation collisions.append" .-> b4
    b5["mutation collisions.append"]
    s1 -. "mutation collisions.append" .-> b5
    click s1 "../modules/concept_identity.md"
    click s2 "../modules/concept_identity.md"
    click s10 "../modules/concept_identity.md"
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
| `find_identity_collisions` | `allocations: Iterable[ConceptAllocation]`, `aliases: Iterable[IdentityAlias]` | `ConceptAllocation`, `IdentityAlias`, `AliasType`, `AliasType`, `AliasType` | - | `tuple(...)` |
| `_typed_tuple` | `values: Iterable[_RecordT]`, `expected_type: type[_RecordT]`, `field: str` | - | - | `result` |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_typed_tuple` | `values: Iterable[_RecordT]`, `expected_type: type[_RecordT]`, `field: str` | - | - | `result` |
| `defaultdict` | - | - | - | - |
| `defaultdict` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| find_identity_collisions | _typed_tuple | 645 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1013 | `isinstance(values, (...))` |
| _typed_tuple | TypeError | 1014 | `TypeError(...)` |
| _typed_tuple | tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1016 | `tuple(values)` |
| _typed_tuple | TypeError | 1018 | `TypeError(...)` |
| _typed_tuple | enumerate | 1021 | `enumerate(result)` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1022 | `isinstance(value, expected_type)` |
| _typed_tuple | TypeError | 1023 | `TypeError(...)` |
| find_identity_collisions | _typed_tuple | 650 | `_typed_tuple(aliases, IdentityAlias, 'aliases')` |
| find_identity_collisions | defaultdict | 653 | `defaultdict(list)` |
| find_identity_collisions | defaultdict | 657 | `defaultdict(list)` |

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
| external_call | `find_identity_collisions` | `defaultdict` | 653 |
| external_call | `find_identity_collisions` | `defaultdict` | 657 |
| step_limit | `find_identity_collisions` | `first 12 steps` | 0 |
| truncated_flow | `find_identity_collisions` | `depth limit` | 0 |

## Behavior

This flow starts at `find_identity_collisions` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
