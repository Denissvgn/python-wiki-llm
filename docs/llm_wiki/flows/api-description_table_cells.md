# description_table_cells

**Entry point:** `description_table_cells` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as description_table_cells
    participant p1 as _markdown_lines
    participant p2 as split_table_row
    participant p3 as is_table_separator
    participant p4 as semantic_table_key
    participant p5 as TableDescriptionCell
    participant p6 as normalize_markdown
    participant p7 as _line_content
    participant p8 as enumerate
    participant p9 as headers.index
    participant p10 as len (src/llm_wiki_cli/services…py:description_table_cells)
    participant p11 as defaultdict
    participant p12 as range
    participant p13 as cells.append (src/llm_wiki_cli/services…py:description_table_cells)
    participant p14 as row[…].strip
    participant p15 as tuple
    participant p16 as re.findall
    participant p17 as line.strip
    participant p18 as all
    participant p19 as re.sub
    participant p20 as stripped.startswith
    participant p21 as re.fullmatch
    participant p22 as key.replace(…).replace(…).replace
    participant p23 as stripped.endswith
    participant p24 as cell.replace
    participant p25 as key.replace(…).replace
    participant p26 as len (src/llm_wiki_cli/services…ections.py:split_table_row)
    participant p27 as key.replace
    p0->>p1: _markdown_lines
    p0->>p2: split_table_row
    p0->>p3: is_table_separator
    p0->>p4: semantic_table_key
    p0->>p5: TableDescriptionCell
    p1->>p6: normalize_markdown
    p1->>p7: _line_content
    p0-->>p8: enumerate(lines)
    p0-->>p9: headers.index('Description')
    p0-->>p10: len (src/llm_wiki_cli/services…py:description_table_cells)(lines)
    p0-->>p11: defaultdict(int)
    p0-->>p12: range(row_start, len(...))
    p0-->>p10: len (src/llm_wiki_cli/services…py:description_table_cells)(lines)
    p0-->>p10: len (src/llm_wiki_cli/services…py:description_table_cells)(row)
    p0-->>p13: cells.append (src/llm_wiki_cli/services…py:description_table_cells)(TableDescriptionCell(...))
    p0-->>p14: row[…].strip
    p0-->>p15: tuple(row)
    p0-->>p15: tuple(cells)
    p1-->>p16: re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))
    p2-->>p17: line.strip
    p3-->>p18: all(...)
    p4-->>p19: re.sub('\\[([^\\]]+)\\]\\([^)]+\\)', '\\1', cell)
    p2-->>p20: stripped.startswith('|')
    p3-->>p21: re.fullmatch(':?-{3,}:?', cell.replace(...))
    p4-->>p22: key.replace(…).replace(…).replace('\\|', '|')
    p2-->>p23: stripped.endswith('|')
    p3-->>p24: cell.replace(' ', '')
    p4-->>p25: key.replace(…).replace('*', '')
    p2-->>p26: len (src/llm_wiki_cli/services…ections.py:split_table_row)(body)
    p4-->>p27: key.replace('`', '')
