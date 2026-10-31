# move_allocation

**Entry point:** `move_allocation` (`api`)
**Source:** [concept_identity](../modules/concept_identity.md)
**Modules touched:** [concept_identity](../modules/concept_identity.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as move_allocation
    participant p1 as validate_identity_registry
    participant p2 as aliases_for_move
    participant p3 as _typed_tuple
    participant p4 as ConceptIdentityError
    participant p5 as ConceptAllocation
    participant p6 as IdentityUpdate
    participant p7 as find_identity_collisions
    participant p8 as _deduplicated_aliases
    participant p9 as identity_coordinate_key
    participant p10 as validate_alias_type
    participant p11 as validate_alias_value
    participant p12 as canonical_path
    participant p13 as mcp_uri
    participant p14 as _entry_for
    participant p15 as validate_locator
    participant p16 as _validate_page_id
    participant p17 as validate_natural_key
    participant p18 as IdentityCollisionError
    participant p19 as _sorted_aliases
    participant p20 as IdentityAlias
    participant p21 as IdentityCollision
    participant p22 as iter_page_kinds
    participant p23 as AliasType
    participant p24 as WikiSurfaceError
    participant p25 as _machine_text
    participant p26 as _contains_uri_userinfo
    participant p27 as PageKind
    participant p28 as _looks_absolute_path
    participant p29 as isinstance (src/llm_wiki_cli/services…entity.py:move_allocation)
    participant p30 as {item.uid: item for item in current}.get
    p0->>p1: validate_identity_registry
    p0->>p2: aliases_for_move
    p0->>p3: _typed_tuple
    p0->>p4: ConceptIdentityError
    p0->>p5: ConceptAllocation
    p0->>p6: IdentityUpdate
    p1->>p7: find_identity_collisions
    p2->>p8: _deduplicated_aliases
    p7->>p9: identity_coordinate_key
    p9->>p10: validate_alias_type
    p9->>p11: validate_alias_value
    p9->>p12: canonical_path
    p9->>p13: mcp_uri
    p12->>p14: _entry_for
    p11->>p15: validate_locator
    p12->>p16: _validate_page_id
    p11->>p17: validate_natural_key
    p1->>p18: IdentityCollisionError
    p1->>p19: _sorted_aliases
    p2->>p20: IdentityAlias
    p7->>p21: IdentityCollision
    p9->>p22: iter_page_kinds
    p10->>p23: AliasType
    p12->>p24: WikiSurfaceError
    p15->>p25: _machine_text
    p15->>p26: _contains_uri_userinfo
    p14->>p27: PageKind
    p15->>p28: _looks_absolute_path
    p0-->>p29: isinstance (src/llm_wiki_cli/services…entity.py:move_allocation)(allocation, ConceptAllocation)
    p0-->>p30: {item.uid: item for item in current}.get(allocation.uid)
```

> Call sequence diagram shows 30 of 168 interactions; 138 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 55 (54 omitted); unresolved 1 of 35 (34 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/concept_identity.py:move_allocation` | 1 | - | external | 3 |
| `src/llm_wiki_cli/services/concept_identity.py:_typed_tuple` | 4 | - | external | 7 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_identity_registry` | 13 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 2 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 16 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 8 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 16 | - | external | 24 |
| `src/llm_wiki_cli/services/concept_identity.py:find_identity_collisions` | 16 | - | unresolved | 15 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 26 | - | external | 1 |
| `src/llm_wiki_cli/services/concept_identity.py:validate_alias_type` | 26 | [src/llm_wiki_cli/services/concept_identity.py](../modules/concept_identity.md) | internal | 1 |
> Omission summary shows 8 of 32 groups; 24 further groups are not expanded here. Counts above include all omitted interactions.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

> Trace truncated at the depth limit; deeper calls are omitted.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 79; effect analysis evaluated: 43, partial: 1, unavailable: 35. Counts include steps omitted from the displayed trace.

Collector observations for 44 source steps with known totals: observed: 205, emitted: 203, omitted: 2. Unavailable totals are excluded.

- Callable record unavailable for one or more source steps; those steps have no represented callable body.
- Effect collector omitted observations before flow assembly; displayed effects are partial.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals | Observed | Emitted | Omitted |
|---|---|---|---|---:|---:|---:|
| `move_allocation` | `available` | `evaluated` | `available` | `7` | `7` | `0` |
| `isinstance (src/llm_wiki_cli/services…entity.py:move_allocation)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…entity.py:move_allocation)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `_typed_tuple` | `available` | `evaluated` | `available` | `4` | `4` | `0` |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `enumerate` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |
| `all` | `not_applicable` | `not_applicable` | `not_applicable` | — | — | — |

