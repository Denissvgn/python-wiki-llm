# validate_identity_registry

**Entry point:** `validate_identity_registry` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as validate_identity_registry
    participant p1 as _typed_tuple
    participant p2 as isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    participant p3 as TypeError
    participant p4 as tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    participant p5 as enumerate
    participant p6 as find_identity_collisions
    participant p7 as defaultdict
    participant p8 as allocations_by_uid[…].append
    participant p9 as current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)
    participant p10 as current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)
    participant p11 as identity_coordinate_key
    participant p12 as validate_alias_type
    participant p13 as isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)
    participant p14 as AliasType
    participant p15 as ConceptIdentityError
    participant p16 as validate_alias_value
    participant p17 as validate_locator
    participant p18 as _machine_text
    participant p19 as isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    participant p20 as len (src/llm_wiki_cli/services…identity.py:_machine_text)
    p0->>p1: _typed_tuple
    p1-->>p2: isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    p1-->>p3: TypeError
    p1-->>p4: tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    p1-->>p3: TypeError
    p1-->>p5: enumerate
    p1-->>p2: isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)
    p1-->>p3: TypeError
    p0->>p1: _typed_tuple
    p0->>p6: find_identity_collisions
    p6->>p1: _typed_tuple
    p6->>p1: _typed_tuple
    p6-->>p7: defaultdict
    p6-->>p7: defaultdict
    p6-->>p7: defaultdict
    p6-->>p8: allocations_by_uid[…].append
    p6-->>p9: current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)
    p6-->>p10: current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)
    p6->>p11: identity_coordinate_key
    p11->>p12: validate_alias_type
    p12-->>p13: isinstance (src/llm_wiki_cli/services…ty.py:validate_alias_type)
    p12->>p14: AliasType
    p12->>p15: ConceptIdentityError
    p11->>p16: validate_alias_value
    p16->>p12: validate_alias_type
    p16->>p17: validate_locator
    p17->>p18: _machine_text
    p18-->>p19: isinstance (src/llm_wiki_cli/services…identity.py:_machine_text)
    p18->>p15: ConceptIdentityError
    p18-->>p20: len (src/llm_wiki_cli/services…identity.py:_machine_text)
```

> Call sequence diagram shows 30 of 163 interactions; 133 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

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
| validate_identity_registry | _typed_tuple | 728 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 983 | `isinstance(values, (...))` |
| _typed_tuple | TypeError | 984 | `TypeError(...)` |
| _typed_tuple | tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 986 | `tuple(values)` |
| _typed_tuple | TypeError | 988 | `TypeError(...)` |
| _typed_tuple | enumerate | 991 | `enumerate(result)` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 992 | `isinstance(value, expected_type)` |
| _typed_tuple | TypeError | 993 | `TypeError(...)` |
| validate_identity_registry | _typed_tuple | 729 | `_typed_tuple(aliases, IdentityAlias, 'aliases')` |
| validate_identity_registry | find_identity_collisions | 730 | `find_identity_collisions(current, historical)` |
| find_identity_collisions | _typed_tuple | 615 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `collisions.append` | `find_identity_collisions` | 641 |
| mutation | `collisions.append` | `find_identity_collisions` | 653 |
| mutation | `collisions.append` | `find_identity_collisions` | 675 |
| mutation | `collisions.append` | `find_identity_collisions` | 687 |
| mutation | `collisions.append` | `find_identity_collisions` | 696 |
| mutation | `collisions.append` | `find_identity_collisions` | 710 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_typed_tuple` | `isinstance` | 983 |
| external_call | `_typed_tuple` | `TypeError` | 984 |
| external_call | `_typed_tuple` | `TypeError` | 988 |
| external_call | `_typed_tuple` | `enumerate` | 991 |
| external_call | `_typed_tuple` | `isinstance` | 992 |
| external_call | `_typed_tuple` | `TypeError` | 993 |
| step_limit | `validate_identity_registry` | `first 12 steps` | 0 |
| truncated_flow | `validate_identity_registry` | `depth limit` | 0 |

## Behavior

This flow starts at `validate_identity_registry` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