```

> Call sequence diagram shows 30 of 47 interactions; 17 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 13 of 15 (2 omitted); unresolved 10 of 23 (13 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:normalize_markdown` | 4 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_line_content` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 10 | - | external | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 10 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/markdown_sections.py:description_table_cells` | 1 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:semantic_table_key` | 38 | - | unresolved | 1 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis partially available.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 10; effect analysis evaluated: 9, partial: 0, unavailable: 1. Counts include steps omitted from the displayed trace.

- Callable record unavailable; the selected entry symbol has no represented callable body.
- Effect collector totals unavailable; observed counts cover captured records only.

| Step | Callable record | Effect analysis | Collector totals |
|---|---|---|---|
| `description_table_cells` | `available` | `evaluated` | `available` |
| `_markdown_lines` | `available` | `evaluated` | `available` |
| `re.findall` | `not_applicable` | `not_applicable` | `not_applicable` |
| `normalize_markdown` | `available` | `evaluated` | `available` |
| `text.replace(…).replace` | `not_applicable` | `not_applicable` | `not_applicable` |
| `text.replace` | `not_applicable` | `not_applicable` | `not_applicable` |
| `_line_content` | `available` | `evaluated` | `available` |
| `line.endswith` | `not_applicable` | `not_applicable` | `not_applicable` |
| `enumerate` | `not_applicable` | `not_applicable` | `not_applicable` |
| `split_table_row` | `available` | `evaluated` | `available` |
| `line.strip` | `not_applicable` | `not_applicable` | `not_applicable` |
| `stripped.startswith` | `not_applicable` | `not_applicable` | `not_applicable` |

```mermaid
flowchart LR
    s1["1. description_table_cells"]
    s2["2. _markdown_lines"]
    s3["3. re.findall"]
    s4["4. normalize_markdown"]
    s5["5. text.replace(…).replace"]
    s6["6. text.replace"]
    s7["7. _line_content"]
    s8["8. line.endswith"]
    s9["9. enumerate"]
    s10["10. split_table_row"]
    s11["11. line.strip"]
    s12["12. stripped.startswith"]
    s1 -->|"_markdown_lines(markdown)"| s2
    s2 -. "re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))" .-> s3
    s2 -->|"normalize_markdown(markdown)"| s4
    s4 -. "text.replace(…).replace('\r', '\n')" .-> s5
    s4 -. "text.replace('\r\n', '\n')" .-> s6
    s2 -->|"_line_content(line)"| s7
    s7 -. "line.endswith('\n')" .-> s8
    s1 -. "enumerate(lines)" .-> s9
    s1 -->|"split_table_row(line)"| s10
    s10 -. "line.strip(data not statically known)" .-> s11
    s10 -. "stripped.startswith('|')" .-> s12
    b0["mutation cells.append"]
    s1 -. "mutation cells.append" .-> b0
    b1["mutation current.extend"]
    s10 -. "mutation current.extend" .-> b1
    b2["mutation current.append"]
    s10 -. "mutation current.append" .-> b2
    b3["mutation cells.append"]
    s10 -. "mutation cells.append" .-> b3
    b4["mutation current.append"]
    s10 -. "mutation current.append" .-> b4
    b5["mutation cells.append"]
    s10 -. "mutation cells.append" .-> b5
    click s1 "../modules/markdown_sections.md"
    click s2 "../modules/markdown_sections.md"
    click s4 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
    click s10 "../modules/markdown_sections.md"
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
| `_markdown_lines` | `markdown: str`, `keepends: bool` | - | - | `...` |
| `re.findall` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `_line_content` | `line: str` | - | - | `...` |
| `line.endswith` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `split_table_row` | `line: str` | - | - | `[...]`, `cells` |
| `line.strip` | - | - | - | - |
| `stripped.startswith` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| description_table_cells | _markdown_lines | 566 | `_markdown_lines(markdown)` |
| _markdown_lines | re.findall | 218 | `re.findall('[^\\n]*\\n\|[^\\n]+$', normalize_markdown(...))` |
| _markdown_lines | normalize_markdown | 218 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 82 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 82 | `text.replace('\r\n', '\n')` |
| _markdown_lines | _line_content | 219 | `_line_content(line)` |
| _line_content | line.endswith | 212 | `line.endswith('\n')` |
| description_table_cells | enumerate | 567 | `enumerate(lines)` |
| description_table_cells | split_table_row | 568 | `split_table_row(line)` |
| split_table_row | line.strip | 475 | `line.strip(data not statically known)` |
| split_table_row | stripped.startswith | 476 | `stripped.startswith('\|')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `cells.append` | `description_table_cells` | 589 |
| mutation | `current.extend` | `split_table_row` | 486 |
| mutation | `current.append` | `split_table_row` | 494 |
| mutation | `cells.append` | `split_table_row` | 502 |
| mutation | `current.append` | `split_table_row` | 505 |
| mutation | `cells.append` | `split_table_row` | 507 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_markdown_lines` | `re.findall` | 218 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 82 |
| unresolved_call | `normalize_markdown` | `text.replace` | 82 |
| unresolved_call | `_line_content` | `line.endswith` | 212 |
| external_call | `description_table_cells` | `enumerate` | 567 |
| unresolved_call | `split_table_row` | `line.strip` | 475 |
| unresolved_call | `split_table_row` | `stripped.startswith` | 476 |
| step_limit | `description_table_cells` | `first 12 steps` | 0 |

## Behavior

This flow starts at `description_table_cells` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
