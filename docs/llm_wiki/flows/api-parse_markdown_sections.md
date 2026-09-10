# parse_markdown_sections

**Entry point:** `parse_markdown_sections` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_markdown_sections
    participant p1 as parse_markdown_document
    participant p2 as isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p3 as TypeError
    participant p4 as ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)
    participant p5 as normalize_markdown
    participant p6 as text.replace(…).replace
    participant p7 as text.replace
    participant p8 as list
    participant p9 as _iter_structural_headings
    participant p10 as markdown.splitlines
    participant p11 as _frontmatter_extent
    participant p12 as _line_content(…).removeprefix(…).strip
    participant p13 as _line_content(…).removeprefix
    participant p14 as _line_content
    participant p15 as line.endswith
    participant p16 as enumerate (src/llm_wiki_cli/services…ons.py:_frontmatter_extent)
    participant p17 as _line_content(…).strip
    participant p18 as len (src/llm_wiki_cli/services…ons.py:_frontmatter_extent)
    participant p19 as enumerate (src/llm_wiki_cli/services…:_iter_structural_headings)
    participant p20 as len (src/llm_wiki_cli/services…:_iter_structural_headings)
    participant p21 as re.fullmatch
    participant p22 as re.escape
    participant p23 as _FENCE_OPEN_RE.fullmatch
    participant p24 as opening.groups
    participant p25 as _atx_heading
    participant p26 as _ATX_HEADING_RE.fullmatch
    p0->>p1: parse_markdown_document
    p1-->>p2: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)
    p1-->>p3: TypeError
    p1-->>p2: isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)
    p1-->>p4: ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)
    p1->>p5: normalize_markdown
    p5-->>p6: text.replace(…).replace
    p5-->>p7: text.replace
    p1-->>p8: list
    p1->>p9: _iter_structural_headings
    p9-->>p10: markdown.splitlines
    p9->>p11: _frontmatter_extent
    p11-->>p12: _line_content(…).removeprefix(…).strip
    p11-->>p13: _line_content(…).removeprefix
    p11->>p14: _line_content
    p14-->>p15: line.endswith
    p11-->>p16: enumerate (src/llm_wiki_cli/services…ons.py:_frontmatter_extent)
    p11-->>p17: _line_content(…).strip
    p11->>p14: _line_content
    p11-->>p18: len (src/llm_wiki_cli/services…ons.py:_frontmatter_extent)
    p9-->>p19: enumerate (src/llm_wiki_cli/services…:_iter_structural_headings)
    p9->>p14: _line_content
    p9-->>p20: len (src/llm_wiki_cli/services…:_iter_structural_headings)
    p9-->>p21: re.fullmatch
    p9-->>p22: re.escape
    p9-->>p23: _FENCE_OPEN_RE.fullmatch
    p9-->>p24: opening.groups
    p9-->>p20: len (src/llm_wiki_cli/services…:_iter_structural_headings)
    p9->>p25: _atx_heading
    p25-->>p26: _ATX_HEADING_RE.fullmatch
