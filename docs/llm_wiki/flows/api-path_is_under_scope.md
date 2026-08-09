# path_is_under_scope

**Entry point:** `path_is_under_scope` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as path_is_under_scope
    participant p1 as strip
    participant p2 as replace
    participant p3 as path_is_under
    participant p4 as bool
    participant p5 as startswith
    p0-->>p1: strip
    p0-->>p2: replace
    p0->>p3: path_is_under
    p3-->>p4: bool
    p3-->>p5: startswith
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. path_is_under_scope"]
    s2["2. strip"]
    s3["3. replace"]
    s4["4. path_is_under"]
    s5["5. bool"]
    s6["6. startswith"]
    s1 -. "path.replace('\\', '/').strip('/')" .-> s2
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
| `strip` | - | - | - | - |
| `replace` | - | - | - | - |
| `path_is_under` | `path: str`, `prefix: str` | - | - | `...` |
| `bool` | - | - | - | - |
| `startswith` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| path_is_under_scope | strip | 424 | `path.replace('\\', '/').strip('/')` |
| path_is_under_scope | replace | 424 | `path.replace('\\', '/')` |
| path_is_under_scope | path_is_under | 425 | `path_is_under(normalized, scope_root)` |
| path_is_under | bool | 418 | `bool(prefix)` |
| path_is_under | startswith | 418 | `path.startswith(...)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `path_is_under_scope` | `path.replace('\\', '/').strip` | 424 |
| unresolved_call | `path_is_under_scope` | `path.replace` | 424 |
| unresolved_call | `path_is_under` | `path.startswith` | 418 |

## Behavior

This flow starts at `path_is_under_scope` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
