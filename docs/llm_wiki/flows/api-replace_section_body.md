# replace_section_body

**Entry point:** `replace_section_body` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as replace_section_body
    participant p1 as _markdown_lines
    participant p2 as section_bounds
    participant p3 as '\n'.join
    participant p4 as re.findall
    participant p5 as heading.casefold
    participant p6 as normalize_markdown
    participant p7 as enumerate
    participant p8 as _line_content
    participant p9 as _LEGACY_HEADING_RE.match
    participant p10 as line.strip
    participant p11 as len
    participant p12 as match.group
    participant p13 as match.group(…).strip().casefold
    participant p14 as match.group(…).strip
    participant p15 as range
    participant p16 as lines[…].strip
    participant p17 as next_match.group
    participant p18 as text.replace(…).replace
    participant p19 as line.endswith
    participant p20 as text.replace
    p0->>p1: _markdown_lines
    p0->>p2: section_bounds
    p0->>p1: _markdown_lines
    p0-->>p3: '\n'.join(...)
    p1-->>p4: re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))
    p2-->>p5: heading.casefold
    p1->>p6: normalize_markdown
    p2-->>p7: enumerate(lines)
    p1->>p8: _line_content
    p2-->>p9: _LEGACY_HEADING_RE.match(line.strip(...))
    p2-->>p10: line.strip
    p2-->>p11: len(match.group(...))
    p2-->>p12: match.group(1)
    p2-->>p13: match.group(…).strip().casefold
    p2-->>p14: match.group(…).strip
    p2-->>p12: match.group(2)
    p2-->>p11: len(lines)
    p2-->>p15: range(..., len(...))
    p2-->>p11: len(lines)
    p2-->>p9: _LEGACY_HEADING_RE.match(...)
    p2-->>p16: lines[…].strip
    p2-->>p11: len(next_match.group(...))
    p2-->>p17: next_match.group(1)
    p6-->>p18: text.replace(…).replace('\r', '\n')
    p8-->>p19: line.endswith('\n')
    p6-->>p20: text.replace('\r\n', '\n')
```

> Call sequence diagram shows 26 of 26 interactions; 0 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 7 (0 omitted); unresolved 14 of 14 (0 omitted). These counts cover the captured static trace.
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 6; effect analysis evaluated: 6, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. replace_section_body"]
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
| `replace_section_body` | `markdown: str`, `heading: str`, `body: str` | - | - | `markdown`, `...` |
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
| replace_section_body | _markdown_lines | 714 | `_markdown_lines(markdown)` |
| _markdown_lines | re.findall | 218 | `re.findall('[^\\n]*\\n\|[^\\n]+$', normalize_markdown(...))` |
| _markdown_lines | normalize_markdown | 218 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 82 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 82 | `text.replace('\r\n', '\n')` |
| _markdown_lines | _line_content | 219 | `_line_content(line)` |
| _line_content | line.endswith | 212 | `line.endswith('\n')` |
| replace_section_body | section_bounds | 715 | `section_bounds(lines, heading)` |
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
| step_limit | `replace_section_body` | `first 12 steps` | 0 |

## Behavior

This flow starts at `replace_section_body` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
