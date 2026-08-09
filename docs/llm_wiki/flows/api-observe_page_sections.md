# observe_page_sections

**Entry point:** `observe_page_sections` (`api`)
**Source:** [section_ownership](../modules/section_ownership.md)
**Modules touched:** [knowledge_evidence](../modules/knowledge_evidence.md), [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md), [wiki_surface](../modules/wiki_surface.md)

## Call sequence

<!-- Auto-generated from static call edges. Dashed arrows are external or unresolved calls. Reviewed runtime conditions and side effects belong in Behavior. -->
```mermaid
sequenceDiagram
    participant p0 as observe_page_sections
    participant p1 as _coerce_page_kind
    participant p2 as isinstance
    participant p3 as PageKind
    participant p4 as ValueError
    participant p5 as parse_markdown_document
    participant p6 as TypeError
    participant p7 as normalize_markdown
    participant p8 as replace
    participant p9 as list
    participant p10 as _iter_structural_headings
    participant p11 as splitlines
    participant p12 as _frontmatter_extent
    participant p13 as strip
    participant p14 as removeprefix
    participant p15 as _line_content
    participant p16 as endswith
    participant p17 as enumerate
    participant p18 as len
    participant p19 as fullmatch
    participant p20 as escape
    p0->>p1: _coerce_page_kind
    p1-->>p2: isinstance
    p1->>p3: PageKind
    p1-->>p4: ValueError
    p0->>p5: parse_markdown_document
    p5-->>p2: isinstance
    p5-->>p6: TypeError
    p5-->>p2: isinstance
    p5-->>p4: ValueError
    p5->>p7: normalize_markdown
    p7-->>p8: replace
    p7-->>p8: replace
    p5-->>p9: list
    p5->>p10: _iter_structural_headings
    p10-->>p11: splitlines
    p10->>p12: _frontmatter_extent
    p12-->>p13: strip
    p12-->>p14: removeprefix
    p12->>p15: _line_content
    p15-->>p16: endswith
    p12-->>p17: enumerate
    p12-->>p13: strip
    p12->>p15: _line_content
    p12-->>p18: len
    p10-->>p17: enumerate
    p10->>p15: _line_content
    p10-->>p18: len
    p10-->>p19: fullmatch
    p10-->>p20: escape
    p10-->>p19: fullmatch
```

> Call sequence diagram shows 30 of 174 interactions; 144 omitted to keep the visualization within the 30-interaction and generated-diagram limits.

## Data flow

