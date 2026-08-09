# parse_markdown_document

**Entry point:** `parse_markdown_document` (`api`)
**Source:** [markdown_sections](../modules/markdown_sections.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as parse_markdown_document
    participant p1 as isinstance
    participant p2 as TypeError
    participant p3 as ValueError
    participant p4 as normalize_markdown
    participant p5 as replace
    participant p6 as list
    participant p7 as _iter_structural_headings
    participant p8 as splitlines
    participant p9 as _frontmatter_extent
    participant p10 as strip
    participant p11 as removeprefix
    participant p12 as _line_content
    participant p13 as endswith
    participant p14 as enumerate
    participant p15 as len
    participant p16 as fullmatch
    participant p17 as escape
    participant p18 as groups
    participant p19 as _atx_heading
    p0-->>p1: isinstance
    p0-->>p2: TypeError
    p0-->>p1: isinstance
    p0-->>p3: ValueError
    p0->>p4: normalize_markdown
    p4-->>p5: replace
    p4-->>p5: replace
    p0-->>p6: list
    p0->>p7: _iter_structural_headings
    p7-->>p8: splitlines
    p7->>p9: _frontmatter_extent
    p9-->>p10: strip
    p9-->>p11: removeprefix
    p9->>p12: _line_content
    p12-->>p13: endswith
    p9-->>p14: enumerate
    p9-->>p10: strip
    p9->>p12: _line_content
    p9-->>p15: len
    p7-->>p14: enumerate
    p7->>p12: _line_content
    p7-->>p15: len
    p7-->>p16: fullmatch
    p7-->>p17: escape
    p7-->>p16: fullmatch
    p7-->>p18: groups
    p7-->>p15: len
    p7->>p19: _atx_heading
    p19-->>p16: fullmatch
    p19-->>p18: groups
```

> Call sequence diagram shows 30 of 85 interactions; 55 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. parse_markdown_document"]
    s2["2. isinstance"]
    s3["3. TypeError"]
    s4["4. isinstance"]
    s5["5. ValueError"]
    s6["6. normalize_markdown"]
    s7["7. replace"]
    s8["8. replace"]
    s9["9. list"]
    s10["10. _iter_structural_headings"]
    s11["11. splitlines"]
    s12["12. _frontmatter_extent"]
    s1 -. "isinstance(markdown, str)" .-> s2
    s1 -. "TypeError('markdown must be a string')" .-> s3
    s1 -. "isinstance(page_locator, str)" .-> s4
    s1 -. "ValueError('page_locator must be a non-empty string')" .-> s5
    s1 -->|"normalize_markdown(markdown)"| s6
    s6 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s7
    s6 -. "text.replace('\r\n', '\n')" .-> s8
    s1 -. "list(_iter_structural_headings(...))" .-> s9
    s1 -->|"_iter_structural_headings(normalized)"| s10
    s10 -. "markdown.splitlines(keepends=True)" .-> s11
    s10 -->|"_frontmatter_extent(lines)"| s12
    b0["mutation stack.pop"]
    s1 -. "mutation stack.pop" .-> b0
    b1["mutation candidates.append"]
    s1 -. "mutation candidates.append" .-> b1
    b2["mutation stack.append"]
    s1 -. "mutation stack.append" .-> b2
    b3["mutation utf8_prefix_lengths.append"]
    s1 -. "mutation utf8_prefix_lengths.append" .-> b3
    b4["mutation sections.append"]
    s1 -. "mutation sections.append" .-> b4
    click s1 "../modules/markdown_sections.md"
    click s6 "../modules/markdown_sections.md"
    click s10 "../modules/markdown_sections.md"
    click s12 "../modules/markdown_sections.md"
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
| `parse_markdown_document` | `markdown: str`, `page_locator: str` | `SECTION_ORDER_DOMAIN` | `occurrences[...]` | `MarkdownSectionDocument(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `replace` | - | - | - | - |
| `replace` | - | - | - | - |
| `list` | - | - | - | - |
| `_iter_structural_headings` | `markdown: str` | - | - | - |
| `splitlines` | - | - | - | - |
| `_frontmatter_extent` | `lines: list[str]` | - | - | `0`, `0`, `...`, `len(...)` |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| parse_markdown_document | isinstance | 325 | `isinstance(markdown, str)` |
| parse_markdown_document | TypeError | 326 | `TypeError('markdown must be a string')` |
| parse_markdown_document | isinstance | 327 | `isinstance(page_locator, str)` |
| parse_markdown_document | ValueError | 328 | `ValueError('page_locator must be a non-empty string')` |
| parse_markdown_document | normalize_markdown | 330 | `normalize_markdown(markdown)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n')` |
| parse_markdown_document | list | 331 | `list(_iter_structural_headings(...))` |
| parse_markdown_document | _iter_structural_headings | 331 | `_iter_structural_headings(normalized)` |
| _iter_structural_headings | splitlines | 251 | `markdown.splitlines(keepends=True)` |
| _iter_structural_headings | _frontmatter_extent | 252 | `_frontmatter_extent(lines)` |

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
| unresolved_call | `parse_markdown_document` | `isinstance` | 325 |
| unresolved_call | `parse_markdown_document` | `TypeError` | 326 |
| unresolved_call | `parse_markdown_document` | `isinstance` | 327 |
| unresolved_call | `parse_markdown_document` | `ValueError` | 328 |
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| external_call | `normalize_markdown` | `text.replace` | 81 |
| unresolved_call | `_iter_structural_headings` | `markdown.splitlines` | 251 |
| step_limit | `parse_markdown_document` | `first 12 steps` | 0 |

## Behavior

This flow starts at `parse_markdown_document` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
