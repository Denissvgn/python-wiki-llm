# table_description_cells

**Entry point:** `table_description_cells` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as table_description_cells
    participant p1 as _markdown_lines
    participant p2 as section_bounds
    participant p3 as split_table_row
    participant p4 as is_table_separator
    participant p5 as semantic_table_key
    participant p6 as is_placeholder_description
    participant p7 as normalize_markdown
    participant p8 as _line_content
    participant p9 as range (src/llm_wiki_cli/services…py:table_description_cells)
    participant p10 as headers.index
    participant p11 as len (src/llm_wiki_cli/services…py:table_description_cells)
    participant p12 as row[…].strip
    participant p13 as re.findall
    participant p14 as heading.casefold
    participant p15 as line.strip (src/llm_wiki_cli/services…ections.py:split_table_row)
    participant p16 as all
    participant p17 as re.sub
    participant p18 as value.strip
    participant p19 as enumerate
    participant p20 as stripped.startswith
    participant p21 as re.fullmatch
    participant p22 as key.replace(…).replace(…).replace
    participant p23 as _AUTO_GENERATED_RE.match
    participant p24 as _LEGACY_HEADING_RE.match
    participant p25 as stripped.endswith
    participant p26 as cell.replace
    participant p27 as key.replace(…).replace
    participant p28 as line.strip (src/llm_wiki_cli/services…sections.py:section_bounds)
    participant p29 as len (src/llm_wiki_cli/services…ections.py:split_table_row)
    p0->>p1: _markdown_lines
    p0->>p2: section_bounds
    p0->>p3: split_table_row
    p0->>p4: is_table_separator
    p0->>p5: semantic_table_key
    p0->>p6: is_placeholder_description
    p1->>p7: normalize_markdown
    p1->>p8: _line_content
    p0-->>p9: range (src/llm_wiki_cli/services…py:table_description_cells)(start, end)
    p0-->>p10: headers.index('Description')
    p0-->>p9: range (src/llm_wiki_cli/services…py:table_description_cells)(row_start, end)
    p0-->>p11: len (src/llm_wiki_cli/services…py:table_description_cells)(row)
    p0-->>p12: row[…].strip
    p1-->>p13: re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))
    p2-->>p14: heading.casefold
    p3-->>p15: line.strip (src/llm_wiki_cli/services…ections.py:split_table_row)
    p4-->>p16: all(...)
    p5-->>p17: re.sub('\\[([^\\]]+)\\]\\([^)]+\\)', '\\1', cell)
    p6-->>p18: value.strip
    p2-->>p19: enumerate(lines)
    p3-->>p20: stripped.startswith('|')
    p4-->>p21: re.fullmatch(':?-{3,}:?', cell.replace(...))
    p5-->>p22: key.replace(…).replace(…).replace('\\|', '|')
    p6-->>p23: _AUTO_GENERATED_RE.match(stripped)
    p2-->>p24: _LEGACY_HEADING_RE.match(line.strip(...))
    p3-->>p25: stripped.endswith('|')
    p4-->>p26: cell.replace(' ', '')
    p5-->>p27: key.replace(…).replace('*', '')
    p2-->>p28: line.strip (src/llm_wiki_cli/services…sections.py:section_bounds)
    p3-->>p29: len (src/llm_wiki_cli/services…ections.py:split_table_row)(body)
```

> Call sequence diagram shows 30 of 60 interactions; 30 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 9 of 16 (7 omitted); unresolved 13 of 34 (21 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:normalize_markdown` | 4 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_line_content` | 7 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 9 | - | external | 5 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 9 | - | unresolved | 7 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 27 | - | external | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 27 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/markdown_sections.py:table_description_cells` | 1 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:semantic_table_key` | 52 | - | unresolved | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 11; effect analysis evaluated: 11, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. table_description_cells"]
    s2["2. _markdown_lines"]
    s3["3. re.findall"]
    s4["4. normalize_markdown"]
    s5["5. text.replace(…).replace"]
    s6["6. text.replace"]
    s7["7. _line_content"]
    s8["8. line.endswith"]
    s9["9. section_bounds"]
    s10["10. heading.casefold"]
    s11["11. enumerate"]
    s12["12. _LEGACY_HEADING_RE.match"]
    s1 -->|"_markdown_lines(markdown)"| s2
    s2 -. "re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))" .-> s3
    s2 -->|"normalize_markdown(markdown)"| s4
    s4 -. "text.replace(…).replace('\r', '\n')" .-> s5
    s4 -. "text.replace('\r\n', '\n')" .-> s6
    s2 -->|"_line_content(line)"| s7
    s7 -. "line.endswith('\n')" .-> s8
    s1 -->|"section_bounds(lines, heading)"| s9
    s9 -. "heading.casefold(data not statically known)" .-> s10
    s9 -. "enumerate(lines)" .-> s11
    s9 -. "_LEGACY_HEADING_RE.match(line.strip(...))" .-> s12
    click s1 "../modules/markdown_sections.md"
    click s2 "../modules/markdown_sections.md"
    click s4 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
    click s9 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `table_description_cells` | `markdown: str`, `heading: str` | - | `descriptions[...]` | `{...}`, `descriptions`, `{...}` |
| `_markdown_lines` | `markdown: str`, `keepends: bool` | - | - | `...` |
| `re.findall` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `_line_content` | `line: str` | - | - | `...` |
| `line.endswith` | - | - | - | - |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |
| `heading.casefold` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `_LEGACY_HEADING_RE.match` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| table_description_cells | _markdown_lines | 840 | `_markdown_lines(markdown)` |
| _markdown_lines | re.findall | 218 | `re.findall('[^\\n]*\\n\|[^\\n]+$', normalize_markdown(...))` |
| _markdown_lines | normalize_markdown | 218 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 82 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 82 | `text.replace('\r\n', '\n')` |
| _markdown_lines | _line_content | 219 | `_line_content(line)` |
| _line_content | line.endswith | 212 | `line.endswith('\n')` |
| table_description_cells | section_bounds | 841 | `section_bounds(lines, heading)` |
| section_bounds | heading.casefold | 669 | `heading.casefold(data not statically known)` |
| section_bounds | enumerate | 670 | `enumerate(lines)` |
| section_bounds | _LEGACY_HEADING_RE.match | 671 | `_LEGACY_HEADING_RE.match(line.strip(...))` |

### Boundary effects

*No boundary-effect observations were captured in this static trace.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `_markdown_lines` | `re.findall` | 218 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 82 |
| unresolved_call | `normalize_markdown` | `text.replace` | 82 |
| unresolved_call | `_line_content` | `line.endswith` | 212 |
| unresolved_call | `section_bounds` | `heading.casefold` | 669 |
| external_call | `section_bounds` | `enumerate` | 670 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 671 |
| step_limit | `table_description_cells` | `first 12 steps` | 0 |

## Behavior

This flow starts at `table_description_cells` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