<!-- Auto-generated static analysis. Treat values and boundaries as best-effort hints, not runtime proof. -->
```mermaid
flowchart LR
    s1["1. observe_page_sections"]
    s2["2. _coerce_page_kind"]
    s3["3. isinstance"]
    s4["4. PageKind"]
    s5["5. ValueError"]
    s6["6. parse_markdown_document"]
    s7["7. isinstance"]
    s8["8. TypeError"]
    s9["9. isinstance"]
    s10["10. ValueError"]
    s11["11. normalize_markdown"]
    s12["12. replace"]
    s1 -->|"_coerce_page_kind(page_kind)"| s2
    s2 -. "isinstance(page_kind, PageKind)" .-> s3
    s2 -->|"PageKind(page_kind)"| s4
    s2 -. "ValueError(...)" .-> s5
    s1 -->|"parse_markdown_document(markdown, page_locator)"| s6
    s6 -. "isinstance(markdown, str)" .-> s7
    s6 -. "TypeError('markdown must be a string')" .-> s8
    s6 -. "isinstance(page_locator, str)" .-> s9
    s6 -. "ValueError('page_locator must be a non-empty string')" .-> s10
    s6 -->|"normalize_markdown(markdown)"| s11
    s11 -. "text.replace('\r\n', '\n').replace('\r', '\n')" .-> s12
    b0["mutation observations.append"]
    s1 -. "mutation observations.append" .-> b0
    b1["mutation stack.pop"]
    s6 -. "mutation stack.pop" .-> b1
    b2["mutation candidates.append"]
    s6 -. "mutation candidates.append" .-> b2
    b3["mutation stack.append"]
    s6 -. "mutation stack.append" .-> b3
    b4["mutation utf8_prefix_lengths.append"]
    s6 -. "mutation utf8_prefix_lengths.append" .-> b4
    b5["mutation sections.append"]
    s6 -. "mutation sections.append" .-> b5
    click s1 "../modules/section_ownership.md"
    click s2 "../modules/section_ownership.md"
    click s4 "../modules/wiki_surface.md"
    click s6 "../modules/markdown_sections.md"
    click s11 "../modules/markdown_sections.md"
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
| `observe_page_sections` | `markdown: str`, `page_locator: str`, `page_kind: PageKind \| str`, `index_preserved: bool` | - | `canonical_occurrences[...]`, `ownership_by_locator[...]` | `PageSectionObservations(...)` |
| `_coerce_page_kind` | `page_kind: PageKind \| str` | `PageKind` | - | `page_kind`, `PageKind(...)` |
| `isinstance` | - | - | - | - |
| `PageKind` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `parse_markdown_document` | `markdown: str`, `page_locator: str` | `SECTION_ORDER_DOMAIN` | `occurrences[...]` | `MarkdownSectionDocument(...)` |
| `isinstance` | - | - | - | - |
| `TypeError` | - | - | - | - |
| `isinstance` | - | - | - | - |
| `ValueError` | - | - | - | - |
| `normalize_markdown` | `text: str` | - | - | `...` |
| `replace` | - | - | - | - |

### Call data

| From | To | Line | Call |
|---|---|---:|---|
| observe_page_sections | _coerce_page_kind | 543 | `_coerce_page_kind(page_kind)` |
| _coerce_page_kind | isinstance | 266 | `isinstance(page_kind, PageKind)` |
| _coerce_page_kind | PageKind | 269 | `PageKind(page_kind)` |
| _coerce_page_kind | ValueError | 271 | `ValueError(...)` |
| observe_page_sections | parse_markdown_document | 544 | `parse_markdown_document(markdown, page_locator)` |
| parse_markdown_document | isinstance | 325 | `isinstance(markdown, str)` |
| parse_markdown_document | TypeError | 326 | `TypeError('markdown must be a string')` |
| parse_markdown_document | isinstance | 327 | `isinstance(page_locator, str)` |
| parse_markdown_document | ValueError | 328 | `ValueError('page_locator must be a non-empty string')` |
| parse_markdown_document | normalize_markdown | 330 | `normalize_markdown(markdown)` |
| normalize_markdown | replace | 81 | `text.replace('\r\n', '\n').replace('\r', '\n')` |

### Boundary effects

| Kind | Target | Step | Line |
|---|---|---|---:|
| mutation | `observations.append` | `observe_page_sections` | 575 |
| mutation | `stack.pop` | `parse_markdown_document` | 338 |
| mutation | `candidates.append` | `parse_markdown_document` | 350 |
| mutation | `stack.append` | `parse_markdown_document` | 362 |
| mutation | `utf8_prefix_lengths.append` | `parse_markdown_document` | 366 |
| mutation | `sections.append` | `parse_markdown_document` | 393 |

### Static analysis gaps

| Kind | Step | Target | Line |
|---|---|---|---:|
| unresolved_call | `_coerce_page_kind` | `isinstance` | 266 |
| unresolved_call | `_coerce_page_kind` | `ValueError` | 271 |
| unresolved_call | `parse_markdown_document` | `isinstance` | 325 |
| unresolved_call | `parse_markdown_document` | `TypeError` | 326 |
| unresolved_call | `parse_markdown_document` | `isinstance` | 327 |
| unresolved_call | `parse_markdown_document` | `ValueError` | 328 |
| external_call | `normalize_markdown` | `text.replace('\r\n', '\n').replace` | 81 |
| step_limit | `observe_page_sections` | `first 12 steps` | 0 |

## Behavior

This flow starts at `observe_page_sections` and is classified as `api`. The generated call and data-flow sections are bounded static projections; runtime conditions and side effects require source-level confirmation.
