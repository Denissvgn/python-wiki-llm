# path_is_under_scope

**Entry point:** `path_is_under_scope` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as path_is_under_scope
    participant p1 as path.replace(…).strip
    participant p2 as path.replace
    participant p3 as path_is_under
    participant p4 as bool
    participant p5 as path.startswith
    p0-->>p1: path.replace(…).strip('/')
    p0-->>p2: path.replace('\\', '/')
    p0->>p3: path_is_under
    p3-->>p4: bool(prefix)
    p3-->>p5: path.startswith(...)
```

> Call sequence diagram shows 5 of 5 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 1 of 1 (0 omitted); unresolved 3 of 3 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 2; effect analysis evaluated: 2, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. path_is_under_scope"]
    s2["2. path.replace(…).strip"]
    s3["3. path.replace"]
    s4["4. path_is_under"]
    s5["5. bool"]
    s6["6. path.startswith"]
    s1 -. "path.replace(…).strip('/')" .-> s2
    s1 -. "path.replace('\\', '/')" .-> s3
    s1 -->|"path_is_under(normalized, scope_root)"| s4
    s4 -. "bool(prefix)" .-> s5
    s4 -. "path.startswith(...)" .-> s6
    click s1 "../modules/validation.md"
    click s4 "../modules/validation.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `path_is_under_scope` | `path: str`, `scope_root: str` | - | - | `...` |
| `path.replace(…).strip` | - | - | - | - |
| `path.replace` | - | - | - | - |
| `path_is_under` | `path: str`, `prefix: str` | - | - | `...` |
| `bool` | - | - | - | - |
| `path.startswith` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| path_is_under_scope | path.replace(…).strip | 473 | `path.replace('\\', '/').strip('/')` |
| path_is_under_scope | path.replace | 473 | `path.replace('\\', '/')` |
| path_is_under_scope | path_is_under | 474 | `path_is_under(normalized, scope_root)` |
| path_is_under | bool | 467 | `bool(prefix)` |
| path_is_under | path.startswith | 467 | `path.startswith(...)` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `path_is_under_scope` | `path.replace('\\', '/').strip` | 473 |
| unresolved_call | `path_is_under_scope` | `path.replace` | 473 |
| unresolved_call | `path_is_under` | `path.startswith` | 467 |

## Behavior

This flow starts at `path_is_under_scope` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
