# replace_generated_section

**Entry point:** `replace_generated_section` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md)

## Call sequence

> Static overview in presentation order, not runtime execution order. Arrows retain captured callers; siblings are shown before deeper helper detail.

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as replace_generated_section
    participant p1 as section_body
    participant p2 as replace_section_body
    participant p3 as existing.endswith
    participant p4 as updated.endswith
    participant p5 as normalize_markdown(…).splitlines (src/llm_wiki_cli/services…n_sections.py:section_body)
    participant p6 as normalize_markdown(…).splitlines (src/llm_wiki_cli/services…ns.py:replace_section_body)
    participant p7 as normalize_markdown
    participant p8 as section_bounds
    participant p9 as (…).join(…).strip
    participant p10 as body.splitlines
    participant p11 as '\n'.join (src/llm_wiki_cli/services…n_sections.py:section_body)
    participant p12 as '\n'.join (src/llm_wiki_cli/services…ns.py:replace_section_body)
    participant p13 as trim_blank_lines
    participant p14 as text.replace(…).replace
    participant p15 as heading.casefold
    participant p16 as len (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    participant p17 as text.replace
    participant p18 as enumerate
    participant p19 as lines[…].strip (src/llm_wiki_cli/services…ons.py:trim_blank_lines, 1)
    participant p20 as _LEGACY_HEADING_RE.match
    participant p21 as lines[…].strip (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    participant p22 as line.strip
    participant p23 as len (src/llm_wiki_cli/services…sections.py:section_bounds)
    participant p24 as match.group
    participant p25 as match.group(…).strip().casefold
    participant p26 as match.group(…).strip
    p0->>p1: section_body
    p0->>p1: section_body
    p0->>p2: replace_section_body
    p0-->>p3: existing.endswith('\n')
    p0-->>p4: updated.endswith('\n')
    p1-->>p5: normalize_markdown(…).splitlines (src/llm_wiki_cli/services…n_sections.py:section_body)
    p2-->>p6: normalize_markdown(…).splitlines (src/llm_wiki_cli/services…ns.py:replace_section_body)
    p1->>p7: normalize_markdown
    p2->>p7: normalize_markdown
    p1->>p8: section_bounds
    p2->>p8: section_bounds
    p1-->>p9: (…).join(…).strip
    p2-->>p10: body.splitlines
    p1-->>p11: '\n'.join (src/llm_wiki_cli/services…n_sections.py:section_body)(trim_blank_lines(...))
    p2-->>p12: '\n'.join (src/llm_wiki_cli/services…ns.py:replace_section_body)(...)
    p1->>p13: trim_blank_lines
    p7-->>p14: text.replace(…).replace('\r', '\n')
    p8-->>p15: heading.casefold
    p13-->>p16: len (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)(lines)
    p7-->>p17: text.replace('\r\n', '\n')
    p8-->>p18: enumerate(lines)
    p13-->>p19: lines[…].strip (src/llm_wiki_cli/services…ons.py:trim_blank_lines, 1)
    p8-->>p20: _LEGACY_HEADING_RE.match(line.strip(...))
    p13-->>p21: lines[…].strip (src/llm_wiki_cli/services…ctions.py:trim_blank_lines)
    p8-->>p22: line.strip
    p8-->>p23: len (src/llm_wiki_cli/services…sections.py:section_bounds)(match.group(...))
    p8-->>p24: match.group(1)
    p8-->>p25: match.group(…).strip().casefold
    p8-->>p26: match.group(…).strip
    p8-->>p24: match.group(2)
```

> Call sequence diagram shows 30 of 37 interactions; 7 omitted to keep the visualization within the 30-interaction and generated-diagram limits, with uncertain identities omitted rather than inferred.

> Captured boundary calls: external 3 of 7 (4 omitted); unresolved 19 of 22 (3 omitted). These counts cover the captured static trace.

Omitted captured detail, grouped by actual caller occurrence and target module:

| Caller | Parent step | Target module | Kind | Omitted interactions |
| --- | --- | --- | --- | --- |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 7 | - | external | 4 |
| `src/llm_wiki_cli/services/markdown_sections.py:section_bounds` | 7 | - | unresolved | 3 |
> Detailed flow queries retain their own coverage and limits; omitted paths may execute at runtime.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. replace_generated_section"]
    s2["2. section_body"]
    s3["3. normalize_markdown(…).splitlines (src/llm_wiki_cli/services…n_sections.py:section_body)"]
    s4["4. normalize_markdown"]
    s5["5. text.replace(…).replace"]
    s6["6. text.replace"]
    s7["7. section_bounds"]
    s8["8. heading.casefold"]
    s9["9. enumerate"]
    s10["10. _LEGACY_HEADING_RE.match"]
    s11["11. line.strip"]
    s12["12. len (src/llm_wiki_cli/services…sections.py:section_bounds)"]
    s1 -->|"section_body(existing, heading)"| s2
    s2 -. "normalize_markdown(…).splitlines (src/llm_wiki_cli/services…n_sections.py:section_body)(data not statically known)" .-> s3
    s2 -->|"normalize_markdown(markdown)"| s4
    s4 -. "text.replace(…).replace('\r', '\n')" .-> s5
    s4 -. "text.replace('\r\n', '\n')" .-> s6
    s2 -->|"section_bounds(lines, heading)"| s7
    s7 -. "heading.casefold(data not statically known)" .-> s8
    s7 -. "enumerate(lines)" .-> s9
    s7 -. "_LEGACY_HEADING_RE.match(line.strip(...))" .-> s10
    s7 -. "line.strip(data not statically known)" .-> s11
    s7 -. "len (src/llm_wiki_cli/services…sections.py:section_bounds)(match.group(...))" .-> s12
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/markdown_sections.md"
    click s4 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `replace_generated_section` | `existing: str`, `generated: str`, `heading: str` | - | - | `existing`, `existing`, `updated` |
| `section_body` | `markdown: str`, `heading: str` | - | - | `None`, `...` |
| `normalize_markdown(…).splitlines (src/llm_wiki_cli/services…n_sections.py:section_body)` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `section_bounds` | `lines: list[str]`, `heading: str` | - | - | `(...)`, `None` |
| `heading.casefold` | - | - | - | - |
| `enumerate` | - | - | - | - |
| `_LEGACY_HEADING_RE.match` | - | - | - | - |
| `line.strip` | - | - | - | - |
| `len (src/llm_wiki_cli/services…sections.py:section_bounds)` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| replace_generated_section | section_body | 1236 | `section_body(existing, heading)` |
| section_body | normalize_markdown(…).splitlines (src/llm_wiki_cli/services…n_sections.py:section_body) | 695 | `normalize_markdown(markdown).splitlines(data not statically known)` |
| section_body | normalize_markdown | 695 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| section_body | section_bounds | 696 | `section_bounds(lines, heading)` |
| section_bounds | heading.casefold | 661 | `heading.casefold(data not statically known)` |
| section_bounds | enumerate | 662 | `enumerate(lines)` |
| section_bounds | _LEGACY_HEADING_RE.match | 663 | `_LEGACY_HEADING_RE.match(line.strip(...))` |
| section_bounds | line.strip | 663 | `line.strip(data not statically known)` |
| section_bounds | len (src/llm_wiki_cli/services…sections.py:section_bounds) | 666 | `len(match.group(...))` |

### Boundary effects

*No boundary effects detected.*

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `section_body` | `normalize_markdown(markdown).splitlines` | 695 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `section_bounds` | `heading.casefold` | 661 |
| external_call | `section_bounds` | `enumerate` | 662 |
| unresolved_call | `section_bounds` | `_LEGACY_HEADING_RE.match` | 663 |
| unresolved_call | `section_bounds` | `line.strip` | 663 |
| step_limit | `replace_generated_section` | `first 12 steps` | 0 |

## Behavior

This flow starts at `replace_generated_section` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
