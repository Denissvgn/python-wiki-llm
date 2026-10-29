# replace_generated_section

**Entry point:** `replace_generated_section` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; representative internal continuations and boundary examples precede repeated helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as replace_generated_section
    participant p1 as section_body
    participant p2 as replace_section_body
    participant p3 as _markdown_lines
    participant p4 as section_bounds
    participant p5 as trim_blank_lines
    participant p6 as normalize_markdown
    participant p7 as _line_content
    participant p8 as re.findall
    participant p9 as existing.endswith
    participant p10 as updated.endswith
    participant p11 as (…).join(…).strip
    participant p12 as '\n'.join (src/llm_wiki_cli/services…n_sections.py:section_body)
    participant p13 as '\n'.join (src/llm_wiki_cli/services…ns.py:replace_section_body)
    participant p14 as heading.casefold
    participant p15 as len (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    participant p16 as enumerate
    participant p17 as lines[…].strip (src/llm_wiki_cli/services…ons.py:trim_blank_lines, 1)
    participant p18 as _LEGACY_HEADING_RE.match
    participant p19 as lines[…].strip (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    participant p20 as line.strip
    participant p21 as len (src/llm_wiki_cli/services…sections.py:section_bounds)
    participant p22 as match.group
    participant p23 as match.group(…).strip().casefold
    participant p24 as match.group(…).strip
    participant p25 as range
    participant p26 as lines[…].strip (src/llm_wiki_cli/services…sections.py:section_bounds)
    p0->>p1: section_body
    p0->>p2: replace_section_body
    p1->>p3: _markdown_lines
    p1->>p4: section_bounds
    p1->>p5: trim_blank_lines
    p3->>p6: normalize_markdown
    p3->>p7: _line_content
    p3-->>p8: re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))
    p0-->>p9: existing.endswith('\n')
    p0-->>p10: updated.endswith('\n')
    p1-->>p11: (…).join(…).strip
    p1-->>p12: '\n'.join (src/llm_wiki_cli/services…n_sections.py:section_body)(trim_blank_lines(...))
    p2-->>p13: '\n'.join (src/llm_wiki_cli/services…ns.py:replace_section_body)(...)
    p4-->>p14: heading.casefold
    p5-->>p15: len (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)(lines)
    p4-->>p16: enumerate(lines)
    p5-->>p17: lines[…].strip (src/llm_wiki_cli/services…ons.py:trim_blank_lines, 1)
    p4-->>p18: _LEGACY_HEADING_RE.match(line.strip(...))
    p5-->>p19: lines[…].strip (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    p4-->>p20: line.strip
    p4-->>p21: len (src/llm_wiki_cli/services…sections.py:section_bounds)(match.group(...))
    p4-->>p22: match.group(1)
    p4-->>p23: match.group(…).strip().casefold
    p4-->>p24: match.group(…).strip
    p4-->>p22: match.group(2)
    p4-->>p21: len (src/llm_wiki_cli/services…sections.py:section_bounds)(lines)
    p4-->>p25: range(..., len(...))
    p4-->>p21: len (src/llm_wiki_cli/services…sections.py:section_bounds)(lines)
    p4-->>p18: _LEGACY_HEADING_RE.match(...)
    p4-->>p26: lines[…].strip (src/llm_wiki_cli/services…sections.py:section_bounds)
```

> Call sequence diagram shows 30 of 39 interactions; 9 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 7 of 8 (1 omitted); unresolved 16 of 20 (4 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:normalize_markdown` | 5 | - | unresolved | 2 |
| `src/llm_wiki_cli/services/markdown_sections.py:_line_content` | 8 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 10 | - | external | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 10 | - | unresolved | 1 |
| `src/llm_wiki_cli/services/section_ownership.py:replace_generated_section` | 1 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 1 |
| `src/llm_wiki_cli/services/markdown_sections.py:replace_section_body` | 34 | [src/llm_wiki_cli/services/markdown_sections.py](../modules/markdown_sections.md) | internal | 3 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->

### Analysis coverage

**Effect analysis evaluated.** Flow assembly and source effect analysis are separate; empty observations do not prove an empty handler body.

Source steps: 12; effect analysis evaluated: 12, partial: 0, unavailable: 0. Counts include steps omitted from the displayed trace.

```mermaid
flowchart LR
    s1["1. replace_generated_section"]
    s2["2. section_body"]
    s3["3. _markdown_lines"]
    s4["4. re.findall"]
    s5["5. normalize_markdown"]
    s6["6. text.replace(…).replace"]
    s7["7. text.replace"]
    s8["8. _line_content"]
    s9["9. line.endswith"]
    s10["10. section_bounds"]
    s11["11. heading.casefold"]
    s12["12. enumerate"]
    s1 -->|"section_body(existing, heading)"| s2
    s2 -->|"_markdown_lines(markdown)"| s3
    s3 -. "re.findall('[^\\n]*\\n|[^\\n]+$', normalize_markdown(...))" .-> s4
    s3 -->|"normalize_markdown(markdown)"| s5
    s5 -. "text.replace(…).replace('\r', '\n')" .-> s6
    s5 -. "text.replace('\r\n', '\n')" .-> s7
    s3 -->|"_line_content(line)"| s8
    s8 -. "line.endswith('\n')" .-> s9
    s2 -->|"section_bounds(lines, heading)"| s10
    s10 -. "heading.casefold(data not statically known)" .-> s11
    s10 -. "enumerate(lines)" .-> s12
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/markdown_sections.md"
    click s3 "../modules/markdown_sections.md"
    click s5 "../modules/markdown_sections.md"
    click s8 "../modules/markdown_sections.md"
    click s10 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `replace_generated_section` | `existing: str`, `generated: str`, `heading: str` | - | - | `existing`, `existing`, `updated` |
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

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| replace_generated_section | section_body | 1260 | `section_body(existing, heading)` |
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
| step_limit | `replace_generated_section` | `first 12 steps` | 0 |

## Behavior

This flow starts at `replace_generated_section` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
