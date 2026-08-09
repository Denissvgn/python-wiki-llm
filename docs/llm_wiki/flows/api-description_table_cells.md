# description_table_cells

**Entry point:** `description_table_cells` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as description_table_cells
    participant p1 as splitlines
    participant p2 as normalize_markdown
    participant p3 as replace
    participant p4 as enumerate
    participant p5 as split_table_row
    participant p6 as strip
    participant p7 as startswith
    participant p8 as endswith
    participant p9 as len
    participant p10 as extend
    participant p11 as append
    participant p12 as join
    participant p13 as index
    participant p14 as is_table_separator
    participant p15 as all
    participant p16 as fullmatch
    participant p17 as defaultdict
    participant p18 as range
    p0-->>p1: splitlines
    p0->>p2: normalize_markdown
    p2-->>p3: replace
    p2-->>p3: replace
    p0-->>p4: enumerate
    p0->>p5: split_table_row
    p5-->>p6: strip
    p5-->>p7: startswith
    p5-->>p8: endswith
    p5-->>p9: len
    p5-->>p9: len
    p5-->>p10: extend
    p5-->>p9: len
    p5-->>p11: append
    p5-->>p11: append
    p5-->>p6: strip
    p5-->>p12: join
    p5-->>p11: append
    p5-->>p11: append
    p5-->>p6: strip
    p5-->>p12: join
    p0-->>p13: index
    p0-->>p9: len
    p0->>p14: is_table_separator
    p14-->>p15: all
    p14-->>p16: fullmatch
    p14-->>p3: replace
    p0->>p5: split_table_row
    p0-->>p17: defaultdict
    p0-->>p18: range
```

> Call sequence diagram shows 30 of 44 interactions; 14 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. description_table_cells"]
    s2["2. splitlines"]
    s3["3. normalize_markdown"]
    s4["4. replace"]
    s5["5. replace"]
    s6["6. enumerate"]
    s7["7. split_table_row"]
    s8["8. strip"]
    s9["9. startswith"]
    s10["10. endswith"]
    s11["11. len"]
    s12["12. len"]
    s1 -. "normalize_markdown(markdown).splitlines(data not statically known)" .-> s2
    s1 -->|"normalize_markdown(markdown)"| s3
    s3 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s4
    s3 -. "text.replace('\r\n', '\n')" .-> s5
    s1 -. "enumerate(lines)" .-> s6
    s1 -->|"split_table_row(line)"| s7
    s7 -. "line.strip(data not statically known)" .-> s8
    s7 -. "stripped.startswith('|')" .-> s9
    s7 -. "stripped.endswith('|')" .-> s10
    s7 -. "len(body)" .-> s11
    s7 -. "len(body)" .-> s12
    b0["mutation cells.append"]
    s1 -. "mutation cells.append" .-> b0
    b1["mutation current.extend"]
    s7 -. "mutation current.extend" .-> b1
    b2["mutation current.append"]
    s7 -. "mutation current.append" .-> b2
    b3["mutation cells.append"]
    s7 -. "mutation cells.append" .-> b3
    b4["mutation current.append"]
    s7 -. "mutation current.append" .-> b4
    b5["mutation cells.append"]
    s7 -. "mutation cells.append" .-> b5
    click s1 "../modules/markdown_sections.md"
    click s3 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
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
| `description_table_cells` | `markdown: str` | - | `occurrences[...]` | `tuple(...)`, `(...)` |
| `splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `split_table_row` | `line: str` | - | - | `[...]`, `cells` |
| `strip` | - | - | - | - |
| `startswith` | - | - | - | - |
| `endswith` | - | - | - | - |
| `len` | - | - | - | - |
| `len` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| description_table_cells | splitlines | 558 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| description_table_cells | normalize_markdown | 558 | `normalize_markdown(markdown)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n')` |
| description_table_cells | enumerate | 559 | `enumerate(lines)` |
| description_table_cells | split_table_row | 560 | `split_table_row(line)` |
| split_table_row | strip | 467 | `line.strip(data not statically known)` |
| split_table_row | startswith | 468 | `stripped.startswith('\|')` |
| split_table_row | endswith | 468 | `stripped.endswith('\|')` |
| split_table_row | len | 475 | `len(body)` |
| split_table_row | len | 477 | `len(body)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `cells.append` | `description_table_cells` | 581 |
| mutation | `current.extend` | `split_table_row` | 478 |
| mutation | `current.append` | `split_table_row` | 486 |
| mutation | `cells.append` | `split_table_row` | 494 |
| mutation | `current.append` | `split_table_row` | 497 |
| mutation | `cells.append` | `split_table_row` | 499 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `description_table_cells` | `normalize_markdown(markdown).splitlines` | 558 |
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| external_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `description_table_cells` | `enumerate` | 559 |
| unresolved_call | `split_table_row` | `line.strip` | 467 |
| unresolved_call | `split_table_row` | `stripped.startswith` | 468 |
| unresolved_call | `split_table_row` | `stripped.endswith` | 468 |
| step_limit | `description_table_cells` | `first 12 steps` | 0 |

## Behavior

This flow starts at `description_table_cells` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
