# mixed_table_projection

**Entry point:** `mixed_table_projection` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as mixed_table_projection
    participant p1 as normalize_markdown
    participant p2 as replace
    participant p3 as splitlines
    participant p4 as endswith
    participant p5 as description_table_cells
    participant p6 as enumerate
    participant p7 as split_table_row
    participant p8 as strip
    participant p9 as startswith
    participant p10 as len
    participant p11 as extend
    participant p12 as append
    participant p13 as join
    participant p14 as index
    participant p15 as is_table_separator
    participant p16 as all
    participant p17 as fullmatch
    p0->>p1: normalize_markdown
    p1-->>p2: replace
    p1-->>p2: replace
    p0-->>p3: splitlines
    p0-->>p4: endswith
    p0->>p5: description_table_cells
    p5-->>p3: splitlines
    p5->>p1: normalize_markdown
    p5-->>p6: enumerate
    p5->>p7: split_table_row
    p7-->>p8: strip
    p7-->>p9: startswith
    p7-->>p4: endswith
    p7-->>p10: len
    p7-->>p10: len
    p7-->>p11: extend
    p7-->>p10: len
    p7-->>p12: append
    p7-->>p12: append
    p7-->>p8: strip
    p7-->>p13: join
    p7-->>p12: append
    p7-->>p12: append
    p7-->>p8: strip
    p7-->>p13: join
    p5-->>p14: index
    p5-->>p10: len
    p5->>p15: is_table_separator
    p15-->>p16: all
    p15-->>p17: fullmatch
```

> Call sequence diagram shows 30 of 71 interactions; 41 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. mixed_table_projection"]
    s2["2. normalize_markdown"]
    s3["3. replace"]
    s4["4. replace"]
    s5["5. splitlines"]
    s6["6. endswith"]
    s7["7. description_table_cells"]
    s8["8. splitlines"]
    s9["9. normalize_markdown"]
    s10["10. enumerate"]
    s11["11. split_table_row"]
    s12["12. strip"]
    s1 -->|"normalize_markdown(section_markdown)"| s2
    s2 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s3
    s2 -. "text.replace('\r\n', '\n')" .-> s4
    s1 -. "normalized.splitlines(data not statically known)" .-> s5
    s1 -. "normalized.endswith('\n')" .-> s6
    s1 -->|"description_table_cells(normalized)"| s7
    s7 -. "normalize_markdown(markdown).splitlines(data not statically known)" .-> s8
    s7 -->|"normalize_markdown(markdown)"| s9
    s7 -. "enumerate(lines)" .-> s10
    s7 -->|"split_table_row(line)"| s11
    s11 -. "line.strip(data not statically known)" .-> s12
    b0["mutation semantic_cells.sort"]
    s1 -. "mutation semantic_cells.sort" .-> b0
    b1["mutation cells.append"]
    s7 -. "mutation cells.append" .-> b1
    b2["mutation current.extend"]
    s11 -. "mutation current.extend" .-> b2
    b3["mutation current.append"]
    s11 -. "mutation current.append" .-> b3
    b4["mutation cells.append"]
    s11 -. "mutation cells.append" .-> b4
    b5["mutation current.append"]
    s11 -. "mutation current.append" .-> b5
    b6["mutation cells.append"]
    s11 -. "mutation cells.append" .-> b6
    click s1 "../modules/markdown_sections.md"
    click s2 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
    click s9 "../modules/markdown_sections.md"
    click s11 "../modules/markdown_sections.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
    class b5 boundary
    class b6 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `mixed_table_projection` | `section_markdown: str` | `MIXED_TABLE_DOMAIN`, `MIXED_TABLE_DOMAIN` | `row[...]`, `structural_lines[...]`, `semantic_by_key[...]` | `MixedTableProjection(...)` |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `splitlines` | - | - | - | - |
| `endswith` | - | - | - | - |
| `description_table_cells` | `markdown: str` | - | `occurrences[...]` | `tuple(...)`, `(...)` |
| `splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `enumerate` | - | - | - | - |
| `split_table_row` | `line: str` | - | - | `[...]`, `cells` |
| `strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| mixed_table_projection | normalize_markdown | 605 | `normalize_markdown(section_markdown)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n')` |
| mixed_table_projection | splitlines | 606 | `normalized.splitlines(data not statically known)` |
| mixed_table_projection | endswith | 607 | `normalized.endswith('\n')` |
| mixed_table_projection | description_table_cells | 608 | `description_table_cells(normalized)` |
| description_table_cells | splitlines | 558 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| description_table_cells | normalize_markdown | 558 | `normalize_markdown(markdown)` |
| description_table_cells | enumerate | 559 | `enumerate(lines)` |
| description_table_cells | split_table_row | 560 | `split_table_row(line)` |
| split_table_row | strip | 467 | `line.strip(data not statically known)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `semantic_cells.sort` | `mixed_table_projection` | 629 |
| mutation | `cells.append` | `description_table_cells` | 581 |
| mutation | `current.extend` | `split_table_row` | 478 |
| mutation | `current.append` | `split_table_row` | 486 |
| mutation | `cells.append` | `split_table_row` | 494 |
| mutation | `current.append` | `split_table_row` | 497 |
| mutation | `cells.append` | `split_table_row` | 499 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| external_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `mixed_table_projection` | `normalized.splitlines` | 606 |
| unresolved_call | `mixed_table_projection` | `normalized.endswith` | 607 |
| unresolved_call | `description_table_cells` | `normalize_markdown(markdown).splitlines` | 558 |
| unresolved_call | `description_table_cells` | `enumerate` | 559 |
| unresolved_call | `split_table_row` | `line.strip` | 467 |
| step_limit | `mixed_table_projection` | `first 12 steps` | 0 |

## Behavior

This flow starts at `mixed_table_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