```mermaid
flowchart LR
    s1["1. move_allocation"]
    s2["2. isinstance (src/llm_wiki_cli/services…entity.py:move_allocation)"]
    s3["3. TypeError (src/llm_wiki_cli/services…entity.py:move_allocation)"]
    s4["4. _typed_tuple"]
    s5["5. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s6["6. TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s7["7. tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s8["8. TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s9["9. enumerate"]
    s10["10. isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s11["11. TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple)"]
    s12["12. all"]
    s1 -. "isinstance (src/llm_wiki_cli/services…entity.py:move_allocation)(allocation, ConceptAllocation)" .-> s2
    s1 -. "TypeError (src/llm_wiki_cli/services…entity.py:move_allocation)('allocation must be a ConceptAllocation')" .-> s3
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
| `move_allocation` | `allocation: ConceptAllocation`, `new_reference: ConceptReference`, `allocations: Iterable[ConceptAllocation]`, `aliases: Iterable[IdentityAlias]` | `ConceptAllocation`, `ConceptAllocation` | - | `IdentityUpdate(...)` |
| `isinstance (src/llm_wiki_cli/services…entity.py:move_allocation)` | - | - | - | - |
| `TypeError (src/llm_wiki_cli/services…entity.py:move_allocation)` | - | - | - | - |
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
| move_allocation | isinstance (src/llm_wiki_cli/services…entity.py:move_allocation) | 850 | `isinstance(allocation, ConceptAllocation)` |
| move_allocation | TypeError (src/llm_wiki_cli/services…entity.py:move_allocation) | 851 | `TypeError('allocation must be a ConceptAllocation')` |
| move_allocation | _typed_tuple | 852 | `_typed_tuple(allocations, ConceptAllocation, 'allocations')` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1013 | `isinstance(values, (...))` |
| _typed_tuple | TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1014 | `TypeError(...)` |
| _typed_tuple | tuple (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1016 | `tuple(values)` |
| _typed_tuple | TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1018 | `TypeError(...)` |
| _typed_tuple | enumerate | 1021 | `enumerate(result)` |
| _typed_tuple | isinstance (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1022 | `isinstance(value, expected_type)` |
| _typed_tuple | TypeError (src/llm_wiki_cli/services…_identity.py:_typed_tuple) | 1023 | `TypeError(...)` |
| move_allocation | all | 853 | `all(...)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `move_allocation` | `isinstance` | 850 |
| external_call | `move_allocation` | `TypeError` | 851 |
| external_call | `_typed_tuple` | `isinstance` | 1013 |
| external_call | `_typed_tuple` | `TypeError` | 1014 |
| external_call | `_typed_tuple` | `TypeError` | 1018 |
| external_call | `_typed_tuple` | `enumerate` | 1021 |
| external_call | `_typed_tuple` | `isinstance` | 1022 |
| external_call | `_typed_tuple` | `TypeError` | 1023 |
| external_call | `move_allocation` | `all` | 853 |
| step_limit | `move_allocation` | `first 12 steps` | 0 |
| truncated_flow | `move_allocation` | `depth limit` | 0 |

## Behavior

This flow starts at `move_allocation` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
