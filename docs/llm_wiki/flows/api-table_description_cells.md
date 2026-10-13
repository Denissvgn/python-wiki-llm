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
    participant p1 as normalize_markdown
    participant p2 as section_bounds
    participant p3 as split_table_row
    participant p4 as is_table_separator
    participant p5 as semantic_table_key
    participant p6 as is_placeholder_description
    participant p7 as range (src/llm_wiki_cli/services…py:table_description_cells)
    participant p8 as normalize_markdown(…).splitlines
    participant p9 as headers.index
    participant p10 as len (src/llm_wiki_cli/services…py:table_description_cells)
    participant p11 as row[…].strip
    participant p12 as text.replace(…).replace
    participant p13 as heading.casefold
    participant p14 as line.strip (src/llm_wiki_cli/services…ections.py:split_table_row)
    participant p15 as all
    participant p16 as re.sub
    participant p17 as value.strip
    participant p18 as text.replace
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
    p0->>p1: normalize_markdown
    p0->>p2: section_bounds
    p0->>p3: split_table_row
    p0->>p4: is_table_separator
    p0->>p5: semantic_table_key
    p0->>p6: is_placeholder_description
    p0-->>p7: range (src/llm_wiki_cli/services…py:table_description_cells)(start, end)
    p0-->>p8: normalize_markdown(…).splitlines
    p0-->>p9: headers.index('Description')
    p0-->>p7: range (src/llm_wiki_cli/services…py:table_description_cells)(row_start, end)
    p0-->>p10: len (src/llm_wiki_cli/services…py:table_description_cells)(row)
    p0-->>p11: row[…].strip
    p1-->>p12: text.replace(…).replace('\r', '\n')
    p2-->>p13: heading.casefold
    p3-->>p14: line.strip (src/llm_wiki_cli/services…ections.py:split_table_row)
    p4-->>p15: all(...)
    p5-->>p16: re.sub('\\[([^\\]]+)\\]\\([^)]+\\)', '\\1', cell)
    p6-->>p17: value.strip
    p1-->>p18: text.replace('\r\n', '\n')
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

> Call sequence diagram shows 30 of 57 interactions; 27 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 15 (7 omitted); unresolved 16 of 34 (18 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 6 | - | external | 5 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 6 | - | unresolved | 7 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 24 | - | external | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:split_table_row` | 24 | - | unresolved | 9 |
| `src/llm_wiki_cli/services/markdown_sections.py:table_description_cells` | 1 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:semantic_table_key` | 49 | - | unresolved | 2 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. table_description_cells"]
    s2["2. normalize_markdown(…).splitlines"]
    s3["3. normalize_markdown"]
    s4["4. text.replace(…).replace"]
    s5["5. text.replace"]
    s6["6. section_bounds"]
    s7["7. heading.casefold"]
    s8["8. enumerate"]
    s9["9. _LEGACY_HEADING_RE.match"]
    s10["10. line.strip (src/llm_wiki_cli/services…sections.py:section_bounds)"]
    s11["11. len (src/llm_wiki_cli/services…sections.py:section_bounds)"]
    s12["12. match.group"]
    s1 -. "normalize_markdown(…).splitlines(data not statically known)" .-> s2
    s1 -->|"normalize_markdown(markdown)"| s3
    s3 -. "text.replace(…).replace('\r', '\n')" .-> s4
    s3 -. "text.replace('\r\n', '\n')" .-> s5
    s1 -->|"section_bounds(lines, heading)"| s6
    s6 -. "heading.casefold(data not statically known)" .-> s7
    s6 -. "enumerate(lines)" .-> s8
    s6 -. "_LEGACY_HEADING_RE.match(line.strip(...))" .-> s9
    s6 -. "line.strip (src/llm_wiki_cli/services…sections.py:section_bounds)(data not statically known)" .-> s10
    s6 -. "len (src/llm_wiki_cli/services…sections.py:section_bounds)(match.group(...))" .-> s11
    s6 -. "match.group(1)" .-> s12
    click s1 "../modules/markdown_sections.md"
    click s3 "../modules/markdown_sections.md"
    click s6 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `table_description_cells` | `markdown: str`, `heading: str` | - | `descriptions[...]` | `{...}`, `descriptions`, `{...}` |
| `normalize_markdown(…).splitlines` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |
| `heading.casefold` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `_LEGACY_HEADING_RE.match` | - | - | - | - |
| `line.strip (src/llm_wiki_cli/services…sections.py:section_bounds)` | - | - | - | - |
| `len (src/llm_wiki_cli/services…sections.py:section_bounds)` | - | - | - | - |
| `match.group` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| table_description_cells | normalize_markdown(…).splitlines | 832 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| table_description_cells | normalize_markdown | 832 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| table_description_cells | section_bounds | 833 | `section_bounds(lines, heading)` |
| section_bounds | heading.casefold | 661 | `heading.casefold(data not statically known)` |
| section_bounds | enumerate | 662 | `enumerate(lines)` |
| section_bounds | _LEGACY_HEADING_RE.match | 663 | `_LEGACY_HEADING_RE.match(line.strip(...))` |
| section_bounds | line.strip (src/llm_wiki_cli/services…sections.py:section_bounds) | 663 | `line.strip(data not statically known)` |
| section_bounds | len (src/llm_wiki_cli/services…sections.py:section_bounds) | 666 | `len(match.group(...))` |
| section_bounds | match.group | 666 | `match.group(1)` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `table_description_cells` | `normalize_markdown(markdown).splitlines` | 832 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_bounds` | `heading.casefold` | 661 |
| external_call | `section_bounds` | `enumerate` | 662 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 663 |
| unresolved_call | `section_bounds` | `line.strip` | 663 |
| unresolved_call | `section_bounds` | `match.group` | 666 |
| step_limit | `table_description_cells` | `first 12 steps` | 0 |

## Behavior

This flow starts at `table_description_cells` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
