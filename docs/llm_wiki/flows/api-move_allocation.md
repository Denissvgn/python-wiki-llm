# move_allocation

**Entry point:** `move_allocation` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as move_allocation
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as _typed_tuple
    participant p4 as tuple
    participant p5 as enumerate
    participant p6 as all
    participant p7 as validate_identity_registry
    participant p8 as find_identity_collisions
    participant p9 as defaultdict
    participant p10 as append
    participant p11 as identity_coordinate_key
    participant p12 as validate_alias_type
    participant p13 as AliasType
    participant p14 as ConceptIdentityError
    participant p15 as validate_alias_value
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0->>p3: _typed_tuple
    p3-->>p1: isinstance
    p3-->>p2: TypeError
    p3-->>p4: tuple
    p3-->>p2: TypeError
    p3-->>p5: enumerate
    p3-->>p1: isinstance
    p3-->>p2: TypeError
    p0-->>p6: all
    p0->>p7: validate_identity_registry
    p7->>p3: _typed_tuple
    p7->>p3: _typed_tuple
    p7->>p8: find_identity_collisions
    p8->>p3: _typed_tuple
    p8->>p3: _typed_tuple
    p8-->>p9: defaultdict
    p8-->>p9: defaultdict
    p8-->>p9: defaultdict
    p8-->>p10: append
    p8-->>p10: append
    p8-->>p10: append
    p8->>p11: identity_coordinate_key
    p11->>p12: validate_alias_type
    p12-->>p1: isinstance
    p12->>p13: AliasType
    p12->>p14: ConceptIdentityError
    p11->>p15: validate_alias_value
    p15->>p12: validate_alias_type
```

> Call sequence diagram shows 30 of 168 interactions; 138 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. move_allocation"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. _typed_tuple"]
    s5["5. isinstance"]
    s6["6. TypeError"]
    s7["7. tuple"]
    s8["8. TypeError"]
    s9["9. enumerate"]
    s10["10. isinstance"]
    s11["11. TypeError"]
    s12["12. all"]
    s1 -. "isinstance(allocation, ConceptAllocation)" .-> s2
    s1 -. "TypeError('allocation must be a ConceptAllocation')" .-> s3
    s1 -->|"_typed_tuple(allocations, ConceptAllocation, 'allocations')"| s4
    s4 -. "isinstance(values, (...))" .-> s5
    s4 -. "TypeError(...)" .-> s6
    s4 -. "tuple(values)" .-> s7
    s4 -. "TypeError(...)" .-> s8
    s4 -. "enumerate(result)" .-> s9
    s4 -. "isinstance(value, expected_type)" .-> s10
    s4 -. "TypeError(...)" .-> s11
    s1 -. "all(...)" .-> s12
    click s1 "../modules/concept_identity.md"
    click s4 "../modules/concept_identity.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `move_allocation` | `allocation: ConceptAllocation`, `new_reference: ConceptReference`, `allocations: Iterable[ConceptAllocation]`, `aliases: Iterable[IdentityAlias]` | `ConceptAllocation`, `ConceptAllocation` | - | `IdentityUpdate(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_typed_tuple` | `values: Iterable[_RecordT]`, `expected_type: type[_RecordT]`, `field: str` | - | - | `result` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `tuple` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `all` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| move_allocation | isinstance | 820 | `isinstance(allocation, ConceptAllocation)` |
| move_allocation | TypeError | 821 | `TypeError('allocation must be a ConceptAllocation')` |
| move_allocation | _typed_tuple | 822 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |
| _typed_tuple | isinstance | 983 | `isinstance(values, (...))` |
| _typed_tuple | TypeError | 984 | `TypeError(...)` |
| _typed_tuple | tuple | 986 | `tuple(values)` |
| _typed_tuple | TypeError | 988 | `TypeError(...)` |
| _typed_tuple | enumerate | 991 | `enumerate(result)` |
| _typed_tuple | isinstance | 992 | `isinstance(value, expected_type)` |
| _typed_tuple | TypeError | 993 | `TypeError(...)` |
| move_allocation | all | 823 | `all(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `move_allocation` | `isinstance` | 820 |
| unresolved_call | `move_allocation` | `TypeError` | 821 |
| unresolved_call | `_typed_tuple` | `isinstance` | 983 |
| unresolved_call | `_typed_tuple` | `TypeError` | 984 |
| unresolved_call | `_typed_tuple` | `TypeError` | 988 |
| unresolved_call | `_typed_tuple` | `enumerate` | 991 |
| unresolved_call | `_typed_tuple` | `isinstance` | 992 |
| unresolved_call | `_typed_tuple` | `TypeError` | 993 |
| unresolved_call | `move_allocation` | `all` | 823 |
| step_limit | `move_allocation` | `first 12 steps` | 0 |
| truncated_flow | `move_allocation` | `depth limit` | 0 |

## Behavior

This flow starts at `move_allocation` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
