# is_supported_relationship_kind

**Entry point:** `is_supported_relationship_kind` (`api`)
**Source:** [knowledge_graph](../modules/knowledge_graph.md)
**Modules touched:** [knowledge_graph](../modules/knowledge_graph.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_supported_relationship_kind
    participant p1 as isinstance
    participant p2 as _QUALIFIED_NAME_RE.fullmatch
    p0-->>p1: isinstance(value, str)
    p0-->>p2: _QUALIFIED_NAME_RE.fullmatch(value)
```

> Call sequence diagram shows 2 of 2 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 1 of 1 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 1; effect analysis evaluated: 1, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. is_supported_relationship_kind"]
    s2["2. isinstance"]
    s3["3. _QUALIFIED_NAME_RE.fullmatch"]
    s1 -. "isinstance(value, str)" .-> s2
    s1 -. "_QUALIFIED_NAME_RE.fullmatch(value)" .-> s3
    click s1 "../modules/knowledge_graph.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_supported_relationship_kind` | `value: object` | `CORE_RELATIONSHIP_KINDS` | - | `...` |
| `isinstance` | - | - | - | - |
| `_QUALIFIED_NAME_RE.fullmatch` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_supported_relationship_kind | isinstance | 105 | `isinstance(value, str)` |
| is_supported_relationship_kind | _QUALIFIED_NAME_RE.fullmatch | 107 | `_QUALIFIED_NAME_RE.fullmatch(value)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `is_supported_relationship_kind` | `isinstance` | 105 |
| unresolved_call | `is_supported_relationship_kind` | `_QUALIFIED_NAME_RE.fullmatch` | 107 |

## Behavior

This flow starts at `is_supported_relationship_kind` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
