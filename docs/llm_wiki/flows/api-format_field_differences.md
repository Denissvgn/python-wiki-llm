# format_field_differences

**Entry point:** `format_field_differences` (`api`)
**Source:** [validation](../modules/validation.md)
**Modules touched:** [validation](../modules/validation.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as format_field_differences
    participant p1 as tuple
    participant p2 as str
    participant p3 as append
    participant p4 as join
    p0-->>p1: tuple
    p0-->>p2: str
    p0-->>p1: tuple
    p0-->>p2: str
    p0-->>p3: append
    p0-->>p4: join
    p0-->>p3: append
    p0-->>p4: join
    p0-->>p4: join
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. format_field_differences"]
    s2["2. tuple"]
    s3["3. str"]
    s4["4. tuple"]
    s5["5. str"]
    s6["6. append"]
    s7["7. join"]
    s8["8. append"]
    s9["9. join"]
    s10["10. join"]
    s1 -. "tuple(...)" .-> s2
    s1 -. "str(value)" .-> s3
    s1 -. "tuple(...)" .-> s4
    s1 -. "str(value)" .-> s5
    s1 -. "detail.append(...)" .-> s6
    s1 -. "', '.join(missing_values)" .-> s7
    s1 -. "detail.append(...)" .-> s8
    s1 -. "', '.join(unknown_values)" .-> s9
    s1 -. "'; '.join(detail)" .-> s10
    b0["mutation detail.append"]
    s1 -. "mutation detail.append" .-> b0
    b1["mutation detail.append"]
    s1 -. "mutation detail.append" .-> b1
    click s1 "../modules/validation.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `format_field_differences` | `missing: Iterable[object]`, `unknown: Iterable[object]` | - | - | `...` |
| `tuple` | - | - | - | - |
| `str` | - | - | - | - |
| `tuple` | - | - | - | - |
| `str` | - | - | - | - |
| `append` | - | - | - | - |
| `join` | - | - | - | - |
| `append` | - | - | - | - |
| `join` | - | - | - | - |
| `join` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| format_field_differences | tuple | 57 | `tuple(...)` |
| format_field_differences | str | 57 | `str(value)` |
| format_field_differences | tuple | 58 | `tuple(...)` |
| format_field_differences | str | 58 | `str(value)` |
| format_field_differences | append | 60 | `detail.append(...)` |
| format_field_differences | join | 60 | `', '.join(missing_values)` |
| format_field_differences | append | 62 | `detail.append(...)` |
| format_field_differences | join | 62 | `', '.join(unknown_values)` |
| format_field_differences | join | 63 | `'; '.join(detail)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `detail.append` | `format_field_differences` | 60 |
| mutation | `detail.append` | `format_field_differences` | 62 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `format_field_differences` | `'; '.join` | 63 |

## Behavior

This flow starts at `format_field_differences` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
