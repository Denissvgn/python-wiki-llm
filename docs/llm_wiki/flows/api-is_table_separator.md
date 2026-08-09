# is_table_separator

**Entry point:** `is_table_separator` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as is_table_separator
    participant p1 as all
    participant p2 as fullmatch
    participant p3 as replace
    p0-->>p1: all
    p0-->>p2: fullmatch
    p0-->>p3: replace
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. is_table_separator"]
    s2["2. all"]
    s3["3. fullmatch"]
    s4["4. replace"]
    s1 -. "all(...)" .-> s2
    s1 -. "re.fullmatch(':?-{3,}:?', cell.replace(...))" .-> s3
    s1 -. "cell.replace(' ', '')" .-> s4
    click s1 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `is_table_separator` | `cells: list[str]` | - | - | `False`, `all(...)` |
| `all` | - | - | - | - |
| `fullmatch` | - | - | - | - |
| `replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| is_table_separator | all | 514 | `all(...)` |
| is_table_separator | fullmatch | 514 | `re.fullmatch(':?-{3,}:?', cell.replace(...))` |
| is_table_separator | replace | 514 | `cell.replace(' ', '')` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `is_table_separator` | `all` | 514 |
| external_call | `is_table_separator` | `re.fullmatch` | 514 |
| external_call | `is_table_separator` | `cell.replace` | 514 |

## Behavior

This flow starts at `is_table_separator` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