```

> Call sequence diagram shows 30 of 86 interactions; 56 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_markdown_sections"]
    s2["2. parse_markdown_document"]
    s3["3. isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s4["4. TypeError"]
    s5["5. isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s6["6. ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)"]
    s7["7. normalize_markdown"]
    s8["8. text.replace(…).replace"]
    s9["9. text.replace"]
    s10["10. list"]
    s11["11. _iter_structural_headings"]
    s12["12. markdown.splitlines"]
    s1 -->|"parse_markdown_document(markdown, page_locator)"| s2
    s2 -. "isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(markdown, str)" .-> s3
    s2 -. "TypeError('markdown must be a string')" .-> s4
    s2 -. "isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)(page_locator, str)" .-> s5
    s2 -. "ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)('page_locator must be a non-empty string')" .-> s6
    s2 -->|"normalize_markdown(markdown)"| s7
    s7 -. "text.replace(…).replace('\r', '\n')" .-> s8
    s7 -. "text.replace('\r\n', '\n')" .-> s9
    s2 -. "list(_iter_structural_headings(...))" .-> s10
    s2 -->|"_iter_structural_headings(normalized)"| s11
    s11 -. "markdown.splitlines(keepends=True)" .-> s12
    b0["mutation stack.pop"]
    s2 -. "mutation stack.pop" .-> b0
    b1["mutation candidates.append"]
    s2 -. "mutation candidates.append" .-> b1
    b2["mutation stack.append"]
    s2 -. "mutation stack.append" .-> b2
    b3["mutation utf8_prefix_lengths.append"]
    s2 -. "mutation utf8_prefix_lengths.append" .-> b3
    b4["mutation sections.append"]
    s2 -. "mutation sections.append" .-> b4
    click s1 "../modules/markdown_sections.md"
    click s2 "../modules/markdown_sections.md"
    click s7 "../modules/markdown_sections.md"
    click s11 "../modules/markdown_sections.md"
    classDef boundary stroke:#b45309,stroke-dasharray: 4 2
    class b0 boundary
    class b1 boundary
    class b2 boundary
    class b3 boundary
    class b4 boundary
```

### Step data

| Step | Inputs | Reads | Writes | Returns |
|---|---|---|---|---|
| `parse_markdown_sections` | `markdown: str`, `page_locator: str` | - | - | `...` |
| `parse_markdown_document` | `markdown: str`, `page_locator: str` | `SECTION_ORDER_DOMAIN` | `occurrences[...]` | `MarkdownSectionDocument(...)` |
| `isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance (src/llm_wiki_cli/services…py:parse_markdown_document)` | - | - | - | - |
| `ValueError (src/llm_wiki_cli/services…py:parse_markdown_document)` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `text.replace(…).replace` | - | - | - | - |
| `text.replace` | - | - | - | - |
| `list` | - | - | - | - |
| `_iter_structural_headings` | `markdown: str` | - | - | - |
| `markdown.splitlines` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_markdown_sections | parse_markdown_document | 457 | `parse_markdown_document(markdown, page_locator)` |
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…py:parse_markdown_document) | 325 | `isinstance(markdown, str)` |
| parse_markdown_document | TypeError | 326 | `TypeError('markdown must be a string')` |
| parse_markdown_document | isinstance (src/llm_wiki_cli/services…py:parse_markdown_document) | 327 | `isinstance(page_locator, str)` |
| parse_markdown_document | ValueError (src/llm_wiki_cli/services…py:parse_markdown_document) | 328 | `ValueError('page_locator must be a non-empty string')` |
| parse_markdown_document | normalize_markdown | 330 | `normalize_markdown(markdown)` |
| normalize_markdown | text.replace(…).replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | text.replace | 81 | `text.replace('\r\n', '\n')` |
| parse_markdown_document | list | 331 | `list(_iter_structural_headings(...))` |
| parse_markdown_document | _iter_structural_headings | 331 | `_iter_structural_headings(normalized)` |
| _iter_structural_headings | markdown.splitlines | 251 | `markdown.splitlines(keepends=True)` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `stack.pop` | `parse_markdown_document` | 338 |
| mutation | `candidates.append` | `parse_markdown_document` | 350 |
| mutation | `stack.append` | `parse_markdown_document` | 362 |
| mutation | `utf8_prefix_lengths.append` | `parse_markdown_document` | 366 |
| mutation | `sections.append` | `parse_markdown_document` | 393 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| external_call | `parse_markdown_document` | `isinstance` | 325 |
| external_call | `parse_markdown_document` | `TypeError` | 326 |
| external_call | `parse_markdown_document` | `isinstance` | 327 |
| external_call | `parse_markdown_document` | `ValueError` | 328 |
| unresolved_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| unresolved_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `_iter_structural_headings` | `markdown.splitlines` | 251 |
| step_limit | `parse_markdown_sections` | `first 12 steps` | 0 |

## Behavior

This flow starts at `parse_markdown_sections` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
