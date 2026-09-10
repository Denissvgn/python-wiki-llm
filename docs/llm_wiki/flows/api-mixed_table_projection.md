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
    participant p2 as text.replace(…).replace
    participant p3 as text.replace
    participant p4 as normalized.splitlines
    participant p5 as normalized.endswith
    participant p6 as description_table_cells
    participant p7 as normalize_markdown(…).splitlines
    participant p8 as enumerate
    participant p9 as split_table_row
    participant p10 as line.strip
    participant p11 as stripped.startswith
    participant p12 as stripped.endswith
    participant p13 as len (src/llm_wiki_cli/services…ections.py:split_table_row)
    participant p14 as current.extend
    participant p15 as current.append
    participant p16 as cells.append (src/llm_wiki_cli/services…ections.py:split_table_row)
    participant p17 as (…).join(…).strip
    participant p18 as ''.join
    participant p19 as headers.index
    participant p20 as len (src/llm_wiki_cli/services…py:description_table_cells)
    participant p21 as is_table_separator
    participant p22 as all
    participant p23 as re.fullmatch
    p0->>p1: normalize_markdown
    p1-->>p2: text.replace(…).replace
    p1-->>p3: text.replace
    p0-->>p4: normalized.splitlines
    p0-->>p5: normalized.endswith
    p0->>p6: description_table_cells
    p6-->>p7: normalize_markdown(…).splitlines
    p6->>p1: normalize_markdown
    p6-->>p8: enumerate
    p6->>p9: split_table_row
    p9-->>p10: line.strip
    p9-->>p11: stripped.startswith
    p9-->>p12: stripped.endswith
    p9-->>p13: len (src/llm_wiki_cli/services…ections.py:split_table_row)
    p9-->>p13: len (src/llm_wiki_cli/services…ections.py:split_table_row)
    p9-->>p14: current.extend
    p9-->>p13: len (src/llm_wiki_cli/services…ections.py:split_table_row)
    p9-->>p15: current.append
    p9-->>p16: cells.append (src/llm_wiki_cli/services…ections.py:split_table_row)
    p9-->>p17: (…).join(…).strip
    p9-->>p18: ''.join
    p9-->>p15: current.append
    p9-->>p16: cells.append (src/llm_wiki_cli/services…ections.py:split_table_row)
    p9-->>p17: (…).join(…).strip
    p9-->>p18: ''.join
    p6-->>p19: headers.index
    p6-->>p20: len (src/llm_wiki_cli/services…py:description_table_cells)
    p6->>p21: is_table_separator
    p21-->>p22: all
    p21-->>p23: re.fullmatch
```

> Call sequence diagram shows 30 of 71 interactions; 41 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. mixed_table_projection"]
    s2["2. normalize_markdown"]
    s3["3. text.replace(…).replace"]
    s4["4. text.replace"]
    s5["5. normalized.splitlines"]
    s6["6. normalized.endswith"]
    s7["7. description_table_cells"]
    s8["8. normalize_markdown(…).splitlines"]
    s9["9. normalize_markdown"]
    s10["10. enumerate"]
    s11["11. split_table_row"]
    s12["12. line.strip"]
    s1 -->|"normalize_markdown(section_markdown)"| s2
    s2 -. "text.replace(…).replace('\r', '\n')" .-> s3
    s2 -. "text.replace('\r\n', '\n')" .-> s4
    s1 -. "normalized.splitlines(data not statically known)" .-> s5
    s1 -. "normalized.endswith('\n')" .-> s6
    s1 -->|"description_table_cells(normalized)"| s7
    s7 -. "normalize_markdown(…).splitlines(data not statically known)" .-> s8
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
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `normalized.splitlines` | - | - | - | - |
| `normalized.endswith` | - | - | - | - |
| `description_table_cells` | `markdown: str` | - | `occurrences[...]` | `tuple(...)`, `(...)` |
| `normalize_markdown(…).splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `enumerate` | - | - | - | - |
| `split_table_row` | `line: str` | - | - | `[...]`, `cells` |
| `line.strip` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| mixed_table_projection | normalize_markdown | 605 | `normalize_markdown(section_markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| mixed_table_projection | normalized.splitlines | 606 | `normalized.splitlines(data not statically known)` |
| mixed_table_projection | normalized.endswith | 607 | `normalized.endswith('\n')` |
| mixed_table_projection | description_table_cells | 608 | `description_table_cells(normalized)` |
| description_table_cells | normalize_markdown(…).splitlines | 558 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| description_table_cells | normalize_markdown | 558 | `normalize_markdown(markdown)` |
| description_table_cells | enumerate | 559 | `enumerate(lines)` |
| description_table_cells | split_table_row | 560 | `split_table_row(line)` |
| split_table_row | line.strip | 467 | `line.strip(data not statically known)` |

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
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `mixed_table_projection` | `normalized.splitlines` | 606 |
| unresolved_call | `mixed_table_projection` | `normalized.endswith` | 607 |
| unresolved_call | `description_table_cells` | `normalize_markdown(markdown).splitlines` | 558 |
| external_call | `description_table_cells` | `enumerate` | 559 |
| unresolved_call | `split_table_row` | `line.strip` | 467 |
| step_limit | `mixed_table_projection` | `first 12 steps` | 0 |

## Behavior

This flow starts at `mixed_table_projection` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
