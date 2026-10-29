# find_identity_collisions

**Entry point:** `find_identity_collisions` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as find_identity_collisions
    participant p1 as identity_coordinate_key
    participant p2 as _typed_tuple
    participant p3 as IdentityCollision
    participant p4 as validate_alias_type
    participant p5 as validate_alias_value
    participant p6 as validate_locator
    participant p7 as validate_natural_key
    participant p8 as _machine_text
    participant p9 as validate_exact_page_coordinate
    participant p10 as _safe_decoded_coordinate
    participant p11 as _matches_directory_path
    participant p12 as _matches_directory_uri
    participant p13 as iter_page_kinds
    participant p14 as canonical_path
    participant p15 as mcp_uri
    participant p16 as AliasType
    participant p17 as ConceptIdentityError
    participant p18 as _contains_uri_userinfo
    participant p19 as _looks_absolute_path
    participant p20 as _contains_coordinate_userinfo
    participant p21 as WikiSurfaceError
    participant p22 as is_safe_page_id
    participant p23 as defaultdict
    participant p24 as allocations_by_uid[…].append
    participant p25 as current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)
    participant p26 as current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)
    participant p27 as allocations_by_uid.items
    participant p28 as len (src/llm_wiki_cli/services…:find_identity_collisions)
    p0->>p1: identity_coordinate_key
    p0->>p2: _typed_tuple
    p0->>p3: IdentityCollision
    p1->>p4: validate_alias_type
    p1->>p5: validate_alias_value
    p5->>p6: validate_locator
    p5->>p7: validate_natural_key
    p6->>p8: _machine_text
    p6->>p9: validate_exact_page_coordinate
    p7->>p10: _safe_decoded_coordinate
    p9->>p11: _matches_directory_path
    p9->>p12: _matches_directory_uri
    p1->>p13: iter_page_kinds
    p1->>p14: canonical_path
    p1->>p15: mcp_uri
    p4->>p16: AliasType
    p4->>p17: ConceptIdentityError
    p6->>p18: _contains_uri_userinfo
    p6->>p19: _looks_absolute_path
    p7->>p20: _contains_coordinate_userinfo
    p9->>p21: WikiSurfaceError
    p11->>p22: is_safe_page_id
    p0-->>p23: defaultdict(list)
    p0-->>p24: allocations_by_uid[…].append(allocation)
    p0-->>p23: defaultdict(list)
    p0-->>p23: defaultdict(list)
    p0-->>p25: current_coordinates[…][…].append (src/llm_wiki_cli/services…nd_identity_collisions, 1)(allocation)
    p0-->>p26: current_coordinates[…][…].append (src/llm_wiki_cli/services…:find_identity_collisions)(allocation)
    p0-->>p27: allocations_by_uid.items
    p0-->>p28: len (src/llm_wiki_cli/services…:find_identity_collisions)(records)
```

> Call sequence diagram shows 30 of 167 interactions; 137 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 4 of 60 (56 omitted); unresolved 4 of 45 (41 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:_typed_tuple` | 2 | - | external | 7 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 1 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 7 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 18 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_value` | 22 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 25 | - | external | 6 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 25 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 5 |
| `src/llm_wiki_cli/services/concept_identity.py:_machine_text` | 25 | - | unresolved | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_contains_uri_userinfo` | 40 | - | external | 1 |
> Omission summary shows 8 of 32 groups; 24 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 63; effect analysis evaluated: 31, partial: 0, unavailable: 32. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `find_identity_collisions` | `available` | `evaluated` | `available` |
| `_typed_tuple` | `available` | `evaluated` | `available` |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `TypeError` | `not_applicable` | `not_applicable` | `not_applicable` |
| `tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `TypeError` | `not_applicable` | `not_applicable` | `not_applicable` |
| `enumerate` | `not_applicable` | `not_applicable` | `not_applicable` |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` |
| `TypeError` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_typed_tuple` | `available` | `evaluated` | `available` |
| `defaultdict` | `not_applicable` | `not_applicable` | `not_applicable` |
| `defaultdict` | `not_applicable` | `not_applicable` | `not_applicable` |

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
