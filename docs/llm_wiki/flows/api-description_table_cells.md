# description_table_cells

**Entry point:** `description_table_cells` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as description_table_cells
    participant p1 as normalize_markdown(…).splitlines
    participant p2 as normalize_markdown
    participant p3 as enumerate
    participant p4 as split_table_row
    participant p5 as headers.index
    participant p6 as len (src/llm_wiki_cli/services…py:description_table_cells)
    participant p7 as is_table_separator
    participant p8 as defaultdict
    participant p9 as range
    participant p10 as semantic_table_key
    participant p11 as cells.append (src/llm_wiki_cli/services…py:description_table_cells)
    participant p12 as TableDescriptionCell
    participant p13 as row[…].strip
    participant p14 as tuple
    participant p15 as text.replace(…).replace
    participant p16 as line.strip
    participant p17 as all
    participant p18 as re.sub
    participant p19 as text.replace
    participant p20 as stripped.startswith
    participant p21 as re.fullmatch
    participant p22 as key.replace(…).replace(…).replace
    participant p23 as stripped.endswith
    participant p24 as cell.replace
    participant p25 as key.replace(…).replace
    p0-->>p1: normalize_markdown(…).splitlines
    p0->>p2: normalize_markdown
    p0-->>p3: enumerate(lines)
    p0->>p4: split_table_row
    p0-->>p5: headers.index('Description')
    p0-->>p6: len (src/llm_wiki_cli/services…py:description_table_cells)(lines)
    p0->>p7: is_table_separator
    p0->>p4: split_table_row
    p0-->>p8: defaultdict(int)
    p0-->>p9: range(row_start, len(...))
    p0-->>p6: len (src/llm_wiki_cli/services…py:description_table_cells)(lines)
    p0->>p4: split_table_row
    p0-->>p6: len (src/llm_wiki_cli/services…py:description_table_cells)(row)
    p0->>p10: semantic_table_key
    p0-->>p11: cells.append (src/llm_wiki_cli/services…py:description_table_cells)(TableDescriptionCell(...))
    p0->>p12: TableDescriptionCell
    p0-->>p13: row[…].strip
    p0-->>p14: tuple(row)
    p0-->>p14: tuple(cells)
    p2-->>p15: text.replace(…).replace('\r', '\n')
    p4-->>p16: line.strip
    p7-->>p17: all(...)
    p10-->>p18: re.sub('\\[([^\\]]+)\\]\\([^)]+\\)', '\\1', cell)
    p2-->>p19: text.replace('\r\n', '\n')
    p4-->>p20: stripped.startswith('|')
    p7-->>p21: re.fullmatch(':?-{3,}:?', cell.replace(...))
    p10-->>p22: key.replace(…).replace(…).replace('\\|', '|')
    p4-->>p23: stripped.endswith('|')
    p7-->>p24: cell.replace(' ', '')
    p10-->>p25: key.replace(…).replace('*', '')
```

> Call sequence diagram shows 30 of 44 interactions; 14 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 11 of 14 (3 omitted); unresolved 12 of 23 (11 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 7 | - | external | 3 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 7 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/markdown_sections.py:semantic_table_key` | 35 | - | unresolved | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. description_table_cells"]
    s2["2. normalize_markdown(…).splitlines"]
    s3["3. normalize_markdown"]
    s4["4. text.replace(…).replace"]
    s5["5. text.replace"]
    s6["6. enumerate"]
    s7["7. split_table_row"]
    s8["8. line.strip"]
    s9["9. stripped.startswith"]
    s10["10. stripped.endswith"]
    s11["11. len (src/llm_wiki_cli/services…ections.py:split_table_row)"]
    s12["12. len (src/llm_wiki_cli/services…ections.py:split_table_row)"]
    s1 -. "normalize_markdown(…).splitlines(data not statically known)" .-> s2
    s1 -->|"normalize_markdown(markdown)"| s3
    s3 -. "text.replace(…).replace('\r', '\n')" .-> s4
    s3 -. "text.replace('\r\n', '\n')" .-> s5
    s1 -. "enumerate(lines)" .-> s6
    s1 -->|"split_table_row(line)"| s7
    s7 -. "line.strip(data not statically known)" .-> s8
    s7 -. "stripped.startswith('|')" .-> s9
    s7 -. "stripped.endswith('|')" .-> s10
    s7 -. "len (src/llm_wiki_cli/services…ections.py:split_table_row)(body)" .-> s11
    s7 -. "len (src/llm_wiki_cli/services…ections.py:split_table_row)(body)" .-> s12
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
| `normalize_markdown(…).splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `split_table_row` | `line: str` | - | - | `[...]`, `cells` |
| `line.strip` | - | - | - | - |
| `stripped.startswith` | - | - | - | - |
| `stripped.endswith` | - | - | - | - |
| `len (src/llm_wiki_cli/services…ections.py:split_table_row)` | - | - | - | - |
| `len (src/llm_wiki_cli/services…ections.py:split_table_row)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| description_table_cells | normalize_markdown(…).splitlines | 558 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| description_table_cells | normalize_markdown | 558 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| description_table_cells | enumerate | 559 | `enumerate(lines)` |
| description_table_cells | split_table_row | 560 | `split_table_row(line)` |
| split_table_row | line.strip | 467 | `line.strip(data not statically known)` |
| split_table_row | stripped.startswith | 468 | `stripped.startswith('\|')` |
| split_table_row | stripped.endswith | 468 | `stripped.endswith('\|')` |
| split_table_row | len (src/llm_wiki_cli/services…ections.py:split_table_row) | 475 | `len(body)` |
| split_table_row | len (src/llm_wiki_cli/services…ections.py:split_table_row) | 477 | `len(body)` |

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
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| external_call | `description_table_cells` | `enumerate` | 559 |
| unresolved_call | `split_table_row` | `line.strip` | 467 |
| unresolved_call | `split_table_row` | `stripped.startswith` | 468 |
| unresolved_call | `split_table_row` | `stripped.endswith` | 468 |
| step_limit | `description_table_cells` | `first 12 steps` | 0 |

## Behavior

This flow starts at `description_table_cells` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
