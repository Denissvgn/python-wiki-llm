# split_table_row

**Entry point:** `split_table_row` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as split_table_row
    participant p1 as strip
    participant p2 as startswith
    participant p3 as endswith
    participant p4 as len
    participant p5 as extend
    participant p6 as append
    participant p7 as join
    p0-->>p1: strip
    p0-->>p2: startswith
    p0-->>p3: endswith
    p0-->>p4: len
    p0-->>p4: len
    p0-->>p5: extend
    p0-->>p4: len
    p0-->>p6: append
    p0-->>p6: append
    p0-->>p1: strip
    p0-->>p7: join
    p0-->>p6: append
    p0-->>p6: append
    p0-->>p1: strip
    p0-->>p7: join
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. split_table_row"]
    s2["2. strip"]
    s3["3. startswith"]
    s4["4. endswith"]
    s5["5. len"]
    s6["6. len"]
    s7["7. extend"]
    s8["8. len"]
    s9["9. append"]
    s10["10. append"]
    s11["11. strip"]
    s12["12. join"]
    s1 -. "line.strip(data not statically known)" .-> s2
    s1 -. "stripped.startswith('|')" .-> s3
    s1 -. "stripped.endswith('|')" .-> s4
    s1 -. "len(body)" .-> s5
    s1 -. "len(body)" .-> s6
    s1 -. "current.extend((...))" .-> s7
    s1 -. "len(body)" .-> s8
    s1 -. "current.append(...)" .-> s9
    s1 -. "cells.append(...)" .-> s10
    s1 -. "''.join(current).strip(data not statically known)" .-> s11
    s1 -. "''.join(current)" .-> s12
    b0["mutation current.extend"]
    s1 -. "mutation current.extend" .-> b0
    b1["mutation current.append"]
    s1 -. "mutation current.append" .-> b1
    b2["mutation cells.append"]
    s1 -. "mutation cells.append" .-> b2
    b3["mutation current.append"]
    s1 -. "mutation current.append" .-> b3
    b4["mutation cells.append"]
    s1 -. "mutation cells.append" .-> b4
    click s1 "../modules/markdown_sections.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `split_table_row` | `line: str` | - | - | `[...]`, `cells` |
| `strip` | - | - | - | - |
| `startswith` | - | - | - | - |
| `endswith` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |
| `extend` | - | - | - | - |
| `len` | - | - | - | - |
| `append` | - | - | - | - |
| `append` | - | - | - | - |
| `strip` | - | - | - | - |
| `join` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| split_table_row | strip | 467 | `line.strip(data not statically known)` |
| split_table_row | startswith | 468 | `stripped.startswith('\|')` |
| split_table_row | endswith | 468 | `stripped.endswith('\|')` |
| split_table_row | len | 475 | `len(body)` |
| split_table_row | len | 477 | `len(body)` |
| split_table_row | extend | 478 | `current.extend((...))` |
| split_table_row | len | 483 | `len(body)` |
| split_table_row | append | 486 | `current.append(...)` |
| split_table_row | append | 494 | `cells.append(...)` |
| split_table_row | strip | 494 | `''.join(current).strip(data not statically known)` |
| split_table_row | join | 494 | `''.join(current)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `current.extend` | `split_table_row` | 478 |
| mutation | `current.append` | `split_table_row` | 486 |
| mutation | `cells.append` | `split_table_row` | 494 |
| mutation | `current.append` | `split_table_row` | 497 |
| mutation | `cells.append` | `split_table_row` | 499 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `split_table_row` | `line.strip` | 467 |
| unresolved_call | `split_table_row` | `stripped.startswith` | 468 |
| unresolved_call | `split_table_row` | `stripped.endswith` | 468 |
| step_limit | `split_table_row` | `first 12 steps` | 0 |

## Behavior

This flow starts at `split_table_row` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
