# render_with_pack

**Entry point:** `render_with_pack` (`api`)
**Source:** [domain_pack](../modules/domain_pack.md)
**Modules touched:** [domain_pack](../modules/domain_pack.md), [pack_interfaces](../modules/pack_interfaces.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as render_with_pack
    participant p1 as current_pack
    participant p2 as isinstance
    participant p3 as renderer.render_module
    participant p4 as renderer.render_entity
    participant p5 as renderer.render_page
    participant p6 as TypeError
    participant p7 as _qualified_type_name
    participant p8 as active_pack
    participant p9 as type
    participant p10 as _ACTIVE_PACK.get
    p0->>p1: current_pack
    p0-->>p2: isinstance(request, ModulePageRequest)
    p0-->>p3: renderer.render_module(request)
    p0-->>p2: isinstance(request, EntityPageRequest)
    p0-->>p4: renderer.render_entity(request)
    p0-->>p5: renderer.render_page(request)
    p0-->>p2: isinstance(markdown, str)
    p0-->>p6: TypeError(...)
    p0->>p7: _qualified_type_name
    p1->>p8: active_pack
    p7-->>p9: type(value)
    p8-->>p10: _ACTIVE_PACK.get
```

> Call sequence diagram shows 12 of 12 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 5 of 5 (0 omitted); unresolved 4 of 4 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 4; effect analysis evaluated: 4, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

Collector observations for 4 source steps with known totals: observed: 9, emitted: 9, omitted: 0. Unavailable totals are excluded.

```mermaid
flowchart LR
    s1["1. render_with_pack"]
    s2["2. current_pack"]
    s3["3. active_pack"]
    s4["4. _ACTIVE_PACK.get"]
    s5["5. isinstance"]
    s6["6. renderer.render_module"]
    s7["7. isinstance"]
    s8["8. renderer.render_entity"]
    s9["9. renderer.render_page"]
    s10["10. isinstance"]
    s11["11. TypeError"]
    s12["12. _qualified_type_name"]
    s1 -->|"current_pack(data not statically known)"| s2
    s2 -->|"active_pack(data not statically known)"| s3
    s3 -. "_ACTIVE_PACK.get(data not statically known)" .-> s4
    s1 -. "isinstance(request, ModulePageRequest)" .-> s5
    s1 -. "renderer.render_module(request)" .-> s6
    s1 -. "isinstance(request, EntityPageRequest)" .-> s7
    s1 -. "renderer.render_entity(request)" .-> s8
    s1 -. "renderer.render_page(request)" .-> s9
    s1 -. "isinstance(markdown, str)" .-> s10
    s1 -. "TypeError(...)" .-> s11
    s1 -->|"_qualified_type_name(renderer)"| s12
    click s1 "../modules/domain_pack.md"
    click s2 "../modules/domain_pack.md"
    click s3 "../modules/pack_interfaces.md"
    click s12 "../modules/pack_interfaces.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `render_with_pack` | `request: ModulePageRequest \| EntityPageRequest \| PageRequest` | `ModulePageRequest`, `EntityPageRequest` | - | `markdown` |
| `current_pack` | - | `CODE_DOCS_PACK` | - | `...` |
| `active_pack` | - | - | - | `_ACTIVE_PACK.get(...)` |
| `_ACTIVE_PACK.get` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `renderer.render_module` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `renderer.render_entity` | - | - | - | - |
| `renderer.render_page` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `_qualified_type_name` | `value: object` | - | - | `...` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| render_with_pack | current_pack | 102 | `current_pack(data not statically known)` |
| current_pack | active_pack | 324 | `active_pack(data not statically known)` |
| active_pack | _ACTIVE_PACK.get | 643 | `_ACTIVE_PACK.get(data not statically known)` |
| render_with_pack | isinstance | 103 | `isinstance(request, ModulePageRequest)` |
| render_with_pack | renderer.render_module | 104 | `renderer.render_module(request)` |
| render_with_pack | isinstance | 105 | `isinstance(request, EntityPageRequest)` |
| render_with_pack | renderer.render_entity | 106 | `renderer.render_entity(request)` |
| render_with_pack | renderer.render_page | 108 | `renderer.render_page(request)` |
| render_with_pack | isinstance | 109 | `isinstance(markdown, str)` |
| render_with_pack | TypeError | 110 | `TypeError(...)` |
| render_with_pack | _qualified_type_name | 111 | `_qualified_type_name(renderer)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `active_pack` | `_ACTIVE_PACK.get` | 643 |
| external_call | `render_with_pack` | `isinstance` | 103 |
| unresolved_call | `render_with_pack` | `renderer.render_module` | 104 |
| external_call | `render_with_pack` | `isinstance` | 105 |
| unresolved_call | `render_with_pack` | `renderer.render_entity` | 106 |
| unresolved_call | `render_with_pack` | `renderer.render_page` | 108 |
| external_call | `render_with_pack` | `isinstance` | 109 |
| external_call | `render_with_pack` | `TypeError` | 110 |
| step_limit | `render_with_pack` | `first 12 steps` | 0 |

## Behavior

This flow starts at `render_with_pack` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
