# section_body

**Entry point:** `section_body` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as section_body
    participant p1 as _markdown_lines
    participant p2 as section_bounds
    participant p3 as (…).join(…).strip
    participant p4 as '\n'.join
    participant p5 as trim_blank_lines
    participant p6 as re.findall
    participant p7 as heading.casefold
    participant p8 as len (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    participant p9 as normalize_markdown
    participant p10 as enumerate
    participant p11 as lines[…].strip (src/llm_wiki_cli/services…ons.py:trim_blank_lines, 1)
    participant p12 as _line_content
    participant p13 as _LEGACY_HEADING_RE.match
    participant p14 as lines[…].strip (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    participant p15 as line.strip
    participant p16 as len (src/llm_wiki_cli/services…sections.py:section_bounds)
    participant p17 as match.group
    participant p18 as match.group(…).strip().casefold
    participant p19 as match.group(…).strip
    participant p20 as range
    participant p21 as lines[…].strip (src/llm_wiki_cli/services…sections.py:section_bounds)
    participant p22 as next_match.group
    participant p23 as text.replace(…).replace
    participant p24 as line.endswith
    participant p25 as text.replace
    p0->>p1: _markdown_lines
    p0->>p2: section_bounds
    p0-->>p3: (…).join(…).strip
    p0-->>p4: '\n'.join(trim_blank_lines(...))
    p0->>p5: trim_blank_lines
    p1-->>p6: re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))
    p2-->>p7: heading.casefold
    p5-->>p8: len (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)(lines)
    p1->>p9: normalize_markdown
    p2-->>p10: enumerate(lines)
    p5-->>p11: lines[…].strip (src/llm_wiki_cli/services…ons.py:trim_blank_lines, 1)
    p1->>p12: _line_content
    p2-->>p13: _LEGACY_HEADING_RE.match(line.strip(...))
    p5-->>p14: lines[…].strip (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    p2-->>p15: line.strip
    p2-->>p16: len (src/llm_wiki_cli/services…sections.py:section_bounds)(match.group(...))
    p2-->>p17: match.group(1)
    p2-->>p18: match.group(…).strip().casefold
    p2-->>p19: match.group(…).strip
    p2-->>p17: match.group(2)
    p2-->>p16: len (src/llm_wiki_cli/services…sections.py:section_bounds)(lines)
    p2-->>p20: range(..., len(...))
    p2-->>p16: len (src/llm_wiki_cli/services…sections.py:section_bounds)(lines)
    p2-->>p13: _LEGACY_HEADING_RE.match(...)
    p2-->>p21: lines[…].strip (src/llm_wiki_cli/services…sections.py:section_bounds)
    p2-->>p16: len (src/llm_wiki_cli/services…sections.py:section_bounds)(next_match.group(...))
    p2-->>p22: next_match.group(1)
    p9-->>p23: text.replace(…).replace('\r', '\n')
    p12-->>p24: line.endswith('\n')
    p9-->>p25: text.replace('\r\n', '\n')
```

> Call sequence diagram shows 30 of 30 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 8 of 8 (0 omitted); unresolved 17 of 17 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 6; effect analysis evaluated: 6, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. section_body"]
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
| `section_body` | `markdown: str`, `heading: str` | - | - | `None`, `...` |
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
| section_body | _markdown_lines | 703 | `_markdown_lines(markdown)` |
| _markdown_lines | re.findall | 218 | `re.findall('[^\\n]*\\n\|[^\\n]+$', normalize_markdown(...))` |
| _markdown_lines | normalize_markdown | 218 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 82 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 82 | `text.replace('\r\n', '\n')` |
| _markdown_lines | _line_content | 219 | `_line_content(line)` |
| _line_content | line.endswith | 212 | `line.endswith('\n')` |
| section_body | section_bounds | 704 | `section_bounds(lines, heading)` |
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
| step_limit | `section_body` | `first 12 steps` | 0 |

## Behavior

This flow starts at `section_body` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
