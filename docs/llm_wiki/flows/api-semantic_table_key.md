# semantic_table_key

**Entry point:** `semantic_table_key` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as semantic_table_key
    participant p1 as sub
    participant p2 as replace
    participant p3 as strip
    p0-->>p1: sub
    p0-->>p2: replace
    p0-->>p2: replace
    p0-->>p2: replace
    p0-->>p3: strip
```

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. semantic_table_key"]
    s2["2. sub"]
    s3["3. replace"]
    s4["4. replace"]
    s5["5. replace"]
    s6["6. strip"]
    s1 -. "re.sub('\\[([^\\]]+)\\]\\([^)]+\\)', '\\1', cell)" .-> s2
    s1 -. "key.replace('#96;', '').replace('*', '').replace('\\|', '|')" .-> s3
    s1 -. "key.replace('#96;', '').replace('*', '')" .-> s4
    s1 -. "key.replace('#96;', '')" .-> s5
    s1 -. "key.strip(data not statically known)" .-> s6
    click s1 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `semantic_table_key` | `cell: str` | - | - | `key.strip(...)` |
| `sub` | - | - | - | - |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| semantic_table_key | sub | 520 | `re.sub('\\[([^\\]]+)\\]\\([^)]+\\)', '\\1', cell)` |
| semantic_table_key | replace | 521 | `key.replace('`', '').replace('*', '').replace('\\\|', '\|')` |
| semantic_table_key | replace | 521 | `key.replace('`', '').replace('*', '')` |
| semantic_table_key | replace | 521 | `key.replace('`', '')` |
| semantic_table_key | strip | 522 | `key.strip(data not statically known)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `semantic_table_key` | `re.sub` | 520 |
| external_call | `semantic_table_key` | `key.replace('`', '').replace('*', '').replace` | 521 |
| external_call | `semantic_table_key` | `key.replace('`', '').replace` | 521 |
| external_call | `semantic_table_key` | `key.replace` | 521 |
| unresolved_call | `semantic_table_key` | `key.strip` | 522 |

## Behavior

This flow starts at `semantic_table_key` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
